"""Internal service for linking a companion and organizer account.

This service does not authenticate account ownership.
Callers must independently verify authorization for both accounts.
"""

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.error_codes import ErrorCode
from backend.exceptions import ApiException
from backend.models import AccountLink, AccountLinkProofUse, User, UserRole, UserStatus


def create_account_link(
    db: Session,
    *,
    companion_user_id: int,
    organizer_user_id: int,
) -> AccountLink:
    """Create a link between two independently authenticated accounts."""

    if companion_user_id == organizer_user_id:
        raise ApiException(
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            message="Nie można połączyć konta z samym sobą.",
        )

    companion = db.get(User, companion_user_id)
    organizer = db.get(User, organizer_user_id)

    if companion is None or organizer is None:
        raise ApiException(
            status_code=404,
            code=ErrorCode.USER_NOT_FOUND,
        )

    if companion.role != UserRole.USER.value or organizer.role != UserRole.PARTNER.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    if companion.status != UserStatus.ACTIVE.value or organizer.status != UserStatus.ACTIVE.value:
        raise ApiException(
            status_code=403,
            code=ErrorCode.ACCOUNT_INACTIVE,
        )

    existing = db.query(AccountLink).filter(
        or_(
            AccountLink.user_id == companion_user_id,
            AccountLink.partner_id == organizer_user_id,
        )
    ).first()

    if existing is not None:
        raise ApiException(
            status_code=409,
            code=ErrorCode.VALIDATION_ERROR,
            message="Jedno z kont jest już powiązane.",
        )

    link = AccountLink(
        user_id=companion_user_id,
        partner_id=organizer_user_id,
    )

    try:
        db.add(link)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ApiException(
            status_code=409,
            code=ErrorCode.VALIDATION_ERROR,
            message="Nie udało się połączyć kont. Sprawdź istniejące powiązania.",
        ) from exc

    return link



def create_verified_account_link(
    db: Session,
    *,
    initiating_user_id: int,
    proof: str,
) -> AccountLink:
    """Atomically link accounts and consume a single-use proof.

    The caller must authenticate the initiating user independently.
    Never accept initiating_user_id directly from an untrusted request body.
    """
    from backend.account_link_proof import verify_account_link_proof

    second_user_id, proof_id = verify_account_link_proof(
        proof,
        initiating_user_id=initiating_user_id,
    )

    initiator = db.get(User, initiating_user_id)
    second = db.get(User, second_user_id)

    if initiator is None or second is None:
        raise ApiException(
            status_code=404,
            code=ErrorCode.USER_NOT_FOUND,
        )

    if initiator.role == UserRole.USER.value:
        companion_id = initiator.id
        organizer_id = second.id
    elif initiator.role == UserRole.PARTNER.value:
        companion_id = second.id
        organizer_id = initiator.id
    else:
        raise ApiException(
            status_code=403,
            code=ErrorCode.INSUFFICIENT_ROLE,
        )

    try:
        link = create_account_link(
            db,
            companion_user_id=companion_id,
            organizer_user_id=organizer_id,
        )

        db.add(
            AccountLinkProofUse(
                proof_id=proof_id,
                initiating_user_id=initiating_user_id,
                second_user_id=second_user_id,
            )
        )

        db.commit()
        db.refresh(link)
        return link

    except IntegrityError as exc:
        db.rollback()
        raise ApiException(
            status_code=409,
            code=ErrorCode.VALIDATION_ERROR,
            message="Dowód został już wykorzystany lub konto jest powiązane.",
        ) from exc

    except Exception:
        db.rollback()
        raise
