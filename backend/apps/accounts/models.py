"""Utilisateurs (authentification par e-mail) et appartenances aux espaces."""
from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.accounts.constants import ROLE_CHOICES, ROLE_VIEWER
from core.models import TenantScopedModel, TimeStampedModel


class UserManager(BaseUserManager):
    """Gestionnaire d'utilisateurs dont l'identifiant est l'e-mail."""

    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra: object) -> User:
        """Crée un utilisateur standard.

        Args:
            email: Adresse e-mail, normalisée et unique.
            password: Mot de passe en clair (haché par Django).
            **extra: Champs supplémentaires (``full_name``, ``phone``…).

        Returns:
            L'utilisateur créé.

        Raises:
            ValueError: Si l'e-mail est vide.
        """
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra: object) -> User:
        """Crée un superutilisateur (accès plateforme, pas tenant).

        Args:
            email: Adresse e-mail.
            password: Mot de passe en clair.
            **extra: Champs supplémentaires.

        Returns:
            Le superutilisateur créé.
        """
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Compte humain, indépendant des tenants.

    Un même utilisateur peut appartenir à plusieurs espaces (technicien externalisé).

    Attributes:
        email: Identifiant de connexion unique.
        full_name: Nom affiché.
        phone: Numéro de téléphone (format international).
        locale: Langue préférée (``fr`` par défaut).
        is_active: Autorise ou non la connexion.
        is_staff: Accès à l'administration plateforme.
    """

    email = models.EmailField("e-mail", unique=True)
    full_name = models.CharField("nom complet", max_length=160, blank=True)
    phone = models.CharField("téléphone", max_length=32, blank=True)
    locale = models.CharField("langue", max_length=5, default="fr")
    is_active = models.BooleanField("actif", default=True)
    is_staff = models.BooleanField("équipe plateforme", default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            Le nom complet s'il existe, sinon l'e-mail.
        """
        return self.full_name or self.email


class Membership(TenantScopedModel):
    """Rattachement d'un utilisateur à un espace, avec un rôle.

    Attributes:
        user: Utilisateur concerné.
        role: Rôle dans l'espace (voit ``apps.accounts.constants``).
        is_active: Permet de suspendre l'accès sans supprimer l'historique.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField("rôle", max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        verbose_name = "appartenance"
        verbose_name_plural = "appartenances"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="uniq_membership_tenant_user"),
        ]

    def __str__(self) -> str:
        """Représentation lisible.

        Returns:
            ``"ali@example.com — Propriétaire"``.
        """
        return f"{self.user.email} — {self.get_role_display()}"
