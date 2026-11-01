"""Workers Celery des vouchers.

Un worker ne fait que : résoudre le tenant, appeler un service, journaliser. Aucune
règle métier ici (voir docs/14-conventions-de-code.md).
"""
from __future__ import annotations

import logging

from celery import shared_task

from apps.hotspot.models import VoucherBatch
from apps.hotspot.provisioning import VoucherProvisioner
from core.context import reset_current_tenant, set_current_tenant

logger = logging.getLogger(__name__)

#: Rôle accordé aux traitements système (worker), documenté et jamais exposé au client.
SYSTEM_ROLE = "owner"


@shared_task(name="hotspot.push_batch", bind=True, max_retries=3, default_retry_delay=60)
def push_batch(self: object, batch_id: str) -> dict[str, object]:
    """Pousse un lot vers son routeur en arrière-plan.

    Args:
        self: Instance de tâche fournie par Celery (``bind=True``).
        batch_id: Identifiant UUID du lot.

    Returns:
        Le compte rendu sérialisé (``pushed``, ``failed``, ``errors``).

    Raises:
        VoucherBatch.DoesNotExist: Si le lot n'existe plus (tâche obsolète).
    """
    batch = VoucherBatch.all_objects.select_related("tenant", "plan", "site").get(pk=batch_id)
    token = set_current_tenant(batch.tenant)
    try:
        report = VoucherProvisioner(actor_role=SYSTEM_ROLE).push(batch)
    finally:
        reset_current_tenant(token)

    logger.info("Lot %s poussé : %s codes, %s échecs", batch_id, report.pushed, report.failed)
    return {
        "batch_id": report.batch_id,
        "pushed": report.pushed,
        "failed": report.failed,
        "errors": report.errors,
    }


@shared_task(name="hotspot.sync_batch", bind=True)
def sync_batch(self: object, batch_id: str) -> dict[str, object]:
    """Synchronise les compteurs d'un lot en arrière-plan.

    Args:
        self: Instance de tâche fournie par Celery (``bind=True``).
        batch_id: Identifiant UUID du lot.

    Returns:
        Le compte rendu sérialisé (activés, expirés, épuisés).

    Raises:
        VoucherBatch.DoesNotExist: Si le lot n'existe plus (tâche obsolète).
    """
    batch = VoucherBatch.all_objects.select_related("tenant", "plan", "site").get(pk=batch_id)
    token = set_current_tenant(batch.tenant)
    try:
        report = VoucherProvisioner(actor_role=SYSTEM_ROLE).sync(batch)
    finally:
        reset_current_tenant(token)

    logger.info("Lot %s synchronisé : %s codes vus", batch_id, report.checked)
    return {
        "batch_id": report.batch_id,
        "checked": report.checked,
        "activated": report.activated,
        "expired": report.expired,
        "exhausted": report.exhausted,
    }


@shared_task(name="hotspot.sync_site_batches")
def sync_site_batches(site_id: str) -> int:
    """Synchronise tous les lots d'un site (tâche planifiée).

    Args:
        site_id: Identifiant UUID du site.

    Returns:
        Le nombre de lots traités.
    """
    batch_ids = list(
        VoucherBatch.all_objects.filter(site_id=site_id).values_list("pk", flat=True)
    )
    for batch_id in batch_ids:
        sync_batch.delay(str(batch_id))
    return len(batch_ids)
