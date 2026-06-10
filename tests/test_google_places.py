from unittest.mock import Mock

import pytest
import requests

from backend.core.config import Settings
from backend.core.errors import ProviderError
from backend.services import google_places


def _place(place_id: str, name: str, lat: float, lon: float) -> dict:
    return {
        "id": place_id,
        "displayName": {"text": name},
        "formattedAddress": "Kisumu, Kenya",
        "location": {"latitude": lat, "longitude": lon},
        "rating": 4.4,
        "nationalPhoneNumber": "+254 700 000 000",
        "googleMapsUri": f"https://maps.google.com/?cid={place_id}",
    }


def test_search_deduplicates_and_sorts_nearest(monkeypatch) -> None:
    near = _place("near", "Near Agrovet", -0.101, 34.701)
    far = _place("far", "Far Agrovet", -0.15, 34.75)
    monkeypatch.setattr(
        google_places,
        "_search_keyword",
        lambda keyword, lat, lon, radius: [far, near, near],
    )

    results, radius = google_places.search_nearby_agrovets(-0.1, 34.7)

    assert radius == 10
    assert [result.name for result in results] == ["Near Agrovet", "Far Agrovet"]


def test_search_expands_until_results_found(monkeypatch) -> None:
    place = _place("found", "Expanded Agrovet", -0.25, 34.7)
    calls = []

    def search(keyword, lat, lon, radius):
        calls.append(radius)
        return [place] if radius == 20 else []

    monkeypatch.setattr(google_places, "_search_keyword", search)
    results, radius = google_places.search_nearby_agrovets(-0.1, 34.7)

    assert results
    assert radius == 20
    assert 10 in calls and 20 in calls
    assert 30 not in calls


def test_search_returns_no_results_after_max_radius(monkeypatch) -> None:
    monkeypatch.setattr(
        google_places,
        "_search_keyword",
        lambda keyword, lat, lon, radius: [],
    )

    results, radius = google_places.search_nearby_agrovets(-0.1, 34.7)

    assert results == []
    assert radius == 30


def test_search_request_keeps_key_in_header(monkeypatch) -> None:
    response = Mock()
    response.json.return_value = {"places": []}
    post = Mock(return_value=response)
    monkeypatch.setattr(google_places.requests, "post", post)

    google_places._search_keyword("agrovet", -0.1, 34.7, 10)

    assert "key" not in post.call_args.kwargs["json"]
    assert post.call_args.kwargs["headers"]["X-Goog-Api-Key"]


def test_search_request_timeout_surfaces_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(
        google_places.requests,
        "post",
        Mock(side_effect=requests.Timeout),
    )

    with pytest.raises(ProviderError, match="agrovet_search"):
        google_places._search_keyword("agrovet", -0.1, 34.7, 10)


def test_invalid_provider_coordinates_are_dropped() -> None:
    invalid = _place("invalid", "Invalid Agrovet", 200, 34.7)

    assert google_places._to_dealer(invalid, -0.1, 34.7) is None


def test_missing_key_surfaces_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(google_places, "settings", Settings(google_places_api_key=""))

    with pytest.raises(ProviderError, match="missing Google Places key"):
        google_places.search_nearby_agrovets(-0.1, 34.7)
