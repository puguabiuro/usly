"""Validate two independently authenticated USLY accounts.

The active account token must come from Authorization.
The second account token must come from a separate request field.
Never log or persist either token.
"""

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.error_codes import ErrorCode
from backend.exceptions import ApiException
from backend.models import User, UserRole, UserStatus
from backend.security import JWT_ALGORITHM, JWT_SECRET_KEY


def _user_from_token(db: Session, token: str) -> User:
    if not isinstance(token, str) or not token.strip():
        raise ApiException(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdecimal():
            raise ValueError("Invalid subject")

        user_id = int(subject)
        if user_id <= 0:
            raise ValueError("Invalid subject")

    except (JWTError, ValueError, TypeError):
        raise ApiException(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
        ) from None

    user = db.get(User, user_id)

    if user is None:
        raise ApiException(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
        )

    if user.status != UserStatus.ACTIVE.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.ACCOUNT_INACTIVE,
        )

    return user


def verify_account_link_identities(
    db: Session,
    *,
    active_token: str,
    second_account_token: str,
) -> tuple[User, User]:
    """Return (companion, organizer) after validating both JWTs."""

    active = _user_from_token(db, active_token)
    second = _user_from_token(db, second_account_token)

    if active.id == second.id:
        raise ApiException(
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            message="Nie można połączyć konta z samym sobą.",
        )

    allowed_roles = {UserRole.USER.value, UserRole.PARTNER.value}

    if (
        active.role not in allowed_roles
        or second.role not in allowed_roles
        or active.role == second.role
    ):
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    if active.role == UserRole.USER.value:
        return active, second

    return second, active
