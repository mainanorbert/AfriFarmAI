"""STT language routing and error behaviour (no network calls)."""

from types import SimpleNamespace

import pytest

from backend.core.errors import ProviderError
from backend.services import stt_client as s


def test_english_routes_to_cohere(monkeypatch):
    monkeypatch.setattr(s, "_transcribe_cohere", lambda p, l: "COHERE")
    monkeypatch.setattr(s, "_transcribe_whisper", lambda p, l: "WHISPER")
    assert s.transcribe("/tmp/a.wav", "en") == "COHERE"


def test_swahili_routes_to_whisper(monkeypatch):
    monkeypatch.setattr(s, "_transcribe_cohere", lambda p, l: "COHERE")
    monkeypatch.setattr(s, "_transcribe_whisper", lambda p, l: "WHISPER")
    assert s.transcribe("/tmp/a.wav", "sw") == "WHISPER"


def test_whisper_without_token_raises(monkeypatch):
    monkeypatch.setattr(s, "settings", SimpleNamespace(hf_token=""))
    with pytest.raises(ProviderError):
        s._transcribe_whisper("/tmp/a.wav", "sw")


def test_cohere_without_key_raises(monkeypatch):
    monkeypatch.setattr(s, "settings", SimpleNamespace(cohere_api_key=""))
    with pytest.raises(ProviderError):
        s._transcribe_cohere("/tmp/a.wav", "en")


def test_whisper_api_error_raises(monkeypatch):
    monkeypatch.setattr(s, "settings", SimpleNamespace(hf_token="hf_x"))

    def boom():
        raise RuntimeError("inference down")

    monkeypatch.setattr(s, "_whisper_client", boom)
    with pytest.raises(ProviderError):
        s._transcribe_whisper("/tmp/a.wav", "sw")
