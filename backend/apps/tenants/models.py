"""Modèle du tenant (client du SaaS).

Le tenant n'est **pas** scopé : c'est lui qui définit la portée de toutes les autres
tables. Il ne peut donc pas hériter de ``TenantScopedModel``.
"""
from __future__ import annotations

from django.db import models

from core.models import TimeStampedModel


class TenantStatus(models.TextChoices):
    """Cycle de vie d'un espace de travail."""

    TRIAL = "trial", "Essai"
    ACTIVE = "active", "Actif"
    SUSPENDED = "suspended", "Suspendu"
    CLOSED = "closed", "Fermé"


class Tenant(TimeStampedModel):
    """Client du SaaS : une entreprise et son périmètre de données.

    Attributes:
        slug: Identifiant lisible, unique, utilisé dans les URLs et sous-domaines.
        name: Nom commercial affiché.
        status: État du cycle de vie (essai gratuit, actif, suspendu, fermé).
        plan_code: Offre commerciale souscrite (``trial``, ``starter``, ``pro``…).
        trial_ends_at: Fin de la période d'essai, ``None`` si converti.
        settings: Réglages variables par tenant (polling, options, quotas).
    """

    slug = models.SlugField("identifiant", max_length=60, unique=True)
    name = models.CharField("nom", max_length=120)
    status = models.CharField(
        "statut", max_length=20, choices=TenantStatus.choices, default=TenantStatus.TRIAL
    )
    plan_code = models.CharField("offre", max_length=20, default="trial")
    trial_ends_at = models.DateTimeField("fin d'essai", null=True, blank=True)
    settings = models.JSONField("réglages", default=dict, blank=True)

    class Meta:
        verbose_name = "espace de travail"
        verbose_name_plural = "espaces de travail"
        ordering = ("name",)

    def __str__(self) -> str:
        """Représentation lisible utilisée dans les logs et les scripts.

        Returns:
            Le nom suivi du slug, par exemple ``"Cyber Centre (cyber-centre)"``.
        """
        return f"{self.name} ({self.slug})"

    @property
    def is_active(self) -> bool:
        """Indique si l'espace peut être utilisé.

        Returns:
            ``True`` pour un espace actif ou en essai.
        """
        return self.status in {TenantStatus.TRIAL, TenantStatus.ACTIVE}
