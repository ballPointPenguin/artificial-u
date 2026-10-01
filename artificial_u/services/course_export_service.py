"""
Course export service for ArtificialU.

This service handles exporting a complete course with all related data and assets
into a compressed zip archive suitable for importing into another instance.
The archive layout is documented in ``course_bundle``.
"""

import io
import json
import logging
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.models.core import (
    Course,
    Department,
    Faculty,
    Lecture,
    Professor,
    Topic,
    Voice,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import course_bundle as bundle
from artificial_u.services.storage_service import StorageService
from artificial_u.utils import CourseNotFoundError


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


class CourseExportService:
    """Service for exporting courses with all related data and assets."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        storage_service: StorageService,
        logger=None,
    ):
        """
        Initialize the course export service.

        Args:
            repository_factory: Repository factory instance
            storage_service: Storage service for file operations
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.storage_service = storage_service
        self.logger = logger or logging.getLogger(__name__)

    async def export_course(self, course_id: int) -> Dict[str, Any]:
        """
        Export a complete course with all related data and assets.

        Args:
            course_id: ID of the course to export

        Returns:
            Dict with export metadata (filename, url, size, asset counts, warnings)

        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        self.logger.info(f"Starting export for course {course_id}")

        course_data = await self._fetch_course_data(course_id)

        # Downloads assets and records their archive paths on the serialized records
        files, counts, warnings = await self._collect_assets(course_data)

        zip_data, zip_filename = self._create_zip_archive(course_data, files, counts, warnings)

        success, url = await self.storage_service.upload_export_file(zip_data, zip_filename)
        if not success:
            raise Exception("Failed to upload export archive")

        result = {
            "filename": zip_filename,
            "url": url,
            "size": len(zip_data),
            "course_id": course_id,
            "course_code": course_data["course"]["code"],
            "course_title": course_data["course"]["title"],
            "export_version": bundle.FORMAT_VERSION,
            "exported_at": datetime.now().isoformat(),
            "asset_counts": counts,
            "warnings": warnings,
        }

        self.logger.info(f"Successfully exported course {course_id} to {zip_filename}")
        return result

    async def _fetch_course_data(self, course_id: int) -> Dict[str, Any]:
        """
        Fetch all database entities related to a course.

        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        self.logger.info(f"Fetching course data for course {course_id}")
        repos = self.repository_factory

        course = repos.course.get(course_id)
        if not course:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")

        professor = repos.professor.get(course.professor_id) if course.professor_id else None
        department = repos.department.get(course.department_id) if course.department_id else None
        topics = repos.topic.list_by_course(course_id)
        lectures = repos.lecture.list_by_course(course_id)
        tags = repos.tag.list_for_course(course_id)

        connected_codes: List[str] = []
        for connected_id in course.connected_course_ids or []:
            connected = repos.course.get(connected_id)
            if connected:
                connected_codes.append(connected.code)

        voices: Dict[int, Optional[Voice]] = {}

        def voice_for(voice_id: Optional[int]) -> Optional[Voice]:
            if not voice_id:
                return None
            if voice_id not in voices:
                voices[voice_id] = repos.voice.get(voice_id)
            return voices[voice_id]

        course_dict = self._serialize_course(course)
        course_dict["tags"] = [
            {"name": t.name, "slug": t.slug, "language": t.language} for t in tags
        ]
        course_dict["connected_course_codes"] = sorted(connected_codes)

        return {
            "course": course_dict,
            "professor": self._serialize_professor(
                professor, voice_for(professor.voice_id) if professor else None
            ),
            "department": self._serialize_department(department),
            "topics": [self._serialize_topic(t) for t in topics],
            "lectures": [
                self._serialize_lecture(lecture, voice_for(lecture.voice_id))
                for lecture in lectures
            ],
        }

    async def _collect_assets(  # noqa: C901
        self, course_data: Dict[str, Any]
    ) -> Tuple[Dict[str, bytes], Dict[str, int], List[str]]:
        """
        Download all assets from storage.

        Sets ``record["assets"]`` on the course, professor and lecture records to
        map asset roles to archive paths.

        Returns:
            (files keyed by archive path, counts, warnings)
        """
        self.logger.info("Downloading course assets")
        files: Dict[str, bytes] = {}
        counts = {
            "lectures": len(course_data["lectures"]),
            "topics": len(course_data["topics"]),
            "audio_files": 0,
            "transcripts": 0,
            "timelines": 0,
            "lecture_images": 0,
            "professor_image": 0,
            "course_image": 0,
        }
        warnings: List[str] = []

        async def fetch(url: Optional[str], path: str, label: str) -> bool:
            if not url:
                return False
            data = await self._download_file_from_url(url)
            if not data:
                warnings.append(f"{label}: could not download {url}")
                return False
            files[path] = data
            return True

        course = course_data["course"]
        course["assets"] = {}
        ext = bundle.asset_ext(course.get("image_url"), "png")
        path = bundle.course_image_path(ext)
        if await fetch(course.get("image_url"), path, "Course image"):
            course["assets"]["image"] = path
            counts["course_image"] += 1

        professor = course_data.get("professor")
        if professor:
            professor["assets"] = {}
            ext = bundle.asset_ext(professor.get("image_url"), "png")
            path = bundle.professor_image_path(ext)
            if await fetch(professor.get("image_url"), path, "Professor image"):
                professor["assets"]["image"] = path
                counts["professor_image"] += 1

        for lecture in course_data["lectures"]:
            lid = lecture["id"]
            label = f"Lecture {lid}"
            assets: Dict[str, str] = {}
            lecture["assets"] = assets

            path = bundle.audio_path(lid, bundle.asset_ext(lecture.get("audio_url"), "mp3"))
            if await fetch(lecture.get("audio_url"), path, f"{label} audio"):
                assets["audio"] = path
                counts["audio_files"] += 1

            path = bundle.transcript_path(
                lid, bundle.asset_ext(lecture.get("transcript_url"), "txt")
            )
            if await fetch(lecture.get("transcript_url"), path, f"{label} transcript"):
                assets["transcript"] = path
                counts["transcripts"] += 1

            path = bundle.timeline_path(lid)
            if await fetch(lecture.get("timeline_url"), path, f"{label} timeline"):
                assets["timeline"] = path
                counts["timelines"] += 1

            if lecture.get("images_timeline_url"):
                images_path = await self._collect_lecture_images(
                    lecture, files, counts, warnings, label
                )
                if images_path:
                    assets["images_timeline"] = images_path

        self.logger.info(f"Downloaded {len(files)} asset files")
        return files, counts, warnings

    async def _collect_lecture_images(
        self,
        lecture: Dict[str, Any],
        files: Dict[str, bytes],
        counts: Dict[str, int],
        warnings: List[str],
        label: str,
    ) -> Optional[str]:
        """
        Download a lecture's images timeline and slide images.

        Slide URLs in the timeline are rewritten to archive paths so the timeline
        is portable. Returns the archive path of the rewritten timeline, if any.
        """
        lid = lecture["id"]
        data = await self._download_file_from_url(lecture["images_timeline_url"])
        if not data:
            warnings.append(f"{label} images timeline: could not download")
            return None
        try:
            timeline = json.loads(data.decode("utf-8"))
        except ValueError:
            warnings.append(f"{label} images timeline: invalid JSON, skipped")
            return None

        for fallback_idx, slot in enumerate(timeline.get("slots") or []):
            url = slot.get("url")
            if not url:
                continue
            idx = slot.get("index", fallback_idx)
            path = bundle.lecture_image_path(lid, int(idx), bundle.asset_ext(url, "png"))
            image = await self._download_file_from_url(url)
            if image:
                files[path] = image
                slot["url"] = path
                counts["lecture_images"] += 1
            else:
                warnings.append(f"{label} slide {idx}: could not download {url}")
                slot["url"] = None
                if slot.get("status") == "done":
                    slot["status"] = "pending"

        timeline_path = bundle.images_timeline_path(lid)
        files[timeline_path] = json.dumps(timeline, ensure_ascii=False, indent=2).encode("utf-8")
        return timeline_path

    async def _download_file_from_url(self, url: str) -> Optional[bytes]:
        """Download a file from a storage URL; None if unparseable or missing."""
        bucket, key = self.storage_service.parse_storage_url(url)
        if not bucket or not key:
            self.logger.warning(f"Could not parse storage URL: {url}")
            return None

        file_data, _ = await self.storage_service.download_file(bucket, key)
        return file_data

    def _create_zip_archive(
        self,
        course_data: Dict[str, Any],
        files: Dict[str, bytes],
        counts: Dict[str, int],
        warnings: List[str],
    ) -> Tuple[bytes, str]:
        """Create the zip archive; returns (zip_bytes, filename)."""
        course = course_data["course"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"course_export_{course['code']}_{timestamp}.zip"

        self.logger.info(f"Creating zip archive: {zip_filename}")

        def dump(obj: Any) -> str:
            return json.dumps(obj, indent=2, ensure_ascii=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            manifest = {
                "export_version": bundle.FORMAT_VERSION,
                "exported_at": datetime.now().isoformat(),
                "course_id": course["id"],
                "course_code": course["code"],
                "course_title": course["title"],
                "counts": counts,
                "warnings": warnings,
            }
            zipf.writestr(bundle.MANIFEST_PATH, dump(manifest))
            zipf.writestr(bundle.COURSE_PATH, dump(course))
            if course_data["professor"]:
                zipf.writestr(bundle.PROFESSOR_PATH, dump(course_data["professor"]))
            if course_data["department"]:
                zipf.writestr(bundle.DEPARTMENT_PATH, dump(course_data["department"]))
            zipf.writestr(bundle.TOPICS_PATH, dump(course_data["topics"]))
            zipf.writestr(bundle.LECTURES_PATH, dump(course_data["lectures"]))

            for path, data in files.items():
                zipf.writestr(path, data)

        zip_bytes = zip_buffer.getvalue()
        self.logger.info(f"Created zip archive: {len(zip_bytes)} bytes")
        return zip_bytes, zip_filename

    # Serialization helpers

    def _serialize_course(self, course: Course) -> Dict[str, Any]:
        """Serialize course to dict."""
        return {
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "description": course.description,
            "lectures_per_week": course.lectures_per_week,
            "level": course.level,
            "total_weeks": course.total_weeks,
            "language": course.language,
            "status": course.status,
            "notes": course.notes,
            "image_url": course.image_url,
            "image_created_with": course.image_created_with,
            "department_id": course.department_id,
            "professor_id": course.professor_id,
            "created_by": course.created_by,
            "created_with": course.created_with,
            "created_at": _iso(course.created_at),
            "updated_at": _iso(course.updated_at),
        }

    def _serialize_voice(self, voice: Optional[Voice]) -> Optional[Dict[str, Any]]:
        """Serialize voice metadata (enough to match or recreate it elsewhere)."""
        if not voice:
            return None
        return {
            "tts_backend": voice.tts_backend,
            "external_id": voice.external_id,
            "el_voice_id": voice.el_voice_id,
            "name": voice.name,
            "accent": voice.accent,
            "age": voice.age,
            "category": voice.category,
            "description": voice.description,
            "descriptive": voice.descriptive,
            "gender": voice.gender,
            "language": voice.language,
            "locale": voice.locale,
            "use_case": voice.use_case,
        }

    def _serialize_professor(
        self, professor: Optional[Professor], voice: Optional[Voice] = None
    ) -> Optional[Dict[str, Any]]:
        """Serialize professor to dict, including voice metadata."""
        if not professor:
            return None

        return {
            "id": professor.id,
            "name": professor.name,
            "title": professor.title,
            "accent": professor.accent,
            "age": professor.age,
            "background": professor.background,
            "description": professor.description,
            "gender": professor.gender,
            "personality": professor.personality,
            "specialization": professor.specialization,
            "teaching_style": professor.teaching_style,
            "language": professor.language,
            "tts_backend": professor.tts_backend,
            "image_url": professor.image_url,
            "image_created_with": professor.image_created_with,
            "department_id": professor.department_id,
            "voice_id": professor.voice_id,
            "voice": self._serialize_voice(voice),
            "created_by": professor.created_by,
            "created_with": professor.created_with,
            "created_at": _iso(professor.created_at),
            "updated_at": _iso(professor.updated_at),
        }

    def _serialize_faculty(self, faculty: Optional[Faculty]) -> Optional[Dict[str, Any]]:
        if not faculty:
            return None
        return {
            "name": faculty.name,
            "description": faculty.description,
            "language": faculty.language,
        }

    def _serialize_department(self, department: Optional[Department]) -> Optional[Dict[str, Any]]:
        """Serialize department to dict (with its faculty, if any)."""
        if not department:
            return None

        faculty = None
        if department.faculty_id:
            faculty = self.repository_factory.faculty.get(department.faculty_id)

        return {
            "id": department.id,
            "name": department.name,
            "code": department.code,
            "description": department.description,
            "language": department.language,
            "faculty_id": department.faculty_id,
            "faculty_name": faculty.name if faculty else None,
            "faculty": self._serialize_faculty(faculty),
            "created_at": _iso(department.created_at),
            "updated_at": _iso(department.updated_at),
        }

    def _serialize_topic(self, topic: Topic) -> Dict[str, Any]:
        """Serialize topic to dict."""
        return {
            "id": topic.id,
            "title": topic.title,
            "order": topic.order,
            "week": topic.week,
            "content": topic.content,
            "language": topic.language,
            "course_id": topic.course_id,
            "created_by": topic.created_by,
            "created_with": topic.created_with,
            "created_at": _iso(topic.created_at),
            "updated_at": _iso(topic.updated_at),
        }

    def _serialize_lecture(self, lecture: Lecture, voice: Optional[Voice] = None) -> Dict[str, Any]:
        """Serialize lecture to dict."""
        return {
            "id": lecture.id,
            "revision": lecture.revision,
            "content": lecture.content,
            "summary": lecture.summary,
            "title": lecture.title,
            "language": lecture.language,
            "word_count": lecture.word_count,
            "duration": lecture.duration,
            "audio_url": lecture.audio_url,
            "transcript_url": lecture.transcript_url,
            "timeline_url": lecture.timeline_url,
            "images_timeline_url": lecture.images_timeline_url,
            "course_id": lecture.course_id,
            "topic_id": lecture.topic_id,
            "voice_id": lecture.voice_id,
            "voice": self._serialize_voice(voice),
            "created_by": lecture.created_by,
            "created_with": lecture.created_with,
            "created_at": _iso(lecture.created_at),
            "updated_at": _iso(lecture.updated_at),
        }
