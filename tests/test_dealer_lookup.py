"""Dealer lookup: county filtering, distance ordering, and safe fallback."""

from backend.services.dealers import find_nearby


def test_county_filter_returns_only_matching_county():
    results = find_nearby(county="Kisumu", limit=10)
    assert results, "expected Kisumu dealers"
    assert all(d.county == "Kisumu" for d in results)


def test_unknown_county_falls_back_to_some_dealers():
    results = find_nearby(county="Nowhere", limit=3)
    assert len(results) == 3  # never leave the farmer with nothing


def test_distance_ordering_when_coordinates_given():
    # Near Ahero, Kisumu — nearest dealer should sort first with a distance.
    results = find_nearby(county="Kisumu", lat=-0.1742, lon=34.9180, limit=3)
    assert results[0].distance_km is not None
    distances = [d.distance_km for d in results if d.distance_km is not None]
    assert distances == sorted(distances)
