"""
Audio processor using ElevenLabs API for ArtificialU.
This implementation adds support for custom voice creation, management, and more
advanced text processing for lecture content.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import tempfile
import time

# Import from ElevenLabs Python SDK
from elevenlabs import Voice, VoiceSettings, play
from elevenlabs.client import ElevenLabs
from elevenlabs.api import Voices, User
from elevenlabs.error import APIError, RateLimitError, AuthorizationError

from artificial_u.models.core import Professor, Lecture


class AudioProcessorError(Exception):
    """Base exception for audio processing errors."""
    pass


class APIConnectionError(AudioProcessorError):
    """Exception raised when connection to the API fails."""
    pass


class VoiceCreationError(AudioProcessorError):
    """Exception raised when voice creation fails."""
    pass


class AudioGenerationError(AudioProcessorError):
    """Exception raised when audio generation fails."""
    pass


class AudioProcessor:
    """
    Creates audio content from lectures using the ElevenLabs API with enhanced
    voice customization for professor personas.
    """

    # Maximum retries for API calls
    MAX_RETRIES = 3
    # Wait time between retries (seconds)
    RETRY_WAIT = 2
    # Default max chunk size for text-to-speech
    DEFAULT_CHUNK_SIZE = 4000
    # Default voice model
    DEFAULT_MODEL = "eleven_multilingual_v2"

    def __init__(self, api_key: Optional[str] = None, audio_path: Optional[str] = None):
        """
        Initialize the audio processor.

        Args:
            api_key: ElevenLabs API key. If not provided, will use ELEVENLABS_API_KEY environment variable.
            audio_path: Path to store audio files. If not provided, will use AUDIO_STORAGE_PATH environment
                        variable or default to './audio_files'.
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        self.audio_path = audio_path or os.environ.get(
            "AUDIO_STORAGE_PATH", "./audio_files"
        )
        os.makedirs(self.audio_path, exist_ok=True)

        # Initialize ElevenLabs client with retry mechanism
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            # Test API connection with a simple request
            self._test_api_connection()
            self.logger.info("Successfully initialized ElevenLabs client")
        except Exception as e:
            self.logger.error(f"Failed to initialize ElevenLabs client: {e}")
            raise APIConnectionError(f"Failed to connect to ElevenLabs API: {str(e)}")

        # Cache for voices to avoid repeated API calls
        self.voice_cache = {}
        
        # Load voice mapping from configuration (in a real implementation,
        # this would be loaded from a configuration file)
        self.voice_mapping = self._load_voice_mapping()
        
    def _test_api_connection(self) -> bool:
        """
        Test the connection to the ElevenLabs API.
        
        Returns:
            bool: True if connection successful, False otherwise
        
        Raises:
            APIConnectionError: If connection to API fails
        """
        try:
            # Make a simple API call to test connection
            self.client.voices.get_all()
            return True
        except AuthorizationError as e:
            self.logger.error(f"API authorization error: {e}")
            raise APIConnectionError(f"Invalid API key: {e}")
        except Exception as e:
            self.logger.error(f"API connection error: {e}")
            raise APIConnectionError(f"Failed to connect to ElevenLabs API: {e}")

    def _load_voice_mapping(self) -> Dict[str, str]:
        """
        Load voice mapping from configuration.
        
        In a production environment, this would load from a config file.
        
        Returns:
            Dict[str, str]: Mapping of department types to voice IDs
        """
        # In a real implementation, this would be loaded from a configuration file
        return {
            "stem": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "humanities": "EXAVITQu4vr4xnSDxMaL",  # Bella
            "business": "AZnzlk1XvdvUeBnXmlld",  # Adam
            "default": "21m00Tcm4TlvDq8ikWAM",  # Rachel as default
        }

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

    def _map_professor_to_voice_type(self, professor: Professor) -> str:
        """
        Map a professor to a voice type based on their department and characteristics.
        
        Args:
            professor: Professor profile
            
        Returns:
            str: Voice type identifier (e.g., 'stem', 'humanities', 'business')
        """
        # Convert department to lowercase for case-insensitive matching
        department = professor.department.lower() if professor.department else ""
        
        # Default department type
        department_type = "default"

        # Map departments to categories
        stem_departments = [
            "computer", "physics", "math", "biology", 
            "chemistry", "engineering", "science"
        ]
        
        humanities_departments = [
            "history", "english", "philosophy", "art",
            "music", "language", "literature", "sociology"
        ]
        
        business_departments = [
            "business", "economics", "finance", "management",
            "marketing", "accounting"
        ]
        
        # Check which category the department belongs to
        if any(stem_dept in department for stem_dept in stem_departments):
            department_type = "stem"
        elif any(humanities_dept in department for humanities_dept in humanities_departments):
            department_type = "humanities"
        elif any(business_dept in department for business_dept in business_departments):
            department_type = "business"
        
        return department_type

    def create_professor_voice(self, professor: Professor) -> str:
        """
        Create a custom voice for a professor based on their characteristics.

        Args:
            professor: Professor profile

        Returns:
            str: Voice ID of the created or selected voice
        """
        # Map professor characteristics to a department type
        department_type = self._map_professor_to_voice_type(professor)
        
        # Get voice ID from mapping
        voice_id = self.voice_mapping.get(department_type, self.voice_mapping["default"])
        
        # Create voice settings with appropriate parameters based on professor personality
        stability = 0.5  # Default stability
        similarity_boost = 0.75  # Higher similarity for more consistent output
        style = 0.5  # Balanced style
        
        # Adjust voice parameters based on professor personality
        if professor.personality:
            personality = professor.personality.lower()
            
            # Adjust stability - more stable voices for methodical professors
            if any(trait in personality for trait in ["methodical", "analytical", "precise"]):
                stability = 0.75
            elif any(trait in personality for trait in ["creative", "innovative", "spontaneous"]):
                stability = 0.35
                
            # Adjust style - higher for more expressive professors
            if any(trait in personality for trait in ["enthusiastic", "animated", "inspiring"]):
                style = 0.8
            elif any(trait in personality for trait in ["reserved", "formal", "conservative"]):
                style = 0.25
        
        # Create voice settings
        voice_settings = {
            "voice_id": voice_id,
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        }

        # Update professor's voice settings
        professor.voice_settings = voice_settings

        return voice_id

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

            # Try to get voice from ElevenLabs with retry mechanism
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.client.voices.get_all()
                    matching_voices = [v for v in response.voices if v.voice_id == voice_id]

                    if matching_voices:
                        voice = matching_voices[0]
                        # Update with custom settings if available
                        if (
                            "stability" in professor.voice_settings
                            or "similarity_boost" in professor.voice_settings
                        ):
                            voice_settings = VoiceSettings(
                                stability=professor.voice_settings.get("stability", 0.5),
                                similarity_boost=professor.voice_settings.get(
                                    "similarity_boost", 0.5
                                ),
                                style=professor.voice_settings.get("style", 0.5),
                                use_speaker_boost=professor.voice_settings.get(
                                    "use_speaker_boost", True
                                ),
                            )
                            voice = Voice(
                                voice_id=voice.voice_id,
                                name=voice.name,
                                settings=voice_settings,
                            )

                        if professor.id:
                            self.voice_cache[professor.id] = voice
                        return voice
                    
                    # Voice not found but API call succeeded
                    break
                    
                except RateLimitError as e:
                    if attempt < self.MAX_RETRIES - 1:
                        self.logger.warning(f"Rate limit hit, retrying in {self.RETRY_WAIT}s: {e}")
                        time.sleep(self.RETRY_WAIT)
                    else:
                        self.logger.error(f"Rate limit error after {self.MAX_RETRIES} attempts: {e}")
                        raise VoiceCreationError(f"Rate limit exceeded: {e}")
                except Exception as e:
                    self.logger.error(f"Error retrieving voice: {e}")
                    # Fall through to create new voice

        # Create new voice if not found
        try:
            voice_id = self.create_professor_voice(professor)
            response = self.client.voices.get_all()
            matching_voices = [v for v in response.voices if v.voice_id == voice_id]

            if matching_voices:
                voice = matching_voices[0]
                if professor.id:
                    self.voice_cache[professor.id] = voice
                return voice
            
            raise VoiceCreationError(
                f"Voice created but not found in available voices: {voice_id}"
            )
        except Exception as e:
            self.logger.error(f"Error creating voice for {professor.name}: {e}")
            raise VoiceCreationError(f"Could not create voice for professor {professor.name}: {e}")

    def split_lecture_into_chunks(
        self, text: str, max_chunk_size: int = DEFAULT_CHUNK_SIZE
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
        
    def _call_text_to_speech_with_retry(
        self, 
        text: str, 
        voice_id: str, 
        voice_settings: Optional[VoiceSettings] = None,
        model_id: str = DEFAULT_MODEL
    ) -> bytes:
        """
        Call text-to-speech API with retry mechanism.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            voice_settings: Voice settings to use
            model_id: Model ID to use
            
        Returns:
            bytes: Audio data
            
        Raises:
            AudioGenerationError: If audio generation fails after retries
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                return self.client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=model_id,
                    voice_settings=voice_settings,
                )
            except RateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(f"Rate limit hit, retrying in {self.RETRY_WAIT}s: {e}")
                    time.sleep(self.RETRY_WAIT * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Rate limit error after {self.MAX_RETRIES} attempts: {e}")
                    raise AudioGenerationError(f"Rate limit exceeded: {e}")
            except Exception as e:
                self.logger.error(f"Error converting text to speech: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT)
                else:
                    raise AudioGenerationError(f"Failed to convert text to speech: {e}")

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
        try:
            # Process text to enhance stage directions
            processed_text = self.process_stage_directions(lecture.content)

            # Get appropriate voice
            voice = self.get_voice_for_professor(professor)

            # Split into manageable chunks if needed
            chunks = self.split_lecture_into_chunks(processed_text)

            # Generate audio for each chunk
            audio_segments = []
            total_chunks = len(chunks)
            
            self.logger.info(f"Converting lecture to speech in {total_chunks} chunks")
            
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{total_chunks} ({len(chunk)} characters)")
                
                # Generate audio with appropriate settings and retry mechanism
                audio_segment = self._call_text_to_speech_with_retry(
                    text=chunk,
                    voice_id=voice.voice_id,
                    voice_settings=voice.settings if hasattr(voice, "settings") else None,
                )
                
                audio_segments.append(audio_segment)

            # Combine audio segments (if more than one)
            if len(audio_segments) > 1:
                # In a full implementation, you would use a library like pydub
                # to concatenate the audio segments. For now, we'll use a simple approach.
                self.logger.info(f"Combining {len(audio_segments)} audio segments")
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
            with open(file_path, "wb") as f:
                f.write(audio)
            
            self.logger.info(f"Audio saved to {file_path}")

            return file_path, audio
            
        except Exception as e:
            self.logger.error(f"Error in text_to_speech: {e}")
            raise AudioGenerationError(f"Error generating audio: {e}")

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs.

        Returns:
            List[Dict[str, Any]]: List of voice information dictionaries
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.voices.get_all()
                return [
                    {
                        "voice_id": voice.voice_id,
                        "name": voice.name,
                        "category": getattr(voice, "category", "premade"),
                        "description": getattr(voice, "description", ""),
                    }
                    for voice in response.voices
                ]
            except RateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(f"Rate limit hit, retrying in {self.RETRY_WAIT}s: {e}")
                    time.sleep(self.RETRY_WAIT)
                else:
                    self.logger.error(f"Rate limit error after {self.MAX_RETRIES} attempts: {e}")
                    return []
            except Exception as e:
                self.logger.error(f"Error retrieving voices: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT)
                else:
                    return []
        
        return []

    def get_user_subscription_info(self) -> Dict[str, Any]:
        """
        Get information about the current user's subscription.

        Returns:
            Dict[str, Any]: Subscription information
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                user = self.client.user.get()

                return {
                    "tier": user.subscription.tier,
                    "character_limit": user.subscription.character_limit,
                    "character_count": user.subscription.character_count,
                    "available_characters": user.subscription.character_limit
                    - user.subscription.character_count,
                    "voice_limit": getattr(user.subscription, "voice_limit", None),
                    "voice_count": getattr(user.subscription, "voice_count", None),
                    "can_extend_character_limit": getattr(
                        user.subscription, "can_extend_character_limit", False
                    ),
                    "next_character_count_reset_unix": getattr(
                        user.subscription, "next_character_count_reset_unix", None
                    ),
                }
            except RateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(f"Rate limit hit, retrying in {self.RETRY_WAIT}s: {e}")
                    time.sleep(self.RETRY_WAIT)
                else:
                    self.logger.error(f"Rate limit error after {self.MAX_RETRIES} attempts: {e}")
                    return {}
            except Exception as e:
                self.logger.error(f"Error retrieving subscription info: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT)
                else:
                    return {}
        
        return {}

    def play_audio(self, audio_data: Union[bytes, str]) -> None:
        """
        Play audio using the ElevenLabs play function.
        
        Args:
            audio_data: Audio data as bytes or file path
            
        Raises:
            AudioProcessorError: If audio playback fails
        """
        try:
            # If audio_data is a file path, read the file
            if isinstance(audio_data, str) and os.path.exists(audio_data):
                with open(audio_data, "rb") as f:
                    audio_data = f.read()
                    
            # Play the audio
            play(audio_data)
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            raise AudioProcessorError(f"Error playing audio: {e}")
