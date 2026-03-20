from django.urls import path

from trains.views import (
    line_catalog_view,
    line_rankings_view,
    line_stats_view,
    station_board_view,
    station_delay_trends_view,
    station_hourly_delay_view,
    station_line_probabilities_view,
    station_search_view,
    station_stats_view,
)

urlpatterns = [
    path("stations/search", station_search_view, name="station-search"),
    path("stations/<int:station_id>/board", station_board_view, name="station-board"),
    path("stations/<int:station_id>/stats", station_stats_view, name="station-stats"),
    path("stations/<int:station_id>/hourly-delay", station_hourly_delay_view, name="station-hourly-delay"),
    path("stations/<int:station_id>/delay-trends", station_delay_trends_view, name="station-delay-trends"),
    path(
        "stations/<int:station_id>/line-probabilities",
        station_line_probabilities_view,
        name="station-line-probabilities",
    ),
    path("lines/catalog", line_catalog_view, name="line-catalog"),
    path("lines/rankings", line_rankings_view, name="line-rankings"),
    path("lines/<path:line_name>/stats", line_stats_view, name="line-stats"),
]
