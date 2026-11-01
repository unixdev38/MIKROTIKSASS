"""Configuration de l'application network (parc de routeurs)."""
from django.apps import AppConfig


class NetworkConfig(AppConfig):
    """Application gérant les sites, les routeurs et leurs identifiants."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.network"
    label = "network"
    verbose_name = "Parc réseau"
