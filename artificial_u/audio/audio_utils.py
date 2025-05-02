"""
Audio utilities for ArtificialU.

This module provides utilities for audio file handling, playback, and management.
"""

import logging
import os
from pathlib import Path
from typing import Optional


class AudioUtils:
    """Utilities for audio file handling and management."""

    def __init__(self, base_audio_path: Optional[str] = None, logger=None):
        """
        Initialize audio utilities.

        Args:
            base_audio_path: Base path for audio files
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Set base audio path
        self.base_audio_path = Path(
            base_audio_path or os.environ.get("AUDIO_PATH", "./audio_files")
        )
        self.base_audio_path.mkdir(parents=True, exist_ok=True)

    def get_lecture_audio_path(
        self,
        course_id: str,
        week_number: int,
        lecture_order: int,
        extension: str = "mp3",
    ) -> str:
        """
        Generate a file path for a lecture audio file.

        Args:
            course_id: Course ID
            week_number: Week number
            lecture_order: Lecture order within week
            extension: File extension (default: mp3)

        Returns:
            Absolute path to the audio file
        """
        # Create directory structure: course/week{n}/
        course_dir = self.base_audio_path / course_id
        course_dir.mkdir(parents=True, exist_ok=True)

        week_dir = course_dir / f"week{week_number}"
        week_dir.mkdir(exist_ok=True)

        # Create filename: lecture{n}.{ext}
        filename = f"lecture{lecture_order}.{extension}"

        return str(week_dir / filename)

    def ensure_directory_exists(self, file_path: str) -> None:
        """
        Ensure that the directory for a file path exists.

        Args:
            file_path: Path to file
        """
        directory = os.path.dirname(file_path)
        Path(directory).mkdir(parents=True, exist_ok=True)

    def get_course_directory(self, course_id: str) -> str:
        """
        Get the directory for a course's audio files.

        Args:
            course_id: Course ID

        Returns:
            Path to course directory
        """
        course_dir = self.base_audio_path / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        return str(course_dir)

    def get_week_directory(self, course_id: str, week_number: int) -> str:
        """
        Get the directory for a week's audio files.

        Args:
            course_id: Course ID
            week_number: Week number

        Returns:
            Path to week directory
        """
        course_dir = self.get_course_directory(course_id)
        week_dir = Path(course_dir) / f"week{week_number}"
        week_dir.mkdir(exist_ok=True)
        return str(week_dir)

    def save_audio_file(self, file_path: str, audio_data: bytes) -> None:
        """
        Save audio data to a file.

        Args:
            file_path: Path to save the file
            audio_data: Audio data as bytes
        """
        try:
            # Ensure directory exists
            self.ensure_directory_exists(file_path)

            # Write audio data to file
            with open(file_path, "wb") as f:
                f.write(audio_data)

            self.logger.info(f"Audio saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving audio file: {e}")
            raise

    def read_audio_file(self, file_path: str) -> bytes:
        """
        Read audio data from a file.

        Args:
            file_path: Path to the audio file

        Returns:
            Audio data as bytes
        """
        try:
            with open(file_path, "rb") as f:
                audio_data = f.read()
            return audio_data
        except Exception as e:
            self.logger.error(f"Error reading audio file: {e}")
            raise
