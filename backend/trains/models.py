from django.db import models


class Station(models.Model):
    eva_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=64, default="DE")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ds100 = models.CharField(max_length=24, blank=True)
    short_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.eva_number})"


class TrainSnapshot(models.Model):
    BOARD_TYPE_DEPARTURE = "departure"
    BOARD_TYPE_ARRIVAL = "arrival"
    BOARD_TYPE_CHOICES = [
        (BOARD_TYPE_DEPARTURE, "Departure"),
        (BOARD_TYPE_ARRIVAL, "Arrival"),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="snapshots")
    board_type = models.CharField(max_length=16, choices=BOARD_TYPE_CHOICES)
    record_uid = models.CharField(max_length=180, unique=True)
    external_trip_id = models.CharField(max_length=128, blank=True)
    train_name = models.CharField(max_length=120)
    category = models.CharField(max_length=32, blank=True)
    direction = models.CharField(max_length=255)
    planned_time = models.DateTimeField()
    updated_time = models.DateTimeField(null=True, blank=True)
    delay_minutes = models.PositiveIntegerField(default=0)
    platform = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=40, default="scheduled")
    raw_payload = models.JSONField(default=dict, blank=True)
    service_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["planned_time"]
        indexes = [
            models.Index(fields=["station", "board_type", "planned_time"]),
            models.Index(fields=["station", "board_type", "service_date"]),
            models.Index(fields=["delay_minutes"]),
        ]

    def __str__(self) -> str:
        return f"{self.train_name} {self.direction} {self.planned_time.isoformat()}"


class DailyStationStats(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="daily_stats")
    board_type = models.CharField(max_length=16, choices=TrainSnapshot.BOARD_TYPE_CHOICES)
    stats_date = models.DateField()
    total_trains = models.PositiveIntegerField(default=0)
    average_delay = models.FloatField(default=0)
    median_delay = models.FloatField(default=0)
    on_time_ratio = models.FloatField(default=0)
    delayed_over_5_ratio = models.FloatField(default=0)
    maximum_delay = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("station", "board_type", "stats_date")
        ordering = ["-stats_date", "station"]

    def __str__(self) -> str:
        return f"{self.station.name} {self.board_type} {self.stats_date.isoformat()}"
