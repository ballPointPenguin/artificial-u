"""
Course purge service for ArtificialU.

Deletes a course together with its lectures, topics and stored assets. The plain
course delete refuses to remove a course that still has lectures (FK constraint),
so this is the admin path for removing an unwanted copy, e.g. before re-importing.
Professors, departments and voices are shared records and are never deleted here.
"""

import json
import logging
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.storage_service import StorageService
from artificial_u.utils import CourseNotFoundError

StorageKey = Tuple[str, str]


class CoursePurgeService:
    """Service for hard-deleting a course and everything that belongs to it."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        storage_service: StorageService,
        logger=None,
    ):
        self.repository_factory = repository_factory
        self.storage_service = storage_service
        self.logger = logger or logging.getLogger(__name__)

    async def purge_course(
        self, course_id: int, keep_keys: Optional[Iterable[StorageKey]] = None
    ) -> Dict[str, Any]:
        """
        Delete a course, its lectures, topics, and stored assets.

        Args:
            course_id: Course to delete
            keep_keys: (bucket, key) pairs that must not be deleted from storage,
                e.g. assets just written for a replacement course that reuse the
                same object keys.

        Returns:
            Counts of deleted rows and storage objects

        Raises:
            CourseNotFoundError: If the course doesn't exist
        """
        repos = self.repository_factory
        course = repos.course.get(course_id)
        if not course:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")

        lectures = repos.lecture.list_by_course(course_id)
        asset_keys = await self._collect_asset_keys(course, lectures)
        asset_keys -= set(keep_keys or [])

        lectures_deleted = repos.lecture.delete_by_course(course_id)
        topics_deleted = repos.topic.delete_by_course(course_id)
        repos.course.delete(course_id)
        self.logger.info(
            f"Purged course {course_id} ({course.code}): "
            f"{lectures_deleted} lectures, {topics_deleted} topics"
        )

        assets_deleted = 0
        for bucket, key in sorted(asset_keys):
            if await self.storage_service.delete_file(bucket, key):
                assets_deleted += 1

        return {
            "course_id": course_id,
            "course_code": course.code,
            "lectures_deleted": lectures_deleted,
            "topics_deleted": topics_deleted,
            "assets_deleted": assets_deleted,
        }

    async def _collect_asset_keys(self, course: Any, lectures: Iterable[Any]) -> Set[StorageKey]:
        """Gather (bucket, key) for every stored asset the course owns."""
        keys: Set[StorageKey] = set()

        def add(url: Optional[str]) -> None:
            bucket, key = self.storage_service.parse_storage_url(url) if url else (None, None)
            if bucket and key:
                keys.add((bucket, key))

        add(course.image_url)
        for lecture in lectures:
            add(lecture.audio_url)
            add(lecture.transcript_url)
            add(lecture.timeline_url)
            add(lecture.images_timeline_url)
            for slide_url in await self._slide_urls(lecture.images_timeline_url):
                add(slide_url)
        return keys

    async def _slide_urls(self, images_timeline_url: Optional[str]) -> Set[str]:
        if not images_timeline_url:
            return set()
        bucket, key = self.storage_service.parse_storage_url(images_timeline_url)
        if not bucket or not key:
            return set()
        data, _ = await self.storage_service.download_file(bucket, key)
        if not data:
            return set()
        try:
            timeline = json.loads(data.decode("utf-8"))
        except ValueError:
            return set()
        return {s["url"] for s in timeline.get("slots") or [] if s.get("url")}
