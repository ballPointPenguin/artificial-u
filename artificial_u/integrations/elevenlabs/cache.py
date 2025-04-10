"""
Voice data caching for ElevenLabs integration.

This module handles caching of voice data to reduce API calls and improve performance.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class VoiceCache:
    """
    Caches voice data to reduce API calls and improve performance.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        voice_cache_file: Optional[str] = None,
        mapping_cache_file: Optional[str] = None,
        logger=None,
    ):
        """
        Initialize the voice cache.

        Args:
            cache_dir: Directory for cache files
            voice_cache_file: Path to voice cache file
            mapping_cache_file: Path to professor-voice mapping cache file
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Set cache directory
        self.cache_dir = Path(
            cache_dir or os.environ.get("CACHE_DIR", "./.cache/elevenlabs")
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set cache file paths
        self.voice_cache_file = Path(
            voice_cache_file or self.cache_dir / "voice_data.json"
        )
        self.mapping_cache_file = Path(
            mapping_cache_file or self.cache_dir / "voice_mapping.json"
        )

        # Initialize caches
        self.voice_cache = {}
        self.voice_mapping_db = {}

        # Load caches
        self._load_caches()

    def _load_caches(self) -> None:
        """Load voice and mapping caches from files."""
        self._load_voice_cache()
        self._load_voice_mapping()

    def _load_voice_cache(self) -> None:
        """Load the voice attribute cache from file."""
        if self.voice_cache_file.exists():
            try:
                with open(self.voice_cache_file, "r") as f:
                    self.voice_cache = json.load(f)
                self.logger.debug(
                    f"Loaded {len(self.voice_cache)} voice entries from cache"
                )
            except Exception as e:
                self.logger.error(f"Error loading voice cache: {e}")

    def _save_voice_cache(self) -> None:
        """Save the voice attribute cache to file."""
        try:
            with open(self.voice_cache_file, "w") as f:
                json.dump(self.voice_cache, f)
            self.logger.debug(f"Saved {len(self.voice_cache)} voice entries to cache")
        except Exception as e:
            self.logger.error(f"Error saving voice cache: {e}")

    def _load_voice_mapping(self) -> None:
        """Load the professor-to-voice mapping database from file."""
        if self.mapping_cache_file.exists():
            try:
                with open(self.mapping_cache_file, "r") as f:
                    self.voice_mapping_db = json.load(f)
                self.logger.debug(
                    f"Loaded {len(self.voice_mapping_db)} voice mappings from cache"
                )
            except Exception as e:
                self.logger.error(f"Error loading voice mapping database: {e}")

    def _save_voice_mapping(self) -> None:
        """Save the professor-to-voice mapping database to file."""
        try:
            with open(self.mapping_cache_file, "w") as f:
                json.dump(self.voice_mapping_db, f)
            self.logger.debug(
                f"Saved {len(self.voice_mapping_db)} voice mappings to cache"
            )
        except Exception as e:
            self.logger.error(f"Error saving voice mapping database: {e}")

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a voice from the cache.

        Args:
            voice_id: ID of the voice to retrieve

        Returns:
            Voice data or None if not found
        """
        return self.voice_cache.get(voice_id)

    def set_voice(self, voice_id: str, voice_data: Dict[str, Any]) -> None:
        """
        Add a voice to the cache.

        Args:
            voice_id: ID of the voice
            voice_data: Voice data to cache
        """
        self.voice_cache[voice_id] = voice_data
        self._save_voice_cache()

    def get_voices_by_criteria(self, criteria_key: str) -> List[Dict[str, Any]]:
        """
        Get voices from the cache that match a criteria key.

        Args:
            criteria_key: Cache key for the criteria

        Returns:
            List of matching voices or empty list if none found
        """
        return self.voice_cache.get(criteria_key, [])

    def set_voices_by_criteria(
        self, criteria_key: str, voices: List[Dict[str, Any]]
    ) -> None:
        """
        Cache voices for a specific criteria.

        Args:
            criteria_key: Cache key for the criteria
            voices: List of voice data to cache
        """
        self.voice_cache[criteria_key] = voices
        self._save_voice_cache()

    def get_professor_voice_mapping(self, professor_id: str) -> Optional[str]:
        """
        Get the voice ID mapped to a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            Voice ID or None if not found
        """
        return self.voice_mapping_db.get(professor_id)

    def set_professor_voice_mapping(self, professor_id: str, voice_id: str) -> None:
        """
        Map a voice to a professor.

        Args:
            professor_id: ID of the professor
            voice_id: ID of the voice
        """
        self.voice_mapping_db[professor_id] = voice_id
        self._save_voice_mapping()

    def clear_voice_cache(self) -> None:
        """Clear the voice cache but keep mappings."""
        self.voice_cache = {}
        self._save_voice_cache()

    def clear_mappings(self) -> None:
        """Clear the professor-voice mappings but keep voice cache."""
        self.voice_mapping_db = {}
        self._save_voice_mapping()

    def clear_all(self) -> None:
        """Clear both voice cache and mappings."""
        self.clear_voice_cache()
        self.clear_mappings()

    def build_criteria_key(self, **criteria) -> str:
        """
        Build a cache key from criteria parameters.

        Args:
            **criteria: Criteria parameters

        Returns:
            Cache key string
        """
        # Sort criteria by key for consistent key generation
        sorted_criteria = sorted(
            [(k, v) for k, v in criteria.items() if v is not None], key=lambda x: x[0]
        )

        # Build key string
        key_parts = [f"{k}_{v}" for k, v in sorted_criteria]
        return "voices_" + "_".join(key_parts)

    def rebuild_cache(self, voice_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rebuild the voice cache with new data.

        Args:
            voice_data: List of voice data to cache

        Returns:
            Dictionary with cache rebuild statistics
        """
        start_time = time.time()
        result = {
            "status": "success",
            "voices_cached": 0,
            "errors": [],
            "time_taken": 0,
        }

        try:
            # Start with a fresh cache
            old_cache_size = len(self.voice_cache)
            self.voice_cache = {}

            # Cache each voice
            for voice in voice_data:
                voice_id = voice.get("voice_id")
                if voice_id:
                    self.voice_cache[voice_id] = voice
                    result["voices_cached"] += 1

            # Save the cache
            self._save_voice_cache()

            self.logger.info(
                f"Rebuilt voice cache: {old_cache_size} voices removed, {result['voices_cached']} voices added"
            )

        except Exception as e:
            error_msg = f"Error during cache rebuild: {str(e)}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
            result["status"] = "error"

        # Calculate time taken
        result["time_taken"] = time.time() - start_time

        return result
