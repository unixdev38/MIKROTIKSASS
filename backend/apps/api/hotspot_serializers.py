"""Sérialiseurs des forfaits et vouchers (forme uniquement)."""
from __future__ import annotations

from rest_framework import serializers

from apps.api.serializers import DeviceSiteSerializer
from apps.hotspot.models import Plan, Voucher, VoucherBatch
from apps.hotspot.selectors import VoucherSelector


class PlanSerializer(serializers.ModelSerializer):
    """Forfait exposé en lecture."""

    duration_label = serializers.CharField(read_only=True)

    class Meta:
        model = Plan
        fields = (
            "id", "name", "code", "duration_minutes", "duration_label", "data_cap_mb",
            "rate_limit", "price_fcfa", "is_active",
        )
        read_only_fields = fields


class PlanCreateSerializer(serializers.Serializer):
    """Charge utile de création d'un forfait."""

    name = serializers.CharField(max_length=80)
    code = serializers.CharField(max_length=12)
    duration_minutes = serializers.IntegerField(min_value=1, max_value=525_600)
    price_fcfa = serializers.IntegerField(required=False, min_value=0, default=0)
    data_cap_mb = serializers.IntegerField(required=False, min_value=0, default=0)
    rate_limit = serializers.CharField(required=False, allow_blank=True, max_length=40, default="")


class PlanSummarySerializer(serializers.ModelSerializer):
    """Forfait résumé, imbriqué dans un lot."""

    duration_label = serializers.CharField(read_only=True)

    class Meta:
        model = Plan
        fields = ("id", "name", "code", "duration_label", "data_cap_mb", "price_fcfa")
        read_only_fields = fields


class VoucherBatchSerializer(serializers.ModelSerializer):
    """Lot de vouchers avec ses compteurs d'état."""

    site = DeviceSiteSerializer(read_only=True)
    plan = PlanSummarySerializer(read_only=True)
    counts = serializers.SerializerMethodField()
    device_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = VoucherBatch
        fields = (
            "id", "site", "plan", "device_id", "quantity", "prefix", "note",
            "provisioned_at", "last_sync_at", "counts", "created_at",
        )
        read_only_fields = fields

    def get_counts(self, obj: VoucherBatch) -> dict[str, int]:
        """Compte les vouchers du lot par état.

        Args:
            obj: Lot sérialisé.

        Returns:
            ``{"total": n, "unused": n, "active": n, ...}``.
        """
        annotated = getattr(obj, "total_count", None)
        stats = VoucherSelector.stats(obj)
        if annotated is not None:
            stats["total"] = annotated
        return stats


class VoucherBatchCreateSerializer(serializers.Serializer):
    """Charge utile de génération d'un lot."""

    site_id = serializers.UUIDField()
    plan_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=500, default=10)
    prefix = serializers.CharField(required=False, allow_blank=True, max_length=8, default="")
    note = serializers.CharField(required=False, allow_blank=True, max_length=160, default="")
    device_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class VoucherSerializer(serializers.ModelSerializer):
    """Voucher exposé en lecture (le code sert d'identifiant de vente)."""

    state_label = serializers.CharField(source="get_state_display", read_only=True)
    plan_name = serializers.CharField(source="batch.plan.name", read_only=True)

    class Meta:
        model = Voucher
        fields = (
            "id", "code", "password", "state", "state_label", "plan_name",
            "activated_at", "expires_at", "used_bytes", "last_synced_at", "batch_id",
        )
        read_only_fields = fields


class ProvisionReportSerializer(serializers.Serializer):
    """Compte rendu d'un envoi vers le routeur."""

    batch_id = serializers.CharField()
    device_id = serializers.CharField(allow_blank=True)
    pushed = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


class SyncReportSerializer(serializers.Serializer):
    """Compte rendu d'une synchronisation."""

    batch_id = serializers.CharField()
    checked = serializers.IntegerField()
    activated = serializers.IntegerField()
    expired = serializers.IntegerField()
    exhausted = serializers.IntegerField()
    unknown = serializers.IntegerField()
