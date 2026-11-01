"""Lectures sur les appartenances (aucune écriture)."""
from __future__ import annotations

from apps.accounts.models import Membership, User


class MembershipSelector:
    """Requêtes de lecture des appartenances."""

    @staticmethod
    def for_user(user: User, slug: str | None = None) -> Membership | None:
        """Retourne l'appartenance active d'un utilisateur.

        Args:
            user: Utilisateur authentifié.
            slug: Slug du tenant souhaité ; ``None`` pour prendre le premier espace.

        Returns:
            L'appartenance correspondante, ou ``None`` si l'utilisateur n'a pas accès
            (y compris lorsque le slug demandé ne lui appartient pas).
        """
        queryset = (
            Membership.all_objects.select_related("tenant", "user")
            .filter(user=user, is_active=True, tenant__status__in=["trial", "active"])
        )
        if slug:
            queryset = queryset.filter(tenant__slug=slug)
        return queryset.order_by("tenant__created_at").first()

    @staticmethod
    def list_for_user(user: User) -> list[Membership]:
        """Liste tous les espaces accessibles à un utilisateur.

        Args:
            user: Utilisateur concerné.

        Returns:
            Les appartenances actives, ordonnées par nom d'espace.
        """
        return list(
            Membership.all_objects.select_related("tenant")
            .filter(user=user, is_active=True)
            .order_by("tenant__name")
        )
