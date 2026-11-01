"""Mixins transverses des vues DRF.

Le middleware Django s'exécute **avant** l'authentification DRF : avec un jeton JWT,
l'utilisateur n'est connu qu'au moment de la vue. Ce mixin résout donc le tenant juste
après l'authentification et libère le contexte à la fin de la réponse.
"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.context import ContextToken, reset_current_tenant
from core.tenancy import activate_request_tenant


class TenantContextMixin:
    """Active le tenant courant pendant toute la durée d'une vue DRF.

    Attributes:
        _tenant_token: Jeton de contexte à restaurer en fin de requête.
    """

    _tenant_token: ContextToken | None = None

    def check_permissions(self, request: Request) -> None:
        """Résout le tenant, puis applique les permissions de la vue.

        Args:
            request: Requête authentifiée par DRF.

        Raises:
            PermissionDenied: Si l'utilisateur n'a pas accès à l'espace demandé.
        """
        self._tenant_token = activate_request_tenant(request, strict=True)  # type: ignore[arg-type]
        super().check_permissions(request)  # type: ignore[misc]

    def finalize_response(
        self, request: Request, response: Response, *args: object, **kwargs: object
    ) -> Response:
        """Restaure le contexte avant de renvoyer la réponse.

        Args:
            request: Requête traitée.
            response: Réponse construite par la vue.
            *args: Arguments transmis par DRF.
            **kwargs: Options transmises par DRF.

        Returns:
            La réponse finale.
        """
        if self._tenant_token is not None:
            reset_current_tenant(self._tenant_token)
            self._tenant_token = None
        return super().finalize_response(request, response, *args, **kwargs)  # type: ignore[misc]


class TenantAPIView(TenantContextMixin, APIView):
    """Vue API simple (non-ViewSet) avec résolution du tenant."""
