"""Lectures sur le parc réseau (aucune écriture)."""
from __future__ import annotations

from apps.network.models import Device, Site


class SiteSelector:
    """Requêtes de lecture des sites."""

    @staticmethod
    def get(site_id: str) -> Site:
        """Retourne un site du tenant courant.

        Args:
            site_id: Identifiant UUID du site.

        Returns:
            Le site trouvé.

        Raises:
            NotFoundError: Si le site n'existe pas dans cet espace.
        """
        from core.exceptions import NotFoundError

        site = Site.objects.filter(pk=site_id).first()
        if site is None:
            raise NotFoundError("Ce site n'existe pas dans cet espace.", code="site_not_found")
        return site

    @staticmethod
    def list() -> list[Site]:
        """Liste les sites du tenant courant.

        Returns:
            Les sites triés par nom (filtrés automatiquement par le manager).
        """
        return list(Site.objects.order_by("name"))


class DeviceSelector:
    """Requêtes de lecture des routeurs."""

    @staticmethod
    def list() -> list[Device]:
        """Liste les routeurs du tenant courant avec leur site et leurs identifiants.

        Returns:
            Les routeurs, du plus récemment ajouté au plus ancien.
        """
        return list(
            Device.objects.select_related("site", "credential").order_by("-created_at")
        )

    @staticmethod
    def get(device_id: str) -> Device:
        """Retourne un routeur du tenant courant.

        Args:
            device_id: Identifiant UUID du routeur.

        Returns:
            Le routeur trouvé.

        Raises:
            NotFoundError: Si le routeur n'existe pas ou appartient à un autre tenant
                (volontairement indiscernable : aucune fuite d'existence).
        """
        from core.exceptions import NotFoundError

        device = Device.objects.select_related("site", "credential").filter(pk=device_id).first()
        if device is None:
            raise NotFoundError("Ce routeur n'existe pas dans cet espace.", code="device_not_found")
        return device

    @staticmethod
    def for_worker(device_id: str) -> Device | None:
        """Retourne un routeur sans contexte tenant (usage worker uniquement).

        Args:
            device_id: Identifiant UUID.

        Returns:
            Le routeur, ou ``None`` s'il n'existe pas.
        """
        return Device.all_objects.select_related("site", "credential", "tenant").filter(pk=device_id).first()
