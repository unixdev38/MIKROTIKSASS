"""Mixins des vues HTTP : accès à l'acteur et à son rôle, sans logique métier."""
from __future__ import annotations

from rest_framework.request import Request


class ActorMixin:
    """Expose l'utilisateur et son rôle dans l'espace courant.

    Les valeurs proviennent du contexte posé par ``core.tenancy`` : les vues ne
    devinent jamais un rôle, elles se contentent de le transmettre au service.
    """

    @staticmethod
    def actor_of(request: Request) -> object:
        """Retourne l'utilisateur à l'origine de la requête.

        Args:
            request: Requête DRF authentifiée.

        Returns:
            L'utilisateur courant.
        """
        return request.user

    @staticmethod
    def role_of(request: Request) -> str | None:
        """Retourne le rôle de l'utilisateur dans l'espace courant.

        Args:
            request: Requête DRF authentifiée.

        Returns:
            Le rôle (``owner``, ``technician``…), ou ``None`` sans espace.
        """
        membership = getattr(request, "membership", None)
        return membership.role if membership else None
