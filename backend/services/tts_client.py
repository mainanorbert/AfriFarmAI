"""Spoken replies using Kenyan Edge TTS voices, with gTTS as fallback."""

from __future__ import annotations

import asyncio
import tempfile
from typing import Optional

from backend.core.logging_utils import get_logger
from backend.core.models import Language

log = get_logger("services.tts")

# Dholuo has no dedicated Edge voice, so use the Kenyan Swahili voice.
_EDGE_VOICE: dict[Language, str] = {
    "sw": "sw-KE-ZuriNeural",
    "luo": "sw-KE-ZuriNeural",
    "en": "en-KE-AsiliaNeural",
}

# Lightweight fallback if Edge TTS is temporarily unavailable.
_GTTS_LANG: dict[Language, str] = {"sw": "sw", "luo": "sw", "en": "en"}


async def _synthesize_edge(text: str, language: Language, path: str) -> None:
    """Save speech using a Kenyan Edge TTS voice."""

    import edge_tts

    voice = _EDGE_VOICE.get(language, _EDGE_VOICE["en"])
    await edge_tts.Communicate(text=text, voice=voice).save(path)


def _synthesize_gtts(text: str, language: Language, path: str) -> None:
    """Save speech with gTTS when Edge TTS is unavailable."""

    from gtts import gTTS

    gTTS(text=text, lang=_GTTS_LANG.get(language, "en")).save(path)


def synthesize(text: str, language: Language) -> Optional[str]:
    """Render text to an MP3, preferring Kenyan Edge TTS voices."""

    path = tempfile.mktemp(suffix=".mp3")
    try:
        asyncio.run(_synthesize_edge(text, language, path))
        log.info("synthesize op=tts engine=edge lang=%s ok=1", language)
        return path
    except Exception:
        log.warning("synthesize op=tts engine=edge lang=%s ok=0 fallback=gtts", language)

    try:
        _synthesize_gtts(text, language, path)
        log.info("synthesize op=tts engine=gtts lang=%s ok=1", language)
        return path
    except Exception:
        log.warning("synthesize op=tts engine=gtts lang=%s ok=0", language)
        return None
