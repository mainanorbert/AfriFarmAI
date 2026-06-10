from backend.core import geolocation


def test_browser_coordinates_are_used() -> None:
    assert geolocation.resolve_location(-0.1, 34.7) == (-0.1, 34.7)


def test_unavailable_browser_coordinates_return_none() -> None:
    assert geolocation.resolve_location(None, None) is None
    assert geolocation.resolve_location(-0.1, None) is None
