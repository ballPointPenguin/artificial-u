"""Voice design prompt builder for ElevenLabs Voice Design API.

Assembles a natural-language description of a professor's voice suitable
for submission to the ElevenLabs Voice Design (text-to-voice) API.

Current approach: rule-based template from a handful of structured attributes
(gender, accent, age) combined with a fixed "professorial" core description.

Future enhancement: pass professor attributes (including personality,
teaching_style, etc.) to a fast LLM to produce a richer, more
individualised prompt — the function signature is already designed for this.
"""

from typing import Any, Dict, Optional, Union

# ---------------------------------------------------------------------------
# Age normalisation
# ---------------------------------------------------------------------------

# Categorical strings → prompt phrase
_AGE_STRING_MAP: Dict[str, str] = {
    "young": "in their late 20s",
    "young_adult": "in their late 20s",
    "middle_aged": "in their 40s",
    "middle aged": "in their 40s",
    "old": "in their 60s",
    "elderly": "in their late 60s or 70s",
    "senior": "in their late 60s or 70s",
}

_DEFAULT_AGE_PHRASE = "in their 40s"


def _normalise_age(age_raw: Optional[Union[int, str]]) -> str:
    """Map a raw age value (int or categorical string) to a prompt-friendly phrase.

    The professor model stores ``age`` as an integer (e.g. ``45``). The voice
    mapper also uses categorical strings like ``"middle_aged"``. Both forms are
    accepted.
    """
    if age_raw is None:
        return _DEFAULT_AGE_PHRASE

    # Integer age → bucket
    if isinstance(age_raw, int):
        if age_raw < 30:
            return "in their late 20s"
        if age_raw < 45:
            return "in their mid-30s to early 40s"
        if age_raw < 58:
            return "in their late 40s to mid-50s"
        if age_raw < 70:
            return "in their 60s"
        return "in their 70s"

    # String (categorical or numeric string)
    normalised = str(age_raw).strip().lower()
    if normalised.isdigit():
        return _normalise_age(int(normalised))
    return _AGE_STRING_MAP.get(normalised, _DEFAULT_AGE_PHRASE)


# ---------------------------------------------------------------------------
# Prompt composition — follows ElevenLabs prompting guide structure:
#   Native <Language>. <Gender>, <Age range>. <Quality>.
#   Persona: <2-5 words>. Emotion: <adjectives>.
#   <1-2 sentences about timbre, pacing, delivery>
# ---------------------------------------------------------------------------

_QUALITY = "Studio quality."

_PERSONA = "Persona: knowledgeable university professor."

_EMOTION = "Emotion: calm, engaged, intellectually curious."

_DELIVERY = (
    "Measured pace with deliberate enunciation — comfortable with complex vocabulary "
    "and nuanced ideas. Warm and authoritative without being stiff; "
    "the voice of someone who genuinely loves their subject "
    "and wants students to understand it deeply."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_voice_design_prompt(professor: Dict[str, Any]) -> str:
    """Build an ElevenLabs Voice Design prompt from professor attributes.

    Follows ElevenLabs' recommended prompt structure:
      Native <Language>. <Gender>, <Age range>. <Quality>.
      Persona: ... Emotion: ...
      <Timbre / pacing / delivery description>

    Args:
        professor: Dictionary of professor attributes.  Recognised keys:
            ``gender``   – "male", "female", or any string (optional)
            ``accent``   – e.g. "American", "British", "Norwegian" (optional)
            ``age``      – integer (e.g. 45) or categorical string (optional)
            Additional keys (name, personality, teaching_style, …) are
            accepted but currently unused — reserved for the future LLM path.

    Returns:
        A prose voice-description string ready for the ElevenLabs API.

    Note:
        Future enhancement: when ``personality`` or ``teaching_style`` are
        present, call a fast LLM (e.g. claude-haiku) to weave them into a
        richer, more individualised prompt before the delivery sentence.
    """
    gender_raw = str(professor.get("gender") or "").strip().lower()
    accent_raw = str(professor.get("accent") or "").strip()
    age_raw = professor.get("age")

    # --- Language / accent ---
    if accent_raw:
        # e.g. "Native English, British accent." or "Native English, Oslo accent."
        language_line = f"Native English, {accent_raw} accent."
    else:
        language_line = "Native English."

    # --- Gender + age ---
    gender_desc = {"male": "Male", "female": "Female"}.get(gender_raw, "Neutral")
    age_phrase = _normalise_age(age_raw)
    gender_age_line = f"{gender_desc}, {age_phrase}."

    return " ".join(
        [
            language_line,
            gender_age_line,
            _QUALITY,
            _PERSONA,
            _EMOTION,
            _DELIVERY,
        ]
    )
