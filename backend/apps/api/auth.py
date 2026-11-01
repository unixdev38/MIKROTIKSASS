"""Authentification JWT : connexion, rafraîchissement, déconnexion.

Le jeton ne porte **aucun droit** : l'espace et le rôle sont resolvés à chaque requête
contre la base (``core.tenancy``), ce qui permet de révoquer un accès immédiatement.
"""
from __future__ import annotations

from typing import Any

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import Membership
from apps.accounts.selectors import MembershipSelector
from core.exceptions import DomainValidationError, PermissionDeniedError
from core.tenancy import TENANT_HEADER


def serialize_membership(membership: Membership) -> dict[str, Any]:
    """Résume un espace de travail pour le client.

    Args:
        membership: Appartenance à présenter.

    Returns:
        Un dictionnaire sérialisable : identifiant, slug, nom et rôle.

    Example:
        >>> serialize_membership(membership)["role"]
        'owner'
    """
    return {
        "id": str(membership.tenant_id),
        "slug": membership.tenant.slug,
        "name": membership.tenant.name,
        "role": membership.role,
    }


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Connexion : jetons JWT + profil + espaces de travail accessibles."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Valide les identifiants et enrichit la réponse.

        Args:
            attrs: Données de connexion (``email``, ``password``).

        Returns:
            Les jetons ``access``/``refresh``, l'utilisateur, l'espace actif et la
            liste des espaces avec leurs rôles.

        Raises:
            AuthenticationFailed: Si les identifiants sont invalides.
            PermissionDeniedError: Si l'espace demandé n'est pas accessible.
        """
        data = super().validate(attrs)
        memberships = list(MembershipSelector.list_for_user(self.user))
        requested = self.context["request"].headers.get(TENANT_HEADER)
        active = self._active_membership(memberships, requested)

        data["user"] = {
            "id": str(self.user.pk),
            "email": self.user.email,
            "full_name": self.user.full_name,
        }
        data["tenant"] = serialize_membership(active) if active else None
        data["role"] = active.role if active else None
        data["tenants"] = [serialize_membership(item) for item in memberships]
        return data

    @staticmethod
    def _active_membership(memberships: list[Membership], slug: str | None) -> Membership | None:
        """Choisit l'espace actif à la connexion.

        Args:
            memberships: Espaces de l'utilisateur.
            slug: Slug demandé via l'en-tête ``X-Tenant-Slug``.

        Returns:
            L'espace demandé s'il existe, sinon le premier espace disponible.

        Raises:
            PermissionDeniedError: Si le slug demandé ne correspond à aucun espace.
        """
        if not memberships:
            return None
        if slug:
            for membership in memberships:
                if membership.tenant.slug == slug:
                    return membership
            raise PermissionDeniedError(
                "Vous n'avez pas accès à cet espace de travail.", code="tenant_forbidden"
            )
        return memberships[0]


class TenantTokenObtainPairView(TokenObtainPairView):
    """``POST /auth/token/`` : connexion par e-mail et mot de passe."""

    permission_classes = [AllowAny]
    serializer_class = TenantTokenObtainPairSerializer


class TenantTokenRefreshView(TokenRefreshView):
    """``POST /auth/refresh/`` : renouvelle l'accès (le refresh est renouvelé aussi)."""

    permission_classes = [AllowAny]


class LogoutView(APIView):
    """``POST /auth/logout/`` : inscrit le refresh token sur liste de révocation."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Révoque le refresh token fourni.

        Args:
            request: Requête contenant ``refresh`` dans le corps.

        Returns:
            ``204`` si la révocation a réussi.

        Raises:
            DomainValidationError: Si le jeton est absent ou invalide.
        """
        token = request.data.get("refresh", "")
        if not token:
            raise DomainValidationError("Jeton de rafraîchissement manquant.", code="refresh_required")
        try:
            RefreshToken(token).blacklist()
        except TokenError as exc:
            raise DomainValidationError(
                "Jeton de rafraîchissement invalide ou déjà révoqué.", code="refresh_invalid"
            ) from exc
        return Response(status=204)
