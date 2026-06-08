"""TTS engine selection and fallback logic (no network calls)."""

from types import SimpleNamespace

from backend.services import tts_client as t


def test_stub_mode_uses_gtts(monkeypatch):
    # conftest forces use_real_tts=False.
    monkeypatch.setattr(t, "_synthesize_gtts", lambda text, lang: "GTTS")
    assert t.synthesize("habari", "sw") == "GTTS"


def test_real_path_dholuo_uses_mms(monkeypatch):
    monkeypatch.setattr(t, "settings", SimpleNamespace(use_real_tts=True, hf_token="hf_x"))
    monkeypatch.setattr(t, "_synthesize_mms", lambda text, model, lang: "MMS")
    monkeypatch.setattr(t, "_synthesize_gtts", lambda text, lang: "GTTS")
    assert t.synthesize("misaccess", "luo") == "MMS"


def test_real_path_falls_back_to_gtts_when_mms_fails(monkeypatch):
    monkeypatch.setattr(t, "settings", SimpleNamespace(use_real_tts=True, hf_token="hf_x"))
    monkeypatch.setattr(t, "_synthesize_mms", lambda text, model, lang: None)
    monkeypatch.setattr(t, "_synthesize_gtts", lambda text, lang: "GTTS")
    assert t.synthesize("misaccess", "luo") == "GTTS"


def test_real_path_english_uses_gtts_directly(monkeypatch):
    # No MMS model mapped for English -> straight to gTTS, never calls MMS.
    monkeypatch.setattr(t, "settings", SimpleNamespace(use_real_tts=True, hf_token="hf_x"))

    def fail(*a, **k):
        raise AssertionError("MMS should not be called for English")

    monkeypatch.setattr(t, "_synthesize_mms", fail)
    monkeypatch.setattr(t, "_synthesize_gtts", lambda text, lang: "GTTS")
    assert t.synthesize("hello", "en") == "GTTS"
