"""Service des sites (création d'un lieu de vente).

Séparé de ``DeviceService`` : un site peut exister sans routeur, et inversement.
Réexporté par ``apps.network.services`` pour garder un point d'entrée unique.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from apps.network.models import Site
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover
    from apps.accounts.models import User


class SiteService(BaseService[Site]):
    """Création et mise à jour des sites.

    Args:
        actor: Utilisateur à l'origine de l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def register(self, *, name: str, code: str, city: str = "") -> Site:
        """Crée un site dans l'espace courant.

        Args:
            name: Nom affiché du site.
            code: Code court unique dans l'espace.
            city: Ville (facultative).

        Returns:
            Le site créé.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si le nom ou le code est vide.
            ConflictError: Si le code est déjà utilisé dans cet espace.
        """
        self.assert_role(self.actor_role, "technician")

        clean_name = (name or "").strip()
        clean_code = (code or "").strip().upper()
        if not clean_name:
            raise DomainValidationError("Le nom du site est obligatoire.", code="site_name_required")
        if not clean_code:
            raise DomainValidationError("Le code du site est obligatoire.", code="site_code_required")
        if Site.objects.filter(code=clean_code).exists():
            raise ConflictError(f"Le code « {clean_code} » existe déjà.", code="site_code_taken")

        return Site.objects.create(name=clean_name, code=clean_code, city=city.strip())
