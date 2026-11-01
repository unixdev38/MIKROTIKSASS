"""Modèles abstraits partagés : identifiants, horodatage et portée tenant.

Toute table métier hérite de :class:`TenantScopedModel`. Le manager filtre
automatiquement sur le tenant courant ; ``all_objects`` n'est utilisé que pour les
tâches système, les migrations et les tests d'isolation.
"""
from __future__ import annotations

import uuid

from django.db import models

from core.context import get_current_tenant
from core.exceptions import TenantNotSetError


class TimeStampedModel(models.Model):
    """Base commune : identifiant UUID et horodatage immuable.

    Attributes:
        id: Identifiant UUID v4, généré à la création.
        created_at: Date de création (UTC).
        updated_at: Date de dernière modification (UTC).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedQuerySet(models.QuerySet):
    """QuerySet restreint à un tenant explicite."""

    def for_tenant(self, tenant: models.Model) -> TenantScopedQuerySet:
        """Filtre sur un tenant donné.

        Args:
            tenant: Tenant cible.

        Returns:
            Le queryset filtré (chaînable).
        """
        return self.filter(tenant=tenant)


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
    """Manager qui refuse de travailler hors d'un contexte tenant."""

    def get_queryset(self) -> TenantScopedQuerySet:
        """Retourne le queryset du tenant courant.

        Returns:
            Le queryset filtré sur ``tenant_id`` du contexte.

        Raises:
            TenantNotSetError: Si aucun tenant n'est défini dans le contexte.
        """
        tenant = get_current_tenant()
        if tenant is None:
            raise TenantNotSetError(
                "Aucun tenant dans le contexte : utilisez all_objects pour une opération système."
            )
        return super().get_queryset().filter(tenant_id=tenant.pk)


class TenantScopedModel(TimeStampedModel):
    """Base des données appartenant à un tenant.

    Attributes:
        tenant: Propriétaire de la ligne (jamais nullable).
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
    )

    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args: object, **kwargs: object) -> None:
        """Renseigne le tenant depuis le contexte avant la première sauvegarde."""
        if self._state.adding and getattr(self, "tenant_id", None) is None:
            tenant = get_current_tenant()
            if tenant is None:
                raise TenantNotSetError("Impossible de créer une ligne sans tenant dans le contexte.")
            self.tenant_id = tenant.pk
        super().save(*args, **kwargs)
