"""Resolve validated browser coordinates for nearby-agrovet search."""

from __future__ import annotations

from typing import Optional

def resolve_location(
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[tuple[float, float]]:
    """Return browser coordinates when both values are available."""

    if lat is not None and lon is not None:
        return lat, lon
    return None
