"""Spoken reply for low-literacy farmers, via gTTS.

gTTS speaks Swahili and English well (the project's primary languages). Dholuo
has no gTTS voice, so it is read with the Swahili voice — intelligible to Luo
speakers. (MMS-TTS would give a native Dholuo voice but is not served by HF
Inference and would require bundling torch/transformers locally.)
"""

from __future__ import annotations

import tempfile
from typing import Optional

from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.tts")

# gTTS language codes; Dholuo has no gTTS voice, so fall back to Swahili audio.
_GTTS_LANG: dict[Language, str] = {"sw": "sw", "luo": "sw", "en": "en"}


def synthesize(text: str, language: Language) -> Optional[str]:
    """Render ``text`` to an audio file and return its path, or None on failure.

    Failures (offline, quota) degrade gracefully to None so the farmer still
    gets the written diagnosis even when audio cannot be produced.
    """

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
