"""Spoken reply for low-literacy farmers.

Stub path uses gTTS (Swahili/English supported) so the demo plays real audio.
For Dholuo, swap in MMS-TTS (facebook/mms-tts-luo) on the real path.
"""

from __future__ import annotations

import tempfile
from typing import Optional

from backend.core.config import settings
from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.tts")

# gTTS language codes; Dholuo has no gTTS voice, so fall back to Swahili audio.
_GTTS_LANG: dict[Language, str] = {"sw": "sw", "luo": "sw", "en": "en"}


def synthesize(text: str, language: Language) -> Optional[str]:
    """Render ``text`` to an audio file and return its path, or None on failure."""

    if not settings.use_real_models:
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=_GTTS_LANG.get(language, "en"))
            path = tempfile.mktemp(suffix=".mp3")
            tts.save(path)
            log.info("synthesize stub op=tts lang=%s ok=1", language)
            return path
        except Exception:  # offline / quota — degrade gracefully, no content logged
            log.warning("synthesize stub op=tts lang=%s ok=0", language)
            return None

    # TODO(real): MMS-TTS for Dholuo (facebook/mms-tts-luo); hosted TTS for sw/en.
    raise NotImplementedError("Real TTS not wired yet; set USE_REAL_MODELS=false.")
