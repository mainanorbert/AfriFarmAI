"""Translation/localization via Cohere Tiny Aya (TinyAya-Earth for African
languages), called through the Cohere hosted Chat API.

Two jobs in the pipeline:
  * ``translate_to_english`` — forward-translate the farmer's Swahili/Dholuo so
    the diagnosis model (weak in Swahili) reasons in English.
  * ``localize`` — render the English diagnosis back into the farmer's language.

Both degrade gracefully: any API failure falls back to the original text (for
forward translation) or the hand-written stub template (for localization).
"""

from __future__ import annotations

import re
from functools import lru_cache

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis, Language, Severity

log = get_logger("services.tiny_aya")

_LANG_NAME: dict[Language, str] = {"sw": "Swahili", "luo": "Dholuo (Luo)", "en": "English"}

_SEVERITY_LABEL: dict[Language, dict[Severity, str]] = {
    "sw": {
        Severity.MILD: "kidogo",
        Severity.MODERATE: "wastani",
        Severity.SEVERE: "kali",
        Severity.UNKNOWN: "haijulikani",
    },
    "luo": {
        Severity.MILD: "matin",
        Severity.MODERATE: "madiere",
        Severity.SEVERE: "marach",
        Severity.UNKNOWN: "ok ongʼere",
    },
    "en": {
        Severity.MILD: "mild",
        Severity.MODERATE: "moderate",
        Severity.SEVERE: "severe",
        Severity.UNKNOWN: "unknown",
    },
}

_TEMPLATE: dict[Language, str] = {
    "sw": (
        "Tatizo linalowezekana: {condition} (ukali: {severity}).\n"
        "Tiba: {treatment}\n"
        "Kinga: {prevention}"
    ),
    "luo": (
        "Tuo manyalo bedo: {condition} (rachne: {severity}).\n"
        "Thieth: {treatment}\n"
        "Geng'o: {prevention}"
    ),
    "en": (
        "Likely problem: {condition} (severity: {severity}).\n"
        "Treatment: {treatment}\n"
        "Prevention: {prevention}"
    ),
}


def _model_id() -> str:
    """Cohere API model name (strip any ``CohereLabs/`` HF-style prefix)."""

    return settings.tiny_aya_model.split("/")[-1]


@lru_cache(maxsize=1)
def _client():
    """Lazily build a shared Cohere client (imported only on the real path)."""

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

    return _TEMPLATE["en"].format(
        condition=diagnosis.condition,
        severity=diagnosis.severity.value,
        treatment=diagnosis.treatment or "—",
        prevention=diagnosis.prevention or "—",
    )


def translate_to_english(text: str, source_language: Language) -> str:
    """Translate farmer input to English before diagnosis.

    Returns ``text`` unchanged when the source is already English, the real
    path is off, or the call fails.
    """

    if not settings.use_real_aya or source_language == "en" or not text.strip():
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


def _localize_stub(diagnosis: Diagnosis, language: Language) -> str:
    log.info("localize stub op=translate lang=%s", language)
    template = _TEMPLATE.get(language, _TEMPLATE["en"])
    severity = _SEVERITY_LABEL[language][diagnosis.severity]
    return template.format(
        condition=diagnosis.condition,
        severity=severity,
        treatment=diagnosis.treatment or "—",
        prevention=diagnosis.prevention or "—",
    )


def localize(diagnosis: Diagnosis, language: Language) -> str:
    """Return a farmer-facing message rendered in ``language``."""

    if not settings.use_real_aya:
        return _localize_stub(diagnosis, language)

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
    except Exception:  # degrade to the hand-written template
        log.warning("localize op=translate lang=%s ok=0 fallback=stub", language)
        return _localize_stub(diagnosis, language)
