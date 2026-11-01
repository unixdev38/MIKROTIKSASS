"""Résolution du tenant pour chaque requête HTTP.

Règles :
1. l'en-tête ``X-Tenant-Slug`` peut désigner l'espace de travail actif, mais il est
   **validé** contre les appartenances de l'utilisateur (jamais accepté tel quel) ;
2. à défaut, on retient le premier espace auquel l'utilisateur appartient ;
3. le tenant résolu est posé dans le contexte, puis exposé sur ``request.tenant``
   et ``request.membership``.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse

from core.context import reset_current_tenant, set_current_tenant

if TYPE_CHECKING:  # pragma: no cover
    from apps.accounts.models import Membership

TENANT_HEADER = "X-Tenant-Slug"


class TenantMiddleware:
    """Pose le tenant courant dans le contexte d'exécution.

    Args:
        get_response: Maillon suivant de la chaîne Django.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Résout le tenant, exécute la vue, puis restaure le contexte.

        Args:
            request: Requête entrante.

        Returns:
            La réponse de la vue.
        """
        membership = self._resolve_membership(request)
        tenant = membership.tenant if membership else None
        request.tenant = tenant  # type: ignore[attr-defined]
        request.membership = membership  # type: ignore[attr-defined]
        token = set_current_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            reset_current_tenant(token)

    @staticmethod
    def _resolve_membership(request: HttpRequest) -> Membership | None:
        """Détermine l'appartenance active de l'utilisateur.

        Args:
            request: Requête entrante.

        Returns:
            Le membership retenu, ou ``None`` pour un utilisateur anonyme.
        """
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None

        from apps.accounts.selectors import MembershipSelector

        return MembershipSelector.for_user(user, slug=request.headers.get(TENANT_HEADER))
