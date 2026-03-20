from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from trains.models import Station, TrainSnapshot
from trains.serializers import StationSearchSerializer
from trains.services.helpers import calculate_delay_minutes


class DelayCalculationTests(TestCase):
    def test_delay_negative_values_become_zero(self):
        planned = timezone.now()
        updated = planned - timedelta(minutes=4)

        self.assertEqual(calculate_delay_minutes(planned, updated), 0)


class StationSearchSerializerTests(TestCase):
    def test_station_search_serializer_label(self):
        station = Station.objects.create(
            eva_number="8000105",
            name="Berlin Hbf",
            city="Berlin",
            latitude=52.525,
            longitude=13.369,
        )

        data = StationSearchSerializer(station).data

        self.assertEqual(data["name"], "Berlin Hbf")
        self.assertEqual(data["city"], "Berlin")
        self.assertIn("Berlin Hbf", data["label"])


class BoardEndpointResponseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.station, _ = Station.objects.update_or_create(
            eva_number="8000261",
            defaults={
                "name": "Muenchen Hbf",
                "city": "Muenchen",
                "latitude": 48.140232,
                "longitude": 11.558335,
            },
        )

        planned = timezone.now() + timedelta(minutes=20)
        TrainSnapshot.objects.create(
            station=self.station,
            board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
            record_uid="test-record",
            external_trip_id="trip-1",
            train_name="ICE 101",
            category="ICE",
            direction="Nuernberg Hbf",
            planned_time=planned,
            updated_time=planned + timedelta(minutes=5),
            delay_minutes=5,
            platform="12",
            status="delayed",
            raw_payload={"test": True},
            service_date=planned.date(),
        )
        TrainSnapshot.objects.create(
            station=self.station,
            board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
            record_uid="test-record-2",
            external_trip_id="trip-2",
            train_name="RE 200",
            category="RE",
            direction="Augsburg Hbf",
            planned_time=planned + timedelta(minutes=10),
            updated_time=planned + timedelta(minutes=12),
            delay_minutes=2,
            platform="9",
            status="scheduled",
            raw_payload={"test": True},
            service_date=planned.date(),
        )

    @patch("trains.views.refresh_station_board")
    def test_board_endpoint_returns_normalized_payload(self, refresh_mock):
        refresh_mock.return_value = {
            "source": "sample_data",
            "records_received": 1,
            "inserted": 0,
            "updated": 1,
        }

        response = self.client.get(
            f"/api/stations/{self.station.id}/board",
            {"type": "departure", "window": "2h"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("data", payload)
        self.assertIn("trains", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["trains"]), 1)
        first_train = payload["data"]["trains"][0]
        self.assertIn("planned_time_local", first_train)
        self.assertIn("updated_time_local", first_train)
        self.assertGreaterEqual(len(payload["data"]["trains"]), 2)

    @patch("trains.views.refresh_station_board")
    def test_board_endpoint_supports_line_filter(self, refresh_mock):
        refresh_mock.return_value = {
            "source": "sample_data",
            "records_received": 2,
            "inserted": 0,
            "updated": 2,
        }

        response = self.client.get(
            f"/api/stations/{self.station.id}/board",
            {"type": "departure", "window": "2h", "line": "ICE 101"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(len(payload["data"]["trains"]), 1)
        self.assertTrue(all(train["train_line"] == "ICE 101" for train in payload["data"]["trains"]))

    @patch("trains.views.refresh_station_board")
    def test_board_endpoint_expands_window_when_requested_window_is_empty(self, refresh_mock):
        refresh_mock.return_value = {
            "source": "sample_data",
            "records_received": 0,
            "inserted": 0,
            "updated": 0,
        }

        planned = timezone.now() + timedelta(hours=5)
        TrainSnapshot.objects.create(
            station=self.station,
            board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
            record_uid="test-fallback-window",
            external_trip_id="trip-fallback-window",
            train_name="ICE 999",
            category="ICE",
            direction="Berlin Hbf",
            planned_time=planned,
            updated_time=planned + timedelta(minutes=3),
            delay_minutes=3,
            platform="7",
            status="scheduled",
            raw_payload={"test": True},
            service_date=planned.date(),
        )

        response = self.client.get(
            f"/api/stations/{self.station.id}/board",
            {"type": "departure", "window": "2h", "line": "ICE 999"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["requested_window_hours"], 2)
        self.assertEqual(payload["data"]["window_hours"], 6)
        self.assertTrue(payload["meta"]["window"]["used_fallback"])
        self.assertEqual(len(payload["data"]["trains"]), 1)
        self.assertEqual(payload["data"]["trains"][0]["train_line"], "ICE 999")
        self.assertEqual(refresh_mock.call_count, 2)

    def test_stats_endpoint_expands_window_when_requested_window_is_empty(self):
        planned = timezone.now() + timedelta(hours=5)
        TrainSnapshot.objects.create(
            station=self.station,
            board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
            record_uid="test-fallback-window-stats",
            external_trip_id="trip-fallback-window-stats",
            train_name="ICE 998",
            category="ICE",
            direction="Hamburg Hbf",
            planned_time=planned,
            updated_time=planned + timedelta(minutes=4),
            delay_minutes=4,
            platform="8",
            status="scheduled",
            raw_payload={"test": True},
            service_date=planned.date(),
        )

        response = self.client.get(
            f"/api/stations/{self.station.id}/stats",
            {"type": "departure", "window": "2h", "line": "ICE 998"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["requested_window_hours"], 2)
        self.assertEqual(payload["data"]["window_hours"], 6)
        self.assertTrue(payload["meta"]["window"]["used_fallback"])
        self.assertEqual(payload["data"]["total_trains"], 1)


class LineAnalyticsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.station1, _ = Station.objects.update_or_create(
            eva_number="8000105",
            defaults={
                "name": "Berlin Hbf",
                "city": "Berlin",
                "latitude": 52.525,
                "longitude": 13.369,
            },
        )
        self.station2, _ = Station.objects.update_or_create(
            eva_number="8000261",
            defaults={
                "name": "Muenchen Hbf",
                "city": "Muenchen",
                "latitude": 48.140232,
                "longitude": 11.558335,
            },
        )

        now = timezone.now()
        for index in range(10):
            planned = now + timedelta(minutes=10 + index)
            TrainSnapshot.objects.create(
                station=self.station1 if index % 2 == 0 else self.station2,
                board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
                record_uid=f"line-a-{index}",
                external_trip_id=f"a-{index}",
                train_name="ICE 100",
                category="ICE",
                direction="Hamburg",
                planned_time=planned,
                updated_time=planned + timedelta(minutes=1),
                delay_minutes=1,
                platform="1",
                status="on_time",
                raw_payload={},
                service_date=planned.date(),
            )

        for index in range(10):
            planned = now + timedelta(minutes=40 + index)
            TrainSnapshot.objects.create(
                station=self.station1 if index % 2 == 0 else self.station2,
                board_type=TrainSnapshot.BOARD_TYPE_DEPARTURE,
                record_uid=f"line-b-{index}",
                external_trip_id=f"b-{index}",
                train_name="RE 7",
                category="RE",
                direction="Koeln",
                planned_time=planned,
                updated_time=planned + timedelta(minutes=12),
                delay_minutes=12,
                platform="5",
                status="delayed",
                raw_payload={},
                service_date=planned.date(),
            )

    def test_line_rankings_endpoint_returns_top_lists(self):
        response = self.client.get("/api/lines/rankings", {"days": 14, "min_trains": 5, "top_n": 5})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("most_punctual", payload["data"])
        self.assertIn("most_delayed", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["most_punctual"]), 1)
        self.assertGreaterEqual(len(payload["data"]["most_delayed"]), 1)

    def test_line_catalog_endpoint_returns_lines(self):
        response = self.client.get("/api/lines/catalog", {"days": 30, "limit": 20})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("lines", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["lines"]), 2)

    def test_line_stats_endpoint_returns_summary_and_stations(self):
        response = self.client.get("/api/lines/ICE%20100/stats", {"days": 30, "top_stations": 5})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["line_name"], "ICE 100")
        self.assertIn("summary", payload["data"])
        self.assertIn("risk_forecast", payload["data"])
        self.assertIn("daily", payload["data"])
        self.assertIn("weekly", payload["data"])
        self.assertIn("top_stations", payload["data"])
        self.assertIn("station_profile", payload["data"])

    def test_station_line_probabilities_endpoint_returns_risk_lists(self):
        response = self.client.get(
            f"/api/stations/{self.station1.id}/line-probabilities",
            {"type": "departure", "days": 30, "min_trains": 3, "top_n": 5},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("most_risky", payload["data"])
        self.assertIn("most_reliable", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["most_risky"]), 1)
