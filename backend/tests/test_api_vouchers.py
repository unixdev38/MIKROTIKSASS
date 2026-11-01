"""API des forfaits et vouchers : génération, envoi, export, révocation, rôles."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Membership
from apps.hotspot.models import Plan, VoucherState
from apps.network.services import DeviceService
from core.context import reset_current_tenant, set_current_tenant

User = get_user_model()


@pytest.fixture
def plan(tenant_context):
    """Forfait « 24 h » utilisé par les tests d'API.

    Args:
        tenant_context: Contexte tenant actif.

    Returns:
        Le forfait créé.
    """
    return Plan.objects.create(
        name="24 heures", code="D24", duration_minutes=1440, price_fcfa=500, data_cap_mb=500
    )


@pytest.fixture
def ready_device(tenant_context, site, owner):
    """Routeur simulé prêt à recevoir des vouchers.

    Args:
        tenant_context: Contexte tenant actif.
        site: Site du routeur.
        owner: Propriétaire de l'espace.

    Returns:
        Le routeur enrôlé.
    """
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="hAP · api", management_ip="10.66.1.30", is_simulated=True
    )
    service.attach_credentials(device, username="saas-api", password="secret-routeur")
    device.refresh_from_db()
    return device


def create_batch(client: APIClient, site, plan, quantity: int = 5, prefix: str = "CC01") -> dict:
    """Crée un lot via l'API et renvoie la réponse décodée.

    Args:
        client: Client authentifié.
        site: Site de vente.
        plan: Forfait appliqué.
        quantity: Nombre de codes.
        prefix: Préfixe des codes.

    Returns:
        Le lot sérialisé.
    """
    response = client.post(
        "/api/v1/voucher-batches/",
        {"site_id": str(site.pk), "plan_id": str(plan.pk), "quantity": quantity, "prefix": prefix},
        format="json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def test_create_plan(api_client):
    """L'API crée un forfait et le renvoie avec son libellé de durée."""
    response = api_client.post(
        "/api/v1/plans/",
        {"name": "1 heure", "code": "H1", "duration_minutes": 60, "price_fcfa": 200},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["duration_label"] == "1 h"
    assert body["price_fcfa"] == 200


def test_generate_batch_through_api(api_client, site, plan):
    """La génération renvoie le lot avec ses compteurs (total = quantité)."""
    body = create_batch(api_client, site, plan, quantity=8)

    assert body["quantity"] == 8
    assert body["counts"]["total"] == 8
    assert body["counts"]["unused"] == 8
    assert body["plan"]["code"] == "D24"


def test_provision_and_list_vouchers(api_client, site, plan, ready_device):
    """L'envoi au routeur marque les codes et la liste les expose."""
    batch = create_batch(api_client, site, plan, quantity=6)

    response = api_client.post(f"/api/v1/voucher-batches/{batch['id']}/provision/")

    assert response.status_code == 200
    report = response.json()
    assert report["pushed"] == 6
    assert report["failed"] == 0
    assert report["device_id"] == str(ready_device.pk)

    vouchers = api_client.get(f"/api/v1/vouchers/?batch={batch['id']}").json()
    assert vouchers["count"] == 6
    assert {item["state"] for item in vouchers["results"]} == {VoucherState.PROVISIONED}


def test_sync_marks_codes_as_used(api_client, site, plan, ready_device):
    """Après synchronisation, les codes vus sur le routeur passent en « utilisé »."""
    batch = create_batch(api_client, site, plan, quantity=3)
    api_client.post(f"/api/v1/voucher-batches/{batch['id']}/provision/")

    response = api_client.post(f"/api/v1/voucher-batches/{batch['id']}/sync/")

    assert response.status_code == 200
    body = response.json()
    assert body["checked"] == 3
    assert body["activated"] == 3


def test_export_returns_csv(api_client, site, plan):
    """L'export produit un fichier CSV téléchargeable."""
    batch = create_batch(api_client, site, plan, quantity=4)

    response = api_client.get(f"/api/v1/voucher-batches/{batch['id']}/export/")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response["Content-Disposition"]
    lines = response.content.decode("utf-8").strip().splitlines()
    assert len(lines) == 5


def test_revoke_through_api(api_client, site, plan, ready_device):
    """La révocation passe le code en « révoqué »."""
    batch = create_batch(api_client, site, plan, quantity=2)
    api_client.post(f"/api/v1/voucher-batches/{batch['id']}/provision/")
    voucher = api_client.get(f"/api/v1/vouchers/?batch={batch['id']}").json()["results"][0]

    response = api_client.post(f"/api/v1/vouchers/{voucher['id']}/revoke/")

    assert response.status_code == 200
    assert response.json()["state"] == VoucherState.REVOKED


def test_viewer_cannot_create_plan(tenant_context, tenant, site):
    """Un rôle « viewer » ne peut pas créer de forfait (403)."""
    user = User.objects.create_user(email="lecteur@kora.bf", password="motdepasse-solide-789")
    token = set_current_tenant(tenant)
    try:
        Membership.objects.create(user=user, role="viewer")
    finally:
        reset_current_tenant(token)

    client = APIClient()
    client.force_login(user)
    client.credentials(HTTP_X_TENANT_SLUG=tenant.slug)

    response = client.post(
        "/api/v1/plans/",
        {"name": "Test", "code": "T1", "duration_minutes": 30},
        format="json",
    )

    assert response.status_code == 403


def test_batches_are_isolated_between_tenants(api_client, second_workspace):
    """Un lot d'un autre espace est introuvable (404), jamais visible."""
    _, foreign_site, _ = second_workspace
    token = set_current_tenant(foreign_site.tenant)
    try:
        foreign_plan = Plan.objects.create(name="Autre", code="X1", duration_minutes=30)
    finally:
        reset_current_tenant(token)

    response = api_client.post(
        "/api/v1/voucher-batches/",
        {"site_id": str(foreign_site.pk), "plan_id": str(foreign_plan.pk), "quantity": 2},
        format="json",
    )

    assert response.status_code == 404
    assert response.json()["code"] == "site_not_found"
