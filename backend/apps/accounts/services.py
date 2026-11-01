"""Services de gestion des membres d'un espace."""
from __future__ import annotations

from django.db import transaction

from apps.accounts.constants import ROLE_LABELS, ROLE_RANK, ROLE_VIEWER
from apps.accounts.models import Membership, User
from core.exceptions import ConflictError, DomainValidationError, NotFoundError
from core.services import BaseService


class MembershipService(BaseService[Membership]):
    """Invitation et gestion des rôles.

    Args:
        actor: Utilisateur qui effectue l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def add_member(self, *, user: User, role: str = ROLE_VIEWER) -> Membership:
        """Ajoute un utilisateur à l'espace courant.

        Args:
            user: Utilisateur à rattacher.
            role: Rôle attribué (voir ``ROLE_RANK``).

        Returns:
            L'appartenance créée.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle administrateur.
            DomainValidationError: Si le rôle est inconnu ou supérieur à celui de l'acteur.
            ConflictError: Si l'utilisateur est déjà membre.
        """
        self.assert_role(self.actor_role, "admin")

        if role not in ROLE_RANK:
            raise DomainValidationError(f"Rôle inconnu : « {role} ».", code="role_unknown")
        if ROLE_RANK[role] > ROLE_RANK.get(self.actor_role or "", 0):
            raise DomainValidationError(
                "Vous ne pouvez pas attribuer un rôle supérieur au vôtre.", code="role_too_high"
            )

        tenant = self.require_tenant()
        if Membership.all_objects.filter(tenant=tenant, user=user).exists():
            raise ConflictError("Cet utilisateur est déjà membre de l'espace.", code="member_exists")

        with transaction.atomic():
            return Membership.objects.create(user=user, role=role)

    def change_role(self, *, membership_id: str, role: str) -> Membership:
        """Change le rôle d'un membre existant.

        Args:
            membership_id: Identifiant de l'appartenance à modifier.
            role: Nouveau rôle.

        Returns:
            L'appartenance mise à jour.

        Raises:
            PermissionDeniedError: Si l'acteur n'est pas administrateur.
            NotFoundError: Si l'appartenance n'existe pas dans cet espace.
            DomainValidationError: Si le rôle est inconnu.
        """
        self.assert_role(self.actor_role, "admin")
        if role not in ROLE_LABELS:
            raise DomainValidationError(f"Rôle inconnu : « {role} ».", code="role_unknown")

        membership = Membership.objects.filter(pk=membership_id).first()
        if membership is None:
            raise NotFoundError("Ce membre n'existe pas dans cet espace.", code="member_not_found")

        membership.role = role
        membership.save(update_fields=["role", "updated_at"])
        return membership
