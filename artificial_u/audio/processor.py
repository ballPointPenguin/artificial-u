"""
Simplified Audio processor using ElevenLabs API for ArtificialU.
Focuses on the minimal functionality needed for text-to-speech conversion.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import time

# Import from ElevenLabs Python SDK
from elevenlabs import play
from elevenlabs.client import ElevenLabs

from artificial_u.models.core import Professor, Lecture

# Import the new voice selection system
from artificial_u.integrations.elevenlabs import (
    VoiceSelectionManager,
    get_voice_for_professor,
)


class AudioProcessorError(Exception):
    """Base exception for audio processing errors."""

    pass


class AudioProcessor:
    """
    Creates audio content from lectures using the ElevenLabs API.
    """

    # Default voice model
    DEFAULT_MODEL = "eleven_multilingual_v2"
    # Default max chunk size for text-to-speech
    DEFAULT_CHUNK_SIZE = 4000
    # Maximum retries for API calls
    MAX_RETRIES = 3
    # Wait time between retries (seconds)
    RETRY_WAIT = 2

    # Technical term pronunciation dictionary
    PRONUNCIATION_DICT = {
        # Format: "term": "IPA pronunciation"
        "Anthropic": "ænˈθrɒpɪk",
        "Claude": "klɔːd",
        "Python": "ˈpaɪθɑːn",
        "LaTeX": "ˈleɪtɛk",
        "NumPy": "nʌmˈpaɪ",
        "GOFAI": "ɡoʊˈfaɪ",
        "Tensorflow": "ˈtɛnsərˌfloʊ",
        "PyTorch": "paɪˈtɔːrtʃ",
        "SQL": "ˌɛs kjuː ˈɛl",
        "NoSQL": "noʊ ˌɛs kjuː ˈɛl",
    }

    # Mathematical notation mapping
    MATH_NOTATION = {
        # Greek letters
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
        "δ": "delta",
        "ε": "epsilon",
        "θ": "theta",
        "λ": "lambda",
        "π": "pi",
        "σ": "sigma",
        "τ": "tau",
        "φ": "phi",
        "ω": "omega",
        # Mathematical operators
        "≈": "approximately equal to",
        "≠": "not equal to",
        "≤": "less than or equal to",
        "≥": "greater than or equal to",
        "∑": "sum",
        "∫": "integral",
        "∂": "partial derivative",
        "∞": "infinity",
        "∈": "element of",
        "∩": "intersection",
        "∪": "union",
    }

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

        # Initialize ElevenLabs client
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            self.logger.info("Successfully initialized ElevenLabs client")
        except Exception as e:
            self.logger.error(f"Failed to initialize ElevenLabs client: {e}")
            raise

        # Initialize voice selection manager
        self.voice_manager = VoiceSelectionManager(api_key=self.api_key)

        # Simple voice mapping for different professor types (used as fallback)
        self.voice_mapping = {
            "stem": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "humanities": "EXAVITQu4vr4xnSDxMaL",  # Bella
            "business": "AZnzlk1XvdvUeBnXmlld",  # Adam
            "default": "21m00Tcm4TlvDq8ikWAM",  # Rachel as default
        }

    def process_stage_directions(self, text: str) -> str:
        """
        Process stage directions in the lecture text to enhance the audio output.

        Args:
            text: Lecture text with stage directions in [brackets]

        Returns:
            str: Text prepared for text-to-speech conversion with enhanced markup
        """
        # Replace common stage directions with pauses and tone adjustments
        replacements = [
            # Pauses for various actions
            (r"\[\s*pauses?\s*\]", '<break time="1s"/>'),
            (r"\[\s*long pause\s*\]", '<break time="2s"/>'),
            (r"\[\s*brief pause\s*\]", '<break time="0.5s"/>'),
            # Emotional cues
            (r"\[\s*enthusiastically\s*\]", '<prosody rate="fast" pitch="high">'),
            (r"\[\s*excited(ly)?\s*\]", '<prosody rate="fast" pitch="high">'),
            (r"\[\s*happily\s*\]", '<prosody pitch="high">'),
            (r"\[\s*sadly\s*\]", '<prosody pitch="low" rate="slow">'),
            (r"\[\s*seriously\s*\]", '<prosody pitch="low">'),
            (r"\[\s*thoughtfully\s*\]", '<prosody rate="slow">'),
            (r"\[\s*whispers\s*\]", '<prosody volume="soft">'),
            (r"\[\s*end (of )?(emotion|prosody)\s*\]", "</prosody>"),
            # Remove other stage directions
            (r"\[\s*.*?\s*\]", ""),
        ]

        processed_text = text
        for pattern, replacement in replacements:
            processed_text = re.sub(
                pattern, replacement, processed_text, flags=re.IGNORECASE
            )

        return processed_text

    def enhance_speech_markup(
        self, text: str, professor: Optional[Professor] = None
    ) -> str:
        """
        Enhance text with ElevenLabs-compatible speech markup for better pronunciation.

        Args:
            text: The lecture text to enhance
            professor: Optional professor object to apply discipline-specific enhancements

        Returns:
            str: Text with enhanced speech markup
        """
        # First process stage directions
        enhanced_text = self.process_stage_directions(text)

        # Add natural sentence pauses
        enhanced_text = re.sub(r"([.!?])\s+", r'\1<break time="0.5s"/> ', enhanced_text)

        # Add smaller pauses for commas and semicolons
        enhanced_text = re.sub(r"([,;])\s+", r'\1<break time="0.2s"/> ', enhanced_text)

        # Add pronunciation guides for technical terms
        for term, pronunciation in self.PRONUNCIATION_DICT.items():
            # Only replace whole words (not substrings)
            pattern = r"\b" + re.escape(term) + r"\b"
            replacement = (
                f'<phoneme alphabet="ipa" ph="{pronunciation}">{term}</phoneme>'
            )
            enhanced_text = re.sub(pattern, replacement, enhanced_text)

        # Handle mathematical notation
        for symbol, spoken_form in self.MATH_NOTATION.items():
            enhanced_text = enhanced_text.replace(symbol, spoken_form)

        # Handle discipline-specific processing if professor is provided
        if professor and professor.department:
            enhanced_text = self._apply_discipline_specific_markup(
                enhanced_text, professor
            )

        return enhanced_text

    def _apply_discipline_specific_markup(self, text: str, professor: Professor) -> str:
        """
        Apply discipline-specific speech markup based on professor's department.

        Args:
            text: The lecture text
            professor: Professor object with department information

        Returns:
            str: Text with discipline-specific markup applied
        """
        department = professor.department.lower() if professor.department else ""

        # Physics-related markup
        if any(field in department for field in ["physics", "quantum"]):
            # Handle quantum physics notation
            quantum_replacements = [
                (
                    r"\|ψ⟩",
                    'the quantum state <phoneme alphabet="ipa" ph="saɪ">psi</phoneme>',
                ),
                (r"\|0⟩", "the zero state"),
                (r"\|1⟩", "the one state"),
                (r"ℏ", "h-bar"),
                # More specific quantum notation
                (
                    r"\|ψ⟩\s*=\s*α\|0⟩\s*\+\s*β\|1⟩",
                    'the quantum state <phoneme alphabet="ipa" ph="saɪ">psi</phoneme> equals alpha times the zero state plus beta times the one state',
                ),
            ]

            for pattern, replacement in quantum_replacements:
                text = re.sub(pattern, replacement, text)

        # Math-related markup
        elif any(field in department for field in ["math", "statistic"]):
            # Handle specific math notation
            math_replacements = [
                (r"f\(x\)", "f of x"),
                (r"lim_{x→∞}", "the limit as x approaches infinity of"),
                (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"the fraction \1 over \2"),
            ]

            for pattern, replacement in math_replacements:
                text = re.sub(pattern, replacement, text)

        return text

    def _map_professor_to_voice_type(self, professor: Professor) -> str:
        """
        Map a professor to a voice type based on their department.

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
            "computer",
            "physics",
            "math",
            "biology",
            "chemistry",
            "engineering",
            "science",
        ]

        humanities_departments = [
            "history",
            "english",
            "philosophy",
            "art",
            "music",
            "language",
            "literature",
            "sociology",
        ]

        business_departments = [
            "business",
            "economics",
            "finance",
            "management",
            "marketing",
            "accounting",
        ]

        # Check which category the department belongs to
        if any(stem_dept in department for stem_dept in stem_departments):
            department_type = "stem"
        elif any(
            humanities_dept in department for humanities_dept in humanities_departments
        ):
            department_type = "humanities"
        elif any(business_dept in department for business_dept in business_departments):
            department_type = "business"

        return department_type

    def get_voice_id_for_professor(self, professor: Professor) -> str:
        """
        Get an appropriate voice ID for a professor.

        Args:
            professor: Professor profile

        Returns:
            str: Voice ID to use
        """
        # If professor has voice settings with a voice ID, use that (manual override)
        if professor.voice_settings and "voice_id" in professor.voice_settings:
            return professor.voice_settings["voice_id"]

        try:
            # Use the smart voice selection system
            voice_data = self.voice_manager.get_voice_for_professor(professor)
            return voice_data["voice_id"]
        except Exception as e:
            self.logger.error(f"Error selecting voice using smart system: {e}")
            self.logger.info("Falling back to simple mapping system")

            # If smart selection fails, fall back to the simple mapping
            department_type = self._map_professor_to_voice_type(professor)
            return self.voice_mapping.get(
                department_type, self.voice_mapping["default"]
            )

    def split_lecture_into_chunks(
        self, text: str, max_chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> List[str]:
        """
        Split a long lecture into smaller chunks for processing.

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
        try:
            # Enhance text with speech markup
            processed_text = self.enhance_speech_markup(lecture.content, professor)

            # Get appropriate voice ID
            voice_id = self.get_voice_id_for_professor(professor)

            # Split into manageable chunks if needed
            chunks = self.split_lecture_into_chunks(processed_text)

            # Generate audio for each chunk
            audio_segments = []
            total_chunks = len(chunks)

            self.logger.info(f"Converting lecture to speech in {total_chunks} chunks")

            for i, chunk in enumerate(chunks):
                self.logger.info(
                    f"Processing chunk {i+1}/{total_chunks} ({len(chunk)} characters)"
                )

                # Generate audio with retry mechanism
                for attempt in range(self.MAX_RETRIES):
                    try:
                        # Get audio stream from the API
                        audio_stream = self.client.text_to_speech.convert(
                            text=chunk,
                            voice_id=voice_id,
                            model_id=self.DEFAULT_MODEL,
                        )

                        # Consume the generator if it's a generator (new API behavior)
                        if hasattr(audio_stream, "__iter__") and not isinstance(
                            audio_stream, bytes
                        ):
                            audio_segment = b"".join(
                                chunk
                                for chunk in audio_stream
                                if isinstance(chunk, bytes)
                            )
                        else:
                            # Handle the case where it's already bytes (old API behavior)
                            audio_segment = audio_stream

                        audio_segments.append(audio_segment)
                        break
                    except Exception as e:
                        self.logger.error(f"Error converting text to speech: {e}")
                        if attempt < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_WAIT)
                        else:
                            raise

            # Combine audio segments (if more than one)
            if len(audio_segments) > 1:
                # Simple concatenation - in a full implementation you might
                # want to use a library like pydub to properly merge audio files
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
            raise

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs.

        Returns:
            List[Dict[str, Any]]: List of voice information dictionaries
        """
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
        except Exception as e:
            self.logger.error(f"Error retrieving voices: {e}")
            return []

    def get_user_subscription_info(self) -> Dict[str, Any]:
        """
        Get information about the current user's subscription.

        Returns:
            Dict[str, Any]: Subscription information
        """
        try:
            user = self.client.user.get()

            return {
                "tier": user.subscription.tier,
                "character_limit": user.subscription.character_limit,
                "character_count": user.subscription.character_count,
                "available_characters": user.subscription.character_limit
                - user.subscription.character_count,
            }
        except Exception as e:
            self.logger.error(f"Error retrieving subscription info: {e}")
            return {}

    def play_audio(self, audio_data: Union[bytes, str]) -> None:
        """
        Play audio using the ElevenLabs play function.

        Args:
            audio_data: Audio data as bytes or file path
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
