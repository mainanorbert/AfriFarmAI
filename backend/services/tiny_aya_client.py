"""Translation/localization via Cohere Tiny Aya, called through the Cohere
hosted Chat API. Always live — no canned templates.

Two jobs in the pipeline:
  * ``translate_to_english`` — forward-translate the farmer's Swahili/Dholuo so
    the diagnosis model (weak in Swahili) reasons in English.
  * ``localize`` — render the English diagnosis back into the farmer's language.

If Cohere is unreachable these degrade to the real underlying text (the
original transcript, or the English diagnosis) rather than fabricating output.
"""

from __future__ import annotations

import re
from functools import lru_cache

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis, Language

log = get_logger("services.tiny_aya")

_LANG_NAME: dict[Language, str] = {"sw": "Swahili", "luo": "Dholuo (Luo)", "en": "English"}

_ENGLISH_TEMPLATE = (
    "Likely problem: {condition} (severity: {severity}).\n"
    "Treatment: {treatment}\n"
    "Prevention: {prevention}"
)


def _model_id() -> str:
    """Cohere API model name (strip any ``CohereLabs/`` HF-style prefix)."""

    return settings.tiny_aya_model.split("/")[-1]


@lru_cache(maxsize=1)
def _client():
    """Lazily build a shared Cohere client."""

    import cohere

    return cohere.ClientV2(
        api_key=settings.cohere_api_key,
        timeout=settings.provider_timeout_seconds,
    )


def _clean(text: str) -> str:
    """Drop any echoed ``<text>`` delimiter the model sometimes returns."""

    return re.sub(r"</?text>", "", text, flags=re.IGNORECASE).strip()


def _chat(prompt: str) -> str:
    """Single-turn Tiny Aya chat call returning cleaned response text."""

    resp = _client().chat(
        model=_model_id(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return _clean(resp.message.content[0].text)


def _compose_english(diagnosis: Diagnosis) -> str:
    """Build the canonical English farmer-facing message from a diagnosis."""

    return _ENGLISH_TEMPLATE.format(
        condition=diagnosis.condition,
        severity=diagnosis.severity.value,
        treatment=diagnosis.treatment or "—",
        prevention=diagnosis.prevention or "—",
    )


def translate_to_english(text: str, source_language: Language) -> str:
    """Translate farmer input to English before diagnosis.

    Returns ``text`` unchanged when the source is already English/empty, or if
    the translation call fails (the diagnosis model can still use the original).
    """

    if source_language == "en" or not text.strip():
        return text

    name = _LANG_NAME.get(source_language, "the source language")
    prompt = (
        f"Translate the text between <text> tags from {name} into English. "
        "It describes a crop or animal health problem. Output ONLY the English "
        f"translation, nothing else.\n<text>\n{text}\n</text>"
    )
    try:
        out = _chat(prompt)
        log.info("translate op=to_en lang=%s ok=1", source_language)
        return out or text
    except Exception:  # network/SDK/quota — no content logged
        log.warning("translate op=to_en lang=%s ok=0 fallback=original", source_language)
        return text


def localize(diagnosis: Diagnosis, language: Language) -> str:
    """Return a farmer-facing message rendered in ``language``.

    On a Cohere failure, degrades to the real English diagnosis rather than
    fabricating localized text.
    """

    english = _compose_english(diagnosis)
    if language == "en":
        return english

    name = _LANG_NAME.get(language, "the target language")
    prompt = (
        f"Translate the agricultural advice between <text> tags into {name}. "
        "Use simple words a smallholder farmer understands. Translate accurately "
        "and do not add or remove information. Output ONLY the translation.\n"
        f"<text>\n{english}\n</text>"
    )
    try:
        out = _chat(prompt)
        if not out:
            raise ValueError("empty translation")
        log.info("localize op=translate lang=%s ok=1", language)
        return out
    except Exception:  # degrade to the real English diagnosis
        log.warning("localize op=translate lang=%s ok=0 fallback=english", language)
        return english
