"""Operacje zmiany właściciela tokenu push.

Funkcja wymaga zewnętrznej autoryzacji przełączenia kont.
Nie wykonuje commit, pozostawiając transakcję wywołującemu.
"""

from datetime import datetime

from backend.models import DevicePushToken
from backend.push_ownership_proof import (
    create_push_ownership_proof,
    verify_push_ownership_proof,
)


class PushOwnershipTransferError(Exception):
    pass



def decide_push_registration(
    *,
    existing_owner,
    requesting_user,
    is_active,
    stored_proof_hash,
    supplied_proof,
):
    """Podejmij decyzję bez zmiany stanu bazy danych."""
    if existing_owner is None:
        return "CREATE"

    if existing_owner != requesting_user:
        return "DENY_OTHER_OWNER"

    if stored_proof_hash is None:
        return "BOOTSTRAP_LEGACY_OWNER"

    if not supplied_proof:
        return "DENY_MISSING_PROOF"

    if not verify_push_ownership_proof(
        supplied_proof, stored_proof_hash
    ):
        return "DENY_INVALID_PROOF"

    return "REFRESH_CURRENT_OWNER"

def transfer_push_token(
    db,
    *,
    token: str,
    source_user_id: int,
    target_user_id: int,
    current_proof: str,
    transfer_authorized: bool,
    next_proof: str | None = None,
):
    if not transfer_authorized:
        raise PushOwnershipTransferError("TRANSFER_NOT_AUTHORIZED")

    if source_user_id == target_user_id:
        raise PushOwnershipTransferError("SAME_OWNER")

    row = (
        db.query(DevicePushToken)
        .filter(DevicePushToken.token == token)
        .with_for_update()
        .first()
    )

    if row is None:
        raise PushOwnershipTransferError("TOKEN_NOT_FOUND")

    if row.user_id == target_user_id and row.is_active and next_proof is not None:
        if (
            isinstance(next_proof, str)
            and 43 <= len(next_proof) <= 128
            and all(
                char.isascii() and (char.isalnum() or char in "-_")
                for char in next_proof
            )
            and next_proof != current_proof
            and verify_push_ownership_proof(
                next_proof,
                row.ownership_proof_hash,
            )
        ):
            # Idempotentne ponowienie transferu, który już został zapisany.
            # Nie zmieniamy właściciela ani dowodu.
            return next_proof

    if row.user_id != source_user_id or not row.is_active:
        raise PushOwnershipTransferError("TOKEN_OWNER_CHANGED")

    if not verify_push_ownership_proof(
        current_proof,
        row.ownership_proof_hash,
    ):
        raise PushOwnershipTransferError("INVALID_OR_STALE_PROOF")

    if next_proof is not None:
        import hashlib

        if (
            not isinstance(next_proof, str)
            or len(next_proof) < 43
            or len(next_proof) > 128
            or not all(
                char.isascii() and (char.isalnum() or char in "-_")
                for char in next_proof
            )
            or next_proof == current_proof
        ):
            raise PushOwnershipTransferError("INVALID_NEXT_PROOF")

        new_proof = next_proof
        new_hash = hashlib.sha256(next_proof.encode("utf-8")).hexdigest()
    else:
        new_proof, new_hash = create_push_ownership_proof()

    row.user_id = target_user_id
    row.ownership_proof_hash = new_hash
    row.updated_at = datetime.utcnow()
    row.last_seen_at = row.updated_at

    db.flush()
    return new_proof
