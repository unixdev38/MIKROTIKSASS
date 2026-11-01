"""Services du parc réseau : sites et routeurs.

Chaque méthode est une unité de travail (validations, transaction, résultat typé).
L'enrôlement vit dans ``apps.network.enrollment`` (responsabilité distincte), et la
transformation d'une sonde dans ``apps.network.snapshots``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from apps.mikrotik.schemas import ProbeResult
from apps.mikrotik.services import MikroTikService
from apps.network.enrollment import EnrollmentService
from apps.network.models import Device, DeviceStatus, DeviceTransport, Site
from apps.network.schemas import DeviceSnapshot, EnrollmentBundle
from apps.network.snapshots import build_snapshot
from core.exceptions import ConflictError, DomainValidationError
from core.services import BaseService

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from apps.accounts.models import User


class SiteService(BaseService[Site]):
    """Création et mise à jour des sites.

    Args:
        actor: Utilisateur à l'origine de l'action.
        actor_role: Rôle de cet utilisateur dans l'espace courant.
    """

    def __init__(self, actor: User | None = None, *, actor_role: str | None = None) -> None:
        super().__init__(actor)
        self.actor_role = actor_role

    def register(self, *, name: str, code: str, city: str = "") -> Site:
        """Crée un site dans l'espace courant.

        Args:
            name: Nom affiché du site.
            code: Code court unique dans l'espace.
            city: Ville (facultative).

        Returns:
            Le site créé.

        Raises:
            PermissionDeniedError: Si l'acteur n'a pas le rôle technicien.
            DomainValidationError: Si le nom ou le code est vide.
            ConflictError: Si le code est déjà utilisé dans cet espace.
        """
        self.assert_role(self.actor_role, "technician")

        clean_name = (name or "").strip()
        clean_code = (code or "").strip().upper()
        if not clean_name:
            raise DomainValidationError("Le nom du site est obligatoire.", code="site_name_required")
        if not clean_code:
            raise DomainValidationError("Le code du site est obligatoire.", code="site_code_required")
        if Site.objects.filter(code=clean_code).exists():
            raise ConflictError(f"Le code « {clean_code} » existe déjà.", code="site_code_taken")

        return Site.objects.create(name=clean_name, code=clean_code, city=city.strip())


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
            management_ip: Adresse prévue dans le tunnel.
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
