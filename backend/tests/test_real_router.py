"""Routeur réel : identifiants manuels, port/TLS, et test optionnel en direct.

Le test marqué ``live`` ne s'exécute que si les variables d'environnement décrivent un
routeur joignable (par exemple le CHR x86 sous VirtualBox) :

    MIKROTIK_LIVE_HOST=192.168.56.101 MIKROTIK_LIVE_USER=admin \
    MIKROTIK_LIVE_PASSWORD=••• MIKROTIK_LIVE_HTTP=1 pytest -m live
"""
from __future__ import annotations

import os

import pytest

from apps.mikrotik.backends.rest import RestBackend
from apps.mikrotik.gateway import build_backend
from apps.network.models import DeviceCredential
from apps.network.services import DeviceService
from core.crypto import SecretCipher


def test_rest_backend_builds_url_for_https_and_http():
    """L'URL suit les réglages TLS et de port du routeur."""
    https = RestBackend(host="192.168.56.101", username="admin", secret="x", port=443)
    http = RestBackend(host="192.168.56.101", username="admin", secret="x", port=80, use_tls=False)

    assert https.base_url == "https://192.168.56.101:443"
    assert http.base_url == "http://192.168.56.101:80"


def test_rest_backend_uses_default_ports_when_absent():
    """Sans port explicite, 443 (TLS) ou 80 (HTTP) sont utilisés."""
    assert RestBackend(host="h", username="u", secret="s").base_url == "https://h:443"
    assert RestBackend(host="h", username="u", secret="s", use_tls=False).base_url == "http://h:80"


def test_attach_credentials_stores_secrets_encrypted(tenant_context, site, owner):
    """Les identifiants réels sont chiffrés et le routeur devient non simulé."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="CHR x86 · virtualbox", management_ip="192.168.56.101",
        is_simulated=True, management_port=80, use_tls=False,
    )

    updated = service.attach_credentials(
        device, username="admin", password="mot-de-passe-routeur",
        port=80, use_tls=False, simulated=False,
    )

    credential = DeviceCredential.all_objects.get(device=device)
    stored = SecretCipher.from_settings().decrypt(bytes(credential.secret_encrypted))
    assert stored == "mot-de-passe-routeur"
    assert bytes(credential.secret_encrypted) != b"mot-de-passe-routeur"
    assert credential.api_username == "admin"
    assert updated.is_simulated is False  # demandé explicitement
    assert updated.management_port == 80
    assert updated.use_tls is False


def test_attach_credentials_requires_ip(tenant_context, site, owner):
    """Sans adresse IP, la connexion réelle est refusée avec un message clair."""
    from core.exceptions import DomainValidationError

    service = DeviceService(owner, actor_role="owner")
    device = service.register(site=site, name="Routeur sans IP")

    with pytest.raises(DomainValidationError) as error:
        service.attach_credentials(device, username="admin", password="x")

    assert error.value.code == "device_management_ip_required"


def test_gateway_forwards_port_and_tls(tenant_context, site, owner):
    """Le backend construit pour un routeur réel reprend son port et son schéma."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="CHR", management_ip="192.168.56.101", management_port=80, use_tls=False
    )
    service.attach_credentials(device, username="admin", password="secret-routeur", port=80, use_tls=False)
    device.refresh_from_db()

    backend = build_backend(device)

    assert isinstance(backend, RestBackend)
    assert backend.base_url == "http://192.168.56.101:80"


def test_simulated_device_uses_fake_backend(tenant_context, site, owner):
    """Un routeur simulé ne fait aucun appel réseau, même avec des identifiants."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="Simulé", management_ip="10.66.1.99", is_simulated=True
    )
    service.issue_enrollment(device)
    device.refresh_from_db()

    assert build_backend(device).base_url == "fake://10.66.1.99"


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("MIKROTIK_LIVE_HOST"), reason="aucun routeur réel configuré"
)
def test_live_router_answers_over_rest():
    """Sonde un vrai routeur RouterOS 7 (CHR x86, hAP, RB…)."""
    backend = RestBackend(
        host=os.environ["MIKROTIK_LIVE_HOST"],
        username=os.environ.get("MIKROTIK_LIVE_USER", "admin"),
        secret=os.environ.get("MIKROTIK_LIVE_PASSWORD", ""),
        port=int(os.environ.get("MIKROTIK_LIVE_PORT", "0")) or None,
        use_tls=not bool(os.environ.get("MIKROTIK_LIVE_HTTP")),
    )

    result = backend.probe()

    assert result.is_ok, result.error
    assert result.system_info.version.startswith("7."), result.system_info.version
