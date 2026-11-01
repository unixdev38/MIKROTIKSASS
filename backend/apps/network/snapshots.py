"""Transformation d'un résultat de sonde en état persistable.

Fonction pure, sans base de données : elle facilite les tests et garde les services
sous la limite de 300 lignes (voir docs/14-conventions-de-code.md §3).
"""
from __future__ import annotations

from dataclasses import asdict

from apps.mikrotik.schemas import ProbeResult
from apps.network.models import DeviceStatus
from apps.network.schemas import DeviceSnapshot


def build_snapshot(result: ProbeResult) -> DeviceSnapshot:
    """Transforme un résultat de sonde en état persistable.

    Args:
        result: Résultat renvoyé par un backend MikroTik.

    Returns:
        Un ``DeviceSnapshot`` prêt à être appliqué au routeur.

    Example:
        >>> build_snapshot(ProbeResult(is_ok=False, error="timeout")).status
        'unreachable'
    """
    if not result.is_ok or result.system_info is None:
        return DeviceSnapshot(
            status=DeviceStatus.UNREACHABLE,
            health={"error": result.error},
            is_reachable=False,
            latency_ms=result.latency_ms,
            error=result.error,
        )

    info = result.system_info
    health: dict[str, object] = {
        "identity": info.identity,
        "version": info.version,
        "model": info.model,
        "serial": info.serial,
        "uptime_seconds": info.uptime_seconds,
        "cpu_load_percent": info.cpu_load_percent,
        "memory_used_percent": info.memory_used_percent,
        "board_temperature_c": info.board_temperature_c,
        "latency_ms": result.latency_ms,
        "interfaces": [asdict(iface) for iface in result.interfaces],
        "checked_at": result.checked_at.isoformat() if result.checked_at else None,
    }
    return DeviceSnapshot(
        status=DeviceStatus.ONLINE,
        health=health,
        ros_version=info.version,
        serial=info.serial,
        model_name=info.model,
        is_reachable=True,
        latency_ms=result.latency_ms,
    )
