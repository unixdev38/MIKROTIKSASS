"""Routage de l'API v1."""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.auth import LogoutView, TenantTokenObtainPairView, TenantTokenRefreshView
from apps.api.views import DeviceViewSet, MeView, SiteViewSet

router = DefaultRouter()
router.register("sites", SiteViewSet, basename="site")
router.register("devices", DeviceViewSet, basename="device")

urlpatterns = [
    path("auth/token/", TenantTokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/refresh/", TenantTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
