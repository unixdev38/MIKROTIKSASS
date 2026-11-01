"""Routage racine : API versionnée et sonde de santé."""
from __future__ import annotations

from django.urls import include, path

from core.api.views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("api/v1/", include("apps.api.urls")),
]
