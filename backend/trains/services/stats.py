from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import sqrt

from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import ExtractHour
from django.utils import timezone

from trains.models import TrainSnapshot
from trains.services.helpers import compute_delay_statistics


def queryset_delay_stats(queryset) -> dict:
    delays = list(queryset.values_list("delay_minutes", flat=True))
    return compute_delay_statistics(delays)


def hourly_average_delay(queryset) -> list[dict[str, int | float]]:
    aggregated = (
        queryset.annotate(hour=ExtractHour("planned_time"))
        .values("hour")
        .annotate(avg_delay=Avg("delay_minutes"), trains=Count("id"))
        .order_by("hour")
    )

    return [
        {
            "hour": int(row["hour"]),
            "average_delay": round(float(row["avg_delay"] or 0), 2),
            "trains": int(row["trains"]),
        }
        for row in aggregated
        if row["hour"] is not None
    ]


def delay_distribution(queryset) -> list[dict[str, int]]:
    bins = {
        "0-4": 0,
        "5-9": 0,
        "10-19": 0,
        "20-39": 0,
        "40+": 0,
    }

    for delay in queryset.values_list("delay_minutes", flat=True):
        if delay <= 4:
            bins["0-4"] += 1
        elif delay <= 9:
            bins["5-9"] += 1
        elif delay <= 19:
            bins["10-19"] += 1
        elif delay <= 39:
            bins["20-39"] += 1
        else:
            bins["40+"] += 1

    return [{"bucket": bucket, "count": count} for bucket, count in bins.items()]


def dataset_window_queryset(base_queryset, window_hours: int):
    now = timezone.now()
    window_end = now + timedelta(hours=window_hours)
    return base_queryset.filter(planned_time__gte=now, planned_time__lte=window_end)


def today_queryset(base_queryset):
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    return base_queryset.filter(service_date__gte=today, service_date__lt=tomorrow)


def basic_queryset_summary(queryset) -> dict:
    aggregated = queryset.aggregate(
        total_trains=Count("id"),
        average_delay=Avg("delay_minutes"),
        maximum_delay=Max("delay_minutes"),
    )
    return {
        "total_trains": int(aggregated["total_trains"] or 0),
        "average_delay": round(float(aggregated["average_delay"] or 0), 2),
        "maximum_delay": int(aggregated["maximum_delay"] or 0),
    }


def _ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(part / total, 4)


def _wilson_bounds(successes: int, total: int, z: float = 1.96) -> dict[str, float]:
    if total <= 0:
        return {"lower": 0.0, "upper": 0.0}

    p = successes / total
    denominator = 1 + (z * z / total)
    centre = (p + (z * z / (2 * total))) / denominator
    margin = z * sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denominator

    return {
        "lower": round(max(0.0, centre - margin), 4),
        "upper": round(min(1.0, centre + margin), 4),
    }


def _risk_band(delay_probability: float) -> str:
    if delay_probability >= 0.6:
        return "high"
    if delay_probability >= 0.35:
        return "medium"
    return "low"


def _build_risk_forecast(delays: list[int], average_delay: float | None = None) -> dict:
    total = len(delays)
    delayed_any = len([delay for delay in delays if delay > 0])
    delayed_over_5 = len([delay for delay in delays if delay >= 5])
    delayed_over_10 = len([delay for delay in delays if delay >= 10])

    avg_delay = round(float(average_delay), 2) if average_delay is not None else round(sum(delays) / total, 2) if total else 0.0

    delay_probability = _ratio(delayed_any, total)
    return {
        "sample_size": total,
        "delay_probability": delay_probability,
        "on_time_probability": _ratio(total - delayed_any, total),
        "delay_over_5_probability": _ratio(delayed_over_5, total),
        "delay_over_10_probability": _ratio(delayed_over_10, total),
        "expected_delay_minutes": avg_delay,
        "delay_probability_confidence_95": _wilson_bounds(delayed_any, total),
        "risk_band": _risk_band(delay_probability),
    }


def daily_delay_trends(base_queryset, days: int = 14) -> list[dict]:
    today = timezone.localdate()
    start_date = today - timedelta(days=max(days - 1, 0))

    queryset = base_queryset.filter(service_date__gte=start_date, service_date__lte=today).order_by("service_date")

    grouped_delays: dict[date, list[int]] = defaultdict(list)
    for service_date, delay_minutes in queryset.values_list("service_date", "delay_minutes"):
        grouped_delays[service_date].append(int(delay_minutes))

    trends: list[dict] = []
    cursor = start_date
    while cursor <= today:
        delays = grouped_delays.get(cursor, [])
        stats = compute_delay_statistics(delays)
        trends.append(
            {
                "date": cursor.isoformat(),
                **stats,
            }
        )
        cursor += timedelta(days=1)

    return trends


def weekly_delay_trends(base_queryset, weeks: int = 8) -> list[dict]:
    weeks = max(weeks, 1)
    today = timezone.localdate()
    current_week_start = today - timedelta(days=today.weekday())
    earliest_week_start = current_week_start - timedelta(days=(weeks - 1) * 7)

    queryset = base_queryset.filter(service_date__gte=earliest_week_start, service_date__lte=today).order_by(
        "service_date"
    )

    grouped_delays: dict[date, list[int]] = defaultdict(list)
    for service_date, delay_minutes in queryset.values_list("service_date", "delay_minutes"):
        week_start = service_date - timedelta(days=service_date.weekday())
        grouped_delays[week_start].append(int(delay_minutes))

    trends: list[dict] = []
    cursor = earliest_week_start
    while cursor <= current_week_start:
        week_end = cursor + timedelta(days=6)
        delays = grouped_delays.get(cursor, [])
        stats = compute_delay_statistics(delays)
        trends.append(
            {
                "week_start": cursor.isoformat(),
                "week_end": week_end.isoformat(),
                **stats,
            }
        )
        cursor += timedelta(days=7)

    return trends


def _line_aggregate_rows(days: int, min_trains: int):
    today = timezone.localdate()
    start_date = today - timedelta(days=max(days - 1, 0))
    queryset = TrainSnapshot.objects.filter(service_date__gte=start_date, service_date__lte=today)

    return (
        queryset.values("train_name")
        .annotate(
            total_trains=Count("id"),
            average_delay=Avg("delay_minutes"),
            maximum_delay=Max("delay_minutes"),
            on_time_count=Count("id", filter=Q(delay_minutes=0)),
            delayed_any_count=Count("id", filter=Q(delay_minutes__gt=0)),
            delayed_over_5_count=Count("id", filter=Q(delay_minutes__gte=5)),
            delayed_over_10_count=Count("id", filter=Q(delay_minutes__gte=10)),
            stations_covered=Count("station_id", distinct=True),
        )
        .filter(total_trains__gte=max(min_trains, 1))
    )


def line_rankings(days: int = 14, min_trains: int = 20, top_n: int = 5) -> dict[str, list[dict]]:
    rows = list(_line_aggregate_rows(days=days, min_trains=min_trains))
    parsed_rows: list[dict] = []
    for row in rows:
        total = int(row["total_trains"] or 0)
        on_time = int(row["on_time_count"] or 0)
        delayed_any = int(row["delayed_any_count"] or 0)
        delayed_over_5 = int(row["delayed_over_5_count"] or 0)
        delayed_over_10 = int(row["delayed_over_10_count"] or 0)
        delay_probability = _ratio(delayed_any, total)
        parsed_rows.append(
            {
                "line_name": row["train_name"],
                "total_trains": total,
                "average_delay": round(float(row["average_delay"] or 0), 2),
                "maximum_delay": int(row["maximum_delay"] or 0),
                "on_time_ratio": _ratio(on_time, total),
                "delayed_any_ratio": delay_probability,
                "delayed_over_5_ratio": _ratio(delayed_over_5, total),
                "delayed_over_10_ratio": _ratio(delayed_over_10, total),
                "stations_covered": int(row["stations_covered"] or 0),
                "risk_band": _risk_band(delay_probability),
            }
        )

    most_punctual = sorted(parsed_rows, key=lambda row: (row["average_delay"], row["delayed_any_ratio"]))[:top_n]
    most_delayed = sorted(parsed_rows, key=lambda row: (-row["average_delay"], -row["delayed_any_ratio"]))[:top_n]

    return {"most_punctual": most_punctual, "most_delayed": most_delayed}


def line_stats(line_name: str, days: int = 30, top_stations: int = 10) -> dict:
    today = timezone.localdate()
    start_date = today - timedelta(days=max(days - 1, 0))
    queryset = TrainSnapshot.objects.filter(train_name=line_name, service_date__gte=start_date, service_date__lte=today)

    delays = [int(value) for value in queryset.values_list("delay_minutes", flat=True)]
    summary = compute_delay_statistics(delays)
    risk_forecast = _build_risk_forecast(delays, average_delay=float(summary["average_delay"]))

    daily_map: dict[date, list[int]] = defaultdict(list)
    for service_date, delay_minutes in queryset.values_list("service_date", "delay_minutes"):
        daily_map[service_date].append(int(delay_minutes))

    daily: list[dict] = []
    cursor = start_date
    while cursor <= today:
        stats = compute_delay_statistics(daily_map.get(cursor, []))
        daily.append({"date": cursor.isoformat(), **stats})
        cursor += timedelta(days=1)

    weeks = max((days + 6) // 7, 1)
    weekly = weekly_delay_trends(queryset, weeks=weeks)

    station_rows = (
        queryset.values("station_id", "station__name", "station__city")
        .annotate(
            total_trains=Count("id"),
            average_delay=Avg("delay_minutes"),
            maximum_delay=Max("delay_minutes"),
            on_time_count=Count("id", filter=Q(delay_minutes=0)),
            delayed_any_count=Count("id", filter=Q(delay_minutes__gt=0)),
            delayed_over_5_count=Count("id", filter=Q(delay_minutes__gte=5)),
            delayed_over_10_count=Count("id", filter=Q(delay_minutes__gte=10)),
        )
        .order_by("-total_trains", "-average_delay")[: max(top_stations, 1)]
    )

    station_profile = []
    for row in station_rows:
        total = int(row["total_trains"] or 0)
        delayed_any = int(row["delayed_any_count"] or 0)
        station_profile.append(
            {
                "station_id": int(row["station_id"]),
                "name": row["station__name"],
                "city": row["station__city"] or "",
                "total_trains": total,
                "average_delay": round(float(row["average_delay"] or 0), 2),
                "maximum_delay": int(row["maximum_delay"] or 0),
                "on_time_ratio": _ratio(int(row["on_time_count"] or 0), total),
                "delay_probability": _ratio(delayed_any, total),
                "delay_over_5_probability": _ratio(int(row["delayed_over_5_count"] or 0), total),
                "delay_over_10_probability": _ratio(int(row["delayed_over_10_count"] or 0), total),
                "delay_probability_confidence_95": _wilson_bounds(delayed_any, total),
            }
        )

    most_risky_stations = sorted(
        station_profile,
        key=lambda station: (-station["delay_probability"], -station["average_delay"], -station["total_trains"]),
    )[:5]

    return {
        "summary": summary,
        "risk_forecast": risk_forecast,
        "daily": daily,
        "weekly": weekly,
        "top_stations": station_profile,
        "station_profile": station_profile,
        "most_risky_stations": most_risky_stations,
    }


def station_line_probabilities(
    station_id: int,
    board_type: str,
    days: int = 30,
    min_trains: int = 8,
    top_n: int = 8,
) -> dict:
    today = timezone.localdate()
    start_date = today - timedelta(days=max(days - 1, 0))
    queryset = TrainSnapshot.objects.filter(
        station_id=station_id,
        board_type=board_type,
        service_date__gte=start_date,
        service_date__lte=today,
    )

    rows = (
        queryset.values("train_name", "category")
        .annotate(
            total_trains=Count("id"),
            average_delay=Avg("delay_minutes"),
            maximum_delay=Max("delay_minutes"),
            on_time_count=Count("id", filter=Q(delay_minutes=0)),
            delayed_any_count=Count("id", filter=Q(delay_minutes__gt=0)),
            delayed_over_5_count=Count("id", filter=Q(delay_minutes__gte=5)),
            delayed_over_10_count=Count("id", filter=Q(delay_minutes__gte=10)),
        )
        .filter(total_trains__gte=max(min_trains, 1))
    )

    parsed_rows: list[dict] = []
    for row in rows:
        total = int(row["total_trains"] or 0)
        delayed_any = int(row["delayed_any_count"] or 0)
        delay_probability = _ratio(delayed_any, total)
        parsed_rows.append(
            {
                "line_name": row["train_name"],
                "category": row["category"] or "",
                "total_trains": total,
                "average_delay": round(float(row["average_delay"] or 0), 2),
                "maximum_delay": int(row["maximum_delay"] or 0),
                "on_time_probability": _ratio(int(row["on_time_count"] or 0), total),
                "delay_probability": delay_probability,
                "delay_over_5_probability": _ratio(int(row["delayed_over_5_count"] or 0), total),
                "delay_over_10_probability": _ratio(int(row["delayed_over_10_count"] or 0), total),
                "delay_probability_confidence_95": _wilson_bounds(delayed_any, total),
                "risk_band": _risk_band(delay_probability),
            }
        )

    most_risky = sorted(
        parsed_rows,
        key=lambda row: (-row["delay_probability"], -row["average_delay"], -row["total_trains"]),
    )[: max(top_n, 1)]
    most_reliable = sorted(
        parsed_rows,
        key=lambda row: (row["delay_probability"], row["average_delay"], -row["total_trains"]),
    )[: max(top_n, 1)]

    return {
        "days": days,
        "min_trains": min_trains,
        "top_n": top_n,
        "sampled_lines": len(parsed_rows),
        "most_risky": most_risky,
        "most_reliable": most_reliable,
    }


def line_catalog(days: int = 30, query: str = "", limit: int = 200) -> list[dict]:
    today = timezone.localdate()
    start_date = today - timedelta(days=max(days - 1, 0))

    queryset = TrainSnapshot.objects.filter(service_date__gte=start_date, service_date__lte=today)
    normalized_query = query.strip()
    if normalized_query:
        queryset = queryset.filter(train_name__icontains=normalized_query)

    rows = (
        queryset.values("train_name")
        .annotate(
            total_trains=Count("id"),
            average_delay=Avg("delay_minutes"),
            delayed_any_count=Count("id", filter=Q(delay_minutes__gt=0)),
        )
        .order_by("-total_trains", "train_name")[: max(limit, 1)]
    )

    payload: list[dict] = []
    for row in rows:
        total = int(row["total_trains"] or 0)
        delayed_any = int(row["delayed_any_count"] or 0)
        payload.append(
            {
                "line_name": row["train_name"],
                "total_trains": total,
                "average_delay": round(float(row["average_delay"] or 0), 2),
                "delay_probability": _ratio(delayed_any, total),
            }
        )

    return payload
