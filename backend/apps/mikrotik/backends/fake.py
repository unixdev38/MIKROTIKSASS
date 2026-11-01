"""Backend factice : développement, démonstration et tests.

Il ne contacte aucun routeur et renvoie des données déterministes dérivées de l'hôte,
ce qui permet de tester toute la plateforme sans matériel.
"""
from __future__ import annotations

import hashlib

from apps.mikrotik.backends.base import BaseBackend
from apps.mikrotik.schemas import HotspotUserState, InterfaceState, SystemInfo
from core.exceptions import ExternalServiceError

#: Utilisateurs hotspot simulés, conservés entre deux instances (clé = hôte).
_FAKE_HOTSPOT_USERS: dict[str, dict[str, dict[str, str]]] = {}


def reset_fake_router_state(host: str | None = None) -> None:
    """Efface les utilisateurs simulés (tests, démonstration, remise à zéro).

    Args:
        host: Hôte à oublier, ou ``None`` pour tout effacer.
    """
    if host is None:
        _FAKE_HOTSPOT_USERS.clear()
    else:
        _FAKE_HOTSPOT_USERS.pop(host, None)


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

    def upsert_hotspot_user(
        self,
        *,
        name: str,
        password: str,
        limit_uptime: str = "",
        limit_bytes_total: int = 0,
        rate_limit: str = "",
        comment: str = "",
    ) -> None:
        """Enregistre un utilisateur hotspot en mémoire.

        Args:
            name: Nom d'utilisateur.
            password: Mot de passe (conservé pour permettre une relecture).
            limit_uptime: Durée maximale.
            limit_bytes_total: Volume maximal en octets.
            rate_limit: Limite de débit.
            comment: Commentaire libre.

        Raises:
            ExternalServiceError: Si le backend a été créé en mode échec.
        """
        if self._fail_with:
            raise ExternalServiceError(self._fail_with, code="router_unreachable")
        _FAKE_HOTSPOT_USERS.setdefault(self.host, {})[name] = {
            "password": password,
            "limit-uptime": limit_uptime,
            "limit-bytes-total": str(limit_bytes_total),
            "rate-limit": rate_limit,
            "comment": comment,
        }

    def delete_hotspot_user(self, name: str) -> None:
        """Supprime un utilisateur hotspot simulé.

        Args:
            name: Nom d'utilisateur.

        Raises:
            ExternalServiceError: Si le backend a été créé en mode échec.
        """
        if self._fail_with:
            raise ExternalServiceError(self._fail_with, code="router_unreachable")
        _FAKE_HOTSPOT_USERS.get(self.host, {}).pop(name, None)

    def fetch_hotspot_users(self) -> list[HotspotUserState]:
        """Liste les utilisateurs simulés avec des compteurs plausibles.

        Returns:
            Les utilisateurs enregistrés, du plus ancien au plus récent.

        Raises:
            ExternalServiceError: Si le backend a été créé en mode échec.
        """
        if self._fail_with:
            raise ExternalServiceError(self._fail_with, code="router_unreachable")
        users = _FAKE_HOTSPOT_USERS.get(self.host, {})
        return [
            HotspotUserState(
                name=name,
                bytes_in=18 * 1024 * 1024 + index * 1024 * 1024,
                bytes_out=3 * 1024 * 1024,
                uptime_seconds=900,
                is_active=True,
                comment=payload.get("comment", ""),
            )
            for index, (name, payload) in enumerate(users.items())
        ]
