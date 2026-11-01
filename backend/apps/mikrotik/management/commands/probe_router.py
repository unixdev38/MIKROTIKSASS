"""Test de connexion à un routeur réel (VM VirtualBox, CHR, matériel).

    python manage.py probe_router --host 192.168.56.101 --username admin --password '•••'
    python manage.py probe_router --host 192.168.56.101 --username admin --password '•••' --http --port 80
    python manage.py probe_router --host 10.66.1.14 --username saas-api --password '•••' \
        --tenant demo-kora --device 0f0a…  # enregistre les identifiants sur un routeur

Aucune donnée n'est écrite sauf si ``--device`` et ``--tenant`` sont fournis.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.mikrotik.backends.rest import RestBackend
from apps.network.models import Device
from apps.network.services import DeviceService
from apps.tenants.models import Tenant
from core.context import reset_current_tenant, set_current_tenant


class Command(BaseCommand):
    """Sonde un routeur RouterOS via son API REST et affiche un rapport lisible."""

    help = "Teste la connexion REST à un routeur (routeur x86 VirtualBox, CHR, matériel)."

    def add_arguments(self, parser) -> None:
        """Déclare les options de la commande.

        Args:
            parser: Analyseur d'arguments de Django.
        """
        parser.add_argument("--host", required=True, help="IP du routeur (ex. 192.168.56.101).")
        parser.add_argument("--username", required=True, help="Utilisateur RouterOS (ex. admin).")
        parser.add_argument("--password", required=True, help="Mot de passe de cet utilisateur.")
        parser.add_argument("--port", type=int, default=None, help="Port du service (443 ou 80).")
        parser.add_argument("--http", action="store_true", help="Utilise HTTP au lieu de HTTPS.")
        parser.add_argument("--interfaces", action="store_true", help="Affiche aussi les interfaces.")
        parser.add_argument("--device", help="UUID d'un routeur à configurer avec ces identifiants.")
        parser.add_argument("--tenant", help="Slug de l'espace du routeur (requis avec --device).")

    def handle(self, *args: object, **options: object) -> None:
        """Exécute la sonde et affiche le résultat.

        Args:
            *args: Arguments positionnels (non utilisés).
            **options: Options de la commande.

        Raises:
            CommandError: Si les identifiants sont refusés ou le routeur injoignable.
        """
        host = str(options["host"])
        port = options["port"] or (443 if not options["http"] else 80)
        backend = RestBackend(
            host=host,
            username=str(options["username"]),
            secret=str(options["password"]),
            port=int(port),
            use_tls=not bool(options["http"]),
        )
        self.stdout.write(f"→ {backend.base_url}/rest/system/resource")

        result = backend.probe(with_interfaces=bool(options["interfaces"]))
        if not result.is_ok:
            raise CommandError(f"Échec : {result.error}")

        info = result.system_info
        self.stdout.write(self.style.SUCCESS(f"✔ {info.identity} — RouterOS {info.version} ({info.model})"))
        self.stdout.write(
            f"  série {info.serial} · uptime {info.uptime_seconds}s · CPU {info.cpu_load_percent}% "
            f"· mémoire {info.memory_used_percent}% · {result.latency_ms} ms"
        )
        for interface in result.interfaces:
            state = "up" if interface.is_running else "down"
            self.stdout.write(f"  · {interface.name} ({interface.kind}) {state}")

        if options["device"]:
            self._attach_and_probe(str(options["device"]), str(options["tenant"] or ""), host,
                                   int(port), not bool(options["http"]), str(options["username"]),
                                   str(options["password"]))

    def _attach_and_probe(
        self, device_id: str, tenant_slug: str, host: str, port: int,
        use_tls: bool, username: str, password: str,
    ) -> None:
        """Enregistre les identifiants sur un routeur puis le sonde via le service.

        Args:
            device_id: UUID du routeur.
            tenant_slug: Slug de l'espace de travail.
            host: IP du routeur.
            port: Port du service REST.
            use_tls: Utilise HTTPS.
            username: Utilisateur RouterOS.
            password: Mot de passe.

        Raises:
            CommandError: Si le tenant ou le routeur est introuvable.
        """
        if not tenant_slug:
            raise CommandError("--tenant est obligatoire avec --device.")

        tenant = Tenant.all_objects.filter(slug=tenant_slug).first()
        if tenant is None:
            raise CommandError(f"Espace inconnu : {tenant_slug}.")
        device = Device.all_objects.filter(pk=device_id, tenant=tenant).first()
        if device is None:
            raise CommandError(f"Routeur inconnu dans cet espace : {device_id}.")

        token = set_current_tenant(tenant)
        try:
            device.management_ip = host
            device.save(update_fields=["management_ip", "updated_at"])
            DeviceService(actor_role="owner").attach_credentials(
                device, username=username, password=password, port=port,
                use_tls=use_tls, transport="rest",
            )
            result = DeviceService(actor_role="owner").probe(device)
        finally:
            reset_current_tenant(token)

        state = "en ligne" if result.is_ok else f"hors ligne ({result.error})"
        self.stdout.write(self.style.SUCCESS(f"✔ identifiants enregistrés — routeur {state}"))
