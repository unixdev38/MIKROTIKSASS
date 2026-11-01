"""Configuration de l'application accounts."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Application gérant les utilisateurs et leurs rôles."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Comptes"
