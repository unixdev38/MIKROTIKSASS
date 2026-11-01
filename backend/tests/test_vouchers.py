"""Vouchers : génération des codes, envoi au routeur, quotas et export."""
from __future__ import annotations

import pytest

from apps.hotspot.codes import (
    ALPHABET,
    generate_code,
    normalize_prefix,
    routeros_bytes,
    routeros_uptime,
)
from apps.hotspot.models import Plan, Voucher, VoucherState
from apps.hotspot.provisioning import VoucherProvisioner
from apps.hotspot.services import PlanService, VoucherService
from apps.mikrotik.backends.fake import FakeBackend
from apps.network.services import DeviceService
from core.exceptions import ConflictError, DomainValidationError, PermissionDeniedError

QUANTITY = 12


@pytest.fixture
def plan(tenant_context):
    """Forfait d'une heure, 50 Mo.

    Args:
        tenant_context: Contexte tenant actif.

    Returns:
        Le forfait créé.
    """
    return Plan.objects.create(
        name="1 heure", code="H1", duration_minutes=60, data_cap_mb=50,
        price_fcfa=200, rate_limit="2M/2M",
    )


@pytest.fixture
def simulated_device(tenant_context, site, owner):
    """Routeur simulé enrôlé sur le site de test.

    Args:
        tenant_context: Contexte tenant actif.
        site: Site du routeur.
        owner: Propriétaire de l'espace.

    Returns:
        Le routeur, prêt à recevoir des vouchers.
    """
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="hAP · cyber-centre", management_ip="10.66.1.14", is_simulated=True
    )
    service.attach_credentials(device, username="saas-api", password="secret-routeur")
    device.refresh_from_db()
    return device


@pytest.fixture
def batch(tenant_context, plan, site, owner):
    """Lot de vouchers prêt à être poussé.

    Args:
        tenant_context: Contexte tenant actif.
        plan: Forfait appliqué.
        site: Site de vente.
        owner: Propriétaire de l'espace.

    Returns:
        Le lot généré.
    """
    return VoucherService(owner, actor_role="owner").generate(
        site=site, plan=plan, quantity=QUANTITY, prefix="CC01", note="test"
    )


# --------------------------------------------------------------------- codes
def test_code_alphabet_has_no_ambiguous_characters():
    """Aucun caractère confondable dans les codes (0/O, 1/I/L, 5/S, 2/Z)."""
    assert not set("01OILS25Z") & set(ALPHABET)
    code = generate_code(10)
    assert len(code) == 10
    assert set(code) <= set(ALPHABET)


def test_prefix_and_durations_conversion():
    """Le préfixe est normalisé et les durées converties en notation RouterOS."""
    assert normalize_prefix(" cc 01 ") == "CC01"
    assert routeros_uptime(60) == "1h"
    assert routeros_uptime(90) == "1h30m"
    assert routeros_uptime(1) == "1m"
    assert routeros_uptime(0) == ""
    assert routeros_bytes(50) == 52_428_800


# ------------------------------------------------------------------ génération
def test_generate_creates_unique_unused_codes(batch):
    """Un lot contient autant de codes uniques que demandé, tous inutilisés."""
    vouchers = list(batch.vouchers.all())

    assert len(vouchers) == QUANTITY
    assert len({voucher.code for voucher in vouchers}) == QUANTITY
    assert all(voucher.code.startswith("CC01-") for voucher in vouchers)
    assert {voucher.state for voucher in vouchers} == {VoucherState.UNUSED}
    assert batch.quantity == QUANTITY


def test_generate_is_not_slow_for_five_hundred(tenant_context, plan, site, owner):
    """Un lot de 500 codes (plafond produit) se génère sans collision."""
    batch = VoucherService(owner, actor_role="owner").generate(
        site=site, plan=plan, quantity=500
    )

    assert batch.vouchers.count() == 500


def test_generate_rejects_invalid_quantity(tenant_context, plan, site, owner):
    """Une quantité hors bornes est refusée par le service."""
    service = VoucherService(owner, actor_role="owner")

    with pytest.raises(DomainValidationError) as error:
        service.generate(site=site, plan=plan, quantity=501)

    assert error.value.code == "batch_quantity_invalid"


def test_generate_requires_technician(tenant_context, plan, site, owner):
    """Un rôle insuffisant ne peut pas générer de codes."""
    with pytest.raises(PermissionDeniedError):
        VoucherService(owner, actor_role="viewer").generate(site=site, plan=plan, quantity=5)


def test_plan_codes_are_unique_per_tenant(tenant_context, plan, owner):
    """Deux forfaits ne peuvent pas partager le même code."""
    with pytest.raises(ConflictError):
        PlanService(owner, actor_role="owner").create(name="Autre", code="H1", duration_minutes=30)


def test_inactive_plan_cannot_produce_vouchers(tenant_context, plan, site, owner):
    """Un forfait retiré de la vente est refusé."""
    plan.is_active = False
    plan.save(update_fields=["is_active"])

    with pytest.raises(DomainValidationError) as error:
        VoucherService(owner, actor_role="owner").generate(site=site, plan=plan, quantity=2)

    assert error.value.code == "plan_inactive"


# ---------------------------------------------------------------- provisioning
def test_push_creates_hotspot_users(batch, simulated_device, owner):
    """L'envoi crée un utilisateur hotspot par code et passe les vouchers en « provisionné »."""
    report = VoucherProvisioner(owner, actor_role="owner").push(batch)

    remote = FakeBackend(host="10.66.1.14").fetch_hotspot_users()
    assert report.pushed == QUANTITY
    assert report.failed == 0
    assert len(remote) == QUANTITY
    assert {voucher.state for voucher in batch.vouchers.all()} == {VoucherState.PROVISIONED}


def test_push_is_idempotent(batch, simulated_device, owner):
    """Rejouer l'envoi met à jour les utilisateurs sans créer de doublon."""
    provisioner = VoucherProvisioner(owner, actor_role="owner")
    provisioner.push(batch)
    provisioner.push(batch)

    assert len(FakeBackend(host="10.66.1.14").fetch_hotspot_users()) == QUANTITY


def test_push_without_device_is_explicit(tenant_context, plan, site, owner):
    """Un site sans routeur donne un message actionnable, pas une erreur technique."""
    batch = VoucherService(owner, actor_role="owner").generate(site=site, plan=plan, quantity=3)

    with pytest.raises(DomainValidationError) as error:
        VoucherProvisioner(owner, actor_role="owner").push(batch)

    assert error.value.code == "site_without_device"


# ----------------------------------------------------------------------- quota
def test_sync_records_usage_and_activates(batch, simulated_device, owner):
    """La synchronisation remonte le volume consommé et active les codes vus."""
    provisioner = VoucherProvisioner(owner, actor_role="owner")
    provisioner.push(batch)

    report = provisioner.sync(batch)

    voucher = batch.vouchers.first()
    voucher.refresh_from_db()
    assert report.checked == QUANTITY
    assert report.activated == QUANTITY
    assert voucher.state == VoucherState.ACTIVE
    assert voucher.used_bytes > 0
    assert voucher.expires_at is not None


def test_sync_cuts_codes_beyond_data_cap(tenant_context, plan, site, owner, simulated_device):
    """Un code au-delà de son volume passe en « quota épuisé » (coupure effective sur le routeur)."""
    plan.data_cap_mb = 1  # le backend simulé consomme ~21 Mo
    plan.save(update_fields=["data_cap_mb"])
    batch = VoucherService(owner, actor_role="owner").generate(site=site, plan=plan, quantity=4)
    provisioner = VoucherProvisioner(owner, actor_role="owner")
    provisioner.push(batch)

    report = provisioner.sync(batch)

    assert report.exhausted == 4
    assert {item.state for item in batch.vouchers.all()} == {VoucherState.EXHAUSTED}


def test_revoke_removes_user_from_router(batch, simulated_device, owner):
    """Révoquer un code le supprime du routeur."""
    provisioner = VoucherProvisioner(owner, actor_role="owner")
    provisioner.push(batch)
    voucher = batch.vouchers.first()

    provisioner.revoke(voucher)

    remote = {user.name for user in FakeBackend(host="10.66.1.14").fetch_hotspot_users()}
    voucher.refresh_from_db()
    assert voucher.state == VoucherState.REVOKED
    assert voucher.code not in remote
    assert voucher.is_usable is False


# ----------------------------------------------------------------------- export
def test_export_csv_lists_every_code(batch, owner):
    """L'export contient l'en-tête et une ligne par code."""
    content = VoucherService(owner, actor_role="owner").export_csv(batch)
    lines = content.strip().splitlines()

    assert lines[0].startswith("code,password,forfait,duree")
    assert len(lines) == QUANTITY + 1
    assert any(voucher.code in content for voucher in batch.vouchers.all())


def test_plan_labels_are_human_readable(tenant_context, plan):
    """Les durées des forfaits sont affichées lisiblement."""
    assert plan.duration_label == "1 h"
    plan.duration_minutes = 7 * 1440
    assert plan.duration_label == "7 j"
    plan.duration_minutes = 45
    assert plan.duration_label == "45 min"


def test_vouchers_are_scoped_to_tenant(batch, owner, tenant):
    """Le manager ne renvoie que les vouchers de l'espace courant."""
    assert Voucher.objects.count() == QUANTITY
    assert Plan.objects.count() == 1
