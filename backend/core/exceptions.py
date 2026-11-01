"""Exceptions métier du domaine.

Elles sont indépendantes de Django et de DRF : les services lèvent ces erreurs,
la couche API les traduit en réponses ``application/problem+json`` (RFC 9457).
"""
from __future__ import annotations


class DomainError(Exception):
    """Erreur métier de base.

    Args:
        detail: Message lisible par un humain, en français.
        code: Identifiant stable de l'erreur (utilisé dans les tests et l'API).

    Attributes:
        detail: Message affichable.
        code: Identifiant technique.
        status: Code HTTP associé.
        title: Titre court, par défaut le nom de la classe.
    """

    status: int = 400
    title: str = "Erreur métier"

    def __init__(self, detail: str, *, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.__class__.__name__.lower()

    def as_problem(self) -> dict[str, object]:
        """Sérialise l'erreur au format problem+json.

        Returns:
            Un dictionnaire prêt à être renvoyé par l'API.
        """
        return {
            "type": f"https://api.kora.bf/problems/{self.code}",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "code": self.code,
        }


class NotFoundError(DomainError):
    """Ressource inexistante **ou appartenant à un autre tenant** (fuite d'existence évitée)."""

    status = 404
    title = "Ressource introuvable"


class ConflictError(DomainError):
    """Conflit d'état : doublon, transition invalide, action déjà effectuée."""

    status = 409
    title = "Conflit"


class PermissionDeniedError(DomainError):
    """L'acteur n'a pas le rôle requis pour cette action."""

    status = 403
    title = "Action non autorisée"


class DomainValidationError(DomainError):
    """Donnée invalide du point de vue métier (au-delà du format)."""

    status = 422
    title = "Données invalides"


class ExternalServiceError(DomainError):
    """Un service externe (routeur, agrégateur de paiement) a échoué."""

    status = 503
    title = "Service externe indisponible"


class TenantNotSetError(DomainError):
    """Aucun tenant n'est défini dans le contexte : requête ou tâche mal configurée."""

    status = 500
    title = "Contexte de tenant manquant"
