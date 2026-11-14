"""Tests for the shared select-or-generate decision step."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.selection import ask_for_decision, parse_entity_selection
from artificial_u.utils import ContentGenerationError

LOGGER = logging.getLogger("test.selection")


def _content_service(response):
    service = MagicMock()
    service.generate_text = AsyncMock(return_value=response)
    return service


async def _ask(response, parse=parse_entity_selection):
    return await ask_for_decision(
        _content_service(response),
        prompt="pick one",
        model="test-model",
        parse=parse,
        label="department",
        logger=LOGGER,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_select_decision_is_parsed():
    decision = await _ask(
        "<decision><action>SELECT</action><department_id>7</department_id>"
        "<reasoning>Best fit</reasoning></decision>"
    )

    assert decision == {"action": "SELECT", "entity_id": 7, "reasoning": "Best fit"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_decision_has_no_entity():
    decision = await _ask(
        "<decision><action>GENERATE</action><department_id>null</department_id>"
        "<reasoning>Nothing matches</reasoning></decision>"
    )

    assert decision["action"] == "GENERATE"
    assert decision["entity_id"] is None


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        "",
        "no decision here",
        "<decision><action>MAYBE</action><reasoning>?</reasoning></decision>",
        "<decision><action>SELECT</action><reasoning>forgot the id</reasoning></decision>",
    ],
)
async def test_unusable_responses_raise_content_generation_error(response):
    with pytest.raises(ContentGenerationError):
        await _ask(response)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_model_failure_is_wrapped():
    service = MagicMock()
    service.generate_text = AsyncMock(side_effect=RuntimeError("provider down"))

    with pytest.raises(ContentGenerationError, match="provider down"):
        await ask_for_decision(
            service,
            prompt="p",
            model="m",
            parse=parse_entity_selection,
            label="professor",
            logger=LOGGER,
        )
