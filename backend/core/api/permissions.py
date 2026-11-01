"""Contrôles d'accès transverses."""
from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.constants import ROLE_RANK


class BaseTenantPermission(BasePermission):
    """Vérifie qu'un tenant est résolu et que l'utilisateur y est actif.

    Attributes:
        minimum_role: Rôle minimal accepté (``viewer`` par défaut).
    """

    minimum_role: str = "viewer"
    message = "Vous n'avez pas accès à cet espace de travail."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Contrôle l'accès à la vue.

        Args:
            request: Requête authentifiée.
            view: Vue ciblée.

        Returns:
            ``True`` si le membre est actif et possède au moins le rôle requis.
        """
        tenant = getattr(request, "tenant", None)
        if tenant is None or not request.user.is_authenticated:
            return False
        membership = getattr(request, "membership", None)
        if membership is None:
            return False
        return ROLE_RANK.get(membership.role, 0) >= ROLE_RANK.get(self.minimum_role, 0)
