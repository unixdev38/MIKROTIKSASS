"""Fixtures partagées : utilisateurs, tenants, contexte et client API."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.constants import ROLE_OWNER
from apps.accounts.models import Membership
from apps.network.models import Site
from apps.tenants.models import Tenant
from core.context import reset_current_tenant, set_current_tenant

User = get_user_model()


@pytest.fixture
def owner(db):
    """Utilisateur propriétaire d'un espace.

    Args:
        db: Active la base de données de test.

    Returns:
        Une instance ``User`` persistée.
    """
    return User.objects.create_user(email="ali@cybercentre.bf", password="motdepasse-solide-123")


@pytest.fixture
def tenant(db, owner):
    """Espace de travail dont ``owner`` est propriétaire.

    Args:
        db: Base de test.
        owner: Utilisateur propriétaire.

    Returns:
        Le tenant créé, avec son appartenance ``owner``.
    """
    created = Tenant.objects.create(name="Cyber Centre", slug="cyber-centre", plan_code="trial")
    token = set_current_tenant(created)
    try:
        Membership.objects.create(user=owner, role=ROLE_OWNER)
    finally:
        reset_current_tenant(token)
    return created


@pytest.fixture
def tenant_context(tenant):
    """Installe le tenant dans le contexte pour la durée du test.

    Args:
        tenant: Espace à activer.

    Yields:
        Le tenant actif, puis restaure le contexte précédent.
    """
    token = set_current_tenant(tenant)
    try:
        yield tenant
    finally:
        reset_current_tenant(token)


@pytest.fixture
def site(tenant_context):
    """Site de test dans l'espace courant.

    Args:
        tenant_context: Contexte tenant actif.

    Returns:
        Le site créé.
    """
    return Site.objects.create(name="Cyber Centre-ville", code="CC-01", city="Ouagadougou")


@pytest.fixture
def api_client(owner, tenant) -> APIClient:
    """Client DRF authentifié sur l'espace de ``owner``.

    Args:
        owner: Utilisateur connecté.
        tenant: Espace transmis via l'en-tête ``X-Tenant-Slug``.

    Returns:
        Un client prêt à appeler l'API.
    """
    client = APIClient()
    client.force_login(owner)
    client.credentials(HTTP_X_TENANT_SLUG=tenant.slug)
    return client
