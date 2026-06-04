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

    def normalize_text(self, text: str, backend_name: str = "elevenlabs") -> str:
        """
        Normalize text for TTS using an explicit per-backend processing path.

        Applies shared light-touch normalization, then dispatches to the
        backend-specific handler for pause / stage-direction markup. There is
        no "generic" path: each backend gets explicit treatment.

        Args:
            text: The text to normalize.
            backend_name: TTS backend the text is destined for
                ("elevenlabs", "mistral", "xai"). Unknown backends fall back to
                clean prose (pause directions stripped, no markup).

        Returns:
            Normalized text suitable for the given TTS backend.
        """
        normalized_text = self._normalize_common(text)

        if backend_name == "elevenlabs":
            # SSML-capable: convert pause directions to <break> tags.
            normalized_text = self._convert_pauses(normalized_text, mode="ssml")
        elif backend_name == "xai":
            # xAI markup: [pause]/[long-pause] tags + <soft> stage directions.
            normalized_text = self._process_xai(normalized_text)
        elif backend_name == "mistral":
            # No markup support: strip bracketed pause directions entirely.
            normalized_text = self._strip_pause_directions(normalized_text)
        else:
            self.logger.debug(
                "Unknown TTS backend %r; defaulting to clean-prose processing",
                backend_name,
            )
            normalized_text = self._strip_pause_directions(normalized_text)

        return normalized_text.strip()

    def _normalize_common(self, text: str) -> str:
        """
        Backend-agnostic light-touch normalization shared by all backends.

        Handles hyphenation, dashes (preserving math), markdown headers,
        whitespace, and appending periods to unpunctuated lines. Does NOT
        touch pause / stage-direction markup — that is backend-specific.
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
                    bracket_match = re.search(r"\[([^\[\]]*)\]$", stripped)
                    if bracket_match:
                        inner_text = bracket_match.group(1).rstrip(" \t")
                        if inner_text and inner_text[-1] not in pause_punct:
                            insert_at = bracket_match.start(1) + len(inner_text)
                            core = (
                                stripped[:insert_at]
                                + "."
                                + stripped[insert_at:]
                                + core[len(stripped) :]
                            )
                    elif last_char not in pause_punct:
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

        # Keep em dashes, but prevent them from colliding with adjacent words.
        normalized_text = normalized_text.replace("—", " — ")

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

        return normalized_text

    def _convert_pauses(self, text: str, mode: str = "ssml") -> str:
        """Convert bracketed pause stage directions to backend-specific markup.

        ``mode="ssml"`` renders ElevenLabs ``<break time="Xs" />`` tags;
        ``mode="xai"`` renders xAI ``[pause]`` / ``[long-pause]`` inline tags
        (short pauses ≤1.0s → ``[pause]``; longer / duration pauses → ``[long-pause]``).

        Rules (case-insensitive):
        - [Pause] → 1.0s break / [pause]
        - [Slight pause] → 0.5s break / [pause]
        - [Slight pause for ...] → 1.0s break / [pause] (special case)
        - [Pause for ...] (e.g., emphasis/effect/a moment) → 1.5s break / [long-pause]
        - [Brief pause ...] → 0.5s break / [pause]
        - [Pauses thoughtfully] → 1.5s break / [long-pause]
        - [Pause, ...] or [Pauses, ...] → 1.0s break / [pause] (general pause with description)
        - [Pauses for N seconds] → dynamic break / [long-pause]
        - [Pauses at ...] is left unchanged
        """

        is_xai = mode == "xai"

        def _pause_for_seconds_repl(match: re.Match) -> str:
            if is_xai:
                return " [long-pause] "
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

        # [Slight pause, ...] → short + keep remainder as bracketed comment
        text = re.sub(
            r"\[\s*slight\s+pause\s*,\s*([^\]]+)\]",
            (r" [pause] [\1] " if is_xai else r' <break time="0.5s" /> [\1] '),
            text,
            flags=re.IGNORECASE,
        )

        # [Brief pause, ...] → short + keep remainder as bracketed comment
        text = re.sub(
            r"\[\s*brief\s+pause\s*,\s*([^\]]+)\]",
            (r" [pause] [\1] " if is_xai else r' <break time="0.5s" /> [\1] '),
            text,
            flags=re.IGNORECASE,
        )

        # [Pause, ...] or [Pauses, ...] → short (target comma variants)
        text = re.sub(
            r"\[\s*pauses?\s*,[^\]]*\]",
            (" [pause] " if is_xai else ' <break time="1.0s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # Process exact matches next

        # Exact [Slight pause]
        text = re.sub(
            r"\[\s*slight\s+pause\s*\]",
            (" [pause] " if is_xai else ' <break time="0.5s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # Exact [Pause]
        text = re.sub(
            r"\[\s*pause\s*\]",
            (" [pause] " if is_xai else ' <break time="1.0s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # [Pauses thoughtfully] → long
        text = re.sub(
            r"\[\s*pauses\s+thoughtfully\s*\]",
            (" [long-pause] " if is_xai else ' <break time="1.5s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # Process more general patterns last

        # [Slight pause for X...] → short (special case for "slight pause for")
        text = re.sub(
            r"\[\s*slight\s+pause\s+for\s+[^\]]+\]",
            (" [pause] " if is_xai else ' <break time="1.0s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # [Pause for X...] (emphasis, effect, a moment, etc.) → long
        text = re.sub(
            r"\[\s*pause\s+for\s+[^\]]+\]",
            (" [long-pause] " if is_xai else ' <break time="1.5s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # [Slight pause ...] → short (general case, after comma variant)
        text = re.sub(
            r"\[\s*slight\s+pause[^\]]*\]",
            (" [pause] " if is_xai else ' <break time="0.5s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # [Brief pause ...] → short (general case, after comma variant)
        text = re.sub(
            r"\[\s*brief\s+pause[^\]]*\]",
            (" [pause] " if is_xai else ' <break time="0.5s" /> '),
            text,
            flags=re.IGNORECASE,
        )

        # Collapse any excess whitespace again after insertions
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def _process_xai(self, text: str) -> str:
        """Process text for xAI Grok markup.

        Converts pause stage directions to ``[pause]`` / ``[long-pause]`` inline
        tags, then wraps any remaining bracketed stage directions (e.g.
        ``[walks to the front]``) in ``<soft>...</soft>``. A single trailing
        period inserted by common normalization is dropped from inside the wrap.
        """
        text = self._convert_pauses(text, mode="xai")

        def _wrap_soft(match: re.Match) -> str:
            inner = match.group(1).rstrip()
            # Drop a single trailing period added by line normalization.
            if inner.endswith(".") and not inner.endswith(".."):
                inner = inner[:-1].rstrip()
            return f"<soft>{inner}</soft>"

        # Wrap remaining bracketed directions, but never the [pause]/[long-pause] tags.
        text = re.sub(
            r"\[(?!pause\]|long-pause\])([^\[\]]+)\]",
            _wrap_soft,
            text,
        )
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
