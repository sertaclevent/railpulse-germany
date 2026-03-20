from django.contrib import admin

from trains.models import DailyStationStats, Station, TrainSnapshot


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "eva_number", "city", "ds100", "is_active")
    search_fields = ("name", "eva_number", "city", "ds100")


@admin.register(TrainSnapshot)
class TrainSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "train_name",
        "station",
        "board_type",
        "planned_time",
        "updated_time",
        "delay_minutes",
        "status",
    )
    list_filter = ("board_type", "status", "service_date", "station")
    search_fields = ("train_name", "direction", "external_trip_id", "record_uid")


@admin.register(DailyStationStats)
class DailyStationStatsAdmin(admin.ModelAdmin):
    list_display = (
        "station",
        "stats_date",
        "board_type",
        "total_trains",
        "average_delay",
        "median_delay",
        "maximum_delay",
    )
    list_filter = ("board_type", "stats_date")
