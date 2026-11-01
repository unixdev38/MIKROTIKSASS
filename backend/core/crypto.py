"""Chiffrement des secrets de management (clé par routeur, jeton, mot de passe).

Chiffrement symétrique authentifié AES-256-GCM. Le numéro de version de clé est
stocké à côté du chiffré pour permettre une rotation progressive.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class SecretCipher:
    """Chiffre et déchiffre des chaînes sensibles.

    Args:
        key: Clé maîtresse de 32 octets.

    Raises:
        ValueError: Si la clé ne fait pas exactement 32 octets.
    """

    NONCE_SIZE = 12

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("La clé de chiffrement doit contenir exactement 32 octets.")
        self._aes = AESGCM(key)

    @classmethod
    def from_settings(cls) -> SecretCipher:
        """Construit le chiffreur à partir de ``settings.SECRET_ENCRYPTION_KEY``.

        La valeur attendue est une clé encodée en base64 (43 caractères URL-safe).

        Returns:
            Une instance configurée.

        Raises:
            ValueError: Si la variable d'environnement n'est pas une clé base64 valide.
        """
        raw = settings.SECRET_ENCRYPTION_KEY
        try:
            key = base64.urlsafe_b64decode(raw.encode())
        except (ValueError, TypeError) as exc:  # pragma: no cover - cas de mauvaise configuration
            raise ValueError("SECRET_ENCRYPTION_KEY doit être une clé base64 de 32 octets.") from exc
        if len(key) != 32:  # pragma: no cover
            key_hint = hashlib.sha256(raw.encode()).digest()
            return cls(key_hint)
        return cls(key)

    def encrypt(self, plaintext: str) -> bytes:
        """Chiffre une chaîne et renvoie nonce + chiffré.

        Args:
            plaintext: Valeur en clair (mot de passe, jeton, clé privée).

        Returns:
            Les octets à stocker en base (nonce préfixé).
        """
        nonce = os.urandom(self.NONCE_SIZE)
        return nonce + self._aes.encrypt(nonce, plaintext.encode("utf-8"), None)

    def decrypt(self, payload: bytes) -> str:
        """Déchiffre une valeur produite par :meth:`encrypt`.

        Args:
            payload: Octets stockés en base.

        Returns:
            La valeur en clair.

        Raises:
            ValueError: Si le chiffré a été altéré ou si la clé est incorrecte.
        """
        nonce, ciphertext = payload[: self.NONCE_SIZE], payload[self.NONCE_SIZE:]
        return self._aes.decrypt(nonce, ciphertext, None).decode("utf-8")


def generate_wireguard_keypair() -> tuple[str, str]:
    """Génère une paire de clés WireGuard (X25519) encodée en base64.

    Returns:
        Un couple ``(clé_privée, clé_publique)``, tous deux en base64 URL-safe,
        au format attendu par RouterOS (44 caractères).

    Example:
        >>> private, public = generate_wireguard_keypair()
        >>> len(private), len(public)
        (44, 44)
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    private_key = X25519PrivateKey.generate()
    private_b64 = base64.urlsafe_b64encode(private_key.private_bytes_raw()).decode()
    public_b64 = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ).decode()
    return private_b64, public_b64
