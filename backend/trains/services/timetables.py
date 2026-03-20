from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any

from django.conf import settings

from trains.services.clients import DBApiClient, ExternalAPIError
from trains.services.helpers import calculate_delay_minutes, parse_db_compact_time


class TimetableParseError(Exception):
    pass


def fetch_plan_xml(eva_number: str, service_date: date, hour: int) -> str:
    client = DBApiClient(settings.DB_TIMETABLES_BASE_URL)
    compact_day = service_date.strftime("%y%m%d")
    return client.get_text(f"plan/{eva_number}/{compact_day}/{hour:02d}", accept="application/xml")


def fetch_changes_xml(eva_number: str) -> str:
    client = DBApiClient(settings.DB_TIMETABLES_BASE_URL)
    return client.get_text(f"fchg/{eva_number}", accept="application/xml")


def _parse_changes_map(changes_xml: str, board_type: str) -> dict[str, dict[str, Any]]:
    if not changes_xml.strip():
        return {}

    try:
        root = ET.fromstring(changes_xml)
    except ET.ParseError:
        return {}

    board_tag = "dp" if board_type == "departure" else "ar"
    change_map: dict[str, dict[str, Any]] = {}

    for stop in root.findall("s"):
        trip_id = stop.attrib.get("id", "")
        if not trip_id:
            continue

        board_node = stop.find(board_tag)
        if board_node is None:
            continue

        change_map[trip_id] = {
            "ct": board_node.attrib.get("ct"),
            "cp": board_node.attrib.get("cp"),
            "cs": board_node.attrib.get("cs"),
            "clt": board_node.attrib.get("clt"),
        }

    return change_map


def _extract_direction(path: str, board_type: str) -> str:
    if not path:
        return "Unknown"

    segments = [segment.strip() for segment in path.split("|") if segment.strip()]
    if not segments:
        return "Unknown"

    if board_type == "departure":
        return segments[-1]
    return segments[0]


def _parse_train_name(stop: ET.Element, trip_id: str) -> tuple[str, str]:
    tl = stop.find("tl")
    if tl is None:
        return (trip_id or "Unknown", "")

    category = tl.attrib.get("c", "").strip()
    number = tl.attrib.get("n", "").strip()
    train_name = f"{category} {number}".strip()

    if not train_name:
        train_name = trip_id or "Unknown"

    return (train_name, category)


def parse_plan_board(
    plan_xml: str,
    board_type: str,
    change_map: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if change_map is None:
        change_map = {}

    if not plan_xml.strip():
        return []

    try:
        root = ET.fromstring(plan_xml)
    except ET.ParseError as exc:
        raise TimetableParseError("Could not parse timetable XML payload.") from exc

    board_tag = "dp" if board_type == "departure" else "ar"
    normalized: list[dict[str, Any]] = []

    for stop in root.findall("s"):
        trip_id = stop.attrib.get("id", "")
        board = stop.find(board_tag)
        if board is None:
            continue

        planned_time = parse_db_compact_time(board.attrib.get("pt"))
        if not planned_time:
            continue

        updates = change_map.get(trip_id, {})
        updated_time = parse_db_compact_time(updates.get("ct")) or planned_time

        platform = updates.get("cp") or board.attrib.get("pp", "")
        status = updates.get("cs") or board.attrib.get("ps") or "scheduled"
        path = board.attrib.get("ppth", "")
        direction = _extract_direction(path, board_type)
        train_name, category = _parse_train_name(stop, trip_id)

        normalized.append(
            {
                "external_trip_id": trip_id,
                "train_name": train_name,
                "category": category,
                "direction": direction,
                "planned_time": planned_time,
                "updated_time": updated_time,
                "delay_minutes": calculate_delay_minutes(planned_time, updated_time),
                "platform": platform,
                "status": status,
                "raw_payload": {
                    "plan": {
                        "stop_attrs": stop.attrib,
                        "board_attrs": board.attrib,
                    },
                    "change": updates,
                },
            }
        )

    return normalized


def build_change_map(eva_number: str, board_type: str) -> dict[str, dict[str, Any]]:
    try:
        changes_xml = fetch_changes_xml(eva_number)
        return _parse_changes_map(changes_xml, board_type)
    except ExternalAPIError:
        return {}


def fetch_and_parse_board(
    eva_number: str,
    service_date: date,
    hour: int,
    board_type: str,
    change_map: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if change_map is None:
        change_map = build_change_map(eva_number, board_type)

    plan_xml = fetch_plan_xml(eva_number, service_date, hour)
    return parse_plan_board(plan_xml, board_type, change_map)


def resolve_status(delay_minutes: int, raw_status: str | None) -> str:
    if raw_status and raw_status.lower() in {"c", "cancel", "cancelled"}:
        return "cancelled"
    if delay_minutes > 0:
        return "delayed"
    return "on_time"


def normalize_for_storage(record: dict[str, Any]) -> dict[str, Any]:
    updated_time = record.get("updated_time") or record.get("planned_time")
    delay_minutes = calculate_delay_minutes(record.get("planned_time"), updated_time)

    normalized = dict(record)
    normalized["updated_time"] = updated_time
    normalized["delay_minutes"] = delay_minutes
    normalized["status"] = resolve_status(delay_minutes, record.get("status"))
    return normalized
