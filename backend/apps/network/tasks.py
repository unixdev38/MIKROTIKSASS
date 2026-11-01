"""Workers du parc réseau.

Règle : une tâche ne contient **aucune** logique métier — elle résout le contexte,
appelle un service, journalise le résultat. Toute la décision est dans le service.
"""
from __future__ import annotations

import logging

from celery import shared_task

from apps.network.models import Device
from apps.network.selectors import DeviceSelector
from apps.network.services import DeviceService
from core.context import reset_current_tenant, set_current_tenant

logger = logging.getLogger(__name__)


@shared_task(name="network.probe_device", bind=True, max_retries=3, default_retry_delay=30)
def probe_device(self: object, device_id: str) -> dict[str, object]:
    """Sonde un routeur en arrière-plan et persiste son état.

    Args:
        self: Instance de tâche fournie par Celery (``bind=True``).
        device_id: Identifiant UUID du routeur (chaîne, sérialisable par Celery).

    Returns:
        Un résumé sérialisable : ``{"device_id", "is_ok", "status", "latency_ms", "error"}``.

    Example:
        >>> probe_device.delay("3f2b…")  # déclenché par l'API ou par un planificateur
    """
    device = DeviceSelector.for_worker(device_id)
    if device is None:
        logger.warning("Sonde ignorée : routeur %s introuvable", device_id)
        return {"device_id": device_id, "is_ok": False, "status": "missing", "error": "not_found"}

    token = set_current_tenant(device.tenant)
    try:
        result = DeviceService(actor=None).probe(device)
    finally:
        reset_current_tenant(token)

    logger.info("Sonde %s : ok=%s latence=%sms", device_id, result.is_ok, result.latency_ms)
    return {
        "device_id": device_id,
        "is_ok": result.is_ok,
        "status": Device.objects.all_objects.get(pk=device_id).status,
        "latency_ms": result.latency_ms,
        "error": result.error,
    }


@shared_task(name="network.probe_tenant_devices")
def probe_tenant_devices(tenant_id: str) -> dict[str, object]:
    """Sonde tous les routeurs actifs d'un tenant (planification horaire).

    Args:
        tenant_id: Identifiant UUID du tenant.

    Returns:
        Un résumé ``{"queued": nombre_de_sondes}``.

    Raises:
        LookupError: Si le tenant n'existe pas.
    """
    from apps.tenants.models import Tenant

    tenant = Tenant.objects.filter(pk=tenant_id).first()
    if tenant is None:
        raise LookupError(f"Tenant introuvable : {tenant_id}")

    device_ids = list(
        Device.all_objects.filter(tenant=tenant)
        .exclude(status="disabled")
        .values_list("id", flat=True)
    )
    for device_id in device_ids:
        probe_device.delay(str(device_id))

    return {"queued": len(device_ids)}
