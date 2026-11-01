"""Isolation multi-tenant : un espace ne voit jamais les données d'un autre."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.constants import ROLE_OWNER
from apps.accounts.models import Membership
from apps.network.models import Device, Site
from apps.tenants.models import Tenant
from core.context import get_current_tenant, reset_current_tenant, set_current_tenant
from core.exceptions import TenantNotSetError

User = get_user_model()


@pytest.fixture
def second_workspace(db):
    """Crée un second espace, son propriétaire, un site et un routeur.

    Args:
        db: Base de test.

    Returns:
        Un tuple ``(tenant, site, device)``.
    """
    owner = User.objects.create_user(email="fatou@fai.bf", password="motdepasse-solide-456")
    tenant = Tenant.objects.create(name="FAI Sahel", slug="fai-sahel")
    token = set_current_tenant(tenant)
    try:
        Membership.objects.create(user=owner, role=ROLE_OWNER)
        site = Site.objects.create(name="Site Sahel", code="FS-01")
        device = Device.objects.create(site=site, name="hAP · sahel")
    finally:
        reset_current_tenant(token)
    return tenant, site, device


def test_manager_requires_tenant_context():
    """Sans tenant dans le contexte, toute lecture métier est refusée."""
    reset_current_tenant(set_current_tenant(None))
    with pytest.raises(TenantNotSetError):
        list(Site.objects.all())


def test_sites_are_scoped_to_current_tenant(tenant_context, site, second_workspace):
    """Le tenant courant ne voit que ses propres sites."""
    visible = list(Site.objects.all())

    assert [item.code for item in visible] == ["CC-01"]


def test_api_does_not_leak_other_tenant_devices(api_client, site, second_workspace):
    """L'API ne renvoie jamais les routeurs d'un autre espace."""
    response = api_client.get("/api/v1/devices/")

    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_api_rejects_unknown_tenant_header(api_client):
    """Un en-tête de tenant non autorisé ne donne accès à rien."""
    api_client.credentials(HTTP_X_TENANT_SLUG="espace-inconnu")

    response = api_client.get("/api/v1/devices/")

    assert response.status_code == 403


def test_device_of_other_tenant_is_not_found(api_client, second_workspace):
    """Un routeur d'un autre espace répond 404, pas 403 (aucune fuite d'existence)."""
    _, _, foreign_device = second_workspace

    response = api_client.post(f"/api/v1/devices/{foreign_device.pk}/test-connection/")

    assert response.status_code == 404
    assert response.json()["code"] == "device_not_found"


def test_context_is_restored_after_request(api_client):
    """Le contexte tenant est nettoyé après chaque requête."""
    response = api_client.get("/api/v1/devices/")

    assert response.status_code == 200
    assert get_current_tenant() is None
