"""Application « hotspot » : forfaits, lots de vouchers et codes d'accès."""
from django.apps import AppConfig


class HotspotConfig(AppConfig):
    """Configuration de l'application hotspot."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hotspot"
    verbose_name = "Hotspot & vouchers"
