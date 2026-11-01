"""Structures de données du parc réseau (aucune dépendance ORM)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EnrollmentBundle:
    """Résultat d'un enrôlement : script à coller et informations de suivi.

    Attributes:
        device_id: Identifiant du routeur enrôlé.
        script: Script RouterOS prêt à coller dans WinBox (contient les secrets).
        management_ip: Adresse allouée dans le tunnel.
        api_username: Utilisateur API créé sur le routeur.
        expires_at: Date au-delà de laquelle le script doit être régénéré.
        is_renewal: Vrai si l'enrôlement remplace des identifiants existants.
    """

    device_id: str
    script: str
    management_ip: str
    api_username: str
    expires_at: datetime
    is_renewal: bool = False


@dataclass(frozen=True, slots=True)
class DeviceSnapshot:
    """État d'un routeur après une sonde, prêt à être persisté.

    Attributes:
        status: Statut de supervision à appliquer.
        health: Données de santé sérialisables.
        ros_version: Version relevée (vide si inconnue).
        serial: Numéro de série relevé.
        model_name: Modèle relevé.
        is_reachable: Le routeur a répondu.
        latency_ms: Latence mesurée.
        error: Message d'erreur si injoignable.
    """

    status: str
    health: dict[str, object]
    ros_version: str = ""
    serial: str = ""
    model_name: str = ""
    is_reachable: bool = False
    latency_ms: int = 0
    error: str = ""
