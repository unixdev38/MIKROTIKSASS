"""Configuration de l'application mikrotik (connecteur RouterOS)."""
from django.apps import AppConfig


class MikrotikConfig(AppConfig):
    """Application du connecteur MikroTik : schémas, backends, services."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mikrotik"
    label = "mikrotik"
    verbose_name = "Connecteur MikroTik"
