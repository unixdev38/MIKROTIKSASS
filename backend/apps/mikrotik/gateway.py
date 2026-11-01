"""Fabrique de backends : choisit et configure le bon transport pour un routeur."""
from __future__ import annotations

from django.conf import settings

from apps.mikrotik.backends.base import BaseBackend
from apps.mikrotik.backends.fake import FakeBackend
from apps.mikrotik.backends.rest import RestBackend
from core.crypto import SecretCipher
from core.exceptions import DomainValidationError


def build_backend(device: object, *, fail_with: str | None = None) -> BaseBackend:
    """Construit le backend adapté à un routeur.

    Le choix suit trois règles, dans cet ordre :
    1. ``MIKROTIK_FAKE_MODE`` actif **et** routeur marqué ``is_simulated`` →
       :class:`FakeBackend` (développement, démonstration, tests) ;
    2. transport ``rest`` → :class:`RestBackend` ;
    3. transport ``binary`` → non implémenté à ce stade (P3, backend binaire).

    Args:
        device: Instance de ``apps.network.models.Device`` à joindre.
        fail_with: Force un échec (tests du chemin d'erreur), transmis au backend factice.

    Returns:
        Un backend prêt à l'emploi.

    Raises:
        DomainValidationError: Si le routeur n'a pas d'identifiants d'enrôlement ou si le
            transport demandé n'est pas disponible.
    """
    credential = getattr(device, "credential", None)
    if credential is None:
        raise DomainValidationError(
            "Ce routeur n'a pas encore d'identifiants : lancez son enrôlement.",
            code="device_not_enrolled",
        )

    host = str(getattr(device, "management_ip", "") or "")
    if not host:
        raise DomainValidationError(
            "Aucune adresse de management : l'enrôlement doit définir l'IP du tunnel.",
            code="device_host_missing",
        )

    use_fake = settings.MIKROTIK_FAKE_MODE and getattr(device, "is_simulated", False)
    if use_fake:
        return FakeBackend(host=host, fail_with=fail_with, timeout=settings.MIKROTIK_TIMEOUT_SECONDS)

    secret = SecretCipher.from_settings().decrypt(credential.secret_encrypted)
    transport = getattr(device, "transport", settings.MIKROTIK_DEFAULT_TRANSPORT)

    if transport == "rest":
        return RestBackend(
            host=host,
            username=credential.api_username,
            secret=secret,
            timeout=settings.MIKROTIK_TIMEOUT_SECONDS,
        )

    raise DomainValidationError(
        f"Transport « {transport} » non disponible dans cette version (voir roadmap P3).",
        code="transport_unsupported",
    )
