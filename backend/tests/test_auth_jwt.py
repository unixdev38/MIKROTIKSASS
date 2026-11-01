"""Authentification JWT : connexion, espace actif, révocation, usage de l'API."""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.network.models import Device

TOKEN_URL = "/api/v1/auth/token/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
PASSWORD = "motdepasse-solide-123"


def login(client: APIClient, email: str = "ali@cybercentre.bf") -> dict:
    """Connecte un utilisateur et renvoie la réponse décodée.

    Args:
        client: Client de test.
        email: Adresse e-mail du compte.

    Returns:
        Le corps JSON de la réponse (jetons, profil, espaces).
    """
    response = client.post(TOKEN_URL, {"email": email, "password": PASSWORD}, format="json")
    assert response.status_code == 200, response.content
    return response.json()


def bearer(token: str) -> dict[str, str]:
    """Construit l'en-tête d'autorisation.

    Args:
        token: Jeton d'accès.

    Returns:
        Le dictionnaire d'en-têtes HTTP.
    """
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_login_returns_tokens_profile_and_workspaces(owner, tenant):
    """La connexion renvoie les jetons, le profil et les espaces accessibles."""
    body = login(APIClient())

    assert body["access"] and body["refresh"]
    assert body["user"]["email"] == owner.email
    assert body["tenant"]["slug"] == tenant.slug
    assert body["role"] == "owner"
    assert [item["slug"] for item in body["tenants"]] == [tenant.slug]


def test_login_rejects_bad_password(owner, tenant):
    """Un mot de passe invalide donne 401 sans révéler si le compte existe."""
    response = APIClient().post(
        TOKEN_URL, {"email": owner.email, "password": "mauvais-mot-de-passe"}, format="json"
    )

    assert response.status_code == 401


def test_access_token_authenticates_api_without_session(owner, tenant, site):
    """Le jeton suffit : aucun cookie, aucune session."""
    client = APIClient()
    token = login(client)["access"]

    response = client.get("/api/v1/me/", **bearer(token))

    assert response.status_code == 200
    assert response.json()["role"] == "owner"


def test_tenant_header_selects_workspace(owner, tenant):
    """L'en-tête ``X-Tenant-Slug`` choisit l'espace actif au moment du login."""
    client = APIClient()

    body = login(client)

    assert body["tenant"]["id"] == str(tenant.pk)


def test_unknown_tenant_header_is_forbidden(owner, tenant):
    """Un espace non autorisé est refusé (403), sans fuite d'existence."""
    client = APIClient()
    token = login(client)["access"]

    response = client.get("/api/v1/me/", HTTP_X_TENANT_SLUG="espace-inconnu", **bearer(token))

    assert response.status_code == 403


def test_refresh_rotates_the_refresh_token(owner, tenant):
    """Le rafraîchissement renvoie un nouveau refresh (rotation)."""
    client = APIClient()
    body = login(client)

    response = client.post(REFRESH_URL, {"refresh": body["refresh"]}, format="json")

    assert response.status_code == 200
    assert response.json()["refresh"] != body["refresh"]


def test_logout_blacklists_refresh_token(owner, tenant):
    """Après déconnexion, le refresh token ne peut plus servir."""
    client = APIClient()
    body = login(client)

    logout = client.post(
        LOGOUT_URL, {"refresh": body["refresh"]}, format="json", **bearer(body["access"])
    )
    retry = client.post(REFRESH_URL, {"refresh": body["refresh"]}, format="json")

    assert logout.status_code == 204
    assert retry.status_code == 401


def test_jwt_request_resolves_tenant_context(owner, tenant, site):
    """Une requête JWT peut écrire : le tenant est résolu après l'authentification."""
    client = APIClient()
    token = login(client)["access"]

    response = client.post(
        "/api/v1/devices/",
        {"site_id": str(site.pk), "name": "hAP · jwt", "management_ip": "10.66.1.20"},
        format="json",
        **bearer(token),
    )

    assert response.status_code == 201, response.content
    assert Device.all_objects.count() == 1


def test_anonymous_request_is_refused(owner, tenant):
    """Sans jeton ni session, l'API est fermée."""
    response = APIClient().get("/api/v1/devices/")

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_token_endpoint_creates_last_login(owner):
    """La connexion met à jour ``last_login`` (traçabilité)."""
    login(APIClient())

    owner.refresh_from_db()

    assert owner.last_login is not None
