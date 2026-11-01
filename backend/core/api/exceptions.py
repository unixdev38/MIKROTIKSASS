"""Traduction des erreurs métier en réponses HTTP normalisées."""
from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import DomainError


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Convertit une exception en réponse ``application/problem+json``.

    Les erreurs de domaine (``DomainError``) sont traduites avec leur code HTTP et un
    identifiant de requête ; les autres erreurs passent par le handler DRF standard.

    Args:
        exc: Exception levée par la vue ou le service.
        context: Contexte DRF (contient ``request`` et ``view``).

    Returns:
        Une réponse HTTP, ou ``None`` si DRF ne sait pas la traiter.
    """
    if isinstance(exc, DomainError):
        payload = exc.as_problem()
        payload["request_id"] = _request_id(context)
        return Response(payload, status=exc.status,
                        content_type="application/problem+json")

    response = drf_exception_handler(exc, context)
    if response is not None:
        response["X-Request-ID"] = _request_id(context)
    return response


def _request_id(context: dict[str, Any]) -> str:
    """Extrait (ou fabrique) l'identifiant de corrélation de la requête.

    Args:
        context: Contexte DRF.

    Returns:
        L'identifiant transmis par le client, ou une chaîne vide.
    """
    request = context.get("request")
    return getattr(request, "headers", {}).get("X-Request-ID", "") if request else ""
