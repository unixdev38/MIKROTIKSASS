"""Vues HTTP : résolution, délégation au service, réponse.

Chaque méthode fait moins de 20 lignes et ne contient **aucune** décision métier
(voir docs/14-conventions-de-code.md §1). Les rôles sont contrôlés par les services.
"""
from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView  # noqa: F401 - type des vues publiques

from apps.accounts.selectors import MembershipSelector
from apps.api.serializers import (
    DeviceCreateSerializer,
    DeviceCredentialsSerializer,
    DeviceSerializer,
    MeSerializer,
    SiteCreateSerializer,
    SiteSerializer,
)
from apps.network.selectors import DeviceSelector, SiteSelector
from apps.network.services import DeviceService, SiteService
from core.api.mixins import TenantAPIView
from core.api.views import BaseModelViewSet


class _TenantScopedMixin:
    """Fournit l'acteur et son rôle à partir de la requête.

    Ce mixin n'apporte aucune logique métier : il ne fait que lire le contexte posé
    par ``core.tenancy.TenantMiddleware``.
    """

    @staticmethod
    def actor_of(request: Request) -> object:
        """Retourne l'utilisateur de la requête.

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
            Le rôle (``owner``, ``technician``…), ou ``None`` si aucun espace.
        """
        membership = getattr(request, "membership", None)
        return membership.role if membership else None


class SiteViewSet(_TenantScopedMixin, BaseModelViewSet):
    """Sites de l'espace courant."""

    serializer_class = SiteSerializer
    selector = SiteSelector

    def get_queryset(self):
        """Retourne les sites du tenant courant.

        Returns:
            La liste des sites.
        """
        return SiteSelector.list()

    def create(self, request: Request) -> Response:
        """Crée un site dans l'espace courant.

        Args:
            request: Requête contenant ``name``, ``code`` et éventuellement ``city``.

        Returns:
            Le site créé, avec le code 201.
        """
        payload = SiteCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        site = SiteService(self.actor_of(request), actor_role=self.role_of(request)).register(
            **payload.validated_data
        )
        return Response(SiteSerializer(site).data, status=201)


class DeviceViewSet(_TenantScopedMixin, BaseModelViewSet):
    """Routeurs de l'espace courant."""

    serializer_class = DeviceSerializer
    selector = DeviceSelector

    def get_queryset(self):
        """Retourne les routeurs du tenant courant.

        Returns:
            La liste des routeurs, avec site et identifiants préchargés.
        """
        return DeviceSelector.list()

    def create(self, request: Request) -> Response:
        """Enregistre un routeur dans le parc (sans identifiants).

        Args:
            request: Requête contenant ``site_id``, ``name`` et les champs facultatifs.

        Returns:
            Le routeur créé, au statut ``pending``, avec le code 201.
        """
        payload = DeviceCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = dict(payload.validated_data)
        site = SiteSelector.get(str(data.pop("site_id")))

        device = DeviceService(self.actor_of(request), actor_role=self.role_of(request)).register(
            site=site, **data
        )
        return Response(DeviceSerializer(device).data, status=201)

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request: Request, pk: str | None = None) -> Response:
        """Teste le contact avec un routeur et met à jour son état.

        Args:
            request: Requête authentifiée (POST).
            pk: Identifiant du routeur.

        Returns:
            ``is_ok``, latence, erreur et statut résultant.
        """
        device = DeviceSelector.get(str(pk))
        result = DeviceService(self.actor_of(request), actor_role=self.role_of(request)).probe(device)
        return Response(
            {
                "is_ok": result.is_ok,
                "latency_ms": result.latency_ms,
                "error": result.error,
                "status": device.status,
                "system_info": {
                    "identity": result.system_info.identity,
                    "version": result.system_info.version,
                    "model": result.system_info.model,
                }
                if result.system_info
                else {},
            }
        )

    @action(detail=True, methods=["post"], url_path="credentials")
    def credentials(self, request: Request, pk: str | None = None) -> Response:
        """Renseigne les identifiants réels d'un routeur déjà en service.

        Args:
            request: Requête contenant ``username``, ``password`` et, en option,
                ``port``, ``use_tls`` et ``transport``.
            pk: Identifiant du routeur.

        Returns:
            Le routeur mis à jour (aucun secret dans la réponse).
        """
        payload = DeviceCredentialsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        device = DeviceSelector.get(str(pk))
        updated = DeviceService(
            self.actor_of(request), actor_role=self.role_of(request)
        ).attach_credentials(device, **payload.validated_data)
        return Response(DeviceSerializer(updated).data)

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request: Request, pk: str | None = None) -> Response:
        """Génère le script d'enrôlement à usage unique d'un routeur.

        Args:
            request: Requête authentifiée. ``force=true`` force une rotation.
            pk: Identifiant du routeur.

        Returns:
            Le script, l'adresse de management et la date d'expiration.
        """
        device = DeviceSelector.get(str(pk))
        force = str(request.data.get("force", "")).lower() in {"1", "true", "yes"}
        bundle = DeviceService(
            self.actor_of(request), actor_role=self.role_of(request)
        ).issue_enrollment(device, force=force)
        return Response(
            {
                "device_id": bundle.device_id,
                "script": bundle.script,
                "management_ip": bundle.management_ip,
                "expires_at": bundle.expires_at,
                "is_renewal": bundle.is_renewal,
            }
        )


class MeView(_TenantScopedMixin, TenantAPIView):
    """Profil de l'utilisateur connecté et espaces accessibles."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Retourne l'identité, le rôle et la liste des espaces.

        Args:
            request: Requête authentifiée.

        Returns:
            Les informations de session utiles à la console.
        """
        tenant = getattr(request, "tenant", None)
        memberships = MembershipSelector.list_for_user(request.user)
        payload = {
            "id": request.user.pk,
            "email": request.user.email,
            "full_name": request.user.full_name,
            "tenant": {"id": tenant.pk, "slug": tenant.slug, "name": tenant.name} if tenant else None,
            "role": self.role_of(request),
            "tenants": [
                {"id": membership.tenant.pk, "slug": membership.tenant.slug,
                 "name": membership.tenant.name, "role": membership.role}
                for membership in memberships
            ],
        }
        return Response(MeSerializer(payload).data)
