"""Tests for locating the expected XML document in an LLM response."""

import pytest

from artificial_u.utils.xml_utils import extract_root_xml


@pytest.mark.unit
@pytest.mark.parametrize(
    "response",
    [
        "<output><course><title>T</title></course></output>",
        "Here you go:\n<output>\n<course><title>T</title></course>\n</output>\nDone.",
        "<course><title>T</title></course>",
        "Sure!\n<course>\n<title>T</title>\n</course>",
        # <output> holding only the inner fields is wrapped in the root tag
        "<output><title>T</title></output>",
    ],
)
def test_finds_the_root_document(response):
    xml = extract_root_xml(response, "course")

    assert xml.startswith("<course>") and xml.endswith("</course>")
    assert "<title>T</title>" in xml


@pytest.mark.unit
@pytest.mark.parametrize("response", ["", "no xml at all", "<professor><name>N</name></professor>"])
def test_returns_none_when_the_document_is_missing(response):
    assert extract_root_xml(response, "course") is None


@pytest.mark.unit
def test_empty_root_only_counts_when_allowed():
    assert extract_root_xml("<tags></tags>", "tags") is None
    assert extract_root_xml("<tags></tags>", "tags", allow_empty=True) == "<tags>\n\n</tags>"
