"""Google Places-backed tool for finding nearby agrovets and farm suppliers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests
from pydantic import ValidationError

from backend.core.config import settings
from backend.core.distance import haversine_km
from backend.core.errors import ProviderError
from backend.core.logging_utils import get_logger
from backend.core.models import Dealer

log = get_logger("services.google_places")

_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.nationalPhoneNumber",
        "places.googleMapsUri",
    ]
)
SEARCH_KEYWORDS = (
    "agrovet",
    "farm supply",
    "veterinary pharmacy",
    "animal feed",
    "fertilizer",
    "agricultural store",
)
SEARCH_RADII_KM = (10, 20, 30)


def search_nearby_agrovets(
    lat: float,
    lon: float,
    *,
    limit: int | None = None,
) -> tuple[list[Dealer], int]:
    """Search progressively wider radii and return nearest deduplicated places."""

    if not settings.google_places_api_key:
        raise ProviderError("agrovet_search", "missing Google Places key")

    for radius_km in SEARCH_RADII_KM:
        places: dict[str, Dealer] = {}
        with ThreadPoolExecutor(max_workers=len(SEARCH_KEYWORDS)) as executor:
            keyword_results = executor.map(
                lambda keyword: _search_keyword(keyword, lat, lon, radius_km),
                SEARCH_KEYWORDS,
            )
        for results in keyword_results:
            for place in results:
                dealer = _to_dealer(place, lat, lon)
                if dealer and dealer.distance_km <= radius_km:
                    place_id = str(place.get("id") or dealer.maps_link)
                    places[place_id] = dealer

        if places:
            results = sorted(places.values(), key=lambda dealer: dealer.distance_km)
            log.info(
                "search_nearby op=places ok=1 radius_km=%d n=%d",
                radius_km,
                len(results),
            )
            return (results[:limit] if limit is not None else results), radius_km

    log.info("search_nearby op=places ok=1 radius_km=30 n=0")
    return [], SEARCH_RADII_KM[-1]


def _search_keyword(
    keyword: str,
    lat: float,
    lon: float,
    radius_km: int,
) -> list[dict[str, Any]]:
    """Run one Places Text Search request without logging user location."""

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.google_places_api_key,
        "X-Goog-FieldMask": _FIELD_MASK,
    }
    body = {
        "textQuery": keyword,
        "pageSize": 20,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": radius_km * 1000,
            }
        },
    }
    try:
        response = requests.post(
            _TEXT_SEARCH_URL,
            headers=headers,
            json=body,
            timeout=settings.provider_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("search_keyword op=places ok=0")
        raise ProviderError("agrovet_search") from exc
    return payload.get("places") or []


def _to_dealer(
    place: dict[str, Any],
    origin_lat: float,
    origin_lon: float,
) -> Dealer | None:
    """Validate one Google place and calculate its distance from the farmer."""

    location = place.get("location") or {}
    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
    except (KeyError, TypeError, ValueError):
        return None

    name = place.get("displayName", {}).get("text")
    if not name:
        return None

    maps_link = place.get("googleMapsUri") or (
        f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    )
    try:
        return Dealer(
            name=str(name),
            address=str(place.get("formattedAddress") or "Address unavailable"),
            rating=place.get("rating"),
            phone=place.get("nationalPhoneNumber"),
            lat=lat,
            lon=lon,
            distance_km=round(haversine_km(origin_lat, origin_lon, lat, lon), 1),
            maps_link=str(maps_link),
        )
    except ValidationError:
        return None
