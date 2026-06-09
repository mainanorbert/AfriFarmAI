"""Speech-to-text with per-language routing — always live, no canned data.

  * English  -> Cohere Transcribe (top ASR accuracy on its 14 languages).
  * Swahili / Dholuo -> Whisper (HF Inference). Cohere Transcribe does NOT
    support Swahili/Dholuo, so it must never handle them.

Any failure raises :class:`ProviderError` so the farmer gets an honest message
rather than a fabricated transcript.
"""

from __future__ import annotations

from functools import lru_cache

from backend.core.config import settings
from backend.core.errors import ProviderError
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.stt")


@lru_cache(maxsize=1)
def _whisper_client():
    """Lazily build a shared HF Inference client (hf-inference provider)."""

    from huggingface_hub import InferenceClient

    return InferenceClient(
        model=settings.asr_model,
        token=settings.hf_token,
        provider="hf-inference",
        timeout=settings.provider_timeout_seconds,
    )


@lru_cache(maxsize=1)
def _cohere_client():
    """Lazily build a shared Cohere client for transcription."""

    import cohere

    return cohere.ClientV2(
        api_key=settings.cohere_api_key,
        timeout=settings.provider_timeout_seconds,
    )


def _transcribe_whisper(audio_path: str, language: Language) -> str:
    """Whisper via HF Inference (auto-detects language)."""

    if not settings.hf_token:
        raise ProviderError("transcription", "missing HF token")
    try:
        result = _whisper_client().automatic_speech_recognition(audio_path)
    except Exception as exc:  # no audio/content logged, per privacy guardrails
        log.warning("transcribe op=stt engine=whisper lang=%s ok=0", language)
        raise ProviderError("transcription") from exc
    text = (result.text or "").strip()
    if not text:
        raise ProviderError("transcription", "empty result")
    log.info("transcribe op=stt engine=whisper lang=%s ok=1", language)
    return text


def _transcribe_cohere(audio_path: str, language: Language) -> str:
    """Cohere Transcribe (English only here)."""

    if not settings.cohere_api_key:
        raise ProviderError("transcription", "missing Cohere key")
    try:
        with open(audio_path, "rb") as fh:
            result = _cohere_client().audio.transcriptions.create(
                model=settings.cohere_transcribe_model,
                language=language,
                file=fh,
            )
    except Exception as exc:  # no audio/content logged, per privacy guardrails
        log.warning("transcribe op=stt engine=cohere lang=%s ok=0", language)
        raise ProviderError("transcription") from exc
    text = (result.text or "").strip()
    if not text:
        raise ProviderError("transcription", "empty result")
    log.info("transcribe op=stt engine=cohere lang=%s ok=1", language)
    return text


def transcribe(audio_path: str, language: Language = "sw") -> str:
    """Transcribe the farmer's recording, routing to the right engine.

    English uses Cohere Transcribe; Swahili/Dholuo use Whisper. Raises
    :class:`ProviderError` on any failure.
    """

    if language == "en":
        return _transcribe_cohere(audio_path, language)
    return _transcribe_whisper(audio_path, language)
