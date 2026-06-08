"""Spoken reply for low-literacy farmers.

Two backends:
  * MMS-TTS (Meta) via HF Inference — the real path, and the only option for
    **Dholuo** (``facebook/mms-tts-luo``), which gTTS cannot speak.
  * gTTS — baseline/fallback; speaks Swahili and English well, used when the
    real path is off, has no MMS model for the language, or the call fails.
"""

from __future__ import annotations

import tempfile
from functools import lru_cache
from typing import Optional

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.tts")

# gTTS language codes; Dholuo has no gTTS voice, so fall back to Swahili audio.
_GTTS_LANG: dict[Language, str] = {"sw": "sw", "luo": "sw", "en": "en"}

# Meta MMS-TTS models per language (English stays on gTTS).
_MMS_MODEL: dict[Language, str] = {
    "luo": "facebook/mms-tts-luo",
    "sw": "facebook/mms-tts-swh",
}


def _synthesize_gtts(text: str, language: Language) -> Optional[str]:
    """Baseline TTS via gTTS. Returns an audio path, or None on failure."""

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=_GTTS_LANG.get(language, "en"))
        path = tempfile.mktemp(suffix=".mp3")
        tts.save(path)
        log.info("synthesize op=tts engine=gtts lang=%s ok=1", language)
        return path
    except Exception:  # offline / quota — degrade gracefully, no content logged
        log.warning("synthesize op=tts engine=gtts lang=%s ok=0", language)
        return None


@lru_cache(maxsize=1)
def _client():
    """Lazily build a shared HF Inference client (hf-inference provider)."""

    from huggingface_hub import InferenceClient

    return InferenceClient(
        token=settings.hf_token,
        provider="hf-inference",
        timeout=settings.provider_timeout_seconds,
    )


def _synthesize_mms(text: str, model: str, language: Language) -> Optional[str]:
    """MMS-TTS via HF Inference. Returns a .wav path, or None on failure."""

    try:
        audio = _client().text_to_speech(text, model=model)
        path = tempfile.mktemp(suffix=".wav")
        with open(path, "wb") as fh:
            fh.write(audio)
        log.info("synthesize op=tts engine=mms lang=%s ok=1", language)
        return path
    except Exception:  # no content logged, per privacy guardrails
        log.warning("synthesize op=tts engine=mms lang=%s ok=0", language)
        return None


def synthesize(text: str, language: Language) -> Optional[str]:
    """Render ``text`` to an audio file and return its path, or None on failure.

    On the real path, Dholuo/Swahili use MMS-TTS; anything else, or any failure,
    falls back to gTTS so the farmer still gets a spoken reply.
    """

    if not settings.use_real_tts:
        return _synthesize_gtts(text, language)

    model = _MMS_MODEL.get(language)
    if model and settings.hf_token:
        path = _synthesize_mms(text, model, language)
        if path:
            return path

    return _synthesize_gtts(text, language)
