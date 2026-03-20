from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from trains.models import Station, TrainSnapshot
from trains.services.ingest import refresh_station_board


class Command(BaseCommand):
    help = "Collects latest train delay snapshots from DB APIs and stores normalized records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--station-id",
            type=int,
            default=1,
            help="Station primary key to collect data for (default: 1).",
        )
        parser.add_argument(
            "--board-type",
            choices=["departure", "arrival", "both"],
            default="departure",
            help="Board type to collect.",
        )
        parser.add_argument(
            "--window-hours",
            type=int,
            default=4,
            help="Number of hour slots to ingest from timetables (default: 4).",
        )
        parser.add_argument(
            "--all-stations",
            action="store_true",
            help="Collect snapshots for all active stations instead of a single station.",
        )
        parser.add_argument(
            "--station-limit",
            type=int,
            default=0,
            help="Optional cap for number of stations when --all-stations is used (0 means no cap).",
        )
        parser.add_argument(
            "--skip-errors",
            action="store_true",
            help="Continue processing other stations when one station fails.",
        )

    def handle(self, *args, **options):
        station_id = options["station_id"]
        board_type = options["board_type"]
        window_hours = max(int(options["window_hours"]), 1)
        all_stations = bool(options["all_stations"])
        station_limit = max(int(options["station_limit"]), 0)
        skip_errors = bool(options["skip_errors"])

        if all_stations:
            stations = list(Station.objects.filter(is_active=True).order_by("id"))
            if station_limit > 0:
                stations = stations[:station_limit]
            if not stations:
                raise CommandError("No active stations found. Sync stations first.")
        else:
            try:
                station = Station.objects.get(pk=station_id)
            except Station.DoesNotExist as exc:
                raise CommandError(f"Station with id={station_id} was not found.") from exc
            stations = [station]

        board_types = [board_type]
        if board_type == "both":
            board_types = [TrainSnapshot.BOARD_TYPE_DEPARTURE, TrainSnapshot.BOARD_TYPE_ARRIVAL]

        self.stdout.write(
            self.style.NOTICE(
                f"Collecting snapshots for {len(stations)} station(s), board_type={board_type}, window={window_hours}h"
            )
        )

        failed = 0
        for station in stations:
            self.stdout.write(self.style.NOTICE(f"Station {station.id}: {station.name} ({station.eva_number})"))
            for current_type in board_types:
                try:
                    meta = refresh_station_board(station, current_type, window_hours)
                except Exception as exc:
                    failed += 1
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{current_type}] FAILED station={station.id}: {exc}"
                            )
                        )
                        continue
                    raise CommandError(f"Collection failed for station={station.id}, board_type={current_type}: {exc}") from exc

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{current_type}] source={meta['source']} received={meta['records_received']} "
                        f"inserted={meta['inserted']} updated={meta['updated']}"
                    )
                )

        if failed > 0:
            self.stdout.write(self.style.WARNING(f"Completed with {failed} failed station/board collection(s)."))
