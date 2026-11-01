"""Contexte d'exécution : tenant courant.

Le tenant n'est **jamais** lu depuis un paramètre de requête : il est résolu par
``core.tenancy.TenantMiddleware`` et stocké dans une ``ContextVar``, ce qui permet aux
managers de filtrer automatiquement même dans les tâches Celery.
"""
from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.tenants.models import Tenant

_current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)

#: Type du jeton de restauration renvoyé par :func:`set_current_tenant`.
ContextToken = Token[object]


def set_current_tenant(tenant: Tenant | None) -> Token[Tenant | None]:
    """Définit le tenant courant et renvoie le jeton de restauration.

    Args:
        tenant: Tenant à placer dans le contexte, ou ``None`` pour le vider.

    Returns:
        Le jeton à passer à :func:`reset_current_tenant`.
    """
    return _current_tenant.set(tenant)


def reset_current_tenant(token: Token[Tenant | None]) -> None:
    """Restaure le contexte précédent.

    Args:
        token: Jeton renvoyé par :func:`set_current_tenant`.
    """
    _current_tenant.reset(token)


def get_current_tenant() -> Tenant | None:
    """Retourne le tenant courant.

    Returns:
        Le tenant actif, ou ``None`` si aucun n'est défini (ex. migration, script système).
    """
    return _current_tenant.get()
