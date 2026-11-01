"""Constantes de rôles et de permissions.

Un rôle est un niveau ; les permissions fines sont déduites du niveau.
Ajouter un rôle = ajouter une entrée ici (+ migration si choix de modèle).
"""
from __future__ import annotations

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_TECHNICIAN = "technician"
ROLE_CASHIER = "cashier"
ROLE_VIEWER = "viewer"

ROLE_CHOICES = (
    (ROLE_OWNER, "Propriétaire"),
    (ROLE_ADMIN, "Administrateur"),
    (ROLE_TECHNICIAN, "Technicien"),
    (ROLE_CASHIER, "Caissier"),
    (ROLE_VIEWER, "Lecture seule"),
)

ROLE_RANK: dict[str, int] = {
    ROLE_VIEWER: 10,
    ROLE_CASHIER: 20,
    ROLE_TECHNICIAN: 30,
    ROLE_ADMIN: 40,
    ROLE_OWNER: 50,
}

ROLE_LABELS: dict[str, str] = dict(ROLE_CHOICES)
