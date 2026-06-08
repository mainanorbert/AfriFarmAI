"""Tiny Aya helpers and stub-mode behaviour (no network calls)."""

from types import SimpleNamespace

from backend.core.models import Diagnosis, Severity, Subject
from backend.services import tiny_aya_client as a


def test_model_id_strips_hf_prefix(monkeypatch):
    # settings is a frozen dataclass; swap the module reference instead.
    monkeypatch.setattr(a, "settings", SimpleNamespace(tiny_aya_model="CohereLabs/tiny-aya-global"))
    assert a._model_id() == "tiny-aya-global"
    monkeypatch.setattr(a, "settings", SimpleNamespace(tiny_aya_model="tiny-aya-earth"))
    assert a._model_id() == "tiny-aya-earth"


def test_clean_strips_echoed_text_tags():
    assert a._clean("<text>\nHabari\n</text>") == "Habari"
    assert a._clean("Hello") == "Hello"


def test_translate_to_english_passthrough_when_already_english():
    # source 'en' short-circuits regardless of mode.
    assert a.translate_to_english("My maize is sick", "en") == "My maize is sick"


def test_translate_to_english_passthrough_in_stub_mode():
    # conftest forces use_real_aya=False, so Swahili input is returned unchanged.
    text = "Mahindi yangu yana madoa"
    assert a.translate_to_english(text, "sw") == text


def test_localize_stub_renders_swahili_template():
    d = Diagnosis(
        subject=Subject.CROP,
        condition="Maize leaf blight",
        severity=Severity.MODERATE,
        confidence=0.8,
        treatment="Remove affected leaves.",
        prevention="Rotate crops.",
    )
    out = a.localize(d, "sw")
    assert "Tatizo linalowezekana" in out  # Swahili template label
    assert "Maize leaf blight" in out
    assert "wastani" in out  # moderate -> Swahili severity label
