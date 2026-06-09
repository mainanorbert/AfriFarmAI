"""TTS language mapping and graceful failure (no network calls)."""

from backend.services import tts_client as t


def test_dholuo_maps_to_swahili_voice():
    # Dholuo has no gTTS voice; it is read with the Swahili voice.
    assert t._GTTS_LANG["luo"] == "sw"
    assert t._GTTS_LANG["sw"] == "sw"
    assert t._GTTS_LANG["en"] == "en"


def test_synthesize_returns_none_on_failure(monkeypatch):
    # Simulate gTTS being unavailable -> None, never raises.
    import gtts

    def boom(*a, **k):
        raise RuntimeError("offline")

    monkeypatch.setattr(gtts, "gTTS", boom)
    assert t.synthesize("habari", "sw") is None
