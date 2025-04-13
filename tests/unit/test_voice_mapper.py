from unittest.mock import patch

import pytest

from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.models.core import Professor


@pytest.fixture
def voice_mapper():
    return VoiceMapper()


@pytest.mark.unit
def test_extract_gender_male_variations(voice_mapper):
    """Test gender extraction works for different male variations."""
    # Test various male gender strings
    male_terms = [
        "male",
        "man",
        "m",
        "he",
        "his",
        "him",
        "he/him",
        "he/they",
        "his/theirs",
    ]

    for term in male_terms:
        prof = Professor(
            name="Test Professor",
            title="Test Title",
            specialization="Testing",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
            gender=term,
        )

        gender = voice_mapper.extract_gender(prof)
        assert gender == "male", f"Failed to extract 'male' from gender string '{term}'"


@pytest.mark.unit
def test_extract_gender_female_variations(voice_mapper):
    """Test gender extraction works for different female variations."""
    # Test various female gender strings
    female_terms = [
        "female",
        "woman",
        "f",
        "she",
        "her",
        "hers",
        "she/her",
        "she/they",
        "hers/theirs",
    ]

    for term in female_terms:
        prof = Professor(
            name="Test Professor",
            title="Test Title",
            specialization="Testing",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
            gender=term,
        )

        gender = voice_mapper.extract_gender(prof)
        assert (
            gender == "female"
        ), f"Failed to extract 'female' from gender string '{term}'"


@pytest.mark.unit
def test_extract_gender_nonbinary_variations(voice_mapper):
    """Test gender extraction returns None for nonbinary variations."""
    # Test nonbinary gender strings
    nonbinary_terms = [
        "non-binary",
        "nonbinary",
        "enby",
        "nb",
        "genderqueer",
        "genderfluid",
        "agender",
        "they",
        "them",
        "theirs",
        "they/them",
        "ze",
        "zir",
        "ze/zir",
        "neutral",
        "any",
        "other",
    ]

    for term in nonbinary_terms:
        prof = Professor(
            name="Test Professor",
            title="Test Title",
            specialization="Testing",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
            gender=term,
        )

        gender = voice_mapper.extract_gender(prof)
        assert (
            gender is None
        ), f"Should return None for nonbinary term '{term}', got '{gender}'"


@pytest.mark.unit
def test_extract_gender_no_gender(voice_mapper):
    """Test gender extraction when gender is not provided."""
    # Test with None
    prof = Professor(
        name="Test Professor",
        title="Test Title",
        specialization="Testing",
        background="Test background",
        personality="Test personality",
        teaching_style="Test style",
        gender=None,
    )

    gender = voice_mapper.extract_gender(prof)
    assert gender is None

    # Test with empty string
    prof.gender = ""
    gender = voice_mapper.extract_gender(prof)
    assert gender is None


@pytest.mark.unit
def test_extract_gender_unknown_strings(voice_mapper):
    """Test gender extraction defaults to None for unknown strings."""
    # Test with unrecognized strings
    unknown_terms = ["unknown", "professor", "custom gender", "xyz", "123"]

    for term in unknown_terms:
        prof = Professor(
            name="Test Professor",
            title="Test Title",
            specialization="Testing",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
            gender=term,
        )

        gender = voice_mapper.extract_gender(prof)
        assert (
            gender is None
        ), f"Should return None for unknown term '{term}', got '{gender}'"


@pytest.mark.unit
def test_extract_profile_attributes(voice_mapper):
    """Test that extract_profile_attributes correctly builds attribute dictionary."""
    # Setup
    with (
        patch.object(
            voice_mapper, "extract_gender", return_value="male"
        ) as mock_gender,
        patch.object(
            voice_mapper, "extract_accent", return_value="british"
        ) as mock_accent,
        patch.object(
            voice_mapper, "extract_age", return_value="middle_aged"
        ) as mock_age,
    ):

        prof = Professor(
            name="Test Professor",
            title="Test Title",
            specialization="Testing",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
        )

        # Test with all attributes present
        attributes = voice_mapper.extract_profile_attributes(prof)
        assert attributes.get("gender") == "male"
        assert attributes.get("accent") == "british"
        assert attributes.get("age") == "middle_aged"
        assert attributes.get("language") == "en"
        assert attributes.get("use_case") == "informative_educational"

        # Test with missing attributes
        mock_gender.return_value = None
        mock_accent.return_value = None

        attributes = voice_mapper.extract_profile_attributes(prof)
        assert "gender" not in attributes
        assert "accent" not in attributes
        assert attributes.get("age") == "middle_aged"
        assert attributes.get("language") == "en"
        assert attributes.get("use_case") == "informative_educational"
