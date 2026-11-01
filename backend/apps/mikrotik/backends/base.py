"""Contrat des backends RouterOS.

Un backend ne fait qu'une chose : parler à **un** routeur et normaliser la réponse.
Il n'accède jamais à la base de données (c'est le rôle des services).
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Self

from apps.mikrotik.schemas import InterfaceState, ProbeResult, SystemInfo
from core.exceptions import ExternalServiceError


class BaseBackend(ABC):
    """Backend de communication avec un routeur.

    Args:
        host: Adresse de management (IP du tunnel WireGuard).
        username: Utilisateur API dédié au routeur.
        secret: Mot de passe de cet utilisateur.
        port: Port du service (8729 pour l'API binaire, 443 pour REST).
        use_tls: Chiffre le transport (HTTPS ou API binaire TLS).
        timeout: Délai maximal d'une requête, en secondes.
        verify_tls: Vérifie le certificat du routeur (souvent auto-signé en production).
    """

    def __init__(
        self,
        *,
        host: str,
        username: str,
        secret: str,
        port: int | None = None,
        use_tls: bool = True,
        timeout: int = 10,
        verify_tls: bool = False,
    ) -> None:
        self.host = host
        self.username = username
        self.secret = secret
        self.port = port
        self.use_tls = use_tls
        self.timeout = timeout
        self.verify_tls = verify_tls

    @property
    @abstractmethod
    def base_url(self) -> str:
        """URL (ou adresse de socket) utilisée pour joindre le routeur."""

    @abstractmethod
    def fetch_system_info(self) -> SystemInfo:
        """Récupère l'identité et les ressources du routeur.

        Returns:
            Les informations normalisées.

        Raises:
            ExternalServiceError: Si le routeur ne répond pas ou renvoie une erreur.
        """

    @abstractmethod
    def fetch_interfaces(self) -> list[InterfaceState]:
        """Récupère les interfaces et leurs compteurs.

        Returns:
            La liste des interfaces, éventuellement vide.

        Raises:
            ExternalServiceError: Si l'appel échoue.
        """

    def probe(self, *, with_interfaces: bool = True) -> ProbeResult:
        """Teste le contact et mesure la latence (méthode gabarit).

        Cette implémentation est commune à tous les backends : les sous-classes ne
        fournissent que ``fetch_system_info`` et ``fetch_interfaces``. Les erreurs sont
        capturées pour ne jamais faire échouer un worker sur un routeur éteint.

        Args:
            with_interfaces: Charge aussi les compteurs d'interface.

        Returns:
            Un ``ProbeResult`` : succès avec données, ou échec avec message.
        """
        started = time.perf_counter()
        checked_at = datetime.now(tz=UTC)
        try:
            info = self.fetch_system_info()
            interfaces = self.fetch_interfaces() if with_interfaces else []
        except ExternalServiceError as exc:
            return self._failed(str(exc), started, checked_at)
        except Exception as exc:  # noqa: BLE001 - on ne veut jamais tuer un worker
            return self._failed(f"Erreur inattendue : {exc}", started, checked_at)

        return ProbeResult(
            is_ok=True,
            system_info=info,
            interfaces=interfaces,
            latency_ms=int((time.perf_counter() - started) * 1000),
            checked_at=checked_at,
        )

    def _failed(self, message: str, started: float, checked_at: datetime) -> ProbeResult:
        """Construit un résultat d'échec homogène.

        Args:
            message: Cause lisible de l'échec.
            started: Instant de départ (``time.perf_counter``).
            checked_at: Horodatage de la tentative.

        Returns:
            Un ``ProbeResult`` avec ``is_ok=False``.
        """
        return ProbeResult(
            is_ok=False,
            error=message,
            latency_ms=int((time.perf_counter() - started) * 1000),
            checked_at=checked_at,
        )

    def close(self) -> None:  # noqa: B027 - point d'extension volontairement vide
        """Libère les ressources réseau. Sans effet par défaut."""

    def __enter__(self) -> Self:
        """Entre dans le contexte d'utilisation du backend.

        Returns:
            Le backend lui-même.
        """
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Ferme proprement le backend en sortie de contexte."""
        self.close()
