"""Base des services applicatifs.

Un service = une classe par agrégat métier (device, voucher, facture…), exposant des
**méthodes-action** explicites (``register``, ``issue_enrollment``, ``probe``).
Chaque méthode est une unité de travail : elle valide, écrit dans une transaction et
renvoie un résultat typé. Un service ne connaît ni HTTP ni ``request``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from core.context import get_current_tenant
from core.exceptions import PermissionDeniedError, TenantNotSetError

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User
    from apps.tenants.models import Tenant

ResultT = TypeVar("ResultT")


class BaseService(Generic[ResultT]):
    """Socle commun des services.

    Args:
        actor: Utilisateur à l'origine de l'action (``None`` pour un traitement système,
            par exemple un worker Celery).

    Attributes:
        actor: Acteur de l'action, utilisé pour les contrôles de rôle et l'audit.
    """

    def __init__(self, actor: User | None = None) -> None:
        self.actor = actor

    def require_tenant(self) -> Tenant:
        """Retourne le tenant du contexte ou lève une erreur explicite.

        Returns:
            Le tenant courant.

        Raises:
            TenantNotSetError: Si aucun tenant n'est défini dans le contexte.
        """
        tenant = get_current_tenant()
        if tenant is None:
            raise TenantNotSetError("Cette action nécessite un tenant dans le contexte.")
        return tenant

    def assert_role(self, membership_role: str | None, minimum_role: str) -> None:
        """Vérifie qu'un rôle atteint le niveau minimal requis.

        Args:
            membership_role: Rôle effectif de l'acteur (``None`` si inconnu).
            minimum_role: Rôle minimal exigé par l'action.

        Raises:
            PermissionDeniedError: Si le rôle est insuffisant.
        """
        from apps.accounts.constants import ROLE_LABELS, ROLE_RANK

        if ROLE_RANK.get(membership_role or "", 0) < ROLE_RANK.get(minimum_role, 0):
            raise PermissionDeniedError(
                f"Cette action requiert au moins le rôle « {ROLE_LABELS.get(minimum_role, minimum_role)} »."
            )
