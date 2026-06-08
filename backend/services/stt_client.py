"""Speech-to-text for Swahili (Path A: Whisper large-v3, or fine-tuned MMS).

NOTE: Cohere Transcribe was dropped from the original plan because it does
not support Swahili or Dholuo. Swahili works off-the-shelf with Whisper/MMS;
a fine-tuned checkpoint can replace ``ASR_MODEL`` later for the Well-Tuned
badge without touching callers.
"""

from __future__ import annotations

from functools import lru_cache

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.stt")

# Deterministic stub transcripts so the demo flow runs without model weights.
_STUB_BY_LANG: dict[Language, str] = {
    "sw": "Majani ya mahindi yangu yana madoa ya manjano na yanakauka.",
    "luo": "It bel mara nigi range ma rachar kendo gidwogo motwo.",
    "en": "My maize leaves have yellow spots and are drying up.",
}


def _transcribe_stub(language: Language) -> str:
    log.info("transcribe stub op=stt lang=%s", language)
    return _STUB_BY_LANG.get(language, _STUB_BY_LANG["sw"])


@lru_cache(maxsize=1)
def _client():
    """Lazily build a shared HF Inference client (imported only on real path).

    Pinned to the ``hf-inference`` provider so usage runs on Hugging Face's own
    serverless inference (covered by the HF credit) rather than a third party.
    """

    from huggingface_hub import InferenceClient

    return InferenceClient(
        model=settings.asr_model,
        token=settings.hf_token,
        provider="hf-inference",
        timeout=settings.provider_timeout_seconds,
    )


def transcribe(audio_path: str, language: Language = "sw") -> str:
    """Transcribe a voice message to text in its source language.

    Uses HF Inference ASR (Whisper, which auto-detects the language) on the real
    path. Any failure — missing token, cold-start, network — degrades to a
    representative stub so the rest of the pipeline still runs.
    """

    if not settings.use_real_stt:
        return _transcribe_stub(language)

    if not settings.hf_token:
        log.error("transcribe op=stt error=missing_hf_token fallback=stub")
        return _transcribe_stub(language)

    try:
        result = _client().automatic_speech_recognition(audio_path)
        text = (result.text or "").strip()
        if not text:
            raise ValueError("empty transcription")
        log.info("transcribe op=stt lang=%s ok=1", language)
        return text
    except Exception:  # no audio/content logged, per privacy guardrails
        log.warning("transcribe op=stt lang=%s ok=0 fallback=stub", language)
        return _transcribe_stub(language)
