"""Objets normalisés échangés avec un routeur.

Ces structures sont volontairement indépendantes du transport (REST ou API binaire) :
le reste de l'application ne connaît que ces types, jamais le protocole.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SystemInfo:
    """Identité et ressources d'un routeur.

    Attributes:
        identity: Nom RouterOS (``/system identity``).
        version: Version de RouterOS, par exemple ``"7.16.2"``.
        model: Modèle matériel (``"hAP ac2"``).
        serial: Numéro de série.
        uptime_seconds: Temps depuis le dernier démarrage.
        cpu_load_percent: Charge processeur instantanée (0–100).
        free_memory_bytes: Mémoire libre.
        total_memory_bytes: Mémoire totale.
        board_temperature_c: Température carte, si exposée par le matériel.
    """

    identity: str
    version: str
    model: str
    serial: str
    uptime_seconds: int
    cpu_load_percent: int
    free_memory_bytes: int
    total_memory_bytes: int
    board_temperature_c: float | None = None

    @property
    def memory_used_percent(self) -> int:
        """Calcule l'occupation mémoire.

        Returns:
            Le pourcentage utilisé (0–100), ou 0 si la mémoire totale est inconnue.
        """
        if not self.total_memory_bytes:
            return 0
        used = self.total_memory_bytes - self.free_memory_bytes
        return max(0, min(100, round(used * 100 / self.total_memory_bytes)))


@dataclass(frozen=True, slots=True)
class InterfaceState:
    """État d'une interface réseau (compteurs bruts, cumulés depuis le boot).

    Attributes:
        name: Nom RouterOS (``ether1``, ``bridge-hotspot``).
        kind: Type (``ether``, ``wlan``, ``bridge``).
        is_running: Câble/lien actif.
        is_disabled: Interface désactivée par configuration.
        rx_bytes: Octets reçus depuis le démarrage.
        tx_bytes: Octets émis depuis le démarrage.
    """

    name: str
    kind: str
    is_running: bool
    is_disabled: bool
    rx_bytes: int
    tx_bytes: int


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """Résultat d'une tentative de contact avec un routeur.

    Attributes:
        is_ok: Le routeur a répondu et les données sont exploitables.
        system_info: Identité et ressources, si ``is_ok``.
        interfaces: Interfaces remontées (liste vide si non demandé ou en échec).
        latency_ms: Durée de l'aller-retour, en millisecondes.
        error: Message d'erreur lisible si ``is_ok`` est faux.
        checked_at: Horodatage de la tentative.
    """

    is_ok: bool
    system_info: SystemInfo | None = None
    interfaces: list[InterfaceState] = field(default_factory=list)
    latency_ms: int = 0
    error: str = ""
    checked_at: datetime | None = None
