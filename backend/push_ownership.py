"""Kontrola własności tokenów push dla sesji urządzenia USLY.

Ten moduł definiuje reguły bezpieczeństwa.
Nie jest jeszcze podłączony do endpointów produkcyjnych.
"""

from enum import Enum


class PushOwnershipAction(str, Enum):
    REGISTER_CURRENT_OWNER = "register_current_owner"
    TRANSFER_ON_ACCOUNT_SWITCH = "transfer_on_account_switch"
    TRANSFER_ON_NEW_LOGIN = "transfer_on_new_login"
    UNREGISTER_CURRENT_OWNER = "unregister_current_owner"


class PushOwnershipError(Exception):
    """Nieautoryzowana lub nieaktualna operacja na tokenie push."""


def validate_push_ownership_transition(
    *,
    current_owner_id: int | None,
    requesting_user_id: int,
    action: PushOwnershipAction,
    authorization_verified: bool,
) -> bool:
    """Wstępna walidacja przejścia własności.

    Nie weryfikuje jeszcze kryptograficznego dowodu sesji.
    Nie wolno używać tej funkcji jako samodzielnej autoryzacji.
    """

    if requesting_user_id <= 0:
        raise PushOwnershipError("INVALID_REQUESTING_USER")

    if current_owner_id is None:
        if action == PushOwnershipAction.REGISTER_CURRENT_OWNER:
            return True
        raise PushOwnershipError("PUSH_TOKEN_NOT_REGISTERED")

    if current_owner_id == requesting_user_id:
        if action in (
            PushOwnershipAction.REGISTER_CURRENT_OWNER,
            PushOwnershipAction.UNREGISTER_CURRENT_OWNER,
        ):
            return True

    if action in (
        PushOwnershipAction.TRANSFER_ON_ACCOUNT_SWITCH,
        PushOwnershipAction.TRANSFER_ON_NEW_LOGIN,
    ):
        if not authorization_verified:
            raise PushOwnershipError("PUSH_TRANSFER_NOT_AUTHORIZED")
        if current_owner_id == requesting_user_id:
            raise PushOwnershipError("PUSH_TRANSFER_SAME_OWNER")
        return True

    raise PushOwnershipError("PUSH_OWNER_MISMATCH")
