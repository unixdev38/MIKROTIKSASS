"""API des routeurs : parcours complet (enregistrement, enrôlement, sonde)."""
from __future__ import annotations

from apps.network.models import Device


def test_create_device_returns_201_and_pending_status(api_client, site):
    """L'API crée un routeur et renvoie son état initial."""
    response = api_client.post(
        "/api/v1/devices/",
        {
            "site_id": str(site.pk),
            "name": "hAP-ac2 · cyber-centre",
            "management_ip": "10.66.1.14",
            "is_simulated": True,
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["is_enrolled"] is False
    assert Device.all_objects.count() == 1


def test_enroll_returns_one_time_script(api_client, site):
    """L'enrôlement renvoie le script et n'expose aucun autre secret."""
    created = api_client.post(
        "/api/v1/devices/",
        {"site_id": str(site.pk), "name": "hAP", "management_ip": "10.66.1.14", "is_simulated": True},
        format="json",
    ).json()

    response = api_client.post(f"/api/v1/devices/{created['id']}/enroll/", {}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert "/interface wireguard" in body["script"]
    assert "secret" not in body
    assert body["is_renewal"] is False


def test_test_connection_updates_status(api_client, site):
    """La sonde met à jour le statut et la version du routeur."""
    created = api_client.post(
        "/api/v1/devices/",
        {"site_id": str(site.pk), "name": "hAP", "management_ip": "10.66.1.14", "is_simulated": True},
        format="json",
    ).json()
    api_client.post(f"/api/v1/devices/{created['id']}/enroll/", {}, format="json")

    response = api_client.post(f"/api/v1/devices/{created['id']}/test-connection/", {}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["is_ok"] is True
    assert body["status"] == "online"
    assert body["system_info"]["version"] == "7.16.2"


def test_create_device_with_foreign_site_is_not_found(api_client):
    """Un site inexistant (ou d'un autre espace) renvoie 404."""
    response = api_client.post(
        "/api/v1/devices/",
        {"site_id": "00000000-0000-0000-0000-000000000000", "name": "hAP"},
        format="json",
    )

    assert response.status_code == 404
    assert response.json()["code"] == "site_not_found"


def test_retrieve_device_returns_detail(api_client, site):
    """``GET /devices/{id}/`` renvoie le détail (utilisé par la fiche de la console)."""
    created = api_client.post(
        "/api/v1/devices/",
        {"site_id": str(site.pk), "name": "hAP", "management_ip": "192.168.56.101",
         "management_port": 80, "use_tls": False},
        format="json",
    ).json()

    response = api_client.get(f"/api/v1/devices/{created['id']}/")

    assert response.status_code == 200
    body = response.json()
    assert body["management_port"] == 80
    assert body["use_tls"] is False


def test_update_is_not_exposed(api_client, site):
    """Aucune écriture générique : ``PATCH`` renvoie 405, faute de service dédié."""
    created = api_client.post(
        "/api/v1/devices/", {"site_id": str(site.pk), "name": "hAP"}, format="json"
    ).json()

    assert api_client.patch(f"/api/v1/devices/{created['id']}/", {"name": "x"}, format="json").status_code == 405
    assert api_client.delete(f"/api/v1/devices/{created['id']}/").status_code == 405


def test_me_endpoint_exposes_active_workspace(api_client, tenant):
    """``/me`` renvoie l'espace actif et le rôle de l'utilisateur."""
    response = api_client.get("/api/v1/me/")

    assert response.status_code == 200
    body = response.json()
    assert body["tenant"]["slug"] == tenant.slug
    assert body["role"] == "owner"
    assert len(body["tenants"]) == 1
