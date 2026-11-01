"""Conversions des valeurs RouterOS (durées, entiers, booléens).

Fonctions pures, sans état ni réseau : elles sont partagées par tous les backends.
"""
from __future__ import annotations


def parse_routeros_uptime(raw: str) -> int:
    """Convertit une durée RouterOS (``1w2d3h4m5s``) en secondes.

    Args:
        raw: Chaîne renvoyée par ``/system/resource``.

    Returns:
        La durée équivalente en secondes (0 si la chaîne est vide).

    Example:
        >>> parse_routeros_uptime("1w2d3h")
        788400
    """
    units = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
    total, number = 0, ""
    for char in raw.strip():
        if char.isdigit():
            number += char
        elif char in units and number:
            total += int(number) * units[char]
            number = ""
    return total


def _as_int(value: object) -> int:
    """Convertit une valeur RouterOS en entier, avec repli à 0.

    Args:
        value: Valeur brute (souvent une chaîne).

    Returns:
        L'entier correspondant, ou 0 si non convertible.
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _as_float_or_none(value: object) -> float | None:
    """Convertit une valeur RouterOS en flottant facultatif.

    Args:
        value: Valeur brute.

    Returns:
        Le flottant, ou ``None`` si la valeur est absente ou invalide.
    """
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _as_bool(value: object) -> bool:
    """Interprète les booléens RouterOS (``true``/``false``/``yes``/``no``).

    Args:
        value: Valeur brute.

    Returns:
        ``True`` si la valeur exprime l'affirmation.
    """
    return str(value).strip().lower() in {"true", "yes", "1"}
