"""Unit tests for tag parsing and slug normalization."""

import pytest

from artificial_u.models.converters import parse_tags_xml
from artificial_u.models.repositories.tag import TagRepository


@pytest.mark.unit
def test_parse_tags_xml_returns_names_in_order():
    xml = """<tags>
      <tag>Machine Learning</tag>
      <tag>AI &amp; Society</tag>
      <tag>Ethics</tag>
    </tags>"""
    assert parse_tags_xml(xml) == ["Machine Learning", "AI & Society", "Ethics"]


@pytest.mark.unit
def test_parse_tags_xml_rejects_empty_and_wrong_root():
    with pytest.raises(ValueError):
        parse_tags_xml("<tags></tags>")
    with pytest.raises(ValueError):
        parse_tags_xml("<topics><tag>x</tag></topics>")
    with pytest.raises(ValueError):
        parse_tags_xml("not xml at all")


@pytest.mark.unit
def test_parse_tags_xml_skips_blank_and_placeholder_entries():
    xml = "<tags><tag>  </tag><tag>[GENERATE]</tag><tag>Logic</tag></tags>"
    assert parse_tags_xml(xml) == ["Logic"]


@pytest.mark.unit
def test_slugify_normalizes_case_accents_and_punctuation():
    assert TagRepository.slugify("Quantum Physics") == "quantum-physics"
    assert TagRepository.slugify("Éthique & Société") == "ethique-societe"
    assert TagRepository.slugify("Sci-Fi") == "sci-fi"
    assert TagRepository.slugify("sci fi") == "sci-fi"
    assert TagRepository.slugify("  Trailing  ") == "trailing"


@pytest.mark.unit
def test_slugify_preserves_non_latin_scripts():
    # Future universes (e.g. zh) must not normalize to an empty slug
    assert TagRepository.slugify("哲学") == "哲学"
