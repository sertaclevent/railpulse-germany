from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from trains.models import Station, TrainSnapshot
from trains.serializers import StationSearchSerializer, StationSerializer, TrainSnapshotSerializer
from trains.services.ingest import refresh_station_board
from trains.services.station_data import search_stations_remote, upsert_station
from trains.services.stats import (
    daily_delay_trends,
    delay_distribution,
    line_catalog,
    hourly_average_delay,
    line_rankings,
    line_stats,
    queryset_delay_stats,
    station_line_probabilities,
    weekly_delay_trends,
)
from trains.services.helpers import normalize_window_hours

ALLOWED_BOARD_TYPES = {
    TrainSnapshot.BOARD_TYPE_DEPARTURE,
    TrainSnapshot.BOARD_TYPE_ARRIVAL,
}
WINDOW_FALLBACK_HOURS = 6


def _bad_request(message: str) -> Response:
    return Response(
        {
            "success": False,
            "error": {"message": message},
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _not_found(message: str) -> Response:
    return Response(
        {
            "success": False,
            "error": {"message": message},
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def _safe_server_error() -> Response:
    return Response(
        {
            "success": False,
            "error": {
                "message": "External train data is temporarily unavailable. Please try again shortly.",
            },
        },
        status=status.HTTP_502_BAD_GATEWAY,
    )


def _parse_board_type(raw_type: str | None) -> str | None:
    board_type = (raw_type or TrainSnapshot.BOARD_TYPE_DEPARTURE).strip().lower()
    if board_type not in ALLOWED_BOARD_TYPES:
        return None
    return board_type


def _parse_delay_threshold(raw_value: str | None) -> int:
    if not raw_value:
        return 0

    normalized = raw_value.strip().lower().replace("+", "")
    if normalized in {"all", "0"}:
        return 0
    if normalized.startswith("5"):
        return 5
    if normalized.startswith("10"):
        return 10
    if normalized.isdigit():
        return max(int(normalized), 0)
    return 0


def _parse_int_query(raw_value: str | None, *, default: int, min_value: int, max_value: int) -> int:
    if raw_value is None:
        return default
    try:
        parsed = int(raw_value.strip())
    except (TypeError, ValueError):
        return default
    return min(max(parsed, min_value), max_value)


def _parse_line_filter(raw_value: str | None) -> str:
    if not raw_value:
        return ""
    return raw_value.strip()


def _filtered_queryset(
    station: Station,
    board_type: str,
    window_hours: int,
    delay_threshold: int,
    category_filter: str,
    line_filter: str,
):
    now = timezone.now()
    window_end = now + timedelta(hours=window_hours)

    queryset = TrainSnapshot.objects.filter(
        station=station,
        board_type=board_type,
        planned_time__gte=now,
        planned_time__lte=window_end,
    )

    if delay_threshold > 0:
        queryset = queryset.filter(delay_minutes__gte=delay_threshold)

    if category_filter:
        category_filter = category_filter.strip()
        queryset = queryset.filter(
            Q(category__icontains=category_filter)
            | Q(train_name__icontains=category_filter)
            | Q(direction__icontains=category_filter)
        )

    if line_filter:
        queryset = queryset.filter(train_name__iexact=line_filter)

    return queryset.order_by("planned_time")


def _resolve_window_fallback_queryset(
    station: Station,
    board_type: str,
    window_hours: int,
    delay_threshold: int,
    category_filter: str,
    line_filter: str,
):
    queryset = _filtered_queryset(
        station,
        board_type,
        window_hours,
        delay_threshold,
        category_filter,
        line_filter,
    )
    if queryset.exists() or window_hours >= WINDOW_FALLBACK_HOURS:
        return queryset, window_hours, False

    fallback_queryset = _filtered_queryset(
        station,
        board_type,
        WINDOW_FALLBACK_HOURS,
        delay_threshold,
        category_filter,
        line_filter,
    )
    if fallback_queryset.exists():
        return fallback_queryset, WINDOW_FALLBACK_HOURS, True

    return queryset, window_hours, False


@api_view(["GET"])
def station_search_view(request):
    query = request.query_params.get("q", "").strip()
    limit = _parse_int_query(request.query_params.get("limit"), default=12, min_value=1, max_value=6000)

    queryset = Station.objects.filter(is_active=True)
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(city__icontains=query) | Q(eva_number__icontains=query))

    local_hits = list(queryset[:limit])

    if query and len(local_hits) == 0:
        remote_hits = search_stations_remote(query, limit=limit)
        merged_hits = list(local_hits)
        seen_ids = {station.id for station in local_hits}
        for hit in remote_hits:
            station = upsert_station(hit)
            if station.id in seen_ids:
                continue
            merged_hits.append(station)
            seen_ids.add(station.id)
            if len(merged_hits) >= limit:
                break
        local_hits = merged_hits[:limit]

    data = StationSearchSerializer(local_hits, many=True).data
    return Response({"success": True, "data": data})


@api_view(["GET"])
def station_board_view(request, station_id: int):
    board_type = _parse_board_type(request.query_params.get("type"))
    if not board_type:
        return _bad_request("Query parameter 'type' must be 'departure' or 'arrival'.")

    requested_window_hours = normalize_window_hours(request.query_params.get("window"))
    delay_threshold = _parse_delay_threshold(request.query_params.get("delay_threshold"))
    category_filter = request.query_params.get("category", "")
    line_filter = _parse_line_filter(request.query_params.get("line"))

    try:
        station = Station.objects.get(pk=station_id)
    except Station.DoesNotExist:
        return _not_found("Station was not found.")

    try:
        refresh_meta = refresh_station_board(station, board_type, requested_window_hours)
    except Exception:
        return _safe_server_error()

    refresh_attempts = [{"window_hours": requested_window_hours, **refresh_meta}]
    queryset = _filtered_queryset(
        station,
        board_type,
        requested_window_hours,
        delay_threshold,
        category_filter,
        line_filter,
    )
    effective_window_hours = requested_window_hours
    used_window_fallback = False
    if not queryset.exists() and requested_window_hours < WINDOW_FALLBACK_HOURS:
        try:
            fallback_refresh = refresh_station_board(station, board_type, WINDOW_FALLBACK_HOURS)
            refresh_attempts.append({"window_hours": WINDOW_FALLBACK_HOURS, **fallback_refresh})
        except Exception:
            pass

        queryset, effective_window_hours, used_window_fallback = _resolve_window_fallback_queryset(
            station,
            board_type,
            requested_window_hours,
            delay_threshold,
            category_filter,
            line_filter,
        )

    serializer = TrainSnapshotSerializer(queryset, many=True)

    return Response(
        {
            "success": True,
            "data": {
                "station": StationSerializer(station).data,
                "board_type": board_type,
                "window_hours": effective_window_hours,
                "requested_window_hours": requested_window_hours,
                "filters": {
                    "delay_threshold": delay_threshold,
                    "category": category_filter,
                    "line": line_filter,
                },
                "trains": serializer.data,
            },
            "meta": {
                "refresh": refresh_attempts[-1],
                "refresh_attempts": refresh_attempts,
                "window": {
                    "requested_hours": requested_window_hours,
                    "effective_hours": effective_window_hours,
                    "used_fallback": used_window_fallback,
                },
                "count": queryset.count(),
            },
        }
    )


@api_view(["GET"])
def station_stats_view(request, station_id: int):
    board_type = _parse_board_type(request.query_params.get("type"))
    if not board_type:
        return _bad_request("Query parameter 'type' must be 'departure' or 'arrival'.")

    requested_window_hours = normalize_window_hours(request.query_params.get("window"))
    delay_threshold = _parse_delay_threshold(request.query_params.get("delay_threshold"))
    category_filter = request.query_params.get("category", "")
    line_filter = _parse_line_filter(request.query_params.get("line"))

    try:
        station = Station.objects.get(pk=station_id)
    except Station.DoesNotExist:
        return _not_found("Station was not found.")

    queryset, effective_window_hours, used_window_fallback = _resolve_window_fallback_queryset(
        station,
        board_type,
        requested_window_hours,
        delay_threshold,
        category_filter,
        line_filter,
    )
    stats_payload = queryset_delay_stats(queryset)

    return Response(
        {
            "success": True,
            "data": {
                "station_id": station.id,
                "board_type": board_type,
                "window_hours": effective_window_hours,
                "requested_window_hours": requested_window_hours,
                **stats_payload,
            },
            "meta": {
                "refresh": {"source": "already-refreshed-or-cached"},
                "source": "normalized_database",
                "window": {
                    "requested_hours": requested_window_hours,
                    "effective_hours": effective_window_hours,
                    "used_fallback": used_window_fallback,
                },
            },
        }
    )


@api_view(["GET"])
def station_hourly_delay_view(request, station_id: int):
    board_type = _parse_board_type(request.query_params.get("type"))
    if not board_type:
        return _bad_request("Query parameter 'type' must be 'departure' or 'arrival'.")

    line_filter = _parse_line_filter(request.query_params.get("line"))

    try:
        station = Station.objects.get(pk=station_id)
    except Station.DoesNotExist:
        return _not_found("Station was not found.")

    today = timezone.localdate()
    queryset = TrainSnapshot.objects.filter(
        station=station,
        board_type=board_type,
        service_date=today,
    ).order_by("planned_time")
    if line_filter:
        queryset = queryset.filter(train_name__iexact=line_filter)

    hourly = hourly_average_delay(queryset)
    distribution = delay_distribution(queryset)

    return Response(
        {
            "success": True,
            "data": {
                "station_id": station.id,
                "board_type": board_type,
                "hourly_average_delay": hourly,
                "delay_distribution": distribution,
            },
            "meta": {
                "refresh": {"source": "already-refreshed-or-cached"},
                "source": "normalized_database",
            },
        }
    )


@api_view(["GET"])
def station_delay_trends_view(request, station_id: int):
    board_type = _parse_board_type(request.query_params.get("type"))
    if not board_type:
        return _bad_request("Query parameter 'type' must be 'departure' or 'arrival'.")

    line_filter = _parse_line_filter(request.query_params.get("line"))

    days = _parse_int_query(request.query_params.get("days"), default=14, min_value=7, max_value=90)
    weeks = max((days + 6) // 7, 1)

    try:
        station = Station.objects.get(pk=station_id)
    except Station.DoesNotExist:
        return _not_found("Station was not found.")

    base_queryset = TrainSnapshot.objects.filter(station=station, board_type=board_type)
    if line_filter:
        base_queryset = base_queryset.filter(train_name__iexact=line_filter)
    daily = daily_delay_trends(base_queryset, days=days)
    weekly = weekly_delay_trends(base_queryset, weeks=weeks)

    return Response(
        {
            "success": True,
            "data": {
                "station_id": station.id,
                "board_type": board_type,
                "days": days,
                "daily": daily,
                "weekly": weekly,
            },
            "meta": {
                "source": "normalized_database",
            },
        }
    )


@api_view(["GET"])
def station_line_probabilities_view(request, station_id: int):
    board_type = _parse_board_type(request.query_params.get("type"))
    if not board_type:
        return _bad_request("Query parameter 'type' must be 'departure' or 'arrival'.")

    try:
        station = Station.objects.get(pk=station_id)
    except Station.DoesNotExist:
        return _not_found("Station was not found.")

    days = _parse_int_query(request.query_params.get("days"), default=30, min_value=7, max_value=180)
    min_trains = _parse_int_query(request.query_params.get("min_trains"), default=8, min_value=3, max_value=500)
    top_n = _parse_int_query(request.query_params.get("top_n"), default=8, min_value=3, max_value=30)

    payload = station_line_probabilities(
        station_id=station.id,
        board_type=board_type,
        days=days,
        min_trains=min_trains,
        top_n=top_n,
    )

    return Response(
        {
            "success": True,
            "data": {
                "station_id": station.id,
                "board_type": board_type,
                **payload,
            },
            "meta": {"source": "normalized_database"},
        }
    )


@api_view(["GET"])
def line_catalog_view(request):
    days = _parse_int_query(request.query_params.get("days"), default=30, min_value=7, max_value=180)
    limit = _parse_int_query(request.query_params.get("limit"), default=200, min_value=20, max_value=1000)
    query = request.query_params.get("q", "")

    data = line_catalog(days=days, query=query, limit=limit)
    return Response(
        {
            "success": True,
            "data": {
                "days": days,
                "limit": limit,
                "query": query,
                "lines": data,
            },
            "meta": {"source": "normalized_database"},
        }
    )


@api_view(["GET"])
def line_rankings_view(request):
    days = _parse_int_query(request.query_params.get("days"), default=14, min_value=7, max_value=90)
    min_trains = _parse_int_query(request.query_params.get("min_trains"), default=20, min_value=5, max_value=1000)
    top_n = _parse_int_query(request.query_params.get("top_n"), default=5, min_value=3, max_value=20)

    rankings = line_rankings(days=days, min_trains=min_trains, top_n=top_n)
    return Response(
        {
            "success": True,
            "data": {
                "days": days,
                "min_trains": min_trains,
                "top_n": top_n,
                **rankings,
            },
            "meta": {"source": "normalized_database"},
        }
    )


@api_view(["GET"])
def line_stats_view(request, line_name: str):
    decoded_line = line_name.strip()
    if not decoded_line:
        return _bad_request("Line name must not be empty.")

    days = _parse_int_query(request.query_params.get("days"), default=30, min_value=7, max_value=180)
    top_stations = _parse_int_query(request.query_params.get("top_stations"), default=20, min_value=3, max_value=100)

    payload = line_stats(decoded_line, days=days, top_stations=top_stations)

    return Response(
        {
            "success": True,
            "data": {
                "line_name": decoded_line,
                "days": days,
                **payload,
            },
            "meta": {"source": "normalized_database"},
        }
    )
