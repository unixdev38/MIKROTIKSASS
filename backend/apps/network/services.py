"""Services du parc réseau : sites et routeurs.

Chaque méthode est une unité de travail (validations, transaction, résultat typé).
L'enrôlement vit dans ``apps.network.enrollment`` (responsabilité distincte), et la
transformation d'une sonde dans ``apps.network.snapshots``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.mikrotik.schemas import ProbeResult
from apps.mikrotik.services import MikroTikService
from apps.network.enrollment import EnrollmentService
from apps.network.models import Device, DeviceCredential, DeviceStatus, DeviceTransport, Site
from apps.network.schemas import DeviceSnapshot, EnrollmentBundle
from apps.network.site_services import SiteService  # noqa: F401 - réexport public
from apps.network.snapshots import build_snapshot
from core.crypto import SecretCipher
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User


class DeviceService(BaseService[Device]):
    """Cycle de vie des routeurs : enregistrement, enrôlement, supervision.

    Args:
        actor: Utilisateur à l'origine de l'action (``None`` depuis un worker).
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    # ------------------------------------------------------------------ écritures
    def register(
        self,
        *,
        site: Site,
        name: str,
        serial: str = "",
        model_name: str = "",
        management_ip: str | None = None,
        management_port: int = 443,
        use_tls: bool = True,
        transport: str = DeviceTransport.REST,
        is_simulated: bool = False,
    ) -> Device:
        """Enregistre un routeur dans le parc (sans identifiants).

        L'enrôlement est une étape distincte : on peut préparer un inventaire avant
        d'avoir physiquement accès au matériel.

        Args:
            site: Site de rattachement (appartenant au tenant courant).
            name: Libellé interne du routeur.
            serial: Numéro de série, si déjà connu.
            model_name: Modèle matériel.
            management_ip: Adresse prévue dans le tunnel (ou IP d'un routeur de test).
            management_port: Port du service REST (443, 80, 8080…).
            use_tls: ``True`` pour HTTPS, ``False`` pour HTTP.
            transport: ``rest`` ou ``binary``.
            is_simulated: Marque un routeur de démonstration (aucun appel réseau).

        Returns:
            Le routeur créé, au statut ``pending``.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si le nom est vide ou le transport inconnu.
            ConflictError: Si le numéro de série existe déjà dans l'espace.

        Example:
            >>> device = DeviceService(actor=user, actor_role="owner").register(
            ...     site=site, name="hAP-ac2 · cyber-centre", management_ip="10.66.1.14"
            ... )
        """
        self.assert_role(self.actor_role, "technician")

        clean_name = (name or "").strip()
        if not clean_name:
            raise DomainValidationError("Le nom du routeur est obligatoire.", code="device_name_required")
        if not 1 <= int(management_port) <= 65535:
            raise DomainValidationError(
                "Port de management invalide (1 à 65535).", code="device_port_invalid"
            )
        if transport not in DeviceTransport.values:
            raise DomainValidationError(
                f"Transport inconnu : « {transport} ».", code="device_transport_invalid"
            )
        if serial and Device.objects.filter(serial=serial).exists():
            raise ConflictError("Un routeur avec ce numéro de série existe déjà.", code="device_serial_taken")

        return Device.objects.create(
            site=site,
            name=clean_name,
            serial=serial.strip(),
            model_name=model_name.strip(),
            management_ip=management_ip,
            management_port=management_port,
            use_tls=use_tls,
            transport=transport,
            status=DeviceStatus.PENDING,
            is_simulated=is_simulated,
        )

    def issue_enrollment(self, device: Device, *, force: bool = False) -> EnrollmentBundle:
        """Délègue la génération du script d'enrôlement au service dédié.

        Args:
            device: Routeur à enrôler.
            force: Autorise la rotation des identifiants existants.

        Returns:
            Le script à coller, l'adresse de management et l'échéance.

        Raises:
            DomainValidationError: Si l'adresse de management est absente.
            ConflictError: Si le routeur est déjà enrôlé et ``force`` est faux.
        """
        return EnrollmentService(self.actor, actor_role=self.actor_role).issue(device, force=force)

    def attach_credentials(
        self,
        device: Device,
        *,
        username: str,
        password: str,
        port: int | None = None,
        use_tls: bool | None = None,
        transport: str = DeviceTransport.REST,
        simulated: bool | None = None,
    ) -> Device:
        """Renseigne les identifiants réels d'un routeur déjà déployé.

        Utile pour un routeur qui existe déjà (par exemple un CHR x86 dans une machine
        virtuelle) : on ne génère pas de secrets, on range ceux de l'administrateur,
        chiffrés. Le mode simulation n'est **pas** modifié implicitement : il est piloté
        par ``simulated`` (``None`` = inchangé).

        Args:
            device: Routeur à configurer.
            username: Utilisateur RouterOS disposant de ``rest-api`` (ou ``api``).
            password: Mot de passe de cet utilisateur (chiffré avant écriture).
            port: Port du service (``None`` conserve la valeur du routeur).
            use_tls: ``True`` pour HTTPS, ``False`` pour HTTP (``None`` : inchangé).
            transport: ``rest`` (routeur 7.x) ou ``binary`` (repli).
            simulated: Force le mode simulation ; ``None`` conserve le réglage du routeur.

        Returns:
            Le routeur mis à jour.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si l'utilisateur, le mot de passe ou l'IP est absent.
        """
        self.assert_role(self.actor_role, "technician")

        clean_user = (username or "").strip()
        if not clean_user or not password:
            raise DomainValidationError(
                "Renseignez l'utilisateur et le mot de passe du routeur.",
                code="credentials_incomplete",
            )
        if not device.management_ip:
            raise DomainValidationError(
                "Renseignez d'abord l'adresse IP du routeur.", code="device_management_ip_required"
            )

        cipher = SecretCipher.from_settings()
        with transaction.atomic():
            record = getattr(device, "credential", None) or DeviceCredential(device=device)
            record.api_username = clean_user
            record.secret_encrypted = cipher.encrypt(password)
            record.key_version = settings.SECRET_KEY_VERSION
            record.rotated_at = timezone.now()
            record.save()

            if simulated is not None:
                device.is_simulated = simulated
            device.transport = transport
            if port is not None:
                device.management_port = port
            if use_tls is not None:
                device.use_tls = use_tls
            device.save(
                update_fields=["is_simulated", "transport", "management_port", "use_tls", "updated_at"]
            )
        return device

    def probe(self, device: Device, *, with_interfaces: bool = True) -> ProbeResult:
        """Contacte le routeur et persiste l'état observé.

        Aucune exception réseau n'est propagée : le résultat porte l'échec, et le
        routeur est marqué hors ligne le cas échéant.

        Args:
            device: Routeur à sonder.
            with_interfaces: Charge aussi les compteurs d'interface.

        Returns:
            Le résultat brut du backend (succès ou échec).

        Example:
            >>> result = DeviceService(actor=user, actor_role="technician").probe(device)
            >>> device.status
            'online'
        """
        result = MikroTikService(self.actor).probe(device, with_interfaces=with_interfaces)
        self._apply_snapshot(device, build_snapshot(result))
        return result

    def disable(self, device: Device) -> Device:
        """Désactive la supervision d'un routeur (sans le supprimer).

        Args:
            device: Routeur concerné.

        Returns:
            Le routeur au statut ``disabled``.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle administrateur.
        """
        self.assert_role(self.actor_role, "admin")
        device.status = DeviceStatus.DISABLED
        device.save(update_fields=["status", "updated_at"])
        return device

    # ------------------------------------------------------------------- interne
    @staticmethod
    def _apply_snapshot(device: Device, snapshot: DeviceSnapshot) -> None:
        """Applique un état observé au routeur.

        Args:
            device: Routeur à mettre à jour.
            snapshot: État calculé à partir du résultat de sonde.
        """
        device.status = snapshot.status
        device.health = snapshot.health
        if snapshot.ros_version:
            device.ros_version = snapshot.ros_version
        if snapshot.serial:
            device.serial = snapshot.serial
        if snapshot.model_name:
            device.model_name = snapshot.model_name
        if snapshot.is_reachable:
            device.last_seen_at = timezone.now()
        device.save(
            update_fields=[
                "status", "health", "ros_version", "serial",
                "model_name", "last_seen_at", "updated_at",
            ]
        )
