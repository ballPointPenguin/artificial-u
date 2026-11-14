"""Prompt module for Artificial-U.

Prompt builders live in the submodules (``artificial_u.prompts.lecture`` etc.); this
package provides language dispatch for services that generate content in the course's
language.
"""

from typing import Optional

__all__ = ["SUPPORTED_LANGUAGES", "get_prompts_for_language", "resolve_prompt_language"]

# Registry of supported language codes
SUPPORTED_LANGUAGES = ("en", "fr")


def get_prompts_for_language(language: str = "en"):
    """Return the prompt module for the given language code.

    Callers receive a module with the same public API as this package
    (get_professor_prompt, get_department_prompt, etc.) but with prompts
    written entirely in the target language.

    Args:
        language: ISO 639-1 language code (e.g. "en", "fr"). Defaults to "en".

    Returns:
        Module exposing prompt functions for the requested language.

    Raises:
        ValueError: If the language is not supported.
    """
    if language == "fr":
        from artificial_u.prompts import fr as _fr

        return _fr
    if language == "en":
        import artificial_u.prompts.en as _en

        return _en
    raise ValueError(
        f"Unsupported prompt language: '{language}'. "
        f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
    )


def resolve_prompt_language(language: Optional[str]) -> str:
    """Map a stored language value (e.g. "fr", "fr-CA", None) to a supported prompt language.

    Falls back to English for anything unsupported.
    """
    if language and isinstance(language, str):
        prefix = language.lower()[:2]
        if prefix in SUPPORTED_LANGUAGES:
            return prefix
    return "en"
