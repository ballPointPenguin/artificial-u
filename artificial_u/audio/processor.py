"""
Audio processor using ElevenLabs API for ArtificialU.
This implementation adds support for custom voice creation, management, and more
advanced text processing for lecture content.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import tempfile

# Import from ElevenLabs Python SDK
from elevenlabs import Voice, VoiceSettings, VoiceDesign
from elevenlabs import clone, generate, save, voices, set_api_key
from elevenlabs.api import History, User

from artificial_u.models.core import Professor, Lecture


class AudioProcessor:
    """
    Creates audio content from lectures using the ElevenLabs API with enhanced
    voice customization for professor personas.
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
        set_api_key(self.api_key)

        # Cache for voices to avoid repeated API calls
        self.voice_cache = {}

    def process_stage_directions(self, text: str) -> str:
        """
        Process stage directions in the lecture text to enhance the audio output.

        This implementation:
        1. Converts stage directions to pauses and tone adjustments
        2. Adds SSML markup for improved speech quality

        Args:
            text: Lecture text with stage directions in [brackets]

        Returns:
            str: Text prepared for text-to-speech conversion with enhanced markup
        """
        # Extract stage directions for potential use in voice modulation
        stage_directions = re.findall(r"\[\s*(.+?)\s*\]", text)

        # Replace stage directions with appropriate pauses or SSML
        processed_text = text

        # Replace common stage directions with pauses and tone adjustments
        replacements = [
            # Pauses for various actions
            (r"\[\s*pauses\s*\]", '<break time="1s"/>'),
            (r"\[\s*long pause\s*\]", '<break time="2s"/>'),
            (r"\[\s*brief pause\s*\]", '<break time="0.5s"/>'),
            # Speaking styles
            (r"\[\s*whispers\s*\]", '<prosody volume="soft">'),
            (r"\[\s*speaks softly\s*\]", '<prosody volume="soft">'),
            (r"\[\s*speaks loudly\s*\]", '<prosody volume="loud">'),
            (r"\[\s*excitedly\s*\]", '<prosody rate="fast" pitch="high">'),
            (r"\[\s*dramatically\s*\]", '<prosody pitch="low" rate="slow">'),
            # End markers for speaking styles
            (r"\[\s*resumes normal tone\s*\]", "</prosody>"),
            (r"\[\s*normal voice\s*\]", "</prosody>"),
            # Remove other stage directions
            (r"\[\s*.*?\s*\]", ""),
        ]

        for pattern, replacement in replacements:
            processed_text = re.sub(
                pattern, replacement, processed_text, flags=re.IGNORECASE
            )

        # For ElevenLabs specifically, we can also use their emotional markup
        # Add emotional context cues based on stage directions
        for direction in stage_directions:
            if any(
                emotion in direction.lower()
                for emotion in ["excited", "enthusiastic", "animated"]
            ):
                # Find the sentence after this stage direction and add emotional context
                sentence_after = re.search(
                    r"\[" + re.escape(direction) + r"\]\s*([^.!?]+[.!?])", text
                )
                if sentence_after:
                    original = sentence_after.group(1)
                    modified = f"{original} [excited]"
                    processed_text = processed_text.replace(original, modified)

            elif any(
                emotion in direction.lower()
                for emotion in ["serious", "grave", "solemn"]
            ):
                sentence_after = re.search(
                    r"\[" + re.escape(direction) + r"\]\s*([^.!?]+[.!?])", text
                )
                if sentence_after:
                    original = sentence_after.group(1)
                    modified = f"{original} [serious]"
                    processed_text = processed_text.replace(original, modified)

        return processed_text

    def create_professor_voice(
        self,
        professor: Professor,
        sample_texts: Optional[List[str]] = None,
        voice_name: Optional[str] = None,
    ) -> str:
        """
        Create a custom voice for a professor based on their characteristics.

        Args:
            professor: Professor profile to create voice for
            sample_texts: Optional list of sample texts in the professor's style
                          If provided, will be used to generate voice samples
            voice_name: Optional name for the voice, defaults to professor name

        Returns:
            str: Voice ID of the created or selected voice
        """
        # If professor already has a voice ID, use it
        if professor.voice_settings and "voice_id" in professor.voice_settings:
            voice_id = professor.voice_settings["voice_id"]

            # Verify the voice still exists in ElevenLabs
            available_voices = voices()
            if any(v.voice_id == voice_id for v in available_voices):
                return voice_id

        # Set voice name
        if not voice_name:
            voice_name = f"Prof. {professor.name.split()[-1]}"

        # If we have sample texts, we can create a custom voice
        if sample_texts and len(sample_texts) > 0:
            # For a real custom voice, we would need audio samples
            # But for now, let's design a voice based on professor characteristics

            # Select voice characteristics based on professor attributes
            gender = self._determine_gender(professor)
            age = self._determine_age(professor)
            accent = self._determine_accent(professor)

            voice_description = (
                f"Academic professor with a {accent} accent. "
                f"{gender}, {age}. {professor.personality}. "
                f"Teaching style: {professor.teaching_style}"
            )

            # In a real implementation, you would use the voice cloning API
            # For now, we'll select a pre-made voice that best matches
            voice_id = self._select_best_matching_voice(gender, age, accent)

            # Store voice settings
            professor.voice_settings = {
                "voice_id": voice_id,
                "stability": 0.75,  # Higher stability for more consistent professor voice
                "similarity_boost": 0.75,  # Higher clarity for lecture delivery
                "style": 0.5,  # Moderate expressiveness suitable for lectures
                "description": voice_description,
            }

            return voice_id

    def _determine_gender(self, professor: Professor) -> str:
        """Determine gender from professor attributes for voice selection."""
        background = professor.background.lower()
        name = professor.name.lower()

        if "she" in background or "her" in background:
            return "Female"
        elif "he" in background or "his" in background:
            return "Male"
        # Try to infer from name and title
        elif "mrs" in name or "ms" in name or "miss" in name:
            return "Female"
        elif "mr" in name:
            return "Male"
        else:
            # Default to male for traditional academic settings
            # (This is a simplification - in a real app, you'd want a better default)
            return "Male"

    def _determine_age(self, professor: Professor) -> str:
        """Determine approximate age range from professor attributes."""
        background = professor.background.lower()

        # Look for explicit age mentions
        age_match = re.search(r"(\d+)[- ]year[s]?[- ]old", background)
        if age_match:
            age = int(age_match.group(1))
            if age < 35:
                return "Young adult"
            elif age < 50:
                return "Middle-aged"
            else:
                return "Senior"

        # Look for keywords
        if any(
            word in background for word in ["young", "recent", "junior", "early career"]
        ):
            return "Young adult"
        elif any(
            word in background
            for word in ["senior", "veteran", "emeritus", "distinguished"]
        ):
            return "Senior"
        else:
            return "Middle-aged"  # Default

    def _determine_accent(self, professor: Professor) -> str:
        """Determine accent from professor background."""
        background = professor.background.lower()

        # Check for nationality/region mentions
        accent_mappings = {
            "british": "British",
            "uk": "British",
            "england": "British",
            "american": "American",
            "united states": "American",
            "usa": "American",
            "australian": "Australian",
            "indian": "Indian",
            "south asia": "Indian",
            "russian": "Eastern European",
            "east europe": "Eastern European",
            "french": "French",
            "german": "German",
            "spanish": "Spanish",
            "italian": "Italian",
            "japanese": "Japanese",
            "chinese": "Chinese",
        }

        for keyword, accent in accent_mappings.items():
            if keyword in background:
                return accent

        return "American"  # Default accent

    def _select_best_matching_voice(self, gender: str, age: str, accent: str) -> str:
        """
        Select the best matching voice from available ElevenLabs voices.

        In a production app, you would maintain a mapping of voice characteristics
        to voice IDs, or use the ElevenLabs API to filter voices by labels.

        This is a simplified implementation using a predefined mapping.
        """
        # Mapping of characteristics to ElevenLabs voice IDs
        voice_mapping = {
            # Male voices
            ("Male", "Young adult", "American"): "pNInz6obpgDQGcFmaJgB",  # Adam
            ("Male", "Middle-aged", "American"): "ErXwobaYiN019PkySvjV",  # Antoni
            ("Male", "Senior", "American"): "VR6AewLTigWG4xSOukaG",  # Arnold
            ("Male", "Middle-aged", "British"): "ODq5zmih8GrVes37Dizd",  # Daniel
            ("Male", "Middle-aged", "Eastern European"): "TxGEqnHWrfWFTfGW9XjX",  # Josh
            # Female voices
            ("Female", "Young adult", "American"): "MF3mGyEYCl7XYWbV9V6O",  # Elli
            ("Female", "Middle-aged", "American"): "EXAVITQu4vr4xnSDxMaL",  # Bella
            ("Female", "Senior", "American"): "jsCqWAovK2LkecY7zXl4",  # Dorothy
            ("Female", "Middle-aged", "British"): "XB0fDUnXU5powFXDhCwa",  # Grace
            ("Female", "Young adult", "British"): "GB7d8Zw2ZQWeXV3xSzjG",  # Nicole
            ("Female", "Middle-aged", "Indian"): "t0jbNlBVZ17f02VDIeMI",  # Domi
        }

        # Try to find exact match
        if (gender, age, accent) in voice_mapping:
            return voice_mapping[(gender, age, accent)]

        # Try to find match with same gender and age
        for (g, a, acc), voice_id in voice_mapping.items():
            if g == gender and a == age:
                return voice_id

        # Fall back to gender match
        for (g, a, acc), voice_id in voice_mapping.items():
            if g == gender:
                return voice_id

        # Ultimate fallback - a default voice
        return "ErXwobaYiN019PkySvjV"  # Antoni

    def get_voice_for_professor(self, professor: Professor) -> Voice:
        """
        Get or create an appropriate voice for a professor.

        Args:
            professor: Professor profile

        Returns:
            Voice: ElevenLabs voice object
        """
        # Check cache first to avoid repeated API calls
        if professor.id and professor.id in self.voice_cache:
            return self.voice_cache[professor.id]

        # If professor has voice settings with a voice ID, use that
        if professor.voice_settings and "voice_id" in professor.voice_settings:
            voice_id = professor.voice_settings["voice_id"]

            # Try to get voice from ElevenLabs
            try:
                available_voices = voices()
                matching_voices = [
                    v for v in available_voices if v.voice_id == voice_id
                ]

                if matching_voices:
                    voice = matching_voices[0]
                    # Update with custom settings if available
                    if (
                        "stability" in professor.voice_settings
                        or "similarity_boost" in professor.voice_settings
                    ):
                        voice.settings = VoiceSettings(
                            stability=professor.voice_settings.get("stability", 0.5),
                            similarity_boost=professor.voice_settings.get(
                                "similarity_boost", 0.75
                            ),
                            style=professor.voice_settings.get("style", 0.5),
                            use_speaker_boost=True,
                        )

                    # Cache for future use
                    if professor.id:
                        self.voice_cache[professor.id] = voice

                    return voice
            except Exception as e:
                print(f"Error retrieving voice: {e}")
                # Continue to fallback options

        # If no voice ID or voice not found, create a new voice or select appropriate default
        voice_id = self.create_professor_voice(professor)

        # Use the selected/created voice
        voice = Voice(
            voice_id=voice_id,
            settings=VoiceSettings(
                stability=professor.voice_settings.get("stability", 0.5),
                similarity_boost=professor.voice_settings.get("similarity_boost", 0.75),
                style=professor.voice_settings.get("style", 0.5),
                use_speaker_boost=True,
            ),
        )

        # Cache for future use
        if professor.id:
            self.voice_cache[professor.id] = voice

        return voice

    def split_lecture_into_chunks(
        self, text: str, max_chunk_size: int = 4000
    ) -> List[str]:
        """
        Split a long lecture into smaller chunks for processing.

        ElevenLabs has a limit on text length, so we need to split longer lectures.
        This method tries to split at logical points like paragraph breaks.

        Args:
            text: The lecture text to split
            max_chunk_size: Maximum characters per chunk

        Returns:
            List[str]: List of text chunks
        """
        # If text is short enough, return as is
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split text into paragraphs
        paragraphs = re.split(r"\n\s*\n", text)

        for paragraph in paragraphs:
            # If adding this paragraph would exceed the chunk size and we already have content,
            # save the current chunk and start a new one
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # Add a line break if this isn't the first content in the chunk
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

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
        # Process text to enhance stage directions
        processed_text = self.process_stage_directions(lecture.content)

        # Get appropriate voice
        voice = self.get_voice_for_professor(professor)

        # Split into manageable chunks if needed
        chunks = self.split_lecture_into_chunks(processed_text)

        # Generate audio for each chunk
        audio_segments = []
        for chunk in chunks:
            # Generate audio with appropriate settings
            audio_segment = generate(
                text=chunk,
                voice=voice,
                model="eleven_multilingual_v2",  # Use best available model
                # Optional advanced settings for lecture-appropriate speech
                voice_settings=voice.settings,
            )
            audio_segments.append(audio_segment)

        # Combine audio segments (if more than one)
        if len(audio_segments) > 1:
            # In a full implementation, you would use a library like pydub
            # to concatenate the audio segments. For now, we'll use a simple approach.
            audio = b"".join(audio_segments)
        else:
            audio = audio_segments[0]

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

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs.

        Returns:
            List[Dict[str, Any]]: List of voice information dictionaries
        """
        try:
            available_voices = voices()
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": (
                        "custom"
                        if hasattr(voice, "category") and voice.category == "cloned"
                        else "premade"
                    ),
                    "description": getattr(voice, "description", ""),
                }
                for voice in available_voices
            ]
        except Exception as e:
            print(f"Error retrieving voices: {e}")
            return []

    def get_user_subscription_info(self) -> Dict[str, Any]:
        """
        Get information about the current user's subscription.

        Returns:
            Dict[str, Any]: Subscription information
        """
        try:
            user = User.from_api()
            return {
                "subscription": user.subscription,
                "character_limit": user.subscription.character_limit,
                "character_count": user.subscription.character_count,
                "available_characters": user.subscription.character_limit
                - user.subscription.character_count,
                "can_extend_character_limit": user.subscription.can_extend_character_limit,
                "next_character_count_reset_unix": user.subscription.next_character_count_reset_unix,
                "voice_limit": user.subscription.voice_limit,
                "voice_count": user.subscription.voice_count,
            }
        except Exception as e:
            print(f"Error retrieving subscription info: {e}")
            return {}
