"""STT stub behaviour and real-path graceful degradation (no network calls)."""

from types import SimpleNamespace

from backend.services import stt_client as s


def test_stub_mode_returns_representative_transcript():
    # conftest forces use_real_stt=False.
    out = s.transcribe("/tmp/whatever.wav", "sw")
    assert "mahindi" in out.lower()


def test_real_path_without_token_falls_back_to_stub(monkeypatch):
    monkeypatch.setattr(s, "settings", SimpleNamespace(use_real_stt=True, hf_token=""))
    out = s.transcribe("/tmp/whatever.wav", "luo")
    assert out == s._STUB_BY_LANG["luo"]


def test_real_path_api_error_falls_back_to_stub(monkeypatch):
    monkeypatch.setattr(
        s, "settings", SimpleNamespace(use_real_stt=True, hf_token="hf_x")
    )

    def boom():
        raise RuntimeError("inference down")

    monkeypatch.setattr(s, "_client", boom)
    out = s.transcribe("/tmp/whatever.wav", "sw")
    assert out == s._STUB_BY_LANG["sw"]
