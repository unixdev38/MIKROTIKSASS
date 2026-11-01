"""Enrôlement : génération des secrets, script RouterOS et rotation."""
from __future__ import annotations

import pytest

from apps.network.models import DeviceCredential
from apps.network.services import DeviceService
from core.crypto import SecretCipher
from core.exceptions import ConflictError, DomainValidationError


def test_register_device_starts_pending(tenant_context, site, owner):
    """Un routeur enregistré sans identifiants est en attente."""
    device = DeviceService(owner, actor_role="owner").register(
        site=site, name="hAP-ac2 · cyber-centre", management_ip="10.66.1.14", is_simulated=True
    )

    assert device.status == "pending"
    assert device.management_ip == "10.66.1.14"


def test_enrollment_requires_management_ip(tenant_context, site, owner):
    """Sans adresse de management, l'enrôlement est refusé avec un message clair."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(site=site, name="Routeur sans IP")

    with pytest.raises(DomainValidationError) as error:
        service.issue_enrollment(device)

    assert error.value.code == "device_management_ip_required"


def test_enrollment_returns_routeros_script(tenant_context, site, owner):
    """Le script contient le tunnel, l'utilisateur API et le heartbeat."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="hAP-ac2 · cyber-centre", management_ip="10.66.1.14", is_simulated=True
    )

    bundle = service.issue_enrollment(device)

    assert bundle.script.startswith("# MIKROTIK SAAS")
    assert "/interface wireguard" in bundle.script
    assert "saas-api" in bundle.script
    assert "saas-heartbeat" in bundle.script
    assert bundle.management_ip == "10.66.1.14"
    assert bundle.is_renewal is False


def test_secrets_are_encrypted_at_rest(tenant_context, site, owner):
    """Le mot de passe n'est jamais stocké en clair."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(site=site, name="hAP", management_ip="10.66.1.16", is_simulated=True)
    bundle = service.issue_enrollment(device)

    credential = DeviceCredential.all_objects.get(device=device)
    plaintext = SecretCipher.from_settings().decrypt(bytes(credential.secret_encrypted))

    assert plaintext in bundle.script
    assert bytes(credential.secret_encrypted) != plaintext.encode()
    assert credential.wireguard_public_key in bundle.script or len(credential.wireguard_public_key) == 44


def test_second_enrollment_requires_force(tenant_context, site, owner):
    """Réenrôler sans rotation est refusé : un seul script actif à la fois."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(site=site, name="hAP", management_ip="10.66.1.17", is_simulated=True)
    service.issue_enrollment(device)
    device.refresh_from_db()

    with pytest.raises(ConflictError) as error:
        service.issue_enrollment(device)

    assert error.value.code == "device_already_enrolled"


def test_rotation_generates_new_secret(tenant_context, site, owner):
    """Une rotation produit un nouveau script et invalide l'ancien."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(site=site, name="hAP", management_ip="10.66.1.18", is_simulated=True)
    first = service.issue_enrollment(device)
    device.refresh_from_db()
    second = service.issue_enrollment(device, force=True)

    assert first.script != second.script
    assert second.is_renewal is True


def test_viewer_cannot_register_device(tenant_context, site, owner):
    """Un rôle insuffisant est refusé par le service, pas par la vue."""
    from core.exceptions import PermissionDeniedError

    with pytest.raises(PermissionDeniedError):
        DeviceService(owner, actor_role="viewer").register(site=site, name="Routeur interdit")
