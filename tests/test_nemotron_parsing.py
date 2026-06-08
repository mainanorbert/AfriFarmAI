"""Parsing/coercion for Nemotron responses (no network calls)."""

from backend.core.models import Severity, Subject
from backend.services.nemotron_client import _extract_json, _to_diagnosis


def test_extract_plain_json_object():
    data = _extract_json('{"condition": "Fall Armyworm", "confidence": 0.8}')
    assert data == {"condition": "Fall Armyworm", "confidence": 0.8}


def test_extract_json_from_fenced_block():
    raw = "Here you go:\n```json\n{\"condition\": \"MLN\"}\n```\nthanks"
    assert _extract_json(raw) == {"condition": "MLN"}


def test_extract_strips_reasoning_then_parses():
    raw = "<think>the leaves are yellow, likely MLN</think>\n{\"condition\": \"MLN\"}"
    assert _extract_json(raw) == {"condition": "MLN"}


def test_extract_returns_none_on_garbage():
    assert _extract_json("no json here at all") is None


def test_to_diagnosis_coerces_enums_and_clamps_confidence():
    d = _to_diagnosis(
        {
            "subject": "ANIMAL",
            "condition": "East Coast Fever",
            "severity": "severe",
            "confidence": 1.7,  # out of range -> clamped
            "treatment": "see a vet",
            "prevention": "tick control",
            "escalate": True,
        }
    )
    assert d.subject == Subject.ANIMAL
    assert d.severity == Severity.SEVERE
    assert d.confidence == 1.0
    assert d.escalate is True


def test_to_diagnosis_defaults_on_missing_or_bad_fields():
    d = _to_diagnosis({"severity": "catastrophic", "confidence": "n/a"})
    assert d.subject == Subject.UNKNOWN
    assert d.severity == Severity.UNKNOWN  # unknown enum value -> default
    assert d.confidence == 0.3
    assert d.condition == "Unclear"
