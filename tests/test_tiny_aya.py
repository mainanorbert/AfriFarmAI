"""Tiny Aya helpers and degradation behaviour (no network calls)."""

from types import SimpleNamespace

from backend.core.models import Diagnosis, Severity, Subject
from backend.services import tiny_aya_client as a


def _diag():
    return Diagnosis(
        subject=Subject.CROP,
        condition="Maize leaf blight",
        severity=Severity.MODERATE,
        confidence=0.8,
        treatment="Remove affected leaves.",
        prevention="Rotate crops.",
    )


def test_model_id_strips_hf_prefix(monkeypatch):
    monkeypatch.setattr(a, "settings", SimpleNamespace(tiny_aya_model="CohereLabs/tiny-aya-global"))
    assert a._model_id() == "tiny-aya-global"
    monkeypatch.setattr(a, "settings", SimpleNamespace(tiny_aya_model="tiny-aya-earth"))
    assert a._model_id() == "tiny-aya-earth"


def test_clean_strips_echoed_text_tags():
    assert a._clean("<text>\nHabari\n</text>") == "Habari"
    assert a._clean("Hello") == "Hello"


def test_translate_to_english_passthrough_when_already_english():
    assert a.translate_to_english("My maize is sick", "en") == "My maize is sick"


def test_translate_to_english_uses_model(monkeypatch):
    monkeypatch.setattr(a, "_chat", lambda prompt: "translated to english")
    assert a.translate_to_english("Mahindi yangu", "sw") == "translated to english"


def test_translate_to_english_degrades_to_original_on_failure(monkeypatch):
    def boom(prompt):
        raise RuntimeError("cohere down")

    monkeypatch.setattr(a, "_chat", boom)
    assert a.translate_to_english("Mahindi yangu", "sw") == "Mahindi yangu"


def test_localize_english_returns_composed_english():
    out = a.localize(_diag(), "en")
    assert "Maize leaf blight" in out
    assert "Treatment:" in out


def test_localize_swahili_uses_model(monkeypatch):
    monkeypatch.setattr(a, "_chat", lambda prompt: "ujumbe kwa Kiswahili")
    assert a.localize(_diag(), "sw") == "ujumbe kwa Kiswahili"


def test_localize_degrades_to_english_on_failure(monkeypatch):
    def boom(prompt):
        raise RuntimeError("cohere down")

    monkeypatch.setattr(a, "_chat", boom)
    out = a.localize(_diag(), "sw")
    assert "Maize leaf blight" in out  # fell back to the real English diagnosis
