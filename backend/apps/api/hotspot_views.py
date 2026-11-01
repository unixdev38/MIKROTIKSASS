"""Vues HTTP des forfaits et des vouchers : résolution, délégation, réponse.

Aucune règle métier ici : chaque méthode tient en quelques lignes et appelle un service
(``PlanService``, ``VoucherService``, ``VoucherProvisioner``).
"""
from __future__ import annotations

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.api.hotspot_serializers import (
    PlanCreateSerializer,
    PlanSerializer,
    VoucherBatchCreateSerializer,
    VoucherBatchSerializer,
    VoucherSerializer,
)
from apps.api.mixins import ActorMixin
from apps.hotspot.provisioning import VoucherProvisioner
from apps.hotspot.selectors import PlanSelector, VoucherBatchSelector, VoucherSelector
from apps.hotspot.services import PlanService, VoucherService
from apps.network.selectors import DeviceSelector, SiteSelector
from core.api.views import BaseModelViewSet


class PlanViewSet(ActorMixin, BaseModelViewSet):
    """Forfaits de l'espace courant."""

    serializer_class = PlanSerializer
    selector = PlanSelector

    def get_queryset(self):
        """Liste les forfaits, actifs par défaut.

        Returns:
            Les forfaits, éventuellement retirés de la vente.
        """
        include_inactive = self.request.query_params.get("include_inactive", "") in {
            "1", "true", "yes",
        }
        return PlanSelector.list(include_inactive=include_inactive)

    def create(self, request: Request) -> Response:
        """Crée un forfait.

        Args:
            request: Requête contenant ``name``, ``code``, ``duration_minutes``…

        Returns:
            Le forfait créé, avec le code 201.
        """
        payload = PlanCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        plan = PlanService(self.actor_of(request), actor_role=self.role_of(request)).create(
            **payload.validated_data
        )
        return Response(PlanSerializer(plan).data, status=201)


class VoucherBatchViewSet(ActorMixin, BaseModelViewSet):
    """Lots de vouchers : génération, envoi au routeur, synchronisation, export."""

    serializer_class = VoucherBatchSerializer
    selector = VoucherBatchSelector

    def get_queryset(self):
        """Liste les lots du tenant courant.

        Returns:
            Les lots, avec site, forfait et compteurs.
        """
        return VoucherBatchSelector.list()

    def create(self, request: Request) -> Response:
        """Génère un lot de codes.

        Args:
            request: Requête contenant ``site_id``, ``plan_id`` et ``quantity``.

        Returns:
            Le lot créé, avec le code 201.
        """
        payload = VoucherBatchCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = dict(payload.validated_data)
        site = SiteSelector.get(str(data.pop("site_id")))
        plan = PlanSelector.get(str(data.pop("plan_id")))
        device_id = data.pop("device_id", None)

        batch = VoucherService(self.actor_of(request), actor_role=self.role_of(request)).generate(
            site=site,
            plan=plan,
            device=DeviceSelector.get(str(device_id)) if device_id else None,
            **data,
        )
        return Response(VoucherBatchSerializer(batch).data, status=201)

    @action(detail=True, methods=["post"], url_path="provision")
    def provision(self, request: Request, pk: str | None = None) -> Response:
        """Envoie le lot vers le routeur (création des utilisateurs hotspot).

        Args:
            request: Requête authentifiée (POST).
            pk: Identifiant du lot.

        Returns:
            Le compte rendu (codes poussés, échecs et messages).
        """
        batch = VoucherBatchSelector.get(str(pk))
        report = VoucherProvisioner(
            self.actor_of(request), actor_role=self.role_of(request)
        ).push(batch)
        return Response(
            {
                "batch_id": report.batch_id,
                "device_id": report.device_id,
                "pushed": report.pushed,
                "failed": report.failed,
                "errors": report.errors,
            }
        )

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request: Request, pk: str | None = None) -> Response:
        """Relit les compteurs du routeur et met à jour les états.

        Args:
            request: Requête authentifiée (POST).
            pk: Identifiant du lot.

        Returns:
            Le compte rendu (activés, expirés, épuisés, inconnus).
        """
        batch = VoucherBatchSelector.get(str(pk))
        report = VoucherProvisioner(
            self.actor_of(request), actor_role=self.role_of(request)
        ).sync(batch)
        return Response(
            {
                "batch_id": report.batch_id,
                "checked": report.checked,
                "activated": report.activated,
                "expired": report.expired,
                "exhausted": report.exhausted,
                "unknown": report.unknown,
            }
        )

    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request: Request, pk: str | None = None) -> HttpResponse:
        """Exporte les codes du lot en CSV.

        Args:
            request: Requête authentifiée.
            pk: Identifiant du lot.

        Returns:
            Un fichier CSV en pièce jointe.
        """
        batch = VoucherBatchSelector.get(str(pk))
        content = VoucherService(
            self.actor_of(request), actor_role=self.role_of(request)
        ).export_csv(batch)
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="vouchers-{batch.site.code}-{pk}.csv"'
        return response


class VoucherViewSet(ActorMixin, BaseModelViewSet):
    """Vouchers de l'espace courant (lecture et révocation)."""

    serializer_class = VoucherSerializer
    selector = VoucherSelector

    def get_queryset(self):
        """Liste les vouchers, filtrables par lot et par état.

        Returns:
            Les vouchers correspondant aux paramètres ``batch`` et ``state``.
        """
        return VoucherSelector.list(
            batch_id=self.request.query_params.get("batch"),
            state=self.request.query_params.get("state"),
        )

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request: Request, pk: str | None = None) -> Response:
        """Révoque un voucher et le retire du routeur.

        Args:
            request: Requête authentifiée (POST).
            pk: Identifiant du voucher.

        Returns:
            Le voucher révoqué.
        """
        voucher = VoucherSelector.get(str(pk))
        updated = VoucherProvisioner(
            self.actor_of(request), actor_role=self.role_of(request)
        ).revoke(voucher)
        return Response(VoucherSerializer(updated).data)
