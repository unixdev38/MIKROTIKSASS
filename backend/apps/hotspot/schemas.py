"""Résultats typés des opérations sur les vouchers."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ProvisionReport:
    """Résultat de l'envoi d'un lot vers un routeur.

    Attributes:
        batch_id: Identifiant du lot traité.
        device_id: Routeur ciblé (chaîne vide si aucun).
        pushed: Codes créés ou mis à jour sur le routeur.
        skipped: Codes déjà présents, laissés tels quels.
        failed: Codes refusés par le routeur.
        errors: Messages d'erreur (tronqués, un par échec).
    """

    batch_id: str
    pushed: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    device_id: str = ""

    @property
    def is_ok(self) -> bool:
        """Indique si aucun code n'a échoué.

        Returns:
            ``True`` si tous les codes ont été acceptés.
        """
        return self.failed == 0


@dataclass(frozen=True, slots=True)
class SyncReport:
    """Résultat de la lecture des compteurs d'un lot.

    Attributes:
        batch_id: Identifiant du lot.
        checked: Codes trouvés sur le routeur.
        activated: Codes vus actifs pour la première fois.
        expired: Codes arrivés à échéance pendant la synchronisation.
        exhausted: Codes ayant atteint leur volume maximal.
        unknown: Codes absents du routeur (non provisionnés ou supprimés).
    """

    batch_id: str
    checked: int = 0
    activated: int = 0
    expired: int = 0
    exhausted: int = 0
    unknown: int = 0
