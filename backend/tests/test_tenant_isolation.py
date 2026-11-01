"""Isolation multi-tenant : un espace ne voit jamais les données d'un autre."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.network.models import Site
from core.context import get_current_tenant, reset_current_tenant, set_current_tenant
from core.exceptions import TenantNotSetError

User = get_user_model()


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
