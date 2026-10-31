"""Short-lived proof of recent authentication for account linking.

A proof must be issued only after the second account successfully
authenticates through its existing password, Google or Apple flow.

Proofs are bound to the initiating account and have a unique ID.
Single-use enforcement happens in the database transaction.
"""

import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from backend.error_codes import ErrorCode
from backend.exceptions import ApiException
from backend.security import JWT_ALGORITHM, JWT_SECRET_KEY


PROOF_PURPOSE = "account_link_second_account"
PROOF_TTL_SECONDS = 120


def create_account_link_proof(
    *,
    user_id: int,
    initiating_user_id: int,
) -> str:
    for value in (user_id, initiating_user_id):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("Invalid user ID")

    if user_id == initiating_user_id:
        raise ValueError("Cannot link account to itself")

    now = datetime.now(timezone.utc)

    return jwt.encode(
        {
            "sub": str(user_id),
            "initiating_user_id": str(initiating_user_id),
            "purpose": PROOF_PURPOSE,
            "jti": secrets.token_hex(32),
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(seconds=PROOF_TTL_SECONDS),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def verify_account_link_proof(
    proof: str,
    *,
    initiating_user_id: int,
) -> tuple[int, str]:
    """Return (second_user_id, proof_id) after validating the JWT."""

    if not isinstance(proof, str) or not proof.strip():
        raise ApiException(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
        )

    try:
        payload = jwt.decode(
            proof,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "require": [
                    "sub",
                    "initiating_user_id",
                    "purpose",
                    "jti",
                    "iat",
                    "nbf",
                    "exp",
                ]
            },
        )

        if payload.get("purpose") != PROOF_PURPOSE:
            raise ValueError("Invalid proof purpose")

        subject = payload.get("sub")
        initiator = payload.get("initiating_user_id")
        proof_id = payload.get("jti")

        if not isinstance(subject, str) or not subject.isdecimal():
            raise ValueError("Invalid subject")

        if not isinstance(initiator, str) or not initiator.isdecimal():
            raise ValueError("Invalid initiator")

        if (
            not isinstance(proof_id, str)
            or len(proof_id) != 64
            or any(c not in "0123456789abcdef" for c in proof_id)
        ):
            raise ValueError("Invalid proof ID")

        second_user_id = int(subject)

        if (
            second_user_id <= 0
            or int(initiator) != initiating_user_id
            or second_user_id == initiating_user_id
        ):
            raise ValueError("Invalid account pairing")

        return second_user_id, proof_id

    except (JWTError, ValueError, TypeError):
        raise ApiException(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
        ) from None
