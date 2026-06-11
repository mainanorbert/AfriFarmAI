"""Spoken replies using hosted VoxCPM2, with gTTS as fallback."""

from __future__ import annotations

import tempfile
from typing import Optional

import requests

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.tts")

# VoxCPM2 supports both application languages.
_VOXCPM_LANGUAGES: set[Language] = {"sw", "en"}
_GTTS_LANG: dict[Language, str] = {"sw": "sw", "en": "en"}


def _synthesize_voxcpm(text: str, path: str) -> None:
    """Request WAV speech from the authenticated Modal VoxCPM2 endpoint."""

    if not settings.modal_tts_url or not settings.modal_key or not settings.modal_secret:
        raise RuntimeError("Modal TTS configuration is incomplete")

    response = requests.post(
        settings.modal_tts_url,
        json={"text": text},
        headers={
            "Modal-Key": settings.modal_key,
            "Modal-Secret": settings.modal_secret,
        },
        timeout=settings.modal_tts_timeout_seconds,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if not content_type.startswith("audio/wav") or not response.content:
        raise RuntimeError("Modal TTS returned an invalid audio response")

    with open(path, "wb") as audio_file:
        audio_file.write(response.content)


def _synthesize_gtts(text: str, language: Language, path: str) -> None:
    """Save speech with gTTS when VoxCPM2 is unavailable."""

    from gtts import gTTS

    gTTS(text=text, lang=_GTTS_LANG.get(language, "en")).save(path)


def synthesize(text: str, language: Language) -> Optional[str]:
    """Render speech, preferring hosted VoxCPM2 for English and Swahili."""

    if language in _VOXCPM_LANGUAGES:
        wav_path = tempfile.mktemp(suffix=".wav")
        try:
            _synthesize_voxcpm(text, wav_path)
            log.info("synthesize op=tts engine=voxcpm2 lang=%s ok=1", language)
            return wav_path
        except Exception:
            log.warning(
                "synthesize op=tts engine=voxcpm2 lang=%s ok=0 fallback=gtts",
                language,
            )

    mp3_path = tempfile.mktemp(suffix=".mp3")
    try:
        _synthesize_gtts(text, language, mp3_path)
        log.info("synthesize op=tts engine=gtts lang=%s ok=1", language)
        return mp3_path
    except Exception:
        log.warning("synthesize op=tts engine=gtts lang=%s ok=0", language)
        return None
