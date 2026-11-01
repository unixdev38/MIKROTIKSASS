"""Backend REST (RouterOS >= 7.1, service ``www-ssl``).

Implémentation volontairement minimale et sans dépendance externe : la bibliothèque
standard suffit pour un GET JSON authentifié en Basic. Les écritures (provisioning)
seront ajoutées en P4 avec la même structure.
"""
from __future__ import annotations

import base64
import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apps.mikrotik.backends.base import BaseBackend
from apps.mikrotik.schemas import InterfaceState, SystemInfo
from core.exceptions import ExternalServiceError


class RestBackend(BaseBackend):
    """Backend HTTP/JSON sur ``https://<routeur>/rest``.

    Args:
        host: Adresse de management.
        username: Utilisateur API.
        secret: Mot de passe de l'utilisateur API.
        port: Port HTTPS du routeur (443 par défaut).
        timeout: Délai par requête, en secondes.
        verify_tls: Vérifie le certificat (les routeurs utilisent souvent un
            certificat auto-signé épinglé, donc ``False`` par défaut).
    """

    @property
    def base_url(self) -> str:
        """URL de base de l'API REST.

        Returns:
            ``https://<host>:<port>`` sans slash final.
        """
        port = self.port or 443
        return f"https://{self.host}:{port}"

    def fetch_system_info(self) -> SystemInfo:
        """Interroge ``/rest/system/identity`` et ``/rest/system/resource``.

        Returns:
            Les informations normalisées du routeur.

        Raises:
            ExternalServiceError: Si le routeur est injoignable, lent, ou renvoie une
                charge utile inexploitable.
        """
        identity = self._get("/rest/system/identity") or {}
        resource = self._get("/rest/system/resource") or {}

        return SystemInfo(
            identity=str(identity.get("name", "")),
            version=str(resource.get("version", "")),
            model=str(resource.get("board-name", "")),
            serial=str(resource.get("serial-number", "")),
            uptime_seconds=parse_routeros_uptime(str(resource.get("uptime", "0s"))),
            cpu_load_percent=_as_int(resource.get("cpu-load")),
            free_memory_bytes=_as_int(resource.get("free-memory")),
            total_memory_bytes=_as_int(resource.get("total-memory")),
            board_temperature_c=_as_float_or_none(resource.get("board-temperature")),
        )

    def fetch_interfaces(self) -> list[InterfaceState]:
        """Interroge ``/rest/interface`` et normalise les compteurs.

        Returns:
            La liste des interfaces, avec ``rx-byte`` / ``tx-byte`` convertis en entiers.

        Raises:
            ExternalServiceError: Si l'appel échoue.
        """
        rows = self._get("/rest/interface") or []
        return [
            InterfaceState(
                name=str(row.get("name", "")),
                kind=str(row.get("type", "ether")),
                is_running=_as_bool(row.get("running")),
                is_disabled=_as_bool(row.get("disabled")),
                rx_bytes=_as_int(row.get("rx-byte")),
                tx_bytes=_as_int(row.get("tx-byte")),
            )
            for row in rows
            if isinstance(row, dict)
        ]

    def _get(self, path: str) -> Any:
        """Exécute un GET authentifié et décode le JSON.

        Args:
            path: Chemin REST, par exemple ``"/rest/system/resource"``.

        Returns:
            La charge utile décodée (liste ou dictionnaire).

        Raises:
            ExternalServiceError: En cas d'erreur réseau, TLS, HTTP ou de décodage.
        """
        token = base64.b64encode(f"{self.username}:{self.secret}".encode()).decode()
        request = Request(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout, context=self._ssl_context()) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ExternalServiceError(
                f"Le routeur a refusé la requête (HTTP {exc.code}).", code="router_http_error"
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ExternalServiceError(
                f"Routeur injoignable ({exc.__class__.__name__}).", code="router_unreachable"
            ) from exc
        except (ValueError, UnicodeDecodeError) as exc:
            raise ExternalServiceError(
                "Réponse du routeur illisible (JSON invalide).", code="router_bad_response"
            ) from exc

    def _ssl_context(self) -> ssl.SSLContext:
        """Construit le contexte TLS selon ``verify_tls``.

        Returns:
            Un contexte SSL prêt à l'emploi.
        """
        context = ssl.create_default_context()
        if not self.verify_tls:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context


def parse_routeros_uptime(raw: str) -> int:
    """Convertit une durée RouterOS (``1w2d3h4m5s``) en secondes.

    Args:
        raw: Chaîne renvoyée par ``/system/resource``.

    Returns:
        La durée équivalente en secondes (0 si la chaîne est vide).

    Example:
        >>> parse_routeros_uptime("1w2d3h")
        788400
    """
    units = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
    total, number = 0, ""
    for char in raw.strip():
        if char.isdigit():
            number += char
        elif char in units and number:
            total += int(number) * units[char]
            number = ""
    return total


def _as_int(value: object) -> int:
    """Convertit une valeur RouterOS en entier, avec repli à 0.

    Args:
        value: Valeur brute (souvent une chaîne).

    Returns:
        L'entier correspondant, ou 0 si non convertible.
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _as_float_or_none(value: object) -> float | None:
    """Convertit une valeur RouterOS en flottant facultatif.

    Args:
        value: Valeur brute.

    Returns:
        Le flottant, ou ``None`` si la valeur est absente ou invalide.
    """
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _as_bool(value: object) -> bool:
    """Interprète les booléens RouterOS (``true``/``false``/``yes``/``no``).

    Args:
        value: Valeur brute.

    Returns:
        ``True`` si la valeur exprime l'affirmation.
    """
    return str(value).strip().lower() in {"true", "yes", "1"}
