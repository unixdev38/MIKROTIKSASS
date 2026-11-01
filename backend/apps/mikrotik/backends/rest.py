"""Backend REST (RouterOS >= 7.1, service ``www-ssl``).

Les lectures système et interface vivent ici ; les opérations hotspot sont fournies par
``HotspotRestMixin`` (``apps.mikrotik.backends.rest_hotspot``), ce qui garde chaque
fichier sous la limite de 300 lignes.

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
from apps.mikrotik.backends.helpers import (
    _as_bool,
    _as_float_or_none,
    _as_int,
    parse_routeros_uptime,
)
from apps.mikrotik.backends.rest_hotspot import HotspotRestMixin
from apps.mikrotik.schemas import InterfaceState, SystemInfo
from core.exceptions import ExternalServiceError


class RestBackend(HotspotRestMixin, BaseBackend):
    """Backend HTTP/JSON sur ``https://<routeur>/rest``.

    Args:
        host: Adresse de management (IP du tunnel, ou IP locale d'un routeur de test).
        username: Utilisateur API.
        secret: Mot de passe de l'utilisateur API.
        port: Port du service ``www``/``www-ssl`` (443 par défaut, 80 si TLS désactivé).
        use_tls: ``True`` pour ``https``, ``False`` pour ``http`` (routeur de test).
        timeout: Délai par requête, en secondes.
        verify_tls: Vérifie le certificat (les routeurs utilisent un certificat
            auto-signé : ``False`` par défaut).
    """

    @property
    def scheme(self) -> str:
        """Schéma d'URL correspondant au réglage TLS.

        Returns:
            ``"https"`` ou ``"http"``.
        """
        return "https" if self.use_tls else "http"

    @property
    def base_url(self) -> str:
        """URL de base de l'API REST.

        Returns:
            ``<schéma>://<host>:<port>`` sans slash final, par exemple
            ``https://10.66.1.14:443``.
        """
        port = self.port or (443 if self.use_tls else 80)
        return f"{self.scheme}://{self.host}:{port}"

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
        return self._request("GET", path)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        """Exécute une requête REST authentifiée.

        Args:
            method: Verbe HTTP (``GET``, ``PUT``, ``PATCH``, ``DELETE``).
            path: Chemin REST (``"/rest/ip/hotspot/user"``).
            payload: Corps JSON éventuel.

        Returns:
            La charge utile décodée (``None`` si le routeur ne renvoie rien).

        Raises:
            ExternalServiceError: En cas d'erreur réseau, TLS, HTTP ou de décodage.
                Le message inclut le détail renvoyé par RouterOS, ce qui rend les
                erreurs de configuration (hotspot absent, policy manquante) lisibles.
        """
        token = base64.b64encode(f"{self.username}:{self.secret}".encode()).decode()
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            context = self._ssl_context() if self.use_tls else None
            with urlopen(request, timeout=self.timeout, context=context) as response:
                raw = response.read().decode("utf-8").strip()
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = self._error_detail(exc)
            raise ExternalServiceError(
                f"Le routeur a refusé la requête (HTTP {exc.code}){detail}.", code="router_http_error"
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ExternalServiceError(
                f"Routeur injoignable ({exc.__class__.__name__}).", code="router_unreachable"
            ) from exc
        except (ValueError, UnicodeDecodeError) as exc:
            raise ExternalServiceError(
                "Réponse du routeur illisible (JSON invalide).", code="router_bad_response"
            ) from exc

    @staticmethod
    def _error_detail(exc: HTTPError) -> str:
        """Extrait le message d'erreur renvoyé par RouterOS.

        Args:
            exc: Erreur HTTP levée par ``urlopen``.

        Returns:
            Un suffixe lisible (``" : hotspot non configuré"``), ou une chaîne vide.
        """
        try:
            body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:  # noqa: BLE001 - le corps d'erreur ne doit jamais masquer l'erreur
            return ""
        if not body:
            return ""
        try:
            parsed = json.loads(body)
            message = parsed.get("detail") or parsed.get("message") or ""
        except (ValueError, AttributeError):
            message = body[:160]
        return f" : {message}" if message else ""

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
