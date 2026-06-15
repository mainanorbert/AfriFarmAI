"""End-to-end pipeline behaviour with mocked live providers."""

import pytest

from backend.core import orchestration as orch
from backend.core.errors import ProviderError
from backend.core.models import AnalyzeRequest, Dealer, Diagnosis, Severity, Subject


@pytest.fixture(autouse=True)
def _mock_providers(monkeypatch):
    """Stand in for the network providers so tests are deterministic/offline."""

    monkeypatch.setattr(orch.stt_client, "transcribe", lambda path, lang: "transcribed")
    monkeypatch.setattr(
        orch.tiny_aya_client, "translate_to_english", lambda text, lang: text
    )
    monkeypatch.setattr(
        orch.tiny_aya_client,
        "localize_condition",
        lambda condition, lang: "Ugonjwa wa majani ya mahindi",
    )
    monkeypatch.setattr(orch.tiny_aya_client, "localize", lambda d, lang: "localized")
    monkeypatch.setattr(orch.tts_client, "synthesize", lambda text, lang: "/tmp/a.mp3")
    monkeypatch.setattr(
        orch,
        "resolve_location",
        lambda lat, lon: (lat, lon) if lat is not None and lon is not None else None,
    )
    monkeypatch.setattr(
        orch.google_places,
        "search_nearby_agrovets",
        lambda lat, lon: (
            [
                Dealer(
                    name="Nearby Agrovet",
                    address="Kisumu, Kenya",
                    rating=4.5,
                    phone="+254700000000",
                    lat=-0.11,
                    lon=34.71,
                    distance_km=1.5,
                    maps_link="https://maps.google.com/example",
                )
            ],
            10,
        ),
    )


def _crop(confidence=0.8):
    return Diagnosis(
        subject=Subject.CROP,
        condition="Maize leaf blight",
        severity=Severity.MODERATE,
        confidence=confidence,
        treatment="Remove affected leaves.",
        prevention="Rotate crops.",
    )


def test_confident_diagnosis_produces_localized_message_and_dealers(monkeypatch):
    monkeypatch.setattr(orch.nemotron_client, "diagnose", lambda t, img=None: _crop())
    result = orch.analyze(
        AnalyzeRequest(language="sw", text="mahindi", lat=-0.1, lon=34.7)
    )
    assert result.diagnosis.subject == Subject.CROP
    assert result.localized_condition == "Ugonjwa wa majani ya mahindi"
    assert result.localized_message == "localized"
    assert result.audio_reply_path == "/tmp/a.mp3"
    assert result.dealers, "expected dealers for a confident diagnosis"
    assert result.dealer_search_status == "success"


def test_gps_coordinates_rank_dealers_by_distance(monkeypatch):
    monkeypatch.setattr(orch.nemotron_client, "diagnose", lambda t, img=None: _crop())
    result = orch.analyze(
        AnalyzeRequest(language="sw", text="mahindi", lat=-0.1742, lon=34.9180)
    )
    assert result.dealers[0].name == "Nearby Agrovet"
    distances = [d.distance_km for d in result.dealers if d.distance_km is not None]
    assert distances == sorted(distances)


def test_animal_case_is_marked_for_escalation(monkeypatch):
    animal = Diagnosis(
        subject=Subject.ANIMAL,
        condition="East Coast Fever",
        severity=Severity.SEVERE,
        confidence=0.7,
        treatment="See a vet.",
        prevention="Tick control.",
    )
    monkeypatch.setattr(orch.nemotron_client, "diagnose", lambda t, img=None: animal)
    result = orch.analyze(AnalyzeRequest(language="en", text="my cow has fever"))
    assert result.diagnosis.escalate is True


def test_low_confidence_is_gated_and_drops_dealers(monkeypatch):
    monkeypatch.setattr(
        orch.nemotron_client, "diagnose", lambda t, img=None: _crop(confidence=0.1)
    )
    result = orch.analyze(AnalyzeRequest(language="en", text="something vague"))
    assert result.low_confidence is True
    assert result.localized_condition is None
    assert result.dealers == []
    assert result.dealer_search_status == "not_requested"


def test_empty_input_returns_notice_without_calling_providers():
    result = orch.analyze(AnalyzeRequest(language="sw", text=""))
    assert result.low_confidence is True
    assert result.dealers == []
    assert result.diagnosis.condition == "No input"


def test_transcription_failure_returns_notice(monkeypatch):
    def boom(path, lang):
        raise ProviderError("transcription")

    monkeypatch.setattr(orch.stt_client, "transcribe", boom)
    result = orch.analyze(AnalyzeRequest(language="sw", audio_path="/tmp/x.wav"))
    assert result.low_confidence is True
    assert result.dealers == []
    assert result.diagnosis.condition == "Audio not understood"


def test_diagnosis_failure_returns_notice(monkeypatch):
    def boom(t, img=None):
        raise ProviderError("diagnosis")

    monkeypatch.setattr(orch.nemotron_client, "diagnose", boom)
    result = orch.analyze(AnalyzeRequest(language="en", text="my maize is sick"))
    assert result.low_confidence is True
    assert result.diagnosis.condition == "Service busy"


def test_image_diagnosis_failure_returns_notice(monkeypatch):
    def boom(*args):
        raise ProviderError("diagnosis")

    monkeypatch.setattr(orch.nemotron_client, "diagnose", boom)

    result = orch.analyze(AnalyzeRequest(language="en", image_path="/tmp/maize.jpg"))

    assert result.low_confidence is True
    assert result.diagnosis.condition == "Service busy"


def test_swahili_diagnosis_failure_returns_swahili_notice(monkeypatch):
    def boom(*args):
        raise ProviderError("diagnosis")

    monkeypatch.setattr(orch.nemotron_client, "diagnose", boom)

    result = orch.analyze(AnalyzeRequest(language="sw", image_path="/tmp/maize.jpg"))

    assert "Huduma ya utambuzi haipatikani" in result.localized_message
    assert "diagnosis service" not in result.localized_message


def test_confident_diagnosis_without_location_requests_location(monkeypatch):
    monkeypatch.setattr(orch.nemotron_client, "diagnose", lambda t, img=None: _crop())
    result = orch.analyze(AnalyzeRequest(language="en", text="maize spots"))

    assert result.dealers == []
    assert result.dealer_search_status == "location_required"


def test_agrovet_search_failure_does_not_hide_diagnosis(monkeypatch):
    monkeypatch.setattr(orch.nemotron_client, "diagnose", lambda t, img=None: _crop())

    def fail(lat, lon):
        raise ProviderError("agrovet_search")

    monkeypatch.setattr(orch.google_places, "search_nearby_agrovets", fail)
    result = orch.analyze(
        AnalyzeRequest(language="en", text="maize spots", lat=-0.1, lon=34.7)
    )

    assert result.diagnosis.condition == "Maize leaf blight"
    assert result.dealer_search_status == "error"
