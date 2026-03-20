from django.urls import path

from core.views import health_view

urlpatterns = [
    path("health", health_view, name="health"),
]
