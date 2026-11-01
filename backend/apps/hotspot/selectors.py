"""Lectures sur les forfaits et les vouchers (aucune écriture)."""
from __future__ import annotations

from django.db.models import Count, Q

from apps.hotspot.models import Plan, Voucher, VoucherBatch, VoucherState
from core.exceptions import NotFoundError


class PlanSelector:
    """Requêtes de lecture des forfaits."""

    @staticmethod
    def list(*, include_inactive: bool = False) -> list[Plan]:
        """Liste les forfaits du tenant courant.

        Args:
            include_inactive: Inclut les forfaits retirés de la vente.

        Returns:
            Les forfaits triés par prix croissant.
        """
        queryset = Plan.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return list(queryset.order_by("price_fcfa", "name"))

    @staticmethod
    def get(plan_id: str) -> Plan:
        """Retourne un forfait du tenant courant.

        Args:
            plan_id: Identifiant UUID du forfait.

        Returns:
            Le forfait trouvé.

        Raises:
            NotFoundError: Si le forfait n'existe pas dans cet espace.
        """
        plan = Plan.objects.filter(pk=plan_id).first()
        if plan is None:
            raise NotFoundError("Ce forfait n'existe pas dans cet espace.", code="plan_not_found")
        return plan


class VoucherBatchSelector:
    """Requêtes de lecture des lots."""

    @staticmethod
    def list() -> list[VoucherBatch]:
        """Liste les lots du tenant courant avec leurs compteurs.

        Returns:
            Les lots, du plus récent au plus ancien, enrichis de ``total_count``,
            ``provisioned_count`` et ``used_count``.
        """
        return list(
            VoucherBatch.objects.select_related("site", "plan", "device")
            .annotate(
                total_count=Count("vouchers"),
                provisioned_count=Count(
                    "vouchers",
                    filter=Q(vouchers__state__in=[VoucherState.PROVISIONED, VoucherState.ACTIVE]),
                ),
                used_count=Count("vouchers", filter=Q(vouchers__state=VoucherState.ACTIVE)),
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get(batch_id: str) -> VoucherBatch:
        """Retourne un lot du tenant courant.

        Args:
            batch_id: Identifiant UUID du lot.

        Returns:
            Le lot trouvé.

        Raises:
            NotFoundError: Si le lot n'existe pas dans cet espace.
        """
        batch = (
            VoucherBatch.objects.select_related("site", "plan", "device")
            .filter(pk=batch_id)
            .first()
        )
        if batch is None:
            raise NotFoundError("Ce lot n'existe pas dans cet espace.", code="batch_not_found")
        return batch


class VoucherSelector:
    """Requêtes de lecture des vouchers."""

    @staticmethod
    def list(*, batch_id: str | None = None, state: str | None = None) -> list[Voucher]:
        """Liste les vouchers du tenant courant.

        Args:
            batch_id: Restreint à un lot.
            state: Restreint à un état (``unused``, ``active``…).

        Returns:
            Les vouchers filtrés, triés par code.
        """
        queryset = Voucher.objects.select_related("batch", "batch__plan", "batch__site")
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        if state:
            queryset = queryset.filter(state=state)
        return list(queryset.order_by("code"))

    @staticmethod
    def get(voucher_id: str) -> Voucher:
        """Retourne un voucher du tenant courant.

        Args:
            voucher_id: Identifiant UUID du voucher.

        Returns:
            Le voucher trouvé.

        Raises:
            NotFoundError: Si le voucher n'existe pas dans cet espace.
        """
        voucher = Voucher.objects.select_related("batch").filter(pk=voucher_id).first()
        if voucher is None:
            raise NotFoundError("Ce voucher n'existe pas dans cet espace.", code="voucher_not_found")
        return voucher

    @staticmethod
    def stats(batch: VoucherBatch) -> dict[str, int]:
        """Compte les vouchers d'un lot par état.

        Args:
            batch: Lot concerné.

        Returns:
            Un dictionnaire ``{"total": n, "unused": n, ...}`` pour chaque état.
        """
        rows = (
            Voucher.objects.filter(batch=batch)
            .values("state")
            .annotate(total=Count("id"))
        )
        stats = {state: 0 for state in VoucherState.values}
        for row in rows:
            stats[row["state"]] = row["total"]
        stats["total"] = sum(stats[state] for state in VoucherState.values)
        return stats
