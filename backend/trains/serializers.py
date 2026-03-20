from django.utils import timezone
from rest_framework import serializers

from trains.models import DailyStationStats, Station, TrainSnapshot


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = [
            "id",
            "eva_number",
            "name",
            "city",
            "state",
            "country",
            "latitude",
            "longitude",
            "ds100",
            "short_description",
        ]


class StationSearchSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ["id", "eva_number", "name", "city", "latitude", "longitude", "label"]

    def get_label(self, obj: Station) -> str:
        city = f" - {obj.city}" if obj.city else ""
        return f"{obj.name}{city}"


class TrainSnapshotSerializer(serializers.ModelSerializer):
    planned_time_local = serializers.SerializerMethodField()
    updated_time_local = serializers.SerializerMethodField()
    destination_or_origin = serializers.CharField(source="direction")
    train_line = serializers.CharField(source="train_name")

    class Meta:
        model = TrainSnapshot
        fields = [
            "id",
            "station",
            "board_type",
            "train_line",
            "category",
            "destination_or_origin",
            "planned_time",
            "updated_time",
            "planned_time_local",
            "updated_time_local",
            "delay_minutes",
            "platform",
            "status",
        ]

    def get_planned_time_local(self, obj: TrainSnapshot) -> str:
        return timezone.localtime(obj.planned_time).isoformat()

    def get_updated_time_local(self, obj: TrainSnapshot) -> str | None:
        if not obj.updated_time:
            return None
        return timezone.localtime(obj.updated_time).isoformat()


class DailyStationStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStationStats
        fields = [
            "station",
            "board_type",
            "stats_date",
            "total_trains",
            "average_delay",
            "median_delay",
            "on_time_ratio",
            "delayed_over_5_ratio",
            "maximum_delay",
            "computed_at",
        ]
