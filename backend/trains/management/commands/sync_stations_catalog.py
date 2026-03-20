from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from trains.services.clients import DBApiClient, ExternalAPIError
from trains.services.station_data import _extract_station_rows, _station_from_payload, upsert_station


class Command(BaseCommand):
    help = "Syncs station catalog from Deutsche Bahn StaDa API into local Station table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10000,
            help="Maximum number of stations fetched from StaDa in one run (default: 10000).",
        )
        parser.add_argument(
            "--federal-state",
            type=str,
            default="",
            help="Optional federal state filter used by StaDa (for example 'Bayern').",
        )

    def handle(self, *args, **options):
        if not settings.DB_API_KEY:
            raise CommandError("DB_API_KEY is missing in environment.")

        limit = max(int(options["limit"]), 1)
        federal_state = str(options["federal_state"] or "").strip()

        params: dict[str, str] = {"limit": str(limit)}
        if federal_state:
            params["federalstate"] = federal_state

        client = DBApiClient(settings.DB_STADA_BASE_URL)
        try:
            payload = client.get_json("stations", params=params)
        except ExternalAPIError as exc:
            raise CommandError(f"StaDa request failed: {exc}") from exc

        rows = _extract_station_rows(payload)
        inserted = 0
        updated = 0

        for row in rows:
            station_data = _station_from_payload(row)
            if not station_data:
                continue
            station = upsert_station(station_data)
            if station.created_at == station.updated_at:
                inserted += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Station sync completed. fetched={len(rows)} inserted_or_touched={inserted + updated} "
                f"(new~={inserted}, updated~={updated})"
            )
        )
