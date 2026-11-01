"""Génération des codes de voucher et conversions RouterOS.

Un code doit être **lisible à voix haute** au comptoir : l'alphabet exclut les
caractères confondables (``0/O``, ``1/I/L``, ``5/S``, ``2/Z``).
"""
from __future__ import annotations

import secrets

#: Alphabet sans ambiguïté visuelle ni phonétique (28 caractères).
ALPHABET = "ACDEFGHJKMNPQRTUVWXY34679"

#: Longueur par défaut d'un code.
DEFAULT_LENGTH = 8


def generate_code(length: int = DEFAULT_LENGTH, *, prefix: str = "") -> str:
    """Génère un code aléatoire cryptographiquement sûr.

    Args:
        length: Nombre de caractères du code (hors préfixe).
        prefix: Préfixe optionnel, déjà normalisé.

    Returns:
        Un code en majuscules, par exemple ``"CC01-K7QF9M3X"``.

    Example:
        >>> len(generate_code(10))
        10
    """
    body = "".join(secrets.choice(ALPHABET) for _ in range(max(4, length)))
    return f"{prefix}-{body}" if prefix else body


def normalize_prefix(prefix: str) -> str:
    """Normalise un préfixe saisi par l'utilisateur.

    Args:
        prefix: Préfixe brut (``"cc 01"``, ``"CC01"``, ``""``).

    Returns:
        Le préfixe en majuscules, sans espace ni tiret, limité à 6 caractères.

    Example:
        >>> normalize_prefix(" cc 01 ")
        'CC01'
    """
    cleaned = "".join(char for char in (prefix or "").upper() if char.isalnum())
    return cleaned[:6]


def routeros_uptime(minutes: int) -> str:
    """Convertit une durée en notation RouterOS (``limit-uptime``).

    Args:
        minutes: Durée en minutes (``0`` = aucune limite).

    Returns:
        Une durée RouterOS comme ``"45m"``, ``"1h"``, ``"1d12h"`` ou ``""``.

    Example:
        >>> routeros_uptime(90)
        '1h30m'
    """
    if not minutes or minutes <= 0:
        return ""
    days, rest = divmod(int(minutes), 1440)
    hours, mins = divmod(rest, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    return "".join(parts)


def routeros_bytes(megabytes: int) -> int:
    """Convertit un volume en octets pour ``limit-bytes-total``.

    Args:
        megabytes: Volume en mégaoctets (``0`` = illimité).

    Returns:
        Le volume en octets, ou ``0`` si illimité.

    Example:
        >>> routeros_bytes(50)
        52428800
    """
    return max(0, int(megabytes)) * 1024 * 1024
