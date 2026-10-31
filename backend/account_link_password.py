"""Fresh password authentication for linking an existing account."""

from sqlalchemy.orm import Session

from backend.account_link_proof import create_account_link_proof
from backend.error_codes import ErrorCode
from backend.exceptions import ApiException
from backend.models import User, UserRole, UserStatus
from backend.security import verify_password


def authenticate_second_account_with_password(
    db: Session,
    *,
    initiating_user: User,
    email: str,
    password: str,
) -> str:
    """Return a short-lived link proof, never an access token.

    The initiating user must already be authenticated by the API.
    The caller must enforce endpoint rate limiting.
    """

    # get_current_user zamyka własną sesję przed wywołaniem endpointu.
    # Pobieramy użytkownika w bieżącej sesji, aby uniknąć DetachedInstanceError.
    initiating_user_id = getattr(initiating_user, "id", None)
    initiating_user = (
        db.query(User).filter(User.id == initiating_user_id).first()
        if initiating_user_id is not None
        else None
    )

    if (
        initiating_user is None
        or initiating_user.status != UserStatus.ACTIVE.value
        or initiating_user.role not in (
            UserRole.USER.value,
            UserRole.PARTNER.value,
        )
    ):
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    normalized_email = str(email or "").strip().lower()

    opposite_role = (
        UserRole.PARTNER.value
        if initiating_user.role == UserRole.USER.value
        else UserRole.USER.value
    )

    second = (
        db.query(User)
        .filter(
            User.email == normalized_email,
            User.role == opposite_role,
        )
        .first()
    )

    if (
        second is None
        or not second.password_hash
        or not isinstance(password, str)
        or not verify_password(password, second.password_hash)
    ):
        raise ApiException(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    if second.status != UserStatus.ACTIVE.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.ACCOUNT_INACTIVE,
        )

    if (
        second.id == initiating_user.id
        or second.role == initiating_user.role
        or second.role not in (
            UserRole.USER.value,
            UserRole.PARTNER.value,
        )
    ):
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    return create_account_link_proof(
        user_id=second.id,
        initiating_user_id=initiating_user.id,
    )
