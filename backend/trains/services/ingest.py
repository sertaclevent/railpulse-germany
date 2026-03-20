from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from trains.models import DailyStationStats, Station, TrainSnapshot
from trains.services.clients import ExternalAPIError
from trains.services.helpers import (
    build_hour_slots,
    build_record_uid,
    calculate_delay_minutes,
    compute_delay_statistics,
    today_local,
)
from trains.services.timetables import (
    TimetableParseError,
    build_change_map,
    fetch_and_parse_board,
    normalize_for_storage,
)

SAMPLE_BOARD_FILE = Path(settings.BASE_DIR) / "sample_data" / "board_departure_munich.json"
SAMPLE_ARRIVAL_FILE = Path(settings.BASE_DIR) / "sample_data" / "board_arrival_munich.json"


def _sample_file_for_type(board_type: str) -> Path:
    if board_type == TrainSnapshot.BOARD_TYPE_ARRIVAL:
        return SAMPLE_ARRIVAL_FILE
    return SAMPLE_BOARD_FILE


def _parse_iso_datetime(value: str | None):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed


def load_sample_board_records(board_type: str) -> list[dict[str, Any]]:
    sample_path = _sample_file_for_type(board_type)
    if not sample_path.exists():
        return []

    try:
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    records: list[dict[str, Any]] = []
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []

    for row in rows:
        if not isinstance(row, dict):
            continue
        now = datetime.now().astimezone()
        minutes_from_now = row.get("minutes_from_now")
        delay_minutes = max(int(row.get("delay_minutes", 0)), 0)

        if isinstance(minutes_from_now, int):
            planned_time = now + timedelta(minutes=minutes_from_now)
            updated_time = planned_time + timedelta(minutes=delay_minutes)
        else:
            planned_time = _parse_iso_datetime(row.get("planned_time"))
            updated_time = _parse_iso_datetime(row.get("updated_time")) or planned_time
        if not planned_time:
            continue

        records.append(
            {
                "external_trip_id": str(row.get("external_trip_id", "sample")),
                "train_name": str(row.get("train_name", "Unknown")),
                "category": str(row.get("category", "")),
                "direction": str(row.get("direction", "Unknown")),
                "planned_time": planned_time,
                "updated_time": updated_time,
                "delay_minutes": delay_minutes,
                "platform": str(row.get("platform", "")),
                "status": str(row.get("status", "scheduled")),
                "raw_payload": row,
            }
        )

    return records


def _persist_records(station: Station, board_type: str, records: list[dict[str, Any]]) -> dict[str, int]:
    inserted = 0
    updated = 0

    with transaction.atomic():
        for record in records:
            normalized = normalize_for_storage(record)
            external_trip_id = normalized.get("external_trip_id") or normalized["train_name"]
            record_uid = build_record_uid(
                station.id,
                board_type,
                str(external_trip_id),
                normalized["planned_time"],
                normalized["direction"],
            )

            defaults = {
                "station": station,
                "board_type": board_type,
                "external_trip_id": str(external_trip_id),
                "train_name": normalized["train_name"],
                "category": normalized.get("category", ""),
                "direction": normalized["direction"],
                "planned_time": normalized["planned_time"],
                "updated_time": normalized.get("updated_time") or normalized["planned_time"],
                "delay_minutes": calculate_delay_minutes(
                    normalized["planned_time"],
                    normalized.get("updated_time") or normalized["planned_time"],
                ),
                "platform": normalized.get("platform", ""),
                "status": normalized.get("status", "scheduled"),
                "raw_payload": normalized.get("raw_payload", {}),
                "service_date": normalized["planned_time"].date(),
            }

            _, created = TrainSnapshot.objects.update_or_create(
                record_uid=record_uid,
                defaults=defaults,
            )
            if created:
                inserted += 1
            else:
                updated += 1

    return {"inserted": inserted, "updated": updated}


def _store_daily_stats(station: Station, board_type: str) -> None:
    stats_date = today_local()
    snapshots = TrainSnapshot.objects.filter(
        station=station,
        board_type=board_type,
        service_date=stats_date,
    )
    delays = list(snapshots.values_list("delay_minutes", flat=True))
    stats = compute_delay_statistics(delays)

    DailyStationStats.objects.update_or_create(
        station=station,
        board_type=board_type,
        stats_date=stats_date,
        defaults=stats,
    )


def _has_fresh_snapshot_cache(station: Station, board_type: str) -> bool:
    ttl_seconds = max(int(getattr(settings, "REFRESH_TTL_SECONDS", 600)), 0)
    if ttl_seconds <= 0:
        return False

    latest_updated = (
        TrainSnapshot.objects.filter(
            station=station,
            board_type=board_type,
            service_date=today_local(),
        )
        .order_by("-updated_at")
        .values_list("updated_at", flat=True)
        .first()
    )
    if not latest_updated:
        return False

    return (timezone.now() - latest_updated).total_seconds() < ttl_seconds


def refresh_station_board(station: Station, board_type: str, window_hours: int) -> dict[str, Any]:
    if _has_fresh_snapshot_cache(station, board_type):
        _store_daily_stats(station, board_type)
        return {
            "source": "cached_data",
            "records_received": 0,
            "inserted": 0,
            "updated": 0,
        }

    records: list[dict[str, Any]] = []
    data_source = "external_api"

    if settings.DEMO_USE_SAMPLE_DATA:
        records = load_sample_board_records(board_type)
        data_source = "sample_data"
    elif not settings.DB_API_KEY:
        if not settings.ALLOW_SAMPLE_FALLBACK:
            raise ExternalAPIError("DB API key is missing.")
        records = load_sample_board_records(board_type)
        data_source = "sample_data"
    else:
        try:
            slots = build_hour_slots(window_hours)
            change_map = build_change_map(station.eva_number, board_type)
            for slot in slots:
                records.extend(
                    fetch_and_parse_board(
                        eva_number=station.eva_number,
                        service_date=slot.date(),
                        hour=slot.hour,
                        board_type=board_type,
                        change_map=change_map,
                    )
                )
        except (ExternalAPIError, TimetableParseError):
            if not settings.ALLOW_SAMPLE_FALLBACK:
                raise
            records = load_sample_board_records(board_type)
            data_source = "sample_data"

    persist_meta = _persist_records(station, board_type, records)
    _store_daily_stats(station, board_type)

    return {
        "source": data_source,
        "records_received": len(records),
        **persist_meta,
    }
