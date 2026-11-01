"""Enrôlement d'un routeur : génération des secrets et du script RouterOS.

Service dédié (séparé de ``DeviceService``) car il porte la responsabilité la plus
sensible du produit : produire des identifiants de management à usage unique.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.network.models import Device, DeviceCredential
from apps.network.schemas import EnrollmentBundle
from apps.network.scripts import EnrollmentScriptContext, render_enrollment_script
from core.crypto import SecretCipher, generate_wireguard_keypair
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User

ENROLLMENT_TTL_HOURS = 24
SECRET_BYTES = 24


class EnrollmentService(BaseService[EnrollmentBundle]):
    """Génère (ou renouvelle) les identifiants de management d'un routeur.

    Args:
        actor: Utilisateur à l'origine de l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def issue(self, device: Device, *, force: bool = False) -> EnrollmentBundle:
        """Produit un script d'enrôlement à usage unique.

        Les secrets sont chiffrés avant persistance et ne sont réaffichables que par
        une rotation : le script est la seule occasion de les lire.

        Args:
            device: Routeur à enrôler.
            force: Autorise la rotation si des identifiants existent déjà.

        Returns:
            Le script, l'adresse de management et l'échéance.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si l'adresse de management est absente.
            ConflictError: Si le routeur est déjà enrôlé et ``force`` est faux.
        """
        self.assert_role(self.actor_role, "technician")

        if not device.management_ip:
            raise DomainValidationError(
                "Renseignez d'abord l'adresse de management du routeur.",
                code="device_management_ip_required",
            )

        credential = getattr(device, "credential", None)
        is_renewal = credential is not None
        if is_renewal and not force:
            raise ConflictError(
                "Ce routeur est déjà enrôlé : utilisez une rotation pour régénérer son script.",
                code="device_already_enrolled",
            )

        secrets_bundle = self._rotate_credentials(device, credential)
        expires_at = timezone.now() + timedelta(hours=ENROLLMENT_TTL_HOURS)
        device.enrollment_expires_at = expires_at
        device.save(update_fields=["enrollment_expires_at", "updated_at"])

        context = self._script_context(device, secrets_bundle)
        return EnrollmentBundle(
            device_id=str(device.pk),
            script=render_enrollment_script(context),
            management_ip=str(device.management_ip),
            api_username=secrets_bundle["api_username"],
            expires_at=expires_at,
            is_renewal=is_renewal,
        )

    def _rotate_credentials(
        self, device: Device, credential: DeviceCredential | None
    ) -> dict[str, str]:
        """Crée ou renouvelle les secrets chiffrés du routeur.

        Args:
            device: Routeur concerné.
            credential: Identifiants existants, ou ``None`` pour une première génération.

        Returns:
            Les secrets **en clair**, uniquement pour le rendu du script.
        """
        cipher = SecretCipher.from_settings()
        api_username = "saas-api"
        api_secret = secrets.token_urlsafe(SECRET_BYTES)
        heartbeat_token = secrets.token_urlsafe(SECRET_BYTES)
        wireguard_private, wireguard_public = generate_wireguard_keypair()

        with transaction.atomic():
            record = credential or DeviceCredential(device=device)
            record.api_username = api_username
            record.secret_encrypted = cipher.encrypt(api_secret)
            record.key_version = settings.SECRET_KEY_VERSION
            record.wireguard_private_key_encrypted = cipher.encrypt(wireguard_private)
            record.wireguard_public_key = wireguard_public
            record.heartbeat_token_encrypted = cipher.encrypt(heartbeat_token)
            record.rotated_at = timezone.now()
            record.save()

        return {
            "api_username": api_username,
            "api_secret": api_secret,
            "heartbeat_token": heartbeat_token,
            "wireguard_private": wireguard_private,
        }

    @staticmethod
    def _script_context(device: Device, secrets_bundle: dict[str, str]) -> EnrollmentScriptContext:
        """Assemble les valeurs injectées dans le gabarit RouterOS.

        Args:
            device: Routeur cible.
            secrets_bundle: Secrets générés par :meth:`_rotate_credentials`.

        Returns:
            Le contexte prêt pour :func:`render_enrollment_script`.
        """
        network = settings.MIKROTIK_MANAGEMENT_NETWORK
        return EnrollmentScriptContext(
            identity=f"{device.site.code.lower()}-{device.pk.hex[:6]}",
            device_name=device.name,
            site_name=device.site.name,
            management_ip=str(device.management_ip),
            management_network=network,
            management_prefix=int(network.split("/")[-1]),
            wireguard_private_key=secrets_bundle["wireguard_private"],
            wireguard_peer_public_key=getattr(settings, "MIKROTIK_WIREGUARD_PUBLIC_KEY", ""),
            wireguard_endpoint=settings.MIKROTIK_WIREGUARD_ENDPOINT,
            wireguard_port=51820,
            api_username=secrets_bundle["api_username"],
            api_secret=secrets_bundle["api_secret"],
            heartbeat_url=f"/hooks/device/{device.pk}/heartbeat",
            heartbeat_token=secrets_bundle["heartbeat_token"],
            brand="Kora",
        )
