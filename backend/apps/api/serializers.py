"""Sérialiseurs de l'API : validation de **forme** uniquement.

Les règles métier (unicité, transitions, quotas) vivent dans les services ; un
sérialiseur se limite aux types, longueurs et formats.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.network.models import Device, DeviceTransport, Site


class SiteSerializer(serializers.ModelSerializer):
    """Site exposé en lecture."""

    class Meta:
        model = Site
        fields = ("id", "name", "code", "city", "created_at")
        read_only_fields = fields


class SiteCreateSerializer(serializers.Serializer):
    """Charge utile de création d'un site."""

    name = serializers.CharField(max_length=120)
    code = serializers.CharField(max_length=20)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")


class DeviceSiteSerializer(serializers.ModelSerializer):
    """Site résumé, imbriqué dans un routeur."""

    class Meta:
        model = Site
        fields = ("id", "name", "code")


class DeviceSerializer(serializers.ModelSerializer):
    """Routeur exposé en lecture (aucun secret)."""

    site = DeviceSiteSerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = (
            "id", "name", "site", "serial", "model_name", "ros_version",
            "management_ip", "transport", "status", "health", "last_seen_at",
            "enrollment_expires_at", "is_simulated", "is_enrolled", "created_at",
        )
        read_only_fields = fields

    def get_is_enrolled(self, obj: Device) -> bool:
        """Indique si le routeur possède des identifiants de management.

        Args:
            obj: Routeur sérialisé.

        Returns:
            ``True`` si une ligne ``DeviceCredential`` existe.
        """
        return getattr(obj, "credential", None) is not None


class DeviceCreateSerializer(serializers.Serializer):
    """Charge utile d'enregistrement d'un routeur.

    Valide la forme ; l'appartenance du site au tenant et les doublons de série sont
    vérifiés par ``DeviceService.register``.
    """

    site_id = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    serial = serializers.CharField(max_length=60, required=False, allow_blank=True, default="")
    model_name = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    management_ip = serializers.IPAddressField(required=False, allow_null=True, default=None)
    transport = serializers.ChoiceField(
        choices=DeviceTransport.choices, required=False, default=DeviceTransport.REST
    )
    is_simulated = serializers.BooleanField(required=False, default=False)


class ProbeResultSerializer(serializers.Serializer):
    """Résultat d'une sonde, exposé à la console."""

    is_ok = serializers.BooleanField()
    latency_ms = serializers.IntegerField()
    error = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    system_info = serializers.DictField(required=False)


class MeSerializer(serializers.Serializer):
    """Identité de l'utilisateur connecté et espace actif."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    tenant = serializers.DictField(allow_null=True)
    role = serializers.CharField(allow_null=True)
    tenants = serializers.ListField(child=serializers.DictField())
