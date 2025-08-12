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

    def __init__(self, logger=None):
        """
        Initialize the speech processor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for TTS without aggressive markup.
        This is a light-touch normalization focused on common issues.

        Args:
            text: The text to normalize

        Returns:
            Normalized text suitable for TTS
        """
        normalized_text = text

        # Fix hyphenated words being read as "minus"
        # Replace hyphens with spaces in hyphenated words (but not standalone dashes)
        # Use a more comprehensive approach to handle multi-word hyphenated phrases
        normalized_text = re.sub(r"(\w)-(\w)", r"\1 \2", normalized_text)

        # Handle em dashes and en dashes more aggressively
        # Remove em dashes completely (they're usually just long pauses)
        normalized_text = normalized_text.replace("—", " ")

        # Remove en dashes when they appear between words
        normalized_text = normalized_text.replace("–", " ")

        # Handle prose dashes (spaced regular dashes) - remove them but preserve math contexts
        # Match: word/space + dash + space + word, but not: digit + space + dash + space + digit
        # This preserves "5 - 1" while removing "She paused - and took a sip"
        normalized_text = re.sub(r"(?<!\d)\s+-\s+(?!\d)", " ", normalized_text)

        # Handle multiple spaces that might result from replacements
        normalized_text = re.sub(r"\s+", " ", normalized_text)

        # Remove markdown title prefixes
        normalized_text = re.sub(r"^#+\s+", "", normalized_text, flags=re.MULTILINE)

        # Apply pause → <break> conversions for bracketed stage directions
        normalized_text = self._apply_pause_breaks(normalized_text)

        return normalized_text.strip()

    def enhance_speech_markup(self, text: str) -> str:
        """
        Enhance text with speech markup for better pronunciation.
        This includes both normalization and advanced markup.

        Args:
            text: The text to enhance

        Returns:
            Enhanced text with speech markup
        """
        # Start with normalized text
        enhanced_text = self.normalize_text(text)

        # Add pronunciation guides for technical terms
        for term, pronunciation in self.PRONUNCIATION_DICT.items():
            # Only replace whole words (not substrings)
            pattern = r"\b" + re.escape(term) + r"\b"
            replacement = f'<phoneme alphabet="ipa" ph="{pronunciation}">{term}</phoneme>'
            enhanced_text = re.sub(pattern, replacement, enhanced_text)

        # Handle mathematical notation
        for symbol, spoken_form in self.MATH_NOTATION.items():
            enhanced_text = enhanced_text.replace(symbol, spoken_form)

        enhanced_text = self._enhance_code_syntax(enhanced_text)
        enhanced_text = self._enhance_equations(enhanced_text)
        enhanced_text = self._enhance_scientific_notation(enhanced_text)

        return enhanced_text

    def _enhance_code_syntax(self, text: str) -> str:
        """
        Enhance code syntax for better speech rendering.

        Args:
            text: The text to enhance

        Returns:
            Text with enhanced code syntax
        """
        # Replace common code syntax elements
        replacements = {
            # Variable declarations
            r"\bvar\b": "variable",
            r"\blet\b": "let",
            r"\bconst\b": "constant",
            # Operators
            r"===": "strictly equals",
            r"!==": "strictly not equals",
            r"==": "equals",
            r"!=": "not equals",
            r"<=": "less than or equal to",
            r">=": "greater than or equal to",
            r"->": "arrow",
            r"=>": "fat arrow",
            # Common syntax
            r"\bfunction\b": "function",
            r"\breturn\b": "return",
            r"\bif\b": "if",
            r"\belse\b": "else",
            r"\bfor\b": "for",
            r"\bwhile\b": "while",
        }

        # Apply replacements
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _enhance_equations(self, text: str) -> str:
        """
        Enhance mathematical equations for better speech rendering.
        Only applies mathematical replacements within likely equation contexts.

        Args:
            text: The text to enhance

        Returns:
            Text with enhanced equations
        """
        # First, handle mathematical operators that don't conflict with regular text
        safe_replacements = {
            # Multi-character operators that are clearly mathematical
            r"\*\*": " to the power of ",
            r">=": " greater than or equal to ",
            r"<=": " less than or equal to ",
            r"!=": " not equal to ",
            r"==": " equals ",
            # Functions
            r"\bsin\b": "sine",
            r"\bcos\b": "cosine",
            r"\btan\b": "tangent",
            r"\blog\b": "logarithm",
            r"\bln\b": "natural logarithm",
            r"\bexp\b": "exponential",
            r"\bsqrt\b": "square root",
            r"\blim\b": "limit",
        }

        # Apply safe replacements globally
        for pattern, replacement in safe_replacements.items():
            text = re.sub(pattern, replacement, text)

        # Handle potentially ambiguous operators only in mathematical contexts
        # Look for patterns like: number operator number, or variable operator variable
        math_context_patterns = {
            # Plus/minus when surrounded by numbers or variables
            r"(\d+|\w)\s*\+\s*(\d+|\w)": r"\1 plus \2",
            r"(\d+|\w)\s*-\s*(\d+|\w)": r"\1 minus \2",
            r"(\d+|\w)\s*\*\s*(\d+|\w)": r"\1 times \2",
            r"(\d+|\w)\s*/\s*(\d+|\w)": r"\1 divided by \2",
        }
        for pattern, replacement in math_context_patterns.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _enhance_scientific_notation(self, text: str) -> str:
        """
        Enhance scientific notation and chemical formulas.

        Args:
            text: The text to enhance

        Returns:
            Text with enhanced scientific notation
        """
        # Enhance chemical formulas (H2O -> "H 2 O")
        text = re.sub(r"([A-Z][a-z]?)(\d+)", r"\1 \2", text)

        # Enhance scientific units
        replacements = {
            # SI units
            r"m/s": "meters per second",
            r"km/h": "kilometers per hour",
            r"kg/m³": "kilograms per cubic meter",
            r"mol/L": "moles per liter",
            # Common units
            r"°C": "degrees Celsius",
            r"°F": "degrees Fahrenheit",
            r"K\b": "Kelvin",
        }

        # Apply replacements
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        return text

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
        # Process comma variants first (more specific patterns)

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
        text = re.sub(r"\s+", " ", text)
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
