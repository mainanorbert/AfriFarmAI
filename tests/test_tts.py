"""VoxCPM2 TTS integration and graceful fallback behavior."""

from types import SimpleNamespace

import pytest

from backend.services import tts_client as t


@pytest.fixture
def modal_settings(monkeypatch):
    configured = SimpleNamespace(
        modal_tts_url="https://modal.test/speech",
        modal_key="test-key",
        modal_secret="test-secret",
        modal_tts_timeout_seconds=300,
    )
    monkeypatch.setattr(t, "settings", configured)
    return configured


def test_synthesize_voxcpm_sends_authenticated_request(
    monkeypatch, tmp_path, modal_settings
):
    path = tmp_path / "reply.wav"

    class Response:
        headers = {"content-type": "audio/wav"}
        content = b"wav-audio"

        @staticmethod
        def raise_for_status():
            return None

    def post(url, json, headers, timeout):
        assert url == modal_settings.modal_tts_url
        assert json == {"text": "habari"}
        assert headers == {
            "Modal-Key": modal_settings.modal_key,
            "Modal-Secret": modal_settings.modal_secret,
        }
        assert timeout == 300
        return Response()

    monkeypatch.setattr(t.tempfile, "mktemp", lambda suffix: str(path))
    monkeypatch.setattr(t.requests, "post", post)
    monkeypatch.setattr(
        t,
        "_synthesize_gtts",
        lambda *args: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
    )

    assert t.synthesize("habari", "sw") == str(path)
    assert path.read_bytes() == b"wav-audio"


def test_synthesize_falls_back_to_gtts_when_voxcpm_fails(monkeypatch, tmp_path):
    paths = {
        ".wav": str(tmp_path / "failed.wav"),
        ".mp3": str(tmp_path / "fallback.mp3"),
    }
    fallback_calls = []
    monkeypatch.setattr(t.tempfile, "mktemp", lambda suffix: paths[suffix])
    monkeypatch.setattr(
        t, "_synthesize_voxcpm", lambda *args: (_ for _ in ()).throw(RuntimeError())
    )
    monkeypatch.setattr(t, "_synthesize_gtts", lambda *args: fallback_calls.append(args))

    assert t.synthesize("habari", "sw") == paths[".mp3"]
    assert fallback_calls == [("habari", "sw", paths[".mp3"])]


def test_voxcpm_supports_all_application_languages():
    assert t._VOXCPM_LANGUAGES == {"sw", "en"}


def test_synthesize_returns_none_when_both_providers_fail(monkeypatch):
    monkeypatch.setattr(
        t, "_synthesize_voxcpm", lambda *args: (_ for _ in ()).throw(RuntimeError())
    )
    monkeypatch.setattr(
        t, "_synthesize_gtts", lambda *args: (_ for _ in ()).throw(RuntimeError())
    )

    assert t.synthesize("habari", "sw") is None


def test_voxcpm_rejects_non_audio_response(monkeypatch, tmp_path, modal_settings):
    class Response:
        headers = {"content-type": "application/json"}
        content = b'{"error":"failed"}'

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(t.requests, "post", lambda *args, **kwargs: Response())

    with pytest.raises(RuntimeError, match="invalid audio response"):
        t._synthesize_voxcpm("habari", str(tmp_path / "reply.wav"))
