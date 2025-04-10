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
    DEFAULT_MODEL = "eleven_flash_v2_5"
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
        For now, we're keeping stage directions as is.

        Args:
            text: Lecture text with stage directions in [brackets]

        Returns:
            str: Text preserved with stage directions
        """
        # For now, leave stage directions intact
        return text

    def enhance_speech_markup(
        self, text: str, professor: Optional[Professor] = None
    ) -> str:
        """
        Enhance text with ElevenLabs-compatible speech markup for better pronunciation.
        Currently focused on minimal processing that preserves the original text structure.

        Args:
            text: The lecture text to enhance
            professor: Optional professor object to apply discipline-specific enhancements

        Returns:
            str: Text with minimal enhancements
        """
        # Keep the stage directions intact
        enhanced_text = text

        # Remove markdown title prefix if present
        # This helps with better TTS rendering (doesn't try to speak "hashtag")
        enhanced_text = re.sub(r"^#\s+", "", enhanced_text)

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
        Preserves stage directions and ensures proper paragraph breaks.

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

        # First split text into paragraphs
        # Preserve markdown formatting (at least two newlines)
        paragraphs = re.split(r"(\n\s*\n)", text)

        # Handle the case where the split results in separator parts that need to be reattached
        # Every odd index element is a separator that we need to reattach to the previous content
        combined_paragraphs = []
        current = ""

        for i, part in enumerate(paragraphs):
            if i % 2 == 0:  # Content
                current = part
            else:  # Separator
                current += part
                combined_paragraphs.append(current)
                current = ""

        # If we have a remaining part, add it
        if current:
            combined_paragraphs.append(current)

        # If combined_paragraphs is empty, use the original split
        if not combined_paragraphs and paragraphs:
            combined_paragraphs = paragraphs

        # Now process the paragraphs
        current_chunk = ""

        for paragraph in combined_paragraphs:
            # If adding this paragraph would exceed the chunk size and we already have content,
            # save the current chunk and start a new one
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # For first paragraph in chunk, don't add extra newlines
                if not current_chunk:
                    current_chunk = paragraph
                else:
                    # Preserve paragraph breaks
                    current_chunk += paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        # Check if any chunk is still too large (e.g., a single paragraph > max_chunk_size)
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                self.logger.info(
                    f"Chunk of size {len(chunk)} exceeds max size, splitting by sentences"
                )
                # Split by sentences
                final_chunks.extend(self._split_by_sentences(chunk, max_chunk_size))
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _split_by_sentences(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Split text by sentences for more precise chunk sizing.
        Preserves stage directions and avoids breaking in the middle of them.

        Args:
            text: The text to split
            max_chunk_size: Maximum characters per chunk

        Returns:
            List[str]: List of text chunks
        """
        # Simple sentence splitter using regex that preserves stage directions
        # Look for sentence endings but not within square brackets
        sentence_pattern = r"(?<=[.!?])\s+(?![^\[]*\])"
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If this sentence would push us over the limit
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Add a space if this isn't the first content in the chunk
            if current_chunk and not current_chunk.endswith(" "):
                current_chunk += " "

            current_chunk += sentence

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def validate_voice_and_model(self, voice_id: str, model_id: str) -> bool:
        """
        Validates that the voice ID exists and is compatible with the specified model.

        Args:
            voice_id: The voice ID to validate
            model_id: The model ID to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Simplified validation that just checks if we can access voices
            # This avoids potential API response structure mismatches
            voices = self.get_available_voices()

            if not voices:
                self.logger.error("Could not retrieve available voices")
                return False

            voice_ids = [
                voice.get("voice_id") for voice in voices if voice.get("voice_id")
            ]
            voice_exists = voice_id in voice_ids

            if not voice_exists:
                self.logger.error(f"Voice ID {voice_id} not found in available voices")
                self.logger.info(f"Available voice IDs: {voice_ids[:5]}...")
                return False

            # For model validation, we'll just use a known model list
            # This avoids potential API mismatches with the models endpoint
            known_models = [
                "eleven_multilingual_v2",
                "eleven_flash_v2_5",
                "eleven_turbo_v2_5",
                "eleven_turbo_v2",
                "eleven_flash_v2",
                "eleven_monolingual_v1",
                "eleven_english_sts_v2",
                "eleven_multilingual_v1",
            ]

            if model_id not in known_models:
                self.logger.warning(
                    f"Model ID {model_id} not in known models list: {known_models}"
                )
                # We'll return True anyway since ElevenLabs may introduce new models

            self.logger.info(f"Validated voice ID {voice_id} and model ID {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error validating voice and model: {str(e)}")
            # Return True to continue despite validation error
            # This is a fallback approach since validation itself shouldn't block TTS
            self.logger.warning("Continuing despite validation error")
            return True

    def save_debug_chunks(self, chunks: List[str], lecture_id: str) -> None:
        """
        Saves processed text chunks to files for debugging.

        Args:
            chunks: List of processed text chunks
            lecture_id: Identifier for the lecture
        """
        try:
            debug_dir = Path(self.audio_path) / "debug" / lecture_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Clear existing debug files for this lecture
            for existing_file in debug_dir.glob("chunk_*.txt"):
                existing_file.unlink()

            # Save each chunk to a separate file
            for i, chunk in enumerate(chunks):
                chunk_file = debug_dir / f"chunk_{i+1:03d}.txt"
                chunk_file.write_text(chunk)

            self.logger.info(f"Saved {len(chunks)} debug chunks to {debug_dir}")

            # Save a summary file with chunk sizes and character counts
            summary_lines = [
                f"Chunk {i+1}: {len(chunk)} chars, {len(chunk.split())} words"
                for i, chunk in enumerate(chunks)
            ]
            summary_file = debug_dir / "chunks_summary.txt"
            summary_file.write_text("\n".join(summary_lines))

        except Exception as e:
            self.logger.error(f"Error saving debug chunks: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests the connection to ElevenLabs API and verifies authentication.

        Returns:
            Dict[str, Any]: Connection status and API information
        """
        try:
            # Try to get user info as a connectivity test
            user_info = self.client.user.get()

            # Try to get available voices
            voices = self.client.voices.get_all()
            voice_count = len(voices.voices) if hasattr(voices, "voices") else 0

            return {
                "status": "connected",
                "subscription_tier": (
                    user_info.subscription.tier
                    if hasattr(user_info, "subscription")
                    else "unknown"
                ),
                "available_voices": voice_count,
                "api_version": getattr(self.client, "version", "unknown"),
            }
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def is_valid_chunk(self, chunk: str) -> bool:
        """
        Validates if a text chunk is suitable for text-to-speech conversion.

        Args:
            chunk: The text chunk to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Check if chunk is empty or only whitespace
        if not chunk or chunk.isspace():
            return False

        # Check if chunk is too short (less than 3 words)
        words = chunk.split()
        if len(words) < 3:
            return False

        # Check if chunk contains any alphanumeric characters
        if not any(c.isalnum() for c in chunk):
            return False

        return True

    def _normalize_voice_settings_for_consistency(
        self, chunks: List[str]
    ) -> Dict[str, float]:
        """
        Analyzes text chunks and adjusts voice settings for more consistent output.

        Args:
            chunks: The text chunks to analyze

        Returns:
            Dict[str, float]: Optimized voice settings
        """
        # Default settings
        settings = {
            "stability": 0.5,  # Higher stability = more consistent voice
            "clarity": 0.75,  # Balance clarity and naturalness
            "style": 0.0,  # Lower style = more consistent output
        }

        # Check for potential volume inconsistency indicators
        all_caps_counts = [
            sum(1 for c in chunk if c.isupper()) / len(chunk) if chunk else 0
            for chunk in chunks
        ]
        exclamation_counts = [chunk.count("!") for chunk in chunks]
        question_counts = [chunk.count("?") for chunk in chunks]

        # Detect if there's high variance in emphasized text
        if (
            max(all_caps_counts) > 0.1
            and (max(all_caps_counts) - min(all_caps_counts)) > 0.05
        ):
            # High variance in caps - increase stability for consistency
            settings["stability"] = 0.7
            self.logger.info(
                "Detected high variance in capitalized text, increasing stability"
            )

        # Check for high punctuation variance
        if (
            max(exclamation_counts) > 3
            and max(exclamation_counts) > 3 * min(exclamation_counts)
        ) or (
            max(question_counts) > 3 and max(question_counts) > 3 * min(question_counts)
        ):
            # High variance in emphasis punctuation - increase stability
            settings["stability"] = min(0.8, settings["stability"] + 0.1)
            # Reduce style to minimize dramatic shifts
            settings["style"] = 0.0
            self.logger.info(
                "Detected high variance in emphasis punctuation, adjusting settings for consistency"
            )

        # Look for explicit SSML volume markers that could cause inconsistency
        volume_markers = sum(chunk.count('<prosody volume="') for chunk in chunks)
        if volume_markers > 0:
            self.logger.info(
                f"Detected {volume_markers} explicit volume markers in SSML"
            )
            # With explicit volume control, we need higher stability
            settings["stability"] = min(0.85, settings["stability"] + 0.15)

        return settings

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
            # Test API connection first
            connection_status = self.test_connection()
            if connection_status.get("status") != "connected":
                self.logger.error(
                    f"ElevenLabs API connection error: {connection_status.get('error', 'Unknown error')}"
                )
                raise AudioProcessorError("Failed to connect to ElevenLabs API")

            # Enhance text with minimal speech markup
            processed_text = self.enhance_speech_markup(lecture.content, professor)

            # Log original vs processed text size for debugging
            self.logger.info(f"Original text size: {len(lecture.content)} chars")
            self.logger.info(f"Processed text size: {len(processed_text)} chars")

            # Get appropriate voice ID
            voice_id = self.get_voice_id_for_professor(professor)
            self.logger.info(f"Using voice_id: {voice_id}")

            # Validate voice and model
            if not self.validate_voice_and_model(voice_id, self.DEFAULT_MODEL):
                self.logger.warning("Falling back to default voice")
                voice_id = self.voice_mapping["default"]

            # Set up voice settings, starting with reasonable defaults
            voice_settings = {"stability": 0.5, "clarity": 0.8, "style": 0.0}

            # Override with professor-specific settings if available
            if professor.voice_settings and isinstance(professor.voice_settings, dict):
                for key in voice_settings:
                    if key in professor.voice_settings:
                        voice_settings[key] = professor.voice_settings[key]

            self.logger.info(f"Using voice settings: {voice_settings}")

            # Use default chunk size - ElevenLabs can handle larger chunks
            # with the minimal processing we're now doing
            chunk_size = self.DEFAULT_CHUNK_SIZE
            self.logger.info(f"Using chunk size: {chunk_size}")

            # Split into manageable chunks
            chunks = self.split_lecture_into_chunks(
                processed_text, max_chunk_size=chunk_size
            )

            # Save chunks for debugging
            lecture_id = (
                f"{lecture.course_id}_w{lecture.week_number}_l{lecture.order_in_week}"
            )
            self.save_debug_chunks(chunks, lecture_id)

            # Generate audio for each chunk
            audio_segments = []
            total_chunks = len(chunks)

            self.logger.info(f"Converting lecture to speech in {total_chunks} chunks")
            self.logger.info(f"Using model: {self.DEFAULT_MODEL}")

            for i, chunk in enumerate(chunks):
                chunk_size = len(chunk)
                word_count = len(chunk.split())
                self.logger.info(
                    f"Processing chunk {i+1}/{total_chunks} ({chunk_size} chars, {word_count} words)"
                )

                # Skip invalid chunks
                if not self.is_valid_chunk(chunk):
                    self.logger.warning(
                        f"Skipping invalid chunk {i+1}: too short or empty"
                    )
                    continue

                # Generate audio with retry mechanism
                for attempt in range(self.MAX_RETRIES):
                    try:
                        self.logger.debug(f"Attempt {attempt+1} for chunk {i+1}")

                        # Get audio stream from the API
                        audio_stream = self.client.text_to_speech.convert(
                            text=chunk,
                            voice_id=voice_id,
                            model_id=self.DEFAULT_MODEL,
                            voice_settings=voice_settings,
                        )

                        # Consume the generator if it's a generator (new API behavior)
                        if hasattr(audio_stream, "__iter__") and not isinstance(
                            audio_stream, bytes
                        ):
                            self.logger.debug(
                                f"Chunk {i+1}: Audio stream is a generator, consuming it"
                            )
                            audio_segment = b"".join(
                                chunk
                                for chunk in audio_stream
                                if isinstance(chunk, bytes)
                            )
                        else:
                            # Handle the case where it's already bytes (old API behavior)
                            self.logger.debug(
                                f"Chunk {i+1}: Audio stream is bytes data"
                            )
                            audio_segment = audio_stream

                        audio_segments.append(audio_segment)
                        self.logger.info(f"Successfully processed chunk {i+1}")
                        break
                    except Exception as e:
                        self.logger.error(
                            f"Error converting chunk {i+1} to speech: {str(e)}"
                        )
                        if attempt < self.MAX_RETRIES - 1:
                            self.logger.info(
                                f"Waiting {self.RETRY_WAIT}s before retry..."
                            )
                            time.sleep(self.RETRY_WAIT)
                        else:
                            self.logger.error(
                                f"Failed to process chunk {i+1} after {self.MAX_RETRIES} attempts"
                            )
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

    def list_available_resources(self) -> Dict[str, Any]:
        """
        Lists available resources from ElevenLabs API for diagnostics.

        Returns:
            Dict[str, Any]: Dictionary containing available voices and models
        """
        result = {"voices": [], "models": [], "subscription": {}, "errors": []}

        # Get available voices
        try:
            voices = self.client.voices.get_all()
            result["voices"] = [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, "category", "unknown"),
                }
                for voice in voices.voices
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving voices: {str(e)}")
            result["errors"].append(f"Voice retrieval error: {str(e)}")

        # Get available models
        try:
            models = self.client.models.get_all()
            result["models"] = [
                {
                    "model_id": model.model_id,
                    "name": model.name,
                    "description": getattr(model, "description", ""),
                }
                for model in models.models
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving models: {str(e)}")
            result["errors"].append(f"Model retrieval error: {str(e)}")

        # Get subscription info
        try:
            result["subscription"] = self.get_user_subscription_info()
        except Exception as e:
            self.logger.error(f"Error retrieving subscription info: {str(e)}")
            result["errors"].append(f"Subscription info retrieval error: {str(e)}")

        return result
