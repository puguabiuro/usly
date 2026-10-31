"""Fresh Google authentication for linking an existing opposite-role account."""

from sqlalchemy.orm import Session

from backend.account_link_proof import create_account_link_proof
from backend.error_codes import ErrorCode
from backend.exceptions import ApiException
from backend.models import User, UserRole, UserStatus


def authenticate_second_account_with_apple(
    db: Session,
    *,
    initiating_user: User,
    apple_sub: str,
) -> str:
    """Issue a link proof for an independently verified Apple identity.

    The caller MUST validate the Apple identity token, audience,
    one-time nonce and authorization code before calling this function.
    This function does not log in as the second account or mutate it.
    """

    initiating_id = getattr(initiating_user, "id", None)

    initiator = (
        db.query(User).filter(User.id == initiating_id).first()
        if initiating_id is not None
        else None
    )

    if (
        initiator is None
        or initiator.status != UserStatus.ACTIVE.value
        or initiator.role not in (
            UserRole.USER.value,
            UserRole.PARTNER.value,
        )
    ):
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    subject = str(apple_sub or "").strip()

    if not subject:
        raise ApiException(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    opposite_role = (
        UserRole.PARTNER.value
        if initiator.role == UserRole.USER.value
        else UserRole.USER.value
    )

    second = (
        db.query(User)
        .filter(
            User.apple_sub == subject,
            User.role == opposite_role,
        )
        .first()
    )

    if second is None:
        raise ApiException(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    if second.status != UserStatus.ACTIVE.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.ACCOUNT_INACTIVE,
        )

    if second.id == initiator.id:
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    return create_account_link_proof(
        user_id=second.id,
        initiating_user_id=initiator.id,
    )


def authenticate_second_account_with_google(
    db: Session,
    *,
    initiating_user: User,
    google_sub: str,
) -> str:
    """Issue a link proof after a verified Google identity is supplied.

    The caller MUST cryptographically verify the Google ID token,
    including its audience, before passing its subject here.
    """

    initiating_id = getattr(initiating_user, "id", None)

    initiator = (
        db.query(User).filter(User.id == initiating_id).first()
        if initiating_id is not None
        else None
    )

    if (
        initiator is None
        or initiator.status != UserStatus.ACTIVE.value
        or initiator.role not in (
            UserRole.USER.value,
            UserRole.PARTNER.value,
        )
    ):
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    subject = str(google_sub or "").strip()

    if not subject:
        raise ApiException(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    opposite_role = (
        UserRole.PARTNER.value
        if initiator.role == UserRole.USER.value
        else UserRole.USER.value
    )

    second = (
        db.query(User)
        .filter(
            User.google_sub == subject,
            User.role == opposite_role,
        )
        .first()
    )

    if second is None:
        raise ApiException(
            status_code=401,
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    if second.status != UserStatus.ACTIVE.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.ACCOUNT_INACTIVE,
        )

    if second.id == initiator.id:
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    return create_account_link_proof(
        user_id=second.id,
        initiating_user_id=initiator.id,
    )
