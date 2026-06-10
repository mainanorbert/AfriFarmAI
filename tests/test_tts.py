"""TTS voice selection and graceful fallback behavior."""

from backend.services import tts_client as t


def test_languages_map_to_kenyan_edge_voices():
    assert t._EDGE_VOICE["sw"] == "sw-KE-ZuriNeural"
    assert t._EDGE_VOICE["luo"] == "sw-KE-ZuriNeural"
    assert t._EDGE_VOICE["en"] == "en-KE-AsiliaNeural"


def test_synthesize_prefers_edge_tts(monkeypatch, tmp_path):
    path = tmp_path / "edge.mp3"

    async def edge(text, language, output):
        assert (text, language, output) == ("habari", "sw", str(path))

    monkeypatch.setattr(t.tempfile, "mktemp", lambda suffix: str(path))
    monkeypatch.setattr(t, "_synthesize_edge", edge)
    monkeypatch.setattr(
        t,
        "_synthesize_gtts",
        lambda *args: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
    )

    assert t.synthesize("habari", "sw") == str(path)


def test_synthesize_falls_back_to_gtts(monkeypatch, tmp_path):
    path = tmp_path / "fallback.mp3"

    async def edge_failure(*args):
        raise RuntimeError("edge unavailable")

    fallback_calls = []
    monkeypatch.setattr(t.tempfile, "mktemp", lambda suffix: str(path))
    monkeypatch.setattr(t, "_synthesize_edge", edge_failure)
    monkeypatch.setattr(t, "_synthesize_gtts", lambda *args: fallback_calls.append(args))

    assert t.synthesize("habari", "sw") == str(path)
    assert fallback_calls == [("habari", "sw", str(path))]


def test_synthesize_returns_none_when_both_providers_fail(monkeypatch):
    async def edge_failure(*args):
        raise RuntimeError("edge unavailable")

    def gtts_failure(*args):
        raise RuntimeError("gtts unavailable")

    monkeypatch.setattr(t, "_synthesize_edge", edge_failure)
    monkeypatch.setattr(t, "_synthesize_gtts", gtts_failure)

    assert t.synthesize("habari", "sw") is None
