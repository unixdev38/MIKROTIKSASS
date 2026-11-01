"""Services des espaces de travail."""
from __future__ import annotations

import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.constants import ROLE_OWNER
from apps.accounts.models import Membership
from apps.tenants.models import Tenant, TenantStatus
from core.context import reset_current_tenant, set_current_tenant
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TenantService(BaseService[Tenant]):
    """Création et cycle de vie des espaces de travail.

    Args:
        actor: Utilisateur à l'origine de l'action (``None`` pour un script).
    """

    def create_workspace(
        self,
        *,
        name: str,
        slug: str,
        owner: object,
        trial_days: int = 14,
        plan_code: str = "trial",
    ) -> Tenant:
        """Crée un espace de travail et y rattache son propriétaire.

        L'opération est atomique : si l'appartenance échoue, l'espace est annulé.
        Le slug est normalisé puis validé (minuscules, tirets, pas d'espace).

        Args:
            name: Nom commercial de l'entreprise.
            slug: Identifiant unique souhaité (``cyber-centre``).
            owner: Utilisateur devenant propriétaire de l'espace.
            trial_days: Durée de l'essai gratuit en jours.
            plan_code: Offre de départ.

        Returns:
            Le tenant créé, avec son propriétaire rattaché.

        Raises:
            DomainValidationError: Si le nom est vide ou le slug invalide.
            ConflictError: Si le slug est déjà utilisé.

        Example:
            >>> tenant = TenantService(actor=user).create_workspace(
            ...     name="Cyber Centre", slug="cyber-centre", owner=user
            ... )
        """
        clean_name = (name or "").strip()
        clean_slug = (slug or "").strip().lower()

        if not clean_name:
            raise DomainValidationError("Le nom de l'espace est obligatoire.", code="tenant_name_required")
        if not SLUG_PATTERN.match(clean_slug):
            raise DomainValidationError(
                "L'identifiant doit contenir uniquement des minuscules, chiffres et tirets.",
                code="tenant_slug_invalid",
            )
        if Tenant.objects.filter(slug=clean_slug).exists():
            raise ConflictError(f"L'identifiant « {clean_slug} » est déjà utilisé.", code="tenant_slug_taken")

        with transaction.atomic():
            tenant = Tenant.objects.create(
                name=clean_name,
                slug=clean_slug,
                status=TenantStatus.TRIAL,
                plan_code=plan_code,
                trial_ends_at=timezone.now() + timedelta(days=trial_days),
            )
            token = set_current_tenant(tenant)
            try:
                Membership.objects.create(user_id=getattr(owner, "pk", owner), role=ROLE_OWNER)
            finally:
                reset_current_tenant(token)

        return tenant

    def close_workspace(self, tenant: Tenant) -> Tenant:
        """Ferme un espace et coupe l'accès (les données restent exportables).

        Args:
            tenant: Espace à fermer.

        Returns:
            L'espace mis à jour.

        Raises:
            ConflictError: Si l'espace est déjà fermé.
        """
        if tenant.status == TenantStatus.CLOSED:
            raise ConflictError("Cet espace est déjà fermé.", code="tenant_already_closed")

        tenant.status = TenantStatus.CLOSED
        tenant.save(update_fields=["status", "updated_at"])
        return tenant
