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

    def enhance_speech_markup(self, text: str) -> str:
        """
        Enhance text with speech markup for better pronunciation.

        Args:
            text: The text to enhance

        Returns:
            Enhanced text with speech markup
        """
        # Start with the original text
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

        Args:
            text: The text to enhance

        Returns:
            Text with enhanced equations
        """
        # Replace common equation syntax
        replacements = {
            # Basic operators
            r"\*\*": " to the power of ",
            r"\*": " times ",
            r"/": " divided by ",
            r"\+": " plus ",
            r"-": " minus ",
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

        # Apply replacements only within equation contexts
        # This is a simplified approach - a more complex implementation would parse equations
        for pattern, replacement in replacements.items():
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
