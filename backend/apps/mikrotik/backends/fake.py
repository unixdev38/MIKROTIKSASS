"""Backend factice : développement, démonstration et tests.

Il ne contacte aucun routeur et renvoie des données déterministes dérivées de l'hôte,
ce qui permet de tester toute la plateforme sans matériel.
"""
from __future__ import annotations

import hashlib

from apps.mikrotik.backends.base import BaseBackend
from apps.mikrotik.schemas import InterfaceState, SystemInfo
from core.exceptions import ExternalServiceError


class FakeBackend(BaseBackend):
    """Routeur simulé, reproductible.

    Args:
        host: Adresse de management (sert de graine pour les valeurs simulées).
        fail_with: Si fourni, toutes les lectures échouent avec ce message — utile
            pour tester le chemin d'erreur (routeur hors ligne).
        **kwargs: Paramètres transmis à :class:`BaseBackend`.
    """

    def __init__(self, *, host: str, fail_with: str | None = None, **kwargs: object) -> None:
        super().__init__(host=host, username="fake", secret="fake", **kwargs)  # type: ignore[arg-type]
        self._fail_with = fail_with

    @property
    def base_url(self) -> str:
        """Adresse simulée du routeur.

        Returns:
            Une URL factice rappelant qu'aucun appel réseau n'est fait.
        """
        return f"fake://{self.host}"

    def fetch_system_info(self) -> SystemInfo:
        """Renvoie une identité de routeur stable pour cet hôte.

        Returns:
            Les informations simulées.

        Raises:
            ExternalServiceError: Si le backend a été créé en mode échec.
        """
        if self._fail_with:
            raise ExternalServiceError(self._fail_with, code="router_unreachable")

        digest = hashlib.sha256(self.host.encode()).digest()
        return SystemInfo(
            identity=f"fake-{self.host.replace('.', '-')}",
            version="7.16.2",
            model="hAP ac2" if digest[0] % 2 == 0 else "RB4011iGS+",
            serial=f"HG{int.from_bytes(digest[1:3], 'big'):05d}",
            uptime_seconds=34 * 86400 + 7 * 3600,
            cpu_load_percent=15 + digest[3] % 25,
            free_memory_bytes=74 * 1024 * 1024,
            total_memory_bytes=128 * 1024 * 1024,
            board_temperature_c=38.0 + digest[4] % 8,
        )

    def fetch_interfaces(self) -> list[InterfaceState]:
        """Renvoie quatre interfaces types (WAN, LAN, deux radios).

        Returns:
            Les interfaces simulées.

        Raises:
            ExternalServiceError: Si le backend a été créé en mode échec.
        """
        if self._fail_with:
            raise ExternalServiceError(self._fail_with, code="router_unreachable")

        return [
            InterfaceState("ether1", "ether", True, False, 92_400_000_000, 18_700_000_000),
            InterfaceState("bridge-hotspot", "bridge", True, False, 31_200_000_000, 4_100_000_000),
            InterfaceState("wlan1", "wlan", True, False, 12_800_000_000, 3_300_000_000),
            InterfaceState("ether5", "ether", False, False, 0, 0),
        ]
