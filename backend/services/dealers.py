"""Agro-dealer lookup over a bundled CSV (no DB, low-connectivity friendly).

Selection is by county; when farmer coordinates are available, results are
ordered by great-circle distance. Only approved dealer phone numbers are
surfaced — no other contact details.
"""

from __future__ import annotations

import csv
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Optional

from backend.core.logging_utils import get_logger
from backend.core.models import Dealer

log = get_logger("services.dealers")

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "dealers.csv"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""

    r = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def _load() -> list[Dealer]:
    """Load and validate dealers from the bundled CSV."""

    dealers: list[Dealer] = []
    with _DATA_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lat = float(row["lat"]) if row.get("lat") else None
            lon = float(row["lon"]) if row.get("lon") else None
            dealers.append(
                Dealer(
                    name=row["name"],
                    county=row["county"],
                    town=row["town"],
                    phone=row["phone"],
                    specialties=row["specialties"],
                    lat=lat,
                    lon=lon,
                )
            )
    return dealers


def find_nearby(
    county: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    limit: int = 3,
) -> list[Dealer]:
    """Return up to ``limit`` dealers, filtered by county and ordered by distance.

    Falls back to all dealers when no county matches, so a farmer always sees
    at least some contacts.
    """

    dealers = _load()

    if county:
        matches = [d for d in dealers if d.county.lower() == county.strip().lower()]
        if matches:
            dealers = matches

    if lat is not None and lon is not None:
        for d in dealers:
            if d.lat is not None and d.lon is not None:
                d.distance_km = round(_haversine_km(lat, lon, d.lat, d.lon), 1)
        dealers.sort(key=lambda d: (d.distance_km is None, d.distance_km or 0.0))

    log.info("find_nearby op=dealers county=%s n=%d", bool(county), min(limit, len(dealers)))
    return dealers[:limit]
