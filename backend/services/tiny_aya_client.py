"""Localization via Cohere Tiny Aya (TinyAya-Earth for African languages).

Renders the English/Swahili diagnosis into the farmer's chosen language. The
stub provides hand-written Swahili/Dholuo templates so the flow is realistic
without calling the model.
"""

from __future__ import annotations

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Diagnosis, Language, Severity

log = get_logger("services.tiny_aya")

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


def localize(diagnosis: Diagnosis, language: Language) -> str:
    """Return a farmer-facing message rendered in ``language``."""

    if not settings.use_real_models:
        log.info("localize stub op=translate lang=%s", language)
        template = _TEMPLATE.get(language, _TEMPLATE["en"])
        severity = _SEVERITY_LABEL[language][diagnosis.severity]
        return template.format(
            condition=diagnosis.condition,
            severity=severity,
            treatment=diagnosis.treatment or "—",
            prevention=diagnosis.prevention or "—",
        )

    # TODO(real): call Cohere Tiny Aya to translate the English diagnosis into
    #   `language`, preserving agronomic terms and safe-handling guidance.
    raise NotImplementedError("Real Tiny Aya not wired yet; set USE_REAL_MODELS=false.")
