from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from django.conf import settings

from trains.models import Station
from trains.services.clients import DBApiClient, ExternalAPIError

SAMPLE_SEARCH_FILE = Path(settings.BASE_DIR) / "sample_data" / "stations_search.json"


def _extract_station_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        if isinstance(payload.get("result"), list):
            return [row for row in payload["result"] if isinstance(row, dict)]
        if isinstance(payload.get("stations"), list):
            return [row for row in payload["stations"] if isinstance(row, dict)]

    return []


def _station_from_payload(item: dict[str, Any]) -> dict[str, Any] | None:
    eva = ""
    eva_numbers = item.get("evaNumbers")
    if isinstance(eva_numbers, list) and eva_numbers:
        first = eva_numbers[0]
        if isinstance(first, dict):
            eva = str(first.get("number", "")).strip()

    if not eva:
        eva = str(item.get("eva", "") or item.get("eva_number", "")).strip()

    if not eva:
        return None

    position = item.get("position") or {}
    if not isinstance(position, dict):
        position = {}

    latitude = position.get("latitude") or item.get("lat")
    longitude = position.get("longitude") or item.get("lon")

    if latitude is None or longitude is None:
        eva_entries = item.get("evaNumbers")
        if isinstance(eva_entries, list):
            for eva_entry in eva_entries:
                if not isinstance(eva_entry, dict):
                    continue
                geo = eva_entry.get("geographicCoordinates")
                if not isinstance(geo, dict):
                    continue
                coords = geo.get("coordinates")
                if isinstance(coords, list) and len(coords) >= 2:
                    longitude = longitude or coords[0]
                    latitude = latitude or coords[1]
                    break

    mailing = item.get("mailingAddress") or {}
    if not isinstance(mailing, dict):
        mailing = {}

    name = str(item.get("name", "")).strip()
    if not name:
        return None

    return {
        "eva_number": eva,
        "name": name,
        "city": str(mailing.get("city", "") or item.get("city", "")).strip(),
        "state": str(mailing.get("state", "") or item.get("state", "")).strip(),
        "country": str(mailing.get("country", "DE") or "DE").strip(),
        "latitude": latitude,
        "longitude": longitude,
        "ds100": str(item.get("ds100", "")).strip(),
        "short_description": str(item.get("federalState", "") or item.get("description", "")).strip(),
    }


def _normalize_query_text(value: str) -> str:
    lowered = value.strip().lower()
    lowered = (
        lowered.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _query_matches_station(query: str, station: dict[str, Any]) -> bool:
    if not query:
        return True

    query_norm = _normalize_query_text(query)
    query_loose = query_norm.replace("ae", "a").replace("oe", "o").replace("ue", "u")

    fields = [
        str(station.get("name", "")),
        str(station.get("city", "")),
        str(station.get("eva_number", "")),
    ]
    haystack = _normalize_query_text(" ".join(fields))
    haystack_loose = haystack.replace("ae", "a").replace("oe", "o").replace("ue", "u")

    return (
        query_norm in haystack
        or query_norm in haystack_loose
        or query_loose in haystack
        or query_loose in haystack_loose
    )


def _load_sample_station_rows(query: str) -> list[dict[str, Any]]:
    if not SAMPLE_SEARCH_FILE.exists():
        return []

    try:
        payload = json.loads(SAMPLE_SEARCH_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    rows = _extract_station_rows(payload)
    normalized_rows = []
    for row in rows:
        station = _station_from_payload(row)
        if not station:
            continue
        if query and not _query_matches_station(query, station):
            continue
        normalized_rows.append(station)
    return normalized_rows


def search_stations_remote(query: str, limit: int = 12) -> list[dict[str, Any]]:
    if settings.DEMO_USE_SAMPLE_DATA:
        return _load_sample_station_rows(query)[:limit]

    if not settings.DB_API_KEY:
        if settings.ALLOW_SAMPLE_FALLBACK:
            return _load_sample_station_rows(query)[:limit]
        return []

    client = DBApiClient(settings.DB_STADA_BASE_URL)

    params: dict[str, str] = {"limit": "10000"}
    if query.isdigit():
        params = {"eva": query}

    try:
        payload = client.get_json("stations", params=params)
    except ExternalAPIError:
        if settings.ALLOW_SAMPLE_FALLBACK:
            return _load_sample_station_rows(query)[:limit]
        return []

    rows = _extract_station_rows(payload)
    result = []
    for item in rows:
        station = _station_from_payload(item)
        if station and _query_matches_station(query, station):
            result.append(station)
    return result[:limit]


def upsert_station(station_data: dict[str, Any]) -> Station:
    defaults = {
        "name": station_data.get("name", ""),
        "city": station_data.get("city", ""),
        "state": station_data.get("state", ""),
        "country": station_data.get("country", "DE"),
        "latitude": station_data.get("latitude"),
        "longitude": station_data.get("longitude"),
        "ds100": station_data.get("ds100", ""),
        "short_description": station_data.get("short_description", ""),
    }

    station, _ = Station.objects.update_or_create(
        eva_number=station_data["eva_number"],
        defaults=defaults,
    )
    return station
