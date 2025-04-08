"""
Audio processing module using ElevenLabs API for text-to-speech conversion.
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
import elevenlabs
from elevenlabs import Voice, VoiceSettings, generate, save

from artificial_u.models.core import Professor, Lecture


class AudioProcessor:
    """
    Creates audio content from lectures using ElevenLabs API.
    """

    def __init__(self, api_key: Optional[str] = None, audio_path: Optional[str] = None):
        """
        Initialize the audio processor.

        Args:
            api_key: ElevenLabs API key. If not provided, will use ELEVENLABS_API_KEY environment variable.
            audio_path: Path to store audio files. If not provided, will use AUDIO_STORAGE_PATH environment
                        variable or default to './audio_files'.
        """
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        self.audio_path = audio_path or os.environ.get(
            "AUDIO_STORAGE_PATH", "./audio_files"
        )
        os.makedirs(self.audio_path, exist_ok=True)

        # Set up ElevenLabs client
        elevenlabs.set_api_key(self.api_key)

    def process_stage_directions(self, text: str) -> str:
        """
        Process stage directions in the lecture text.

        Args:
            text: Lecture text with stage directions in [brackets]

        Returns:
            str: Text prepared for text-to-speech conversion
        """
        # For now, we'll simply remove stage directions as ElevenLabs doesn't natively
        # support interpreting them. In a more advanced implementation, we could:
        # 1. Convert stage directions to SSML for supported voice modulations
        # 2. Use the directions to adjust voice parameters for different segments
        # 3. Create a custom formatting scheme for ElevenLabs

        # Remove stage directions
        clean_text = re.sub(r"\\[.*?\\]", "", text)

        return clean_text

    def get_voice_for_professor(self, professor: Professor) -> Voice:
        """
        Get or create an appropriate voice for a professor.

        Args:
            professor: Professor profile

        Returns:
            Voice: ElevenLabs voice object
        """
        # In a complete implementation, we would:
        # 1. Check if the professor already has a voice ID stored
        # 2. If not, select an appropriate voice based on professor characteristics
        # 3. Customize voice settings to match professor personality

        # For now, we'll use a placeholder approach
        if professor.voice_settings and "voice_id" in professor.voice_settings:
            # Retrieve existing voice
            voice_id = professor.voice_settings["voice_id"]
            # In real implementation, would verify if voice exists in ElevenLabs
            return Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=professor.voice_settings.get("stability", 0.5),
                    similarity_boost=professor.voice_settings.get("clarity", 0.75),
                ),
            )
        else:
            # This is a placeholder. In a real implementation, we would:
            # 1. Analyze professor traits to match to a voice
            # 2. Select an appropriate voice from available ElevenLabs voices
            # 3. Return the selected voice with appropriate settings

            # For example, demographics-based selection (overly simplified):
            default_voices = {
                "male_older": "pNInz6obpgDQGcFmaJgB",  # Adam - older male, authoritative
                "male_middle": "ErXwobaYiN019PkySvjV",  # Antoni - middle-aged male, warm
                "female_middle": "EXAVITQu4vr4xnSDxMaL",  # Bella - middle-aged female, clear
                "female_younger": "MF3mGyEYCl7XYWbV9V6O",  # Elli - younger female, energetic
            }

            # Simplified logic for demo purposes
            gender = (
                "male"
                if "Dr." in professor.name
                and not "female" in professor.personality.lower()
                else "female"
            )
            age = (
                "older"
                if "older" in professor.background.lower()
                or "senior" in professor.title.lower()
                else "middle"
            )
            voice_key = f"{gender}_{age}"

            voice_id = default_voices.get(voice_key, default_voices["male_middle"])

            # In a real implementation, we would store this selection in professor.voice_settings

            return Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
            )

    def text_to_speech(
        self, lecture: Lecture, professor: Professor
    ) -> Tuple[str, bytes]:
        """
        Convert lecture text to speech using an appropriate voice for the professor.

        Args:
            lecture: Lecture to convert
            professor: Professor delivering the lecture

        Returns:
            Tuple[str, bytes]: File path and audio data
        """
        # Process text to remove or adapt stage directions
        processed_text = self.process_stage_directions(lecture.content)

        # Get appropriate voice
        voice = self.get_voice_for_professor(professor)

        # Generate audio
        audio = generate(
            text=processed_text, voice=voice, model="eleven_multilingual_v2"
        )

        # Create file path
        course_dir = Path(self.audio_path) / lecture.course_id
        course_dir.mkdir(parents=True, exist_ok=True)

        week_dir = course_dir / f"week{lecture.week_number}"
        week_dir.mkdir(exist_ok=True)

        file_name = f"lecture{lecture.order_in_week}.mp3"
        file_path = str(week_dir / file_name)

        # Save audio file
        save(audio, file_path)

        return file_path, audio
