"""Kryptograficzny dowód własności tokenu push USLY.

Sam dowód nie uprawnia do zmiany konta. Przekazanie wymaga
dodatkowej autoryzacji po stronie serwera.
"""

import hashlib
import hmac
import secrets


class InvalidPushOwnershipProof(Exception):
    """Dowód własności jest nieprawidłowy lub nieaktualny."""


def create_push_ownership_proof() -> tuple[str, str]:
    """Zwraca losowy dowód i jego skrót do zapisania w bazie."""
    proof = secrets.token_urlsafe(32)
    return proof, hashlib.sha256(proof.encode("utf-8")).hexdigest()


def verify_push_ownership_proof(
    proof: str,
    stored_hash: str,
) -> bool:
    """Weryfikuje dowód bez porównywania jawnych sekretów."""
    if not isinstance(proof, str) or not proof:
        return False
    if not isinstance(stored_hash, str) or len(stored_hash) != 64:
        return False

    actual_hash = hashlib.sha256(proof.encode("utf-8")).hexdigest()
    return hmac.compare_digest(actual_hash, stored_hash)


def rotate_push_ownership_proof(
    *,
    current_proof: str,
    stored_hash: str,
    transfer_authorized: bool,
) -> tuple[str, str]:
    """Wymienia dowód dopiero po jego weryfikacji i autoryzacji."""
    if not transfer_authorized:
        raise InvalidPushOwnershipProof("TRANSFER_NOT_AUTHORIZED")

    if not verify_push_ownership_proof(current_proof, stored_hash):
        raise InvalidPushOwnershipProof("INVALID_OR_STALE_PROOF")

    return create_push_ownership_proof()
