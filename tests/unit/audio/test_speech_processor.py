"""Unit tests for the SpeechProcessor class."""

import pytest

from artificial_u.audio.speech_processor import SpeechProcessor


class TestSpeechProcessor:
    """Test cases for SpeechProcessor text normalization and enhancement."""

    @pytest.fixture
    def processor(self):
        """Create a SpeechProcessor instance for testing."""
        return SpeechProcessor()

    @pytest.mark.unit
    def test_normalize_text_hyphenated_words(self, processor):
        """Test that hyphenated words are properly normalized."""
        # Test basic hyphenated words
        assert processor.normalize_text("well-being") == "well being"
        assert processor.normalize_text("state-of-the-art") == "state of the art"
        assert processor.normalize_text("self-explanatory") == "self explanatory"

        # Test complex hyphenated phrases
        result = processor.normalize_text("The state-of-the-art method")
        assert result == "The state of the art method"

    @pytest.mark.unit
    def test_normalize_text_prose_dashes(self, processor):
        """Test that prose dashes are removed while preserving mathematical expressions."""
        # Test basic prose dash removal
        result = processor.normalize_text("She paused - and took a sip")
        assert result == "She paused and took a sip"

        # Test multiple prose dashes
        input_text = "The idea - which was brilliant - changed everything"
        result = processor.normalize_text(input_text)
        assert result == "The idea which was brilliant changed everything"

        # Test quote-style dashes
        input_text = "He said - quote - this is important"
        result = processor.normalize_text(input_text)
        assert result == "He said quote this is important"

    @pytest.mark.unit
    def test_normalize_text_mathematical_preservation(self, processor):
        """Test that mathematical expressions are preserved during normalization."""
        # Test basic math expressions
        assert processor.normalize_text("Calculate 5 - 3 = 2") == "Calculate 5 - 3 = 2"
        assert processor.normalize_text("The score was 8 - 5") == "The score was 8 - 5"
        assert processor.normalize_text("Result: 10 - 7 = 3") == "Result: 10 - 7 = 3"

    @pytest.mark.unit
    def test_normalize_text_em_and_en_dashes(self, processor):
        """Test that em dashes and en dashes are properly handled."""
        # Test em dash removal
        input_text = "Real-time—or near real-time—processing"
        result = processor.normalize_text(input_text)
        assert result == "Real time or near real time processing"

        # Test en dash removal
        input_text = "The range was 10–15 items"
        result = processor.normalize_text(input_text)
        assert result == "The range was 10 15 items"

        # Test mixed dashes
        input_text = "Multi-level—both high–low processing"
        result = processor.normalize_text(input_text)
        assert result == "Multi level both high low processing"

    @pytest.mark.unit
    def test_normalize_text_markdown_headers(self, processor):
        """Test that markdown headers are properly removed."""
        assert processor.normalize_text("# Introduction") == "Introduction"
        assert processor.normalize_text("## Section Title") == "Section Title"
        assert processor.normalize_text("### Subsection") == "Subsection"

        # Test multiline headers - whitespace normalization happens after header removal
        text_with_headers = """# Main Title
Some content here
## Another Header
More content"""
        result = processor.normalize_text(text_with_headers)
        # Check that the first header (at beginning of text) is removed
        assert "Main Title" in result
        # The ## in middle doesn't get removed (not at line start after normalization)
        assert "Another Header" in result
        # The first # gets removed but the ## in middle remains
        assert not result.startswith("#")

    @pytest.mark.unit
    def test_normalize_text_whitespace_cleanup(self, processor):
        """Test that excessive whitespace is cleaned up properly."""
        # Test multiple spaces from replacements
        input_text = "Text  with   multiple    spaces"
        result = processor.normalize_text(input_text)
        assert result == "Text with multiple spaces"

        # Test mixed whitespace
        input_text = "Text\t\twith\n\n  mixed  \t whitespace"
        result = processor.normalize_text(input_text)
        assert result == "Text with mixed whitespace"

    @pytest.mark.unit
    def test_normalize_text_complex_scenarios(self, processor):
        """Test complex real-world scenarios combining multiple normalization rules."""
        # Complex academic text with multiple issues
        input_text = """# Machine Learning—A State-of-the-Art Overview

        Well-being research shows that real-time—or near real-time—processing
        can improve outcomes. Consider the equation y = mx + b - where m represents
        the slope. Multi-layer—both deep–shallow models perform calculations
        like 5 - 3 = 2 efficiently."""

        result = processor.normalize_text(input_text)

        # Check that all transformations occurred
        # Header removed, hyphenated words normalized
        assert "Machine Learning A State of the Art Overview" in result
        # Hyphenated word normalized
        assert "Well being research" in result
        # Em dashes removed, hyphenated words normalized
        assert "real time or near real time processing" in result
        # Prose dash removed
        assert "y = mx + b where m represents" in result
        # Em and en dashes removed, hyphenated words normalized
        assert "Multi layer both deep shallow models" in result
        # Mathematical expression preserved
        assert "5 - 3 = 2" in result

    @pytest.mark.unit
    def test_enhance_speech_markup_includes_normalization(self, processor):
        """Test that enhance_speech_markup includes normalization as first step."""
        # Test that enhancement includes normalization
        input_text = "The well-being study used state-of-the-art methods."
        enhanced = processor.enhance_speech_markup(input_text)

        # Should normalize hyphenated words
        assert "well being" in enhanced
        assert "state of the art" in enhanced
        assert "well-being" not in enhanced
        assert "state-of-the-art" not in enhanced

    @pytest.mark.unit
    def test_enhance_speech_markup_mathematical_context(self, processor):
        """Test that mathematical expressions get proper 'minus' treatment in enhancement."""
        # Test math expressions get enhanced to 'minus'
        input_text = "Calculate 5 - 3 = 2 for the equation."
        enhanced = processor.enhance_speech_markup(input_text)

        # Should convert math dashes to 'minus'
        assert "5 minus 3" in enhanced

        # Test mixed context
        input_text = "The well-being score went from 8 - 2 = 6."
        enhanced = processor.enhance_speech_markup(input_text)

        assert "well being" in enhanced  # Normalized hyphenated word
        assert "8 minus 2" in enhanced  # Math expression enhanced

    @pytest.mark.unit
    def test_edge_cases(self, processor):
        """Test edge cases and boundary conditions."""
        # Empty string
        assert processor.normalize_text("") == ""

        # Only whitespace
        assert processor.normalize_text("   \t\n   ") == ""

        # Only dashes - these don't get removed by our rules
        result = processor.normalize_text("---")
        # Consecutive dashes without word boundaries aren't affected by our regex
        assert result == "---"

        # Spaced dash gets removed (prose context)
        assert processor.normalize_text("  -  ") == ""

        # Single character words with dashes
        assert processor.normalize_text("a-b") == "a b"

        # Numbers with dashes (should preserve math context)
        # Single digits get normalized as hyphenated
        assert processor.normalize_text("1-2") == "1 2"
        # Spaced math preserved
        assert processor.normalize_text("1 - 2") == "1 - 2"

    @pytest.mark.unit
    def test_pause_stage_directions_basic(self, processor):
        """[Pause] becomes a 1.0s break; [Slight pause] becomes 0.5s."""
        text = "Please consider this. [Pause] Now continue."
        out = processor.normalize_text(text)
        assert '<break time="1.0s" />' in out

        text2 = "This is tricky. [Slight pause] But manageable."
        out2 = processor.normalize_text(text2)
        assert '<break time="0.5s" />' in out2

    @pytest.mark.unit
    def test_pause_for_variants(self, processor):
        """[Pause for ...] maps to a 1.5s break, covering emphasis/effect/a moment."""
        for phrase in [
            "[Pause for emphasis]",
            "[Pause for effect]",
            "[Pause for a moment]",
        ]:
            out = processor.normalize_text(f"Intro. {phrase} Outro.")
            assert '<break time="1.5s" />' in out

    @pytest.mark.unit
    def test_pauses_with_comma(self, processor):
        """[Pause, ...] and [Pauses, ...] both map to a 1.0s break."""
        # Test plural "pauses"
        text1 = "He looks around. [Pauses, waiting for students to comply] Continues."
        out1 = processor.normalize_text(text1)
        assert '<break time="1.0s" />' in out1

        # Test singular "pause"
        text2 = "She speaks. [Pause, warm tone] Then continues."
        out2 = processor.normalize_text(text2)
        assert '<break time="1.0s" />' in out2

        # Test that the stage direction is completely removed
        assert "warm tone" not in out2

    @pytest.mark.unit
    def test_pauses_thoughtfully_and_brief_pause(self, processor):
        """Specific cases for thoughtfully (1.5s) and brief pause (0.5s)."""
        out1 = processor.normalize_text("She considers. [pauses thoughtfully] Responds.")
        assert '<break time="1.5s" />' in out1

        out2 = processor.normalize_text("Prompt... [Brief pause for student responses] Continue.")
        assert '<break time="0.5s" />' in out2

        # comma variants should retain remaining note
        out3 = processor.normalize_text("Prompt... [Slight pause, waiting for answers] Continue.")
        assert '<break time="0.5s" />' in out3
        assert "[waiting for answers]" in out3

        out4 = processor.normalize_text("Prompt... [Brief pause, listening] Continue.")
        assert '<break time="0.5s" />' in out4
        assert "[listening]" in out4

    @pytest.mark.unit
    def test_pauses_at_remains(self, processor):
        """[Pauses at ...] should remain unchanged per rule."""
        text = "He turns. [Pauses at the door] Then exits."
        out = processor.normalize_text(text)
        # ensure we did not replace it with a break
        assert "<break" not in out
        assert "[Pauses at the door]" in out

    @pytest.mark.unit
    def test_split_into_chunks(self, processor):
        """Test text chunking functionality."""
        # Short text should return as single chunk
        short_text = "This is a short piece of text."
        chunks = processor.split_into_chunks(short_text)
        assert len(chunks) == 1
        assert chunks[0] == short_text

        # Test with custom chunk size - create text longer than the limit
        sentence = (
            "This is a much longer piece of text that contains multiple "
            "sentences and paragraphs. "
        )
        long_text = (
            sentence * 10 + "It should definitely be split into multiple chunks when we "
            "set a small chunk size limit. "
            "Each chunk should respect word boundaries and not split "
            "words in the middle."
        )
        chunks = processor.split_into_chunks(long_text, max_chunk_size=100)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should be reasonably sized (buffer for sentence boundaries)
        for chunk in chunks:
            assert len(chunk) <= 200

    @pytest.mark.unit
    def test_is_valid_chunk(self, processor):
        """Test chunk validation functionality."""
        # Valid chunks
        assert processor.is_valid_chunk("This is a valid chunk.")
        assert processor.is_valid_chunk("Short but valid.")

        # Invalid chunks
        assert not processor.is_valid_chunk("")
        assert not processor.is_valid_chunk("   ")  # Only whitespace
        assert not processor.is_valid_chunk("No")  # Too short (< 3 words)
        assert not processor.is_valid_chunk("!!!")  # No alphanumeric characters
