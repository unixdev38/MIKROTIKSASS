"""Démonstration de bout en bout : espace, routeur, enrôlement, sonde.

    python manage.py demo_smoke

Aucun matériel requis : le routeur est simulé (``MIKROTIK_FAKE_MODE``).
Le script est idempotent : on peut le relancer, il réutilise l'existant.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.network.models import Device
from apps.network.selectors import DeviceSelector, SiteSelector
from apps.network.services import DeviceService, SiteService
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from core.context import reset_current_tenant, set_current_tenant

User = get_user_model()


class Command(BaseCommand):
    """Crée un espace de démonstration et joue le parcours complet."""

    help = "Démonstration : tenant, site, routeur, enrôlement et sonde (routeur simulé)."

    def handle(self, *args: object, **options: object) -> None:
        """Exécute la démonstration.

        Args:
            *args: Arguments positionnels (non utilisés).
            **options: Options de commande (non utilisées).
        """
        self.stdout.write(self.style.MIGRATE_HEADING("1. Espace de travail"))
        user, _ = User.objects.get_or_create(
            email="demo@kora.bf", defaults={"full_name": "Ali Kaboré"}
        )
        user.set_password("demo-mot-de-passe-2026")
        user.save()

        tenant = Tenant.objects.filter(slug="demo-kora").first()
        if tenant is None:
            tenant = TenantService(actor=user).create_workspace(
                name="Démo Kora", slug="demo-kora", owner=user
            )
        self.stdout.write(f"   tenant  : {tenant}")

        token = set_current_tenant(tenant)
        try:
            self.stdout.write(self.style.MIGRATE_HEADING("2. Site et routeur"))
            site = SiteSelector.list()[0] if SiteSelector.list() else SiteService(
                user, actor_role="owner"
            ).register(name="Cyber Centre-ville", code="CC-01", city="Ouagadougou")
            self.stdout.write(f"   site    : {site}")

            device = next(
                (item for item in DeviceSelector.list() if item.is_simulated), None
            ) or DeviceService(user, actor_role="owner").register(
                site=site, name="hAP-ac2 · cyber-centre",
                management_ip="10.66.1.14", is_simulated=True,
            )
            self.stdout.write(f"   routeur : {device} ({device.status})")

            self.stdout.write(self.style.MIGRATE_HEADING("3. Enrôlement"))
            device.refresh_from_db()
            bundle = DeviceService(user, actor_role="owner").issue_enrollment(
                device, force=bool(getattr(device, "credential", None))
            )
            expires = f"{bundle.expires_at:%d/%m %H:%M}"
            self.stdout.write(f"   script  : {len(bundle.script)} caractères, expire le {expires}")
            self.stdout.write(f"   extrait : {bundle.script.splitlines()[0]}")

            self.stdout.write(self.style.MIGRATE_HEADING("4. Sonde"))
            device.refresh_from_db()
            result = DeviceService(user, actor_role="owner").probe(device)
            device = Device.all_objects.get(pk=device.pk)
            self.stdout.write(
                f"   ok={result.is_ok} latence={result.latency_ms} ms statut={device.status} "
                f"version={device.ros_version} cpu={device.health.get('cpu_load_percent')}%"
            )
        finally:
            reset_current_tenant(token)

        self.stdout.write(self.style.SUCCESS("\nDémonstration terminée : le parcours complet fonctionne."))
