"""Service du connecteur : point d'entrée unique vers un routeur.

Aucune écriture en base ici : le service renvoie un résultat normalisé, la persistance
appartient aux services métier (``apps.network.services``).
"""
from __future__ import annotations

import logging

from apps.mikrotik.gateway import build_backend
from apps.mikrotik.schemas import ProbeResult, SystemInfo
from core.services import BaseService

logger = logging.getLogger(__name__)


class MikroTikService(BaseService[ProbeResult]):
    """Interroge un routeur via le backend approprié.

    Args:
        actor: Utilisateur à l'origine de l'action (``None`` depuis un worker).
    """

    def probe(self, device: object, *, with_interfaces: bool = True) -> ProbeResult:
        """Teste le contact avec un routeur et mesure la latence.

        Le service ne lève jamais d'exception réseau : un routeur éteint est un cas
        normal, pas une erreur de programmation. Le résultat porte l'échec.

        Args:
            device: Routeur à interroger (doit posséder ``credential``).
            with_interfaces: Charge aussi les compteurs d'interface (coût réseau plus élevé).

        Returns:
            Le résultat du contact, avec ``is_ok`` à ``False`` en cas d'échec.

        Example:
            >>> result = MikroTikService().probe(device)
            >>> result.is_ok, result.latency_ms
            (True, 38)
        """
        with build_backend(device) as backend:
            result = backend.probe(with_interfaces=with_interfaces)

        if result.is_ok:
            logger.debug("Routeur %s joignable en %s ms", device.pk, result.latency_ms)
        else:
            logger.warning("Routeur %s injoignable : %s", device.pk, result.error)
        return result

    def system_info(self, device: object) -> SystemInfo:
        """Récupère l'identité du routeur, sans tolérance à l'échec.

        Args:
            device: Routeur cible.

        Returns:
            Les informations du routeur.

        Raises:
            ExternalServiceError: Si le routeur ne répond pas.
        """
        with build_backend(device) as backend:
            return backend.fetch_system_info()
