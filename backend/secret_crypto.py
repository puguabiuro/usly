from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


APPLE_TOKEN_ENCRYPTION_KEY_ENV = "APPLE_TOKEN_ENCRYPTION_KEY"


class SecretCryptoError(Exception):
    """Base error for encrypted secret storage."""


class SecretCryptoNotConfiguredError(SecretCryptoError):
    """Encryption key is not configured."""


class SecretCryptoInvalidTokenError(SecretCryptoError):
    """Encrypted value cannot be decrypted."""


def _get_fernet() -> Fernet:
    key = os.getenv(
        APPLE_TOKEN_ENCRYPTION_KEY_ENV,
        "",
    ).strip()

    if not key:
        raise SecretCryptoNotConfiguredError(
            "Apple token encryption key is not configured."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise SecretCryptoNotConfiguredError(
            "Apple token encryption key is invalid."
        ) from exc


def encrypt_secret(value: str) -> str:
    plaintext = str(value or "")

    if not plaintext:
        raise SecretCryptoError(
            "Secret value is empty."
        )

    encrypted = _get_fernet().encrypt(
        plaintext.encode("utf-8")
    )

    return encrypted.decode("utf-8")


def decrypt_secret(value: str) -> str:
    ciphertext = str(value or "")

    if not ciphertext:
        raise SecretCryptoError(
            "Encrypted secret value is empty."
        )

    try:
        decrypted = _get_fernet().decrypt(
            ciphertext.encode("utf-8")
        )
    except InvalidToken as exc:
        raise SecretCryptoInvalidTokenError(
            "Encrypted secret could not be decrypted."
        ) from exc

    return decrypted.decode("utf-8")
