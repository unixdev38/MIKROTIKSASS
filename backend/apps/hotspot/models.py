"""Forfaits, lots de vouchers et codes d'accès hotspot.

Un **forfait** décrit ce que vend le cybercafé (1 h, 24 h, 7 j…). Un **lot** est une
génération de N codes pour un site et un forfait. Un **voucher** est un code vendable,
dont l'état reflète ce que le routeur constate (connecté, quota épuisé, révoqué).
"""
from __future__ import annotations

from django.db import models

from apps.network.models import Device, Site
from core.models import TenantScopedModel


class VoucherState(models.TextChoices):
    """Cycle de vie d'un voucher."""

    UNUSED = "unused", "Généré"
    PROVISIONED = "provisioned", "Sur le routeur"
    ACTIVE = "active", "Utilisé"
    EXHAUSTED = "exhausted", "Quota épuisé"
    EXPIRED = "expired", "Expiré"
    REVOKED = "revoked", "Révoqué"


class Plan(TenantScopedModel):
    """Forfait vendu par un espace de travail.

    Attributes:
        name: Nom commercial (``1 heure``, ``Journée``).
        code: Code court unique dans l'espace (``H1``, ``D24``).
        duration_minutes: Durée de connexion accordée, en minutes.
        data_cap_mb: Volume inclus en Mo (``0`` = illimité).
        rate_limit: Limite de débit RouterOS (``"2M/2M"``), vide = aucune.
        price_fcfa: Prix de vente en francs CFA.
        is_active: Forfait encore commercialisé.
    """

    name = models.CharField("nom", max_length=80)
    code = models.CharField("code", max_length=12)
    duration_minutes = models.PositiveIntegerField("durée (minutes)", default=60)
    data_cap_mb = models.PositiveIntegerField("volume (Mo)", default=0)
    rate_limit = models.CharField("limite de débit", max_length=40, blank=True)
    price_fcfa = models.PositiveIntegerField("prix (FCFA)", default=0)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        verbose_name = "forfait"
        verbose_name_plural = "forfaits"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_plan_code_per_tenant"),
        ]

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le nom du forfait suivi de son code.
        """
        return f"{self.name} ({self.code})"

    @property
    def duration_label(self) -> str:
        """Durée formatée pour l'affichage.

        Returns:
            ``"60 min"``, ``"24 h"`` ou ``"7 j"`` selon la durée.
        """
        if self.duration_minutes % 1440 == 0:
            return f"{self.duration_minutes // 1440} j"
        if self.duration_minutes % 60 == 0:
            return f"{self.duration_minutes // 60} h"
        return f"{self.duration_minutes} min"


class VoucherBatch(TenantScopedModel):
    """Lot de codes générés en une fois.

    Attributes:
        site: Site de vente (détermine le routeur cible par défaut).
        plan: Forfait appliqué à tous les codes du lot.
        device: Routeur ciblé, forcé si le site en compte plusieurs.
        quantity: Nombre de codes demandés.
        prefix: Préfixe lisible ajouté aux codes.
        note: Commentaire libre (caisse, campagne…).
        provisioned_at: Date du dernier envoi réussi vers le routeur.
        last_sync_at: Date de la dernière lecture des compteurs.
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="voucher_batches")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="batches")
    device = models.ForeignKey(
        Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="voucher_batches"
    )
    quantity = models.PositiveIntegerField("quantité", default=0)
    prefix = models.CharField("préfixe", max_length=8, blank=True)
    note = models.CharField("note", max_length=160, blank=True)
    provisioned_at = models.DateTimeField("envoyé au routeur le", null=True, blank=True)
    last_sync_at = models.DateTimeField("dernière synchronisation", null=True, blank=True)

    class Meta:
        verbose_name = "lot de vouchers"
        verbose_name_plural = "lots de vouchers"

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le forfait, le site et la quantité.
        """
        return f"{self.quantity} × {self.plan.name} @ {self.site.code}"


class Voucher(TenantScopedModel):
    """Code d'accès vendable (un utilisateur hotspot sur le routeur).

    Attributes:
        batch: Lot d'origine.
        code: Code imprimé et vendu (sert d'utilisateur hotspot).
        password: Mot de passe associé (identique au code par défaut).
        state: État constaté ou déduit.
        activated_at: Première connexion constatée sur le routeur.
        expires_at: Fin de validité calculée à l'activation.
        used_bytes: Volume consommé (entrant + sortant), en octets.
        last_synced_at: Date de la dernière lecture sur le routeur.
    """

    batch = models.ForeignKey(VoucherBatch, on_delete=models.CASCADE, related_name="vouchers")
    code = models.CharField("code", max_length=16)
    password = models.CharField("mot de passe", max_length=16, blank=True)
    state = models.CharField(
        "état", max_length=20, choices=VoucherState.choices, default=VoucherState.UNUSED
    )
    activated_at = models.DateTimeField("activé le", null=True, blank=True)
    expires_at = models.DateTimeField("expire le", null=True, blank=True)
    used_bytes = models.BigIntegerField("volume consommé (octets)", default=0)
    last_synced_at = models.DateTimeField("synchronisé le", null=True, blank=True)

    class Meta:
        verbose_name = "voucher"
        verbose_name_plural = "vouchers"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_voucher_code_per_tenant"),
        ]
        indexes = [models.Index(fields=["batch", "state"], name="idx_voucher_batch_state")]

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le code et son état.
        """
        return f"{self.code} ({self.get_state_display()})"

    @property
    def is_usable(self) -> bool:
        """Indique si le code peut encore servir.

        Returns:
            ``True`` si le code n'est ni révoqué, ni épuisé, ni expiré.
        """
        return self.state not in {
            VoucherState.REVOKED, VoucherState.EXHAUSTED, VoucherState.EXPIRED,
        }
