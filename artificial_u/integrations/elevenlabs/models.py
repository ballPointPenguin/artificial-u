"""ElevenLabs TTS model constants."""

from typing import Any, Dict

ELEVENLABS_V4_MODEL = "eleven_v4"

# Models that work with any library voice regardless of the voice's cached
# ``verified_languages`` (which only lists models a voice was explicitly verified
# against and is sparse for newer models).
UNGATED_MODELS = frozenset({ELEVENLABS_V4_MODEL})

# Model used when a voice cannot be rendered with an ungated model.
FALLBACK_MODEL = "eleven_flash_v2_5"


def voice_lists_model(voice: Dict[str, Any], model_id: str) -> bool:
    """Return True if the voice's ``verified_languages`` explicitly lists ``model_id``."""
    for item in voice.get("verified_languages") or []:
        if isinstance(item, dict):
            item_model = item.get("model_id")
        else:
            item_model = getattr(item, "model_id", None)
        if item_model == model_id:
            return True
    return False
