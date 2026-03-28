"""
Course export service for ArtificialU.

This service handles exporting a complete course with all related data and assets
into a compressed zip archive suitable for importing into another instance.
"""

import io
import json
import logging
import zipfile
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from artificial_u.models.core import Course, Department, Lecture, Professor, Topic
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.storage_service import StorageService
from artificial_u.utils import CourseNotFoundError


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
            Dict with export metadata (filename, url, size, asset counts)

        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        self.logger.info(f"Starting export for course {course_id}")

        # Fetch all course data
        course_data = await self._fetch_course_data(course_id)

        # Download assets
        assets = await self._download_assets(course_data)

        # Create zip archive
        zip_data, zip_filename = self._create_zip_archive(course_data, assets)

        # Upload to exports bucket
        success, url = await self._upload_export(zip_data, zip_filename)

        if not success:
            raise Exception("Failed to upload export archive")

        # Build result metadata
        result = {
            "filename": zip_filename,
            "url": url,
            "size": len(zip_data),
            "course_id": course_id,
            "course_code": course_data["course"]["code"],
            "course_title": course_data["course"]["title"],
            "exported_at": datetime.now().isoformat(),
            "asset_counts": {
                "lectures": len(course_data["lectures"]),
                "topics": len(course_data["topics"]),
                "audio_files": assets["counts"]["audio"],
                "transcripts": assets["counts"]["transcripts"],
                "professor_image": 1 if assets.get("professor_image") else 0,
            },
        }

        self.logger.info(f"Successfully exported course {course_id} to {zip_filename}")
        return result

    async def _fetch_course_data(self, course_id: int) -> Dict[str, Any]:
        """
        Fetch all database entities related to a course.

        Args:
            course_id: Course ID

        Returns:
            Dict containing course, professor, department, topics, and lectures

        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        self.logger.info(f"Fetching course data for course {course_id}")

        # Get course
        course_repo = self.repository_factory.course
        course = course_repo.get(course_id)
        if not course:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")

        # Get professor
        professor = None
        if course.professor_id:
            professor_repo = self.repository_factory.professor
            professor = professor_repo.get(course.professor_id)

        # Get department
        department = None
        if course.department_id:
            department_repo = self.repository_factory.department
            department = department_repo.get(course.department_id)

        # Get topics
        topic_repo = self.repository_factory.topic
        topics = topic_repo.list_by_course(course_id)

        # Get lectures
        lecture_repo = self.repository_factory.lecture
        lectures = lecture_repo.list_by_course(course_id)

        # Get voice data if professor has a voice
        voice = None
        if professor and professor.voice_id:
            voice_repo = self.repository_factory.voice
            voice = voice_repo.get(professor.voice_id)

        return {
            "course": self._serialize_course(course),
            "professor": self._serialize_professor(professor, voice),
            "department": self._serialize_department(department),
            "topics": [self._serialize_topic(t) for t in topics],
            "lectures": [self._serialize_lecture(lecture) for lecture in lectures],
        }

    async def _download_assets(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download all assets (images, audio, transcripts) from storage.

        Args:
            course_data: Course data dict from _fetch_course_data

        Returns:
            Dict with downloaded assets and counts
        """
        self.logger.info("Downloading course assets")

        assets = {
            "professor_image": None,
            "audio_files": {},  # lecture_id -> bytes
            "transcripts": {},  # lecture_id -> bytes
            "counts": {"audio": 0, "transcripts": 0},
        }

        # Download professor image
        professor = course_data.get("professor")
        if professor and professor.get("image_url"):
            image_data = await self._download_file_from_url(professor["image_url"])
            if image_data:
                assets["professor_image"] = image_data
                self.logger.info("Downloaded professor image")

        # Download lecture audio and transcripts
        for lecture in course_data["lectures"]:
            lecture_id = lecture["id"]

            # Audio file
            if lecture.get("audio_url"):
                audio_data = await self._download_file_from_url(lecture["audio_url"])
                if audio_data:
                    assets["audio_files"][lecture_id] = audio_data
                    assets["counts"]["audio"] += 1

            # Transcript file
            if lecture.get("transcript_url"):
                transcript_data = await self._download_file_from_url(lecture["transcript_url"])
                if transcript_data:
                    assets["transcripts"][lecture_id] = transcript_data
                    assets["counts"]["transcripts"] += 1

        self.logger.info(
            f"Downloaded {assets['counts']['audio']} audio files "
            f"and {assets['counts']['transcripts']} transcripts"
        )
        return assets

    async def _download_file_from_url(self, url: str) -> Optional[bytes]:
        """
        Download a file from storage URL.

        Args:
            url: Storage URL

        Returns:
            File bytes or None if download fails
        """
        bucket, key = self.storage_service.parse_storage_url(url)
        if not bucket or not key:
            self.logger.warning(f"Could not parse storage URL: {url}")
            return None

        file_data, _ = await self.storage_service.download_file(bucket, key)
        return file_data

    def _create_zip_archive(
        self, course_data: Dict[str, Any], assets: Dict[str, Any]
    ) -> Tuple[bytes, str]:
        """
        Create a zip archive with course data and assets.

        Args:
            course_data: Course data dict
            assets: Downloaded assets dict

        Returns:
            Tuple of (zip_bytes, filename)
        """
        course_code = course_data["course"]["code"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"course_export_{course_code}_{timestamp}.zip"

        self.logger.info(f"Creating zip archive: {zip_filename}")

        # Create zip in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add manifest
            manifest = {
                "export_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "course_id": course_data["course"]["id"],
                "course_code": course_code,
                "course_title": course_data["course"]["title"],
            }
            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Add course data as JSON files
            zipf.writestr("course.json", json.dumps(course_data["course"], indent=2))

            if course_data["professor"]:
                zipf.writestr("professor.json", json.dumps(course_data["professor"], indent=2))

            if course_data["department"]:
                zipf.writestr("department.json", json.dumps(course_data["department"], indent=2))

            zipf.writestr("topics.json", json.dumps(course_data["topics"], indent=2))
            zipf.writestr("lectures.json", json.dumps(course_data["lectures"], indent=2))

            # Add assets
            # Professor image
            if assets.get("professor_image"):
                professor = course_data.get("professor", {})
                image_url = professor.get("image_url", "")
                # Get extension from URL or default to png
                ext = "png"
                if "." in image_url:
                    ext = image_url.rsplit(".", 1)[-1].split("?")[0]  # Handle query params
                zipf.writestr(f"assets/professor/image.{ext}", assets["professor_image"])

            # Audio files
            for lecture_id, audio_data in assets["audio_files"].items():
                zipf.writestr(f"assets/audio/lecture_{lecture_id}.mp3", audio_data)

            # Transcript files
            for lecture_id, transcript_data in assets["transcripts"].items():
                zipf.writestr(f"assets/transcripts/lecture_{lecture_id}.txt", transcript_data)

        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        self.logger.info(f"Created zip archive: {len(zip_bytes)} bytes")
        return zip_bytes, zip_filename

    async def _upload_export(self, zip_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Upload the export archive to the exports bucket.

        Args:
            zip_data: Zip file bytes
            filename: Filename for the archive

        Returns:
            Tuple of (success, url)
        """
        self.logger.info(f"Uploading export archive: {filename}")
        return await self.storage_service.upload_export_file(zip_data, filename)

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
            "department_id": course.department_id,
            "professor_id": course.professor_id,
            "created_by": course.created_by,
            "created_with": course.created_with,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        }

    def _serialize_professor(
        self, professor: Optional[Professor], voice: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Serialize professor to dict, including voice metadata."""
        if not professor:
            return None

        prof_dict = {
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
            "image_url": professor.image_url,
            "department_id": professor.department_id,
            "voice_id": professor.voice_id,
            "created_by": professor.created_by,
            "created_with": professor.created_with,
            "created_at": professor.created_at.isoformat() if professor.created_at else None,
            "updated_at": professor.updated_at.isoformat() if professor.updated_at else None,
        }

        # Include voice metadata if available
        if voice:
            prof_dict["voice"] = {
                "el_voice_id": voice.el_voice_id,
                "name": voice.name,
                "accent": voice.accent,
                "age": voice.age,
                "gender": voice.gender,
                "language": voice.language,
                "locale": voice.locale,
            }

        return prof_dict

    def _serialize_department(self, department: Optional[Department]) -> Optional[Dict[str, Any]]:
        """Serialize department to dict."""
        if not department:
            return None

        # Load faculty name if faculty_id is present
        faculty_name = None
        if department.faculty_id:
            faculty = self.repository_factory.faculty.get(department.faculty_id)
            if faculty:
                faculty_name = faculty.name

        return {
            "id": department.id,
            "name": department.name,
            "code": department.code,
            "faculty_id": department.faculty_id,
            "faculty_name": faculty_name,
            "description": department.description,
            "created_at": department.created_at.isoformat() if department.created_at else None,
            "updated_at": department.updated_at.isoformat() if department.updated_at else None,
        }

    def _serialize_topic(self, topic: Topic) -> Dict[str, Any]:
        """Serialize topic to dict."""
        return {
            "id": topic.id,
            "title": topic.title,
            "order": topic.order,
            "week": topic.week,
            "content": topic.content,
            "course_id": topic.course_id,
            "created_by": topic.created_by,
            "created_with": topic.created_with,
            "created_at": topic.created_at.isoformat() if topic.created_at else None,
            "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
        }

    def _serialize_lecture(self, lecture: Lecture) -> Dict[str, Any]:
        """Serialize lecture to dict."""
        return {
            "id": lecture.id,
            "revision": lecture.revision,
            "content": lecture.content,
            "summary": lecture.summary,
            "title": lecture.title,
            "audio_url": lecture.audio_url,
            "transcript_url": lecture.transcript_url,
            "course_id": lecture.course_id,
            "topic_id": lecture.topic_id,
            "created_by": lecture.created_by,
            "created_with": lecture.created_with,
            "created_at": lecture.created_at.isoformat() if lecture.created_at else None,
            "updated_at": lecture.updated_at.isoformat() if lecture.updated_at else None,
        }
