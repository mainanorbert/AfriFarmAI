"""End-to-end pipeline behaviour on the stub path."""

from backend.core.models import AnalyzeRequest, Severity, Subject
from backend.core.orchestration import analyze


def test_maize_symptom_text_produces_crop_diagnosis_and_dealers():
    req = AnalyzeRequest(
        language="sw",
        text="Majani ya mahindi yana madoa ya manjano",
        county="Kisumu",
    )
    result = analyze(req)
    assert result.diagnosis.subject == Subject.CROP
    assert result.diagnosis.confidence >= 0.45
    assert result.localized_message  # localized output present
    assert result.dealers, "expected dealer suggestions for a confident diagnosis"


def test_gps_coordinates_rank_dealers_by_distance():
    # Coordinates at Ahero (Lakeside Farm Supplies) — it should rank first with
    # a real distance, and the list should be distance-ordered.
    req = AnalyzeRequest(
        language="sw",
        text="Mahindi yangu yana madoa ya manjano",
        lat=-0.1742,
        lon=34.9180,
    )
    result = analyze(req)
    assert result.dealers, "expected dealers for a confident diagnosis"
    assert result.dealers[0].distance_km is not None
    assert result.dealers[0].name == "Lakeside Farm Supplies"
    distances = [d.distance_km for d in result.dealers if d.distance_km is not None]
    assert distances == sorted(distances)


def test_animal_case_is_marked_for_escalation():
    req = AnalyzeRequest(language="en", text="my cow has fever", county="Nakuru")
    result = analyze(req)
    assert result.diagnosis.subject == Subject.ANIMAL
    assert result.diagnosis.escalate is True


def test_empty_input_is_low_confidence_with_no_dealers():
    req = AnalyzeRequest(language="sw", text="", county="Kisumu")
    result = analyze(req)
    assert result.low_confidence is True
    assert result.dealers == []


def test_unrecognized_symptom_falls_back_safely():
    req = AnalyzeRequest(language="en", text="something vague and unclear")
    result = analyze(req)
    assert result.low_confidence is True
    assert result.diagnosis.severity == Severity.UNKNOWN
