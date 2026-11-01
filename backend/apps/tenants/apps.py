"""Configuration de l'application tenants."""
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Application gérant les espaces de travail."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    label = "tenants"
    verbose_name = "Espaces de travail"
