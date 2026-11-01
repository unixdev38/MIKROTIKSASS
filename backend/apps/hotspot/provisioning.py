"""Envoi des vouchers vers RouterOS et récupération des compteurs.

Le provisionneur est le **seul** module qui écrit sur le routeur pour les vouchers.
Il compose les services existants (``VoucherService``) plutôt que de dupliquer les règles,
et reste idempotent : rejouer un lot met à jour les utilisateurs sans créer de doublon.
"""
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.hotspot.codes import routeros_bytes, routeros_uptime
from apps.hotspot.models import Voucher, VoucherBatch, VoucherState
from apps.hotspot.schemas import ProvisionReport, SyncReport
from apps.hotspot.services import VoucherService
from apps.mikrotik.gateway import build_backend
from apps.network.models import Device
from core.exceptions import ExternalServiceError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User

#: Nombre d'erreurs consécutives avant d'abandonner (routeur mal configuré).
MAX_CONSECUTIVE_ERRORS = 5


class VoucherProvisioner(BaseService[ProvisionReport]):
    """Pousse des codes sur un routeur et lit ce qu'il en dit.

    Args:
        actor: Utilisateur à l'origine de l'action (``None`` depuis un worker).
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    # ------------------------------------------------------------------ envoi
    def push(self, batch: VoucherBatch) -> ProvisionReport:
        """Crée (ou met à jour) les utilisateurs hotspot du lot.

        Args:
            batch: Lot à envoyer.

        Returns:
            Le compte rendu : combien de codes poussés, ignorés ou refusés.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si aucun routeur n'est disponible ou s'il n'est pas enrôlé.
            ExternalServiceError: Si le routeur est injoignable (aucun code modifié).
        """
        self.assert_role(self.actor_role, "technician")
        service = VoucherService(self.actor, actor_role=self.actor_role)
        device = service.target_device(batch)
        backend = build_backend(device)

        plan = batch.plan
        limit_uptime = routeros_uptime(plan.duration_minutes)
        limit_bytes = routeros_bytes(plan.data_cap_mb)
        comment = f"kora:{batch.pk}"

        vouchers = list(batch.vouchers.filter(state__in=[VoucherState.UNUSED, VoucherState.PROVISIONED]))
        pushed, failed, errors = 0, 0, []
        now = timezone.now()

        for voucher in vouchers:
            try:
                backend.upsert_hotspot_user(
                    name=voucher.code,
                    password=voucher.password or voucher.code,
                    limit_uptime=limit_uptime,
                    limit_bytes_total=limit_bytes,
                    rate_limit=plan.rate_limit,
                    comment=comment,
                )
            except ExternalServiceError as exc:
                failed += 1
                errors.append(f"{voucher.code} : {exc}"[:200])
                if failed >= MAX_CONSECUTIVE_ERRORS and pushed == 0:
                    break
                continue
            voucher.state = VoucherState.PROVISIONED
            voucher.updated_at = now
            pushed += 1

        with transaction.atomic():
            Voucher.objects.bulk_update(vouchers, ["state", "updated_at"])
            batch.device = device
            batch.provisioned_at = timezone.now() if pushed else batch.provisioned_at
            batch.save(update_fields=["device", "provisioned_at", "updated_at"])

        return ProvisionReport(
            batch_id=str(batch.pk),
            device_id=str(device.pk),
            pushed=pushed,
            skipped=0,
            failed=failed,
            errors=errors,
        )

    # ---------------------------------------------------------- synchronisation
    def sync(self, batch: VoucherBatch) -> SyncReport:
        """Récupère les compteurs du routeur et met à jour les états.

        Args:
            batch: Lot à synchroniser.

        Returns:
            Le compte rendu de la synchronisation (activés, expirés, épuisés).

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si aucun routeur n'est disponible.
            ExternalServiceError: Si la lecture des utilisateurs échoue.
        """
        self.assert_role(self.actor_role, "technician")
        device = self._device_of(batch)
        backend = build_backend(device)
        limit = routeros_bytes(batch.plan.data_cap_mb)
        duration = batch.plan.duration_minutes

        remote = {state.name: state for state in backend.fetch_hotspot_users()}
        now = timezone.now()
        changed: list[Voucher] = []
        checked = activated = expired = exhausted = unknown = 0

        for voucher in batch.vouchers.select_related("batch").exclude(state=VoucherState.REVOKED):
            seen = remote.get(voucher.code)
            if seen is None:
                unknown += 1
                continue

            checked += 1
            voucher.used_bytes = seen.total_bytes
            voucher.last_synced_at = now
            voucher.updated_at = now

            if seen.uptime_seconds > 0 and voucher.state == VoucherState.PROVISIONED:
                activated += 1
                voucher.state = VoucherState.ACTIVE
                voucher.activated_at = voucher.activated_at or now
                voucher.expires_at = voucher.expires_at or now + timedelta(minutes=duration)

            if voucher.expires_at and now >= voucher.expires_at:
                expired += 1
                voucher.state = VoucherState.EXPIRED
            elif limit and voucher.used_bytes >= limit:
                exhausted += 1
                voucher.state = VoucherState.EXHAUSTED

            changed.append(voucher)

        with transaction.atomic():
            Voucher.objects.bulk_update(
                changed, ["used_bytes", "last_synced_at", "state", "activated_at", "expires_at", "updated_at"]
            )
            batch.last_sync_at = now
            batch.save(update_fields=["last_sync_at", "updated_at"])

        return SyncReport(
            batch_id=str(batch.pk),
            checked=checked,
            activated=activated,
            expired=expired,
            exhausted=exhausted,
            unknown=unknown,
        )

    # -------------------------------------------------------------- révocation
    def revoke(self, voucher: Voucher, *, remove_from_router: bool = True) -> Voucher:
        """Révoque un code et, par défaut, le retire du routeur.

        Args:
            voucher: Voucher à révoquer.
            remove_from_router: Supprime aussi l'utilisateur hotspot.

        Returns:
            Le voucher révoqué.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            ExternalServiceError: Si le routeur refuse la suppression (état inchangé).
        """
        self.assert_role(self.actor_role, "technician")
        if remove_from_router and voucher.state != VoucherState.UNUSED:
            backend = build_backend(self._device_of(voucher.batch))
            backend.delete_hotspot_user(voucher.code)

        voucher.state = VoucherState.REVOKED
        voucher.save(update_fields=["state", "updated_at"])
        return voucher

    # ------------------------------------------------------------------ interne
    @staticmethod
    def _device_of(batch: VoucherBatch) -> Device:
        """Retourne le routeur associé au lot.

        Args:
            batch: Lot concerné.

        Returns:
            Le routeur ciblé, à défaut le premier routeur du site.

        Raises:
            DomainValidationError: Si aucun routeur n'est disponible.
        """
        return VoucherService.target_device(batch)
