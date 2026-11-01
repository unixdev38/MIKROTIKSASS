"""Lectures liées aux tenants (aucune écriture ici)."""
from __future__ import annotations

from apps.tenants.models import Tenant


class TenantSelector:
    """Requêtes de lecture sur les espaces de travail."""

    @staticmethod
    def by_slug(slug: str) -> Tenant | None:
        """Retourne un tenant par son identifiant lisible.

        Args:
            slug: Identifiant unique de l'espace.

        Returns:
            Le tenant correspondant, ou ``None`` s'il n'existe pas.
        """
        return Tenant.objects.filter(slug=slug).first()

    @staticmethod
    def all_active() -> list[Tenant]:
        """Liste les espaces non fermés.

        Returns:
            Les tenants dont le statut n'est pas ``closed``.
        """
        return list(Tenant.objects.exclude(status="closed"))
