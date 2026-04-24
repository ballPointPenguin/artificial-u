"""
Speech processor for enhancing text for text-to-speech conversion.

This module provides utilities for processing text to improve TTS quality,
including special handling for technical terms, stage directions, and mathematical notation.
"""

import logging
import re
from typing import List


class SpeechProcessor:
    """
    Processes text for optimal text-to-speech conversion.
    Handles specialized text enhancements for academic content.
    """

    def __init__(self, logger=None):
        """
        Initialize the speech processor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def normalize_text(self, text: str, supports_ssml: bool = True) -> str:
        """
        Normalize text for TTS without aggressive markup.
        This is a light-touch normalization focused on common issues.

        Args:
            text: The text to normalize
            supports_ssml: Whether the TTS backend supports SSML-like tags
                (e.g., <break> tags). Defaults to True for ElevenLabs
                compatibility. Set to False for backends like Mistral.

        Returns:
            Normalized text suitable for TTS
        """

        def _append_period_to_unpunctuated_lines(s: str) -> str:
            pause_punct = {".", ",", ";", "?", "!", ":", "…"}
            out_lines: List[str] = []

            for line in s.splitlines(keepends=True):
                line_ending = "\n" if line.endswith("\n") else ""
                core = line[:-1] if line_ending else line

                stripped = core.rstrip(" \t")
                if stripped and any(ch.isalnum() for ch in stripped):
                    last_char = stripped[-1]
                    if last_char not in pause_punct:
                        core = stripped + "." + core[len(stripped) :]

                out_lines.append(core + line_ending)

            return "".join(out_lines)

        normalized_text = text

        # Fix hyphenated words being read as "minus"
        # Replace hyphens with spaces in hyphenated words (but not standalone dashes)
        # Use a more comprehensive approach to handle multi-word hyphenated phrases
        normalized_text = re.sub(r"(\w)-(\w)", r"\1 \2", normalized_text)

        # Handle leading-dash letter clusters like "-ER" → "E R" or "-ed" → "e d"
        normalized_text = re.sub(
            r"(?:(?<=\s)|^)-([A-Z]{2,})(?=\b)",
            lambda m: " ".join(m.group(1)),
            normalized_text,
            flags=re.IGNORECASE,
        )

        # Handle em dashes and en dashes more aggressively
        # Remove em dashes completely (they're usually just long pauses)
        normalized_text = normalized_text.replace("—", " ")

        # Remove en dashes when they appear between words
        normalized_text = normalized_text.replace("–", " ")

        # Handle prose dashes (spaced regular dashes) - remove them but preserve math contexts
        # Match: word/space + dash + space + word, but not: digit + space + dash + space + digit
        # This preserves "5 - 1" while removing "She paused - and took a sip"
        normalized_text = re.sub(r"(?<!\d)\s+-\s+(?!\d)", " ", normalized_text)

        # Handle multiple spaces that might result from replacements (preserve newlines)
        normalized_text = re.sub(r"[ \t]+", " ", normalized_text)

        # Add a pause at the end of unpunctuated lines (preserve newlines)
        normalized_text = _append_period_to_unpunctuated_lines(normalized_text)

        # Remove markdown title prefixes
        normalized_text = re.sub(r"^#+\s+", "", normalized_text, flags=re.MULTILINE)

        # Apply pause conversions for bracketed stage directions
        if supports_ssml:
            # Convert to <break> SSML tags (ElevenLabs and other SSML-capable backends)
            normalized_text = self._apply_pause_breaks(normalized_text)
        else:
            # For non-SSML backends, strip stage direction brackets entirely
            normalized_text = self._strip_pause_directions(normalized_text)

        return normalized_text.strip()

    def _apply_pause_breaks(self, text: str) -> str:
        """Convert bracketed pause stage directions to ElevenLabs <break> tags.

        Rules (case-insensitive):
        - [Pause] → <break time="1.0s" />
        - [Slight pause] → <break time="0.5s" />
        - [Slight pause for ...] → <break time="1.0s" /> (special case)
        - [Pause for ...] (e.g., emphasis/effect/a moment) → <break time="1.5s" />
        - [Brief pause ...] → <break time="0.5s" />
        - [Pauses thoughtfully] → <break time="1.5s" />
        - [Pause, ...] or [Pauses, ...] → <break time="1.0s" /> (general pause with description)
        - [Pauses at ...] is left unchanged
        """

        def _pause_for_seconds_repl(match: re.Match) -> str:
            raw = match.group(1).strip().lower()
            raw = re.sub(r"[.?!]+$", "", raw).strip()

            word_numbers = {
                "zero": 0,
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
                "six": 6,
                "seven": 7,
                "eight": 8,
                "nine": 9,
                "ten": 10,
            }

            seconds_match = re.match(r"^(\d+(?:\.\d+)?)\s*seconds?$", raw)
            if seconds_match:
                seconds = float(seconds_match.group(1))
                seconds = max(seconds, 0.0)
                return f' <break time="{seconds:.1f}s" /> '

            if raw in word_numbers:
                seconds = float(word_numbers[raw])
                return f' <break time="{seconds:.1f}s" /> '

            # Fall back to a natural long pause when the duration isn't parseable.
            return ' <break time="1.5s" /> '

        # Process comma variants first (more specific patterns)

        # [Pauses for three seconds.] → dynamic break length
        text = re.sub(
            r"\[\s*pauses?\s+for\s+([^\]]+?)\s*\]",
            _pause_for_seconds_repl,
            text,
            flags=re.IGNORECASE,
        )

        # [Slight pause, ...] → 0.5s + keep remainder as bracketed comment
        text = re.sub(
            r"\[\s*slight\s+pause\s*,\s*([^\]]+)\]",
            r' <break time="0.5s" /> [\1] ',
            text,
            flags=re.IGNORECASE,
        )

        # [Brief pause, ...] → 0.5s + keep remainder as bracketed comment
        text = re.sub(
            r"\[\s*brief\s+pause\s*,\s*([^\]]+)\]",
            r' <break time="0.5s" /> [\1] ',
            text,
            flags=re.IGNORECASE,
        )

        # [Pause, ...] or [Pauses, ...] → 1.0s (target comma variants)
        text = re.sub(
            r"\[\s*pauses?\s*,[^\]]*\]",
            ' <break time="1.0s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # Process exact matches next

        # Exact [Slight pause]
        text = re.sub(
            r"\[\s*slight\s+pause\s*\]",
            ' <break time="0.5s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # Exact [Pause]
        text = re.sub(
            r"\[\s*pause\s*\]",
            ' <break time="1.0s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # [Pauses thoughtfully] → 1.5s
        text = re.sub(
            r"\[\s*pauses\s+thoughtfully\s*\]",
            ' <break time="1.5s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # Process more general patterns last

        # [Slight pause for X...] → 1.0s (special case for "slight pause for")
        text = re.sub(
            r"\[\s*slight\s+pause\s+for\s+[^\]]+\]",
            ' <break time="1.0s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # [Pause for X...] (emphasis, effect, a moment, etc.) → 1.5s
        text = re.sub(
            r"\[\s*pause\s+for\s+[^\]]+\]",
            ' <break time="1.5s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # [Slight pause ...] → 0.5s (general case, after comma variant)
        text = re.sub(
            r"\[\s*slight\s+pause[^\]]*\]",
            ' <break time="0.5s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # [Brief pause ...] → 0.5s (general case, after comma variant)
        text = re.sub(
            r"\[\s*brief\s+pause[^\]]*\]",
            ' <break time="0.5s" /> ',
            text,
            flags=re.IGNORECASE,
        )

        # Collapse any excess whitespace again after insertions
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def _strip_pause_directions(self, text: str) -> str:
        """Remove bracketed pause stage directions for non-SSML backends.

        Instead of converting to <break> tags, simply removes the bracketed
        directives so the TTS engine sees clean prose with natural punctuation.
        """
        # Remove all pause-related bracketed directions
        text = re.sub(
            r"\[\s*(?:slight\s+)?(?:brief\s+)?pauses?\b[^\]]*\]",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def split_into_chunks(self, text: str, max_chunk_size: int = 4000) -> List[str]:
        """
        Split text into smaller chunks for processing.

        Args:
            text: The text to split
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # If text is short enough, return as is
        if len(text) <= max_chunk_size:
            return [text]

        # Split by paragraphs first
        chunks = []
        paragraphs = re.split(r"(\n\s*\n)", text)

        current_chunk = ""

        for i, paragraph in enumerate(paragraphs):
            # If adding this paragraph would exceed the chunk size and we already have content
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk += paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        # Check if any chunk is still too large
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                # Split by sentences
                final_chunks.extend(self._split_by_sentences(chunk, max_chunk_size))
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _split_by_sentences(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Split text by sentences for more precise chunk sizing.

        Args:
            text: The text to split
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # Split by sentence endings but preserve stage directions
        sentence_pattern = r"(?<=[.!?])\s+(?![^\[]*\])"
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If this sentence would push us over the limit
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk and not current_chunk.endswith(" "):
                    current_chunk += " "
                current_chunk += sentence

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def is_valid_chunk(self, chunk: str) -> bool:
        """
        Check if a text chunk is suitable for TTS conversion.

        Args:
            chunk: The text chunk to validate

        Returns:
            True if the chunk is valid for TTS
        """
        # Check if chunk is empty or only whitespace
        if not chunk or chunk.isspace():
            return False

        # Check if chunk is too short (less than 3 words)
        if len(chunk.split()) < 3:
            return False

        # Check if chunk contains any alphanumeric characters
        if not any(c.isalnum() for c in chunk):
            return False

        return True
