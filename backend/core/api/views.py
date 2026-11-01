"""Vues de base et sonde de santé.

Les vues exposées ici ne contiennent aucune logique métier : elles délèguent
systématiquement à un service (voir docs/14-conventions-de-code.md).
"""
from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import TenantContextMixin
from core.api.permissions import BaseTenantPermission


def health(request: HttpRequest) -> JsonResponse:
    """Sonde de disponibilité (utilisée par le proxy et la supervision).

    Args:
        request: Requête HTTP (non utilisée).

    Returns:
        ``{"status": "ok", "time": "<iso8601>"}`` avec le code 200.
    """
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})


class BaseModelViewSet(TenantContextMixin, ModelViewSet):
    """ViewSet tenant-scopé, sans logique métier.

    Les sous-classes déclarent ``selector`` (lecture) et ``service_class`` (écriture).

    Attributes:
        selector: Classe de lecture (hérite de ``BaseSelector``).
        service_class: Classe de service chargée des écritures.
        http_method_names: Verbes autorisés par défaut.
    """

    permission_classes = [IsAuthenticated, BaseTenantPermission]
    selector: type | None = None
    service_class: type | None = None
    # Les écritures passent par des actions explicites : pas de PATCH/DELETE tant
    # qu'aucun service de mise à jour n'existe (l'API renvoie alors 405, sans mentir).
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self) -> Any:
        """Retourne le queryset du tenant courant via le sélecteur déclaré.

        Returns:
            Un queryset déjà filtré (et éventuellement optimisé).

        Raises:
            NotImplementedError: Si ``selector`` n'est pas déclaré.
        """
        if self.selector is None:  # pragma: no cover - erreur de programmation
            raise NotImplementedError("Déclarez `selector` sur le ViewSet.")
        return self.selector.list()

    def get_object(self) -> Any:
        """Retourne l'objet ciblé via le sélecteur déclaré.

        Le sélecteur applique le filtrage par tenant et renvoie une erreur 404 homogène
        (``site_not_found``, ``device_not_found``) au lieu d'une erreur technique.

        Returns:
            L'objet demandé.

        Raises:
            NotImplementedError: Si ``selector`` n'est pas déclaré.
            NotFoundError: Si l'objet n'existe pas dans cet espace.
        """
        if self.selector is None:  # pragma: no cover - erreur de programmation
            raise NotImplementedError("Déclarez `selector` sur le ViewSet.")
        lookup = self.lookup_url_kwarg or self.lookup_field
        obj = self.selector.get(str(self.kwargs[lookup]))
        self.check_object_permissions(self.request, obj)
        return obj

    def response_ok(self, data: Any, *, status: int = 200) -> Response:
        """Construit une réponse JSON standard.

        Args:
            data: Charge utile sérialisable.
            status: Code HTTP à renvoyer.

        Returns:
            La réponse DRF.
        """
        return Response(data, status=status)


class PublicAPIViewMixin:
    """Mixin pour les rares vues publiques (portail captif, webhooks)."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []


def current_tenant_of(request: Request) -> Any:
    """Retourne le tenant résolu pour une requête DRF.

    Args:
        request: Requête DRF.

    Returns:
        Le tenant courant, ou ``None``.
    """
    return getattr(request, "tenant", None)
