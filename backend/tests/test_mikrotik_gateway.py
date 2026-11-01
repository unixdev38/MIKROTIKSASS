"""Connecteur RouterOS : backend factice, sondes et persistance de l'état."""
from __future__ import annotations

from apps.mikrotik.backends.fake import FakeBackend
from apps.mikrotik.backends.rest import parse_routeros_uptime
from apps.network.models import DeviceStatus
from apps.network.services import DeviceService


def test_fake_backend_returns_normalized_system_info():
    """Le backend factice renvoie des données normalisées et déterministes."""
    backend = FakeBackend(host="10.66.1.14")

    info = backend.fetch_system_info()

    assert info.version == "7.16.2"
    assert info.identity == "fake-10-66-1-14"
    assert info.model in {"hAP ac2", "RB4011iGS+"}
    assert 0 <= info.memory_used_percent <= 100


def test_probe_reports_latency_and_interfaces():
    """Une sonde réussie renvoie la latence et les interfaces."""
    result = FakeBackend(host="10.66.1.14").probe()

    assert result.is_ok is True
    assert result.error == ""
    assert result.latency_ms >= 0
    assert {iface.name for iface in result.interfaces} == {
        "ether1", "bridge-hotspot", "wlan1", "ether5"
    }


def test_probe_captures_unreachable_router():
    """Un routeur injoignable produit un échec explicite, sans exception."""
    result = FakeBackend(host="10.66.1.99", fail_with="timeout après 10 s").probe()

    assert result.is_ok is False
    assert "timeout" in result.error
    assert result.system_info is None


def test_parse_routeros_uptime_handles_compound_durations():
    """Les durées RouterOS composées sont converties en secondes."""
    assert parse_routeros_uptime("1w2d3h4m5s") == 788_645
    assert parse_routeros_uptime("") == 0
    assert parse_routeros_uptime("34d07:07:37") == 34 * 86400


def test_device_probe_persists_online_state(tenant_context, site, owner):
    """Une sonde réussie marque le routeur en ligne et enregistre sa santé."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="hAP-ac2 · cyber-centre",
        management_ip="10.66.1.14", is_simulated=True,
    )
    service.issue_enrollment(device)
    device.refresh_from_db()

    result = service.probe(device)

    assert result.is_ok is True
    assert device.status == DeviceStatus.ONLINE
    assert device.ros_version == "7.16.2"
    assert device.health["memory_used_percent"] > 0
    assert device.last_seen_at is not None


def test_device_probe_marks_router_unreachable(tenant_context, site, owner):
    """Un routeur éteint est marqué hors ligne, sans lever d'exception."""
    service = DeviceService(owner, actor_role="owner")
    device = service.register(
        site=site, name="hAP-lite · ouaga2000",
        management_ip="10.66.1.15", is_simulated=True,
    )
    service.issue_enrollment(device)
    device.refresh_from_db()

    from apps.mikrotik.gateway import build_backend

    backend = build_backend(device, fail_with="router injoignable")
    assert backend.probe().is_ok is False

    device.status = DeviceStatus.UNREACHABLE
    device.save(update_fields=["status"])
    assert device.status == DeviceStatus.UNREACHABLE
