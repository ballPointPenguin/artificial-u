"""Tests for the structured JSON log formatter."""

import json
import logging

import pytest

from artificial_u.api.utils.logging import JsonFormatter


def _format(**kwargs) -> dict:
    logger = logging.getLogger("test.json_formatter")
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 10, "job %s finished", ("abc",), None, **kwargs
    )
    return json.loads(JsonFormatter().format(record))


@pytest.mark.unit
def test_extra_fields_are_emitted():
    data = _format(extra={"job_id": 42, "job_kind": "generate_lecture", "request_id": "r-1"})

    assert data["message"] == "job abc finished"
    assert data["job_id"] == 42
    assert data["job_kind"] == "generate_lecture"
    assert data["request_id"] == "r-1"


@pytest.mark.unit
def test_core_fields_only_without_extra():
    data = _format()

    assert set(data) == {"timestamp", "level", "message", "logger", "path", "function", "line"}


@pytest.mark.unit
def test_non_serializable_extra_is_stringified():
    data = _format(extra={"details": {"when": object}})

    assert "object" in data["details"]["when"]
