from backend.core.distance import haversine_km


def test_haversine_returns_zero_for_same_point() -> None:
    assert haversine_km(-0.1, 34.7, -0.1, 34.7) == 0


def test_haversine_returns_expected_short_distance() -> None:
    distance = haversine_km(-0.1, 34.7, -0.11, 34.71)
    assert 1.5 < distance < 1.6
