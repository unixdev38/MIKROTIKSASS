"""Résolution du tenant pour chaque requête HTTP.

Règles :
1. l'en-tête ``X-Tenant-Slug`` peut désigner l'espace de travail actif, mais il est
   **validé** contre les appartenances de l'utilisateur (jamais accepté tel quel) ;
2. à défaut, on retient le premier espace auquel l'utilisateur appartient ;
3. le tenant résolu est posé dans le contexte, puis exposé sur ``request.tenant``
   et ``request.membership``.

Deux points d'entrée utilisent ce module :
- :class:`TenantMiddleware`, pour les requêtes classiques (session Django, admin) ;
- :class:`core.api.mixins.TenantContextMixin`, pour l'API : avec un jeton JWT,
  l'utilisateur n'est connu qu'**après** l'authentification DRF, donc après le
  middleware — la résolution doit alors se faire dans la vue.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse

from core.context import ContextToken, reset_current_tenant, set_current_tenant

if TYPE_CHECKING:  # pragma: no cover
    from apps.accounts.models import Membership

TENANT_HEADER = "X-Tenant-Slug"


def membership_for_request(request: HttpRequest) -> Membership | None:
    """Détermine l'appartenance active de l'utilisateur sur une requête.

    Args:
        request: Requête portant (ou non) un utilisateur authentifié.

    Returns:
        Le membership correspondant à l'en-tête ``X-Tenant-Slug``, ou le premier
        espace de l'utilisateur, ou ``None`` pour un visiteur anonyme.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None

    from apps.accounts.selectors import MembershipSelector

    return MembershipSelector.for_user(user, slug=request.headers.get(TENANT_HEADER))


def activate_request_tenant(request: HttpRequest, *, strict: bool = False) -> ContextToken:
    """Résout le tenant et l'active dans le contexte courant.

    La fonction pose ``request.tenant`` et ``request.membership`` (utilisés par les
    permissions) puis retourne le jeton à repasser à :func:`reset_current_tenant`.

    Args:
        request: Requête en cours de traitement.
        strict: Si vrai, un en-tête désignant un espace inaccessible lève une erreur
            au lieu de retomber silencieusement sur « aucun espace ». Utilisé par l'API
            (une réponse 403 est alors produite), pas par le middleware.

    Returns:
        Le jeton de contexte à restaurer en fin de requête.

    Raises:
        PermissionDeniedError: Si ``strict`` et que l'espace demandé n'est pas accessible.
    """
    membership = membership_for_request(request)
    if membership is None and strict and request.headers.get(TENANT_HEADER):
        from core.exceptions import PermissionDeniedError

        raise PermissionDeniedError(
            "Vous n'avez pas accès à cet espace de travail.", code="tenant_forbidden"
        )
    tenant = membership.tenant if membership else None
    request.tenant = tenant  # type: ignore[attr-defined]
    request.membership = membership  # type: ignore[attr-defined]
    return set_current_tenant(tenant)


class TenantMiddleware:
    """Pose le tenant courant dans le contexte pour les requêtes non-API.

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
        token = activate_request_tenant(request)
        try:
            return self.get_response(request)
        finally:
            reset_current_tenant(token)
