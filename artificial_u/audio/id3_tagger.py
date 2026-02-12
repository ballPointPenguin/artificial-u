"""
ID3 metadata tagging for lecture audio files.

This module provides functionality to add ID3v2 metadata tags to MP3 files,
making them more organized and informative when played in media players.
"""

import io
import logging
from datetime import datetime
from typing import Optional

from mutagen.id3 import COMM, TALB, TCON, TDRC, TIT2, TPE1, TRCK
from mutagen.mp3 import MP3


class ID3Tagger:
    """Service for adding ID3 metadata tags to MP3 audio files."""

    ARTIST = "Artificial-U"
    GENRE = "Spoken Word"

    def __init__(self, logger=None):
        """
        Initialize the ID3 tagger.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def get_duration_seconds(self, audio_bytes: bytes) -> Optional[int]:
        """
        Get the duration of an MP3 audio file in whole seconds.

        Args:
            audio_bytes: Raw MP3 audio data

        Returns:
            int: Duration in seconds, or None if duration cannot be determined
        """
        if not audio_bytes:
            return None

        try:
            audio = MP3(io.BytesIO(audio_bytes))
            if audio.info and audio.info.length:
                return int(audio.info.length)
            return None
        except Exception as e:
            self.logger.warning(f"Failed to read audio duration: {e}")
            return None

    def add_tags_to_audio(
        self,
        audio_bytes: bytes,
        title: str,
        album: str,
        track_number: int,
        year: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> bytes:
        """
        Add ID3v2 tags to MP3 audio bytes.

        Args:
            audio_bytes: Raw MP3 audio data
            title: Track title (lecture title)
            album: Album name (course name)
            track_number: Track number (sequential lecture number in course)
            year: Publication year (defaults to current year)
            comment: Optional comment field

        Returns:
            bytes: MP3 audio data with ID3 tags added

        Raises:
            Exception: If tagging fails
        """
        if not audio_bytes:
            raise ValueError("audio_bytes cannot be empty")

        if not title:
            raise ValueError("title is required")

        if not album:
            raise ValueError("album is required")

        if track_number < 1:
            raise ValueError("track_number must be >= 1")

        try:
            # Create a file-like object from bytes
            # IMPORTANT: We must save back to the SAME BytesIO object for mutagen to work correctly
            audio_file = io.BytesIO(audio_bytes)

            # Load the MP3 file
            audio = MP3(audio_file)

            # Add ID3 tags if they don't exist
            if audio.tags is None:
                audio.add_tags()

            # Set standard tags
            audio.tags.add(TIT2(encoding=3, text=title))  # Title
            audio.tags.add(TPE1(encoding=3, text=self.ARTIST))  # Artist
            audio.tags.add(TALB(encoding=3, text=album))  # Album
            audio.tags.add(TCON(encoding=3, text=self.GENRE))  # Genre
            audio.tags.add(TRCK(encoding=3, text=str(track_number)))  # Track number

            # Set year (default to current year if not provided)
            if year is None:
                year = datetime.now().year
            audio.tags.add(TDRC(encoding=3, text=str(year)))  # Recording date

            # Add comment if provided
            if comment:
                audio.tags.add(COMM(encoding=3, lang="eng", desc="", text=comment))  # Comment

            # Save tags back to the SAME BytesIO object
            # Mutagen's save() modifies the file in-place, so we must use the same BytesIO
            audio.save(audio_file)

            # Get the bytes with tags
            audio_file.seek(0)
            tagged_bytes = audio_file.read()

            self.logger.info(
                f"Successfully added ID3 tags to audio: title='{title}', "
                f"album='{album}', track={track_number}"
            )

            return tagged_bytes

        except Exception as e:
            self.logger.error(f"Failed to add ID3 tags to audio: {e}", exc_info=True)
            raise

    def calculate_track_number(
        self,
        topic_week: int,
        topic_order: int,
        course_id: int,
        repository_factory=None,
    ) -> int:
        """
        Calculate sequential track number for a lecture based on its position in the course.

        Track numbers are calculated sequentially across all weeks. For example:
        - Week 1, Lecture 1 -> Track 1
        - Week 1, Lecture 2 -> Track 2
        - Week 2, Lecture 1 -> Track 3
        - etc.

        Args:
            topic_week: Week number of the topic
            topic_order: Order/position of the lecture within the topic
            course_id: Course ID to query all topics
            repository_factory: Repository factory to access database (optional)

        Returns:
            int: Sequential track number starting from 1

        Raises:
            ValueError: If repository_factory is not provided
        """
        if repository_factory is None:
            # If we don't have access to the repository, use a simple calculation
            # This is a fallback and may not be accurate for courses with varying
            # numbers of lectures per week
            self.logger.warning(
                "Calculating track number without repository access - "
                "using simplified calculation"
            )
            # Assume 3 lectures per week as a default
            return ((topic_week - 1) * 3) + topic_order

        try:
            # Get all topics for the course, ordered by week and order
            topics = repository_factory.topic.list_by_course(course_id)

            # Sort topics by week, then by order
            sorted_topics = sorted(topics, key=lambda t: (t.week, t.order))

            # Count lectures before this topic
            track_number = 0
            for topic in sorted_topics:
                if topic.week < topic_week:
                    # All lectures from earlier weeks
                    lectures = repository_factory.lecture.list_by_topic(topic.id)
                    track_number += len(lectures) if lectures else 1  # Assume at least 1
                elif topic.week == topic_week and topic.order < topic_order:
                    # Lectures from earlier in the same week
                    lectures = repository_factory.lecture.list_by_topic(topic.id)
                    track_number += len(lectures) if lectures else 1  # Assume at least 1

            # Add the current lecture's order within its topic
            track_number += topic_order

            self.logger.debug(
                f"Calculated track number {track_number} for "
                f"week {topic_week}, order {topic_order}"
            )

            return track_number

        except Exception as e:
            self.logger.error(f"Error calculating track number: {e}", exc_info=True)
            # Fallback to simple calculation
            return ((topic_week - 1) * 3) + topic_order

    def generate_comment(
        self,
        model_name: Optional[str] = None,
        include_elevenlabs: bool = True,
    ) -> str:
        """
        Generate a comment string for the ID3 tag.

        Args:
            model_name: Name of the AI model used for generation
            include_elevenlabs: Whether to mention ElevenLabs voice synthesis

        Returns:
            str: Comment text for ID3 tag
        """
        parts = []

        if model_name:
            parts.append(f"Generated by {model_name}")

        if include_elevenlabs:
            synthesis_text = "ElevenLabs voice synthesis"
            if parts:
                parts.append(f"with {synthesis_text}")
            else:
                parts.append(f"Generated with {synthesis_text}")

        return " ".join(parts) if parts else ""
