"""Shared "select an existing entity or generate a new one" decision step.

The department, professor and course selector services each build their own prompt and
then ask the model for a ``<decision>``; this module holds the part they have in common.
"""

import logging
from typing import Any, Callable, Dict

from artificial_u.prompts.selection import parse_selection_decision
from artificial_u.services.content_service import ContentService
from artificial_u.utils import ContentGenerationError


def parse_entity_selection(response: str) -> Dict[str, Any]:
    """Parse a department/professor decision and check the action is one we understand."""
    decision = parse_selection_decision(response)
    if decision["action"] not in ("SELECT", "GENERATE"):
        raise ContentGenerationError(f"Invalid action in decision: {decision['action']}")
    return decision


async def ask_for_decision(
    content_service: ContentService,
    *,
    prompt: str,
    model: str,
    parse: Callable[[str], Dict[str, Any]],
    label: str,
    logger: logging.Logger,
) -> Dict[str, Any]:
    """Ask the model for a selection decision and parse it.

    Args:
        content_service: Service used to call the model
        prompt: The selection prompt
        model: Model to ask
        parse: Turns the raw response into a decision dict (raises on malformed output)
        label: What is being selected, for log and error messages (e.g. "department")
        logger: Logger of the calling service

    Raises:
        ContentGenerationError: If the call fails, the response is empty, or it cannot be parsed
    """
    try:
        logger.info(f"Calling AI for {label} selection decision...")
        # No system prompt: it tends to add text around the decision that breaks parsing
        response = await content_service.generate_text(prompt=prompt, model=model)
        logger.info(f"Received AI response for {label} selection")

        if not response:
            raise ContentGenerationError(f"AI returned empty response for {label} selection")

        return parse(response)
    except ContentGenerationError:
        raise
    except Exception as e:
        error_msg = f"Failed to get AI selection decision: {e}"
        logger.error(error_msg, exc_info=True)
        raise ContentGenerationError(error_msg) from e
