from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha1
from statistics import median
from zoneinfo import ZoneInfo

from django.utils import timezone

DB_TIME_FORMAT = "%y%m%d%H%M"
LOCAL_TZ = ZoneInfo("Europe/Berlin")


def parse_db_compact_time(value: str | None) -> datetime | None:
    if not value:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    try:
        parsed = datetime.strptime(stripped, DB_TIME_FORMAT)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(stripped)
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, LOCAL_TZ)
    return parsed


def calculate_delay_minutes(planned_time: datetime | None, updated_time: datetime | None) -> int:
    if not planned_time or not updated_time:
        return 0

    delay = int((updated_time - planned_time).total_seconds() // 60)
    return max(delay, 0)


def normalize_window_hours(window: str | None) -> int:
    if not window:
        return 2

    normalized = window.strip().lower().replace("hours", "h").replace("hour", "h")
    mapping = {
        "current": 1,
        "current-hour": 1,
        "1h": 1,
        "2h": 2,
        "4h": 4,
        "6h": 6,
    }
    if normalized in mapping:
        return mapping[normalized]

    if normalized.isdigit():
        return max(1, min(int(normalized), 12))

    if normalized.endswith("h") and normalized[:-1].isdigit():
        return max(1, min(int(normalized[:-1]), 12))

    return 2


def build_hour_slots(window_hours: int) -> list[datetime]:
    now_local = timezone.localtime(timezone.now()).replace(minute=0, second=0, microsecond=0)
    slots = [now_local + timedelta(hours=offset) for offset in range(0, window_hours + 1)]
    deduped: list[datetime] = []
    seen = set()
    for slot in slots:
        signature = (slot.date(), slot.hour)
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(slot)
    return deduped


def build_record_uid(
    station_id: int,
    board_type: str,
    external_trip_id: str,
    planned_time: datetime,
    direction: str,
) -> str:
    raw = f"{station_id}|{board_type}|{external_trip_id}|{planned_time.isoformat()}|{direction}"
    return sha1(raw.encode("utf-8")).hexdigest()


def safe_float(value: int | float, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)


def compute_delay_statistics(delays: list[int]) -> dict[str, float | int]:
    if not delays:
        return {
            "total_trains": 0,
            "average_delay": 0.0,
            "median_delay": 0.0,
            "on_time_ratio": 0.0,
            "delayed_any_ratio": 0.0,
            "delayed_over_5_ratio": 0.0,
            "delayed_over_10_ratio": 0.0,
            "maximum_delay": 0,
        }

    total = len(delays)
    on_time = len([delay for delay in delays if delay == 0])
    delayed_any = len([delay for delay in delays if delay > 0])
    over_5 = len([delay for delay in delays if delay >= 5])
    over_10 = len([delay for delay in delays if delay >= 10])

    return {
        "total_trains": total,
        "average_delay": round(sum(delays) / total, 2),
        "median_delay": round(float(median(delays)), 2),
        "on_time_ratio": safe_float(on_time, total),
        "delayed_any_ratio": safe_float(delayed_any, total),
        "delayed_over_5_ratio": safe_float(over_5, total),
        "delayed_over_10_ratio": safe_float(over_10, total),
        "maximum_delay": max(delays),
    }


def today_local() -> date:
    return timezone.localdate()
