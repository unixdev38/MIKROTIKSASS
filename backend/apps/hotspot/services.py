"""Services des forfaits et des lots de vouchers.

- ``PlanService`` : catalogue commercial (création, retrait).
- ``VoucherService`` : génération des codes, révocation, export.

L'envoi vers le routeur vit dans ``apps.hotspot.provisioning`` (autre responsabilité),
les lectures dans ``apps.hotspot.selectors``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.hotspot.codes import DEFAULT_LENGTH, generate_code, normalize_prefix
from apps.hotspot.exporters import vouchers_to_csv
from apps.hotspot.models import Plan, Voucher, VoucherBatch, VoucherState
from apps.network.models import Device, Site
from apps.network.selectors import DeviceSelector
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User

#: Nombre maximal de codes générés en une fois (au-delà : découper le lot).
MAX_BATCH_SIZE = 500

#: Nombre de tentatives pour éviter une collision de code.
CODE_ATTEMPTS = 25


class PlanService(BaseService[Plan]):
    """Catalogue des forfaits d'un espace de travail.

    Args:
        actor: Utilisateur à l'origine de l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def create(
        self,
        *,
        name: str,
        code: str,
        duration_minutes: int,
        price_fcfa: int = 0,
        data_cap_mb: int = 0,
        rate_limit: str = "",
    ) -> Plan:
        """Crée un forfait vendable.

        Args:
            name: Nom commercial affiché en caisse.
            code: Code court unique dans l'espace (``H1``, ``D24``).
            duration_minutes: Durée de connexion en minutes (> 0).
            price_fcfa: Prix de vente en francs CFA.
            data_cap_mb: Volume inclus en Mo (0 = illimité).
            rate_limit: Limite de débit RouterOS (``"2M/2M"``), vide = aucune.

        Returns:
            Le forfait créé.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle administrateur.
            DomainValidationError: Si un champ obligatoire est invalide.
            ConflictError: Si le code est déjà utilisé dans cet espace.
        """
        self.assert_role(self.actor_role, "admin")

        clean_name = (name or "").strip()
        clean_code = (code or "").strip().upper()
        if not clean_name:
            raise DomainValidationError("Le nom du forfait est obligatoire.", code="plan_name_required")
        if not clean_code:
            raise DomainValidationError("Le code du forfait est obligatoire.", code="plan_code_required")
        if int(duration_minutes) <= 0:
            raise DomainValidationError(
                "La durée doit être supérieure à zéro.", code="plan_duration_invalid"
            )
        if int(price_fcfa) < 0 or int(data_cap_mb) < 0:
            raise DomainValidationError(
                "Le prix et le volume ne peuvent pas être négatifs.", code="plan_values_invalid"
            )
        if Plan.objects.filter(code=clean_code).exists():
            raise ConflictError(f"Le code « {clean_code} » existe déjà.", code="plan_code_taken")

        return Plan.objects.create(
            name=clean_name,
            code=clean_code,
            duration_minutes=int(duration_minutes),
            price_fcfa=int(price_fcfa),
            data_cap_mb=int(data_cap_mb),
            rate_limit=(rate_limit or "").strip(),
        )

    def deactivate(self, plan: Plan) -> Plan:
        """Retire un forfait de la vente (sans toucher aux lots existants).

        Args:
            plan: Forfait à retirer.

        Returns:
            Le forfait désactivé.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle administrateur.
        """
        self.assert_role(self.actor_role, "admin")
        plan.is_active = False
        plan.save(update_fields=["is_active", "updated_at"])
        return plan


class VoucherService(BaseService[VoucherBatch]):
    """Génération et gestion des codes d'accès.

    Args:
        actor: Utilisateur à l'origine de l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def generate(
        self,
        *,
        site: Site,
        plan: Plan,
        quantity: int,
        prefix: str = "",
        note: str = "",
        device: Device | None = None,
    ) -> VoucherBatch:
        """Génère un lot de codes pour un site et un forfait.

        Les codes sont uniques dans l'espace : la génération réessaie en cas de
        collision (probabilité négligeable, mais jamais supposée nulle).

        Args:
            site: Site de vente.
            plan: Forfait appliqué.
            quantity: Nombre de codes (1 à 500).
            prefix: Préfixe lisible ajouté devant chaque code.
            note: Commentaire libre.
            device: Routeur ciblé (sinon le premier routeur du site).

        Returns:
            Le lot créé, avec ses vouchers.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si la quantité ou le forfait est invalide.
            ConflictError: Si les codes ne peuvent pas être rendus uniques.
        """
        self.assert_role(self.actor_role, "technician")

        if not 1 <= int(quantity) <= MAX_BATCH_SIZE:
            raise DomainValidationError(
                f"La quantité doit être comprise entre 1 et {MAX_BATCH_SIZE}.",
                code="batch_quantity_invalid",
            )
        if not plan.is_active:
            raise DomainValidationError(
                "Ce forfait n'est plus commercialisé.", code="plan_inactive"
            )

        clean_prefix = normalize_prefix(prefix)
        codes = self._unique_codes(clean_prefix, int(quantity))

        with transaction.atomic():
            batch = VoucherBatch.objects.create(
                site=site,
                plan=plan,
                device=device,
                quantity=len(codes),
                prefix=clean_prefix,
                note=(note or "").strip(),
            )
            # ``bulk_create`` ne passe pas par ``save()`` : le tenant est posé explicitement.
            Voucher.objects.bulk_create(
                [
                    Voucher(
                        tenant=batch.tenant, batch=batch, code=code,
                        password=code, state=VoucherState.UNUSED,
                    )
                    for code in codes
                ]
            )
        return batch

    def revoke(self, voucher: Voucher) -> Voucher:
        """Marque un voucher comme révoqué (le retrait du routeur est fait par le provisionneur).

        Args:
            voucher: Voucher à révoquer.

        Returns:
            Le voucher révoqué.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
        """
        self.assert_role(self.actor_role, "technician")
        voucher.state = VoucherState.REVOKED
        voucher.save(update_fields=["state", "updated_at"])
        return voucher

    def export_csv(self, batch: VoucherBatch) -> str:
        """Exporte les vouchers d'un lot au format CSV.

        Args:
            batch: Lot à exporter.

        Returns:
            Le contenu CSV (une ligne par code).
        """
        self.require_tenant()
        return vouchers_to_csv(list(batch.vouchers.select_related("batch", "batch__plan").order_by("code")))

    @staticmethod
    def target_device(batch: VoucherBatch) -> Device:
        """Détermine le routeur qui doit recevoir le lot.

        Args:
            batch: Lot concerné.

        Returns:
            Le routeur forcé sur le lot, sinon le premier routeur actif du site.

        Raises:
            DomainValidationError: Si le site ne compte aucun routeur.
        """
        if batch.device_id:
            return DeviceSelector.get(str(batch.device_id))

        device = next(
            (item for item in DeviceSelector.list() if item.site_id == batch.site_id), None
        )
        if device is None:
            raise DomainValidationError(
                "Aucun routeur sur ce site : ajoutez-en un avant de pousser les vouchers.",
                code="site_without_device",
            )
        return device

    @staticmethod
    def _unique_codes(prefix: str, quantity: int) -> list[str]:
        """Fabrique ``quantity`` codes uniques dans l'espace courant.

        Args:
            prefix: Préfixe déjà normalisé.
            quantity: Nombre de codes à produire.

        Returns:
            La liste des codes, dans l'ordre de génération.

        Raises:
            ConflictError: Si aucune combinaison unique n'est trouvée après plusieurs essais.
        """
        existing = set(
            Voucher.objects.filter(code__startswith=f"{prefix}-" if prefix else "").values_list(
                "code", flat=True
            )
        )
        codes: list[str] = []
        for _ in range(CODE_ATTEMPTS):
            while len(codes) < quantity:
                candidate = generate_code(DEFAULT_LENGTH, prefix=prefix)
                if candidate in existing:
                    break
                existing.add(candidate)
                codes.append(candidate)
            if len(codes) == quantity:
                return codes
        raise ConflictError(
            "Impossible de générer des codes uniques : réessayez avec un autre préfixe.",
            code="voucher_codes_exhausted",
        )
