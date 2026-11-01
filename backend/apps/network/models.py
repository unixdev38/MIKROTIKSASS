"""Sites, routeurs et identifiants de management.

Les mots de passe et clés sont **toujours** stockés chiffrés (``core.crypto``) :
aucun champ en clair n'existe dans ce module.
"""
from __future__ import annotations

from django.db import models

from core.models import TenantScopedModel


class DeviceStatus(models.TextChoices):
    """État de supervision d'un routeur."""

    PENDING = "pending", "En attente"
    ONLINE = "online", "En ligne"
    DEGRADED = "degraded", "Dégradé"
    UNREACHABLE = "unreachable", "Hors ligne"
    DISABLED = "disabled", "Désactivé"


class DeviceTransport(models.TextChoices):
    """Transport utilisé pour joindre le routeur."""

    REST = "rest", "REST (HTTPS)"
    BINARY = "binary", "API binaire (8729)"


class Site(TenantScopedModel):
    """Lieu physique regroupant des routeurs (cybercafé, hôtel, école).

    Attributes:
        name: Nom affiché.
        code: Code court unique dans l'espace (``CC-01``).
        city: Ville, utilisée pour le regroupement et les rapports.
    """

    name = models.CharField("nom", max_length=120)
    code = models.CharField("code", max_length=20)
    city = models.CharField("ville", max_length=80, blank=True)

    class Meta:
        verbose_name = "site"
        verbose_name_plural = "sites"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_site_code_per_tenant"),
        ]

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le nom du site suivi de son code, par exemple ``"Cyber Centre (CC-01)"``.
        """
        return f"{self.name} ({self.code})"


class Device(TenantScopedModel):
    """Routeur MikroTik rattaché à un site.

    Attributes:
        site: Site d'installation.
        name: Libellé interne (``hAP-ac2 · cyber-centre``).
        serial: Numéro de série relevé sur le matériel.
        model_name: Modèle (``hAP ac2``).
        ros_version: Version de RouterOS au dernier contact.
        management_ip: Adresse dans le tunnel WireGuard.
        transport: Transport de management effectivement utilisé.
        status: État de supervision.
        health: Dernier état de santé normalisé (dict sérialisable).
        last_seen_at: Dernier contact réussi.
        is_simulated: Routeur de démonstration (aucun matériel joignable).
        enrollment_expires_at: Expiration du script d'enrôlement en cours.
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField("nom", max_length=120)
    serial = models.CharField("numéro de série", max_length=60, blank=True)
    model_name = models.CharField("modèle", max_length=80, blank=True)
    ros_version = models.CharField("version RouterOS", max_length=20, blank=True)
    management_ip = models.GenericIPAddressField("IP de management", null=True, blank=True)
    transport = models.CharField(
        "transport", max_length=10, choices=DeviceTransport.choices, default=DeviceTransport.REST
    )
    status = models.CharField(
        "statut", max_length=20, choices=DeviceStatus.choices, default=DeviceStatus.PENDING
    )
    health = models.JSONField("santé", default=dict, blank=True)
    last_seen_at = models.DateTimeField("dernier contact", null=True, blank=True)
    is_simulated = models.BooleanField("simulé", default=False)
    enrollment_expires_at = models.DateTimeField("expiration enrôlement", null=True, blank=True)

    class Meta:
        verbose_name = "routeur"
        verbose_name_plural = "routeurs"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "serial"], condition=~models.Q(serial=""),
                name="uniq_device_serial_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le nom du routeur suivi de son site.
        """
        return f"{self.name} — {self.site.name}"


class DeviceCredential(TenantScopedModel):
    """Identifiants de management d'un routeur (valeurs chiffrées uniquement).

    Attributes:
        device: Routeur concerné (relation 1–1).
        api_username: Utilisateur API dédié créé sur le routeur.
        secret_encrypted: Mot de passe chiffré (AES-256-GCM, nonce préfixé).
        key_version: Version de la clé de chiffrement utilisée.
        wireguard_private_key_encrypted: Clé privée WireGuard chiffrée.
        wireguard_public_key: Clé publique correspondante (non secrète).
        heartbeat_token_encrypted: Jeton du heartbeat sortant, chiffré.
        rotated_at: Date de la dernière rotation des identifiants.
    """

    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="credential")
    api_username = models.CharField("utilisateur API", max_length=60, default="saas-api")
    secret_encrypted = models.BinaryField("mot de passe chiffré")
    key_version = models.PositiveSmallIntegerField("version de clé", default=1)
    wireguard_private_key_encrypted = models.BinaryField("clé privée WireGuard chiffrée")
    wireguard_public_key = models.CharField("clé publique WireGuard", max_length=64, blank=True)
    heartbeat_token_encrypted = models.BinaryField("jeton heartbeat chiffré")
    rotated_at = models.DateTimeField("dernière rotation", null=True, blank=True)

    class Meta:
        verbose_name = "identifiants de routeur"
        verbose_name_plural = "identifiants de routeur"

    def __str__(self) -> str:
        """Représentation lisible, sans jamais exposer de secret.

        Returns:
            Le nom d'utilisateur API et le routeur concerné.
        """
        return f"{self.api_username} @ {self.device_id}"
