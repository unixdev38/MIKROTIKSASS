"""Extension hotspot du backend REST : utilisateurs et sessions.

Le mixin ne connaît que ``_get`` / ``_request`` fournis par
:class:`apps.mikrotik.backends.rest.RestBackend` : il ne peut pas être utilisé seul
(héritage volontairement partiel, dans l'esprit du patron *mixin*).
"""
from __future__ import annotations

from typing import Any

from apps.mikrotik.backends.helpers import _as_bool, _as_int, parse_routeros_uptime
from apps.mikrotik.schemas import HotspotUserState


class HotspotRestMixin:
    """Opérations hotspot (``/rest/ip/hotspot``) d'un routeur RouterOS 7."""

    # ------------------------------------------------------- hotspot (vouchers)
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
        """Crée ou met à jour un utilisateur hotspot sur le routeur.

        Args:
            name: Nom d'utilisateur (= code du voucher).
            password: Mot de passe associé.
            limit_uptime: Durée maximale RouterOS (``"1h"``, ``"7d"``).
            limit_bytes_total: Volume maximal en octets (0 = illimité).
            rate_limit: Limite de débit RouterOS (``"2M/2M"``).
            comment: Commentaire libre.

        Raises:
            ExternalServiceError: Si le routeur refuse l'écriture. Le message contient
                alors le détail RouterOS (par exemple hotspot non configuré).
        """
        payload: dict[str, Any] = {"name": name, "password": password}
        if limit_uptime:
            payload["limit-uptime"] = limit_uptime
        if limit_bytes_total:
            payload["limit-bytes-total"] = str(limit_bytes_total)
        if rate_limit:
            payload["rate-limit"] = rate_limit
        if comment:
            payload["comment"] = comment

        existing = self._find_hotspot_user(name)
        if existing:
            self._request("PATCH", f"/rest/ip/hotspot/user/{existing['.id']}", payload)
        else:
            self._request("PUT", "/rest/ip/hotspot/user", payload)

    def delete_hotspot_user(self, name: str) -> None:
        """Supprime un utilisateur hotspot et sa session éventuelle.

        Args:
            name: Nom d'utilisateur.

        Raises:
            ExternalServiceError: Si le routeur refuse la suppression.
        """
        for session in self._get(f"/rest/ip/hotspot/active?name={name}") or []:
            if isinstance(session, dict) and session.get(".id"):
                self._request("DELETE", f"/rest/ip/hotspot/active/{session['.id']}")

        existing = self._find_hotspot_user(name)
        if existing:
            self._request("DELETE", f"/rest/ip/hotspot/user/{existing['.id']}")

    def fetch_hotspot_users(self) -> list[HotspotUserState]:
        """Liste les utilisateurs hotspot et leurs compteurs.

        Returns:
            Les utilisateurs configurés sur le routeur.

        Raises:
            ExternalServiceError: Si la lecture échoue.
        """
        rows = self._get("/rest/ip/hotspot/user") or []
        states = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            states.append(
                HotspotUserState(
                    name=str(row.get("name", "")),
                    bytes_in=_as_int(row.get("bytes-in")),
                    bytes_out=_as_int(row.get("bytes-out")),
                    uptime_seconds=parse_routeros_uptime(str(row.get("uptime", "0s"))),
                    is_active=not _as_bool(row.get("disabled")),
                    comment=str(row.get("comment", "")),
                )
            )
        return states

    def _find_hotspot_user(self, name: str) -> dict[str, Any] | None:
        """Retrouve un utilisateur hotspot par son nom.

        Args:
            name: Nom d'utilisateur recherché.

        Returns:
            La ligne RouterOS (avec ``.id``), ou ``None`` s'il n'existe pas.

        Raises:
            ExternalServiceError: Si la lecture échoue.
        """
        rows = self._get("/rest/ip/hotspot/user") or []
        return next(
            (row for row in rows if isinstance(row, dict) and row.get("name") == name), None
        )

