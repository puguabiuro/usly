from __future__ import annotations

from typing import Dict

from backend.error_codes import ErrorCode

DEFAULT_LANG = "pl"
SUPPORTED_LANGS = {"pl", "en"}

# Krótkie, przyjazne komunikaty dla UI.
MESSAGES: Dict[str, Dict[ErrorCode, str]] = {
    "pl": {
        # AUTH
        ErrorCode.AUTH_REQUIRED: "Musisz się zalogować.",
        ErrorCode.AUTH_INVALID_TOKEN: "Sesja wygasła lub token jest nieprawidłowy.",

        # VALIDATION
        ErrorCode.VALIDATION_ERROR: "Nieprawidłowe dane.",
        ErrorCode.AGE_TOO_LOW: "Musisz mieć co najmniej 16 lat.",
        ErrorCode.EMAIL_ALREADY_EXISTS: "Ten e-mail jest już zajęty.",
        ErrorCode.TERMS_REQUIRED: "Zaakceptuj regulamin.",

        # EVENTS
        ErrorCode.EVENT_NOT_FOUND: "Nie znaleziono wydarzenia.",
        ErrorCode.EVENT_FULL: "Brak miejsc na to wydarzenie.",

        # GENERIC
        ErrorCode.INTERNAL_ERROR: "Wystąpił błąd serwera. Spróbuj ponownie.",
        ErrorCode.EVENT_NOT_PUBLISHED: "Wydarzenie nie jest opublikowane.",
        ErrorCode.PROFILE_NOT_FOUND: "Nie znaleziono profilu użytkownika.",
        ErrorCode.GROUP_NOT_FOUND: "Nie znaleziono grupy.",
        ErrorCode.GROUP_LIMIT_REACHED: "Osiągnięto limit grup dla Twojego planu.",
        ErrorCode.GROUP_CREATE_LIMIT_REACHED: "Twój plan nie pozwala utworzyć kolejnej grupy.",
        ErrorCode.GROUP_OWNER_CANNOT_LEAVE: "Jako właściciel grupy nie możesz jej opuścić. Możesz ją zamknąć.",
        ErrorCode.ALREADY_JOINED: "Już dołączyłeś/aś do tego wydarzenia.",
        ErrorCode.NOT_JOINED: "Nie jesteś zapisany/a na to wydarzenie.",
        ErrorCode.FORBIDDEN_NOT_OWNER: "Brak uprawnień (nie jesteś właścicielem).",
        ErrorCode.INVALID_EVENT_DATES: "Nieprawidłowe daty wydarzenia.",
        ErrorCode.INVALID_STATUS_TRANSITION: "Nieprawidłowa zmiana statusu.",
        ErrorCode.INVALID_STATUS_FILTER: "Nieprawidłowy filtr statusu.",
        ErrorCode.INVALID_SORT: "Nieprawidłowe sortowanie.",
        ErrorCode.invalid_file_type: "Nieprawidłowy typ pliku.",
        ErrorCode.file_too_large_max_5mb: "Plik jest za duży (maks. 5 MB).",
        ErrorCode.age_min_must_be_lte_age_max: "Minimalny wiek nie może być większy niż maksymalny.",
        ErrorCode.interest_too_long_max_40: "Zainteresowanie jest za długie (maks. 40 znaków).",
        ErrorCode.too_many_interests_max_20: "Za dużo zainteresowań (maks. 20).",
        ErrorCode.RATE_LIMITED: "Zbyt wiele prób. Spróbuj ponownie za chwilę.",

        # LOGIN
        ErrorCode.INVALID_CREDENTIALS: "Nieprawidłowy e-mail lub hasło.",
        ErrorCode.ACCOUNT_INACTIVE: "To konto zostało usunięte lub jest nieaktywne.",
        ErrorCode.INSUFFICIENT_ROLE: "To konto nie ma dostępu do tej części aplikacji.",
        ErrorCode.ALREADY_SAVED: "To wydarzenie jest już zapisane.",
        ErrorCode.CANNOT_ADD_SELF: "Nie możesz dodać siebie.",
        ErrorCode.CANNOT_INVITE_SELF: "Nie możesz zaprosić samego/samej siebie.",
        ErrorCode.CANNOT_MESSAGE_SELF: "Nie możesz napisać wiadomości do siebie.",
        ErrorCode.CURRENT_PASSWORD_INVALID: "Obecne hasło jest nieprawidłowe.",
        ErrorCode.FRIEND_REQUEST_NOT_FOUND: "Nie znaleziono zaproszenia do znajomych.",
        ErrorCode.GROUP_ACCESS_REQUIRES_MEMBERSHIP: "Dostęp do tej grupy wymaga członkostwa.",
        ErrorCode.GROUP_INVITATION_ALREADY_PENDING: "Zaproszenie do grupy jest już oczekujące.",
        ErrorCode.GROUP_INVITATION_NOT_FOUND: "Nie znaleziono zaproszenia do grupy.",
        ErrorCode.GROUP_INVITE_ONLY_FOR_FRIENDS: "Do grupy możesz zapraszać tylko znajomych.",
        ErrorCode.GROUP_INVITE_PLAN_REQUIRED: "Twój plan nie pozwala zapraszać do grupy.",
        ErrorCode.GROUP_INVITE_REQUIRES_MEMBERSHIP: "Aby zapraszać do grupy, musisz być jej członkiem.",
        ErrorCode.GROUP_MEMBERSHIP_REQUIRED: "Ta akcja wymaga członkostwa w grupie.",
        ErrorCode.INVALID_PLAN: "Nieprawidłowy plan.",
        ErrorCode.NEW_PASSWORD_SAME_AS_CURRENT: "Nowe hasło musi być inne niż obecne.",
        ErrorCode.PASSWORD_INVALID: "Hasło jest nieprawidłowe.",
        ErrorCode.PLAN_ACTIVE_EVENT_LIMIT_REACHED: "Twój plan nie pozwala opublikować kolejnego aktywnego wydarzenia.",
        ErrorCode.SAVE_NOT_FOUND: "Nie znaleziono zapisanego wydarzenia.",
        ErrorCode.USER_ALREADY_IN_GROUP: "Ten użytkownik jest już w grupie.",
        ErrorCode.USER_NOT_FOUND: "Nie znaleziono użytkownika.",
        ErrorCode.USER_NOT_FOUND_LEGACY: "Nie znaleziono użytkownika.",
        ErrorCode.PASSWORD_RESET_TOKEN_INVALID: "Link do resetu hasła jest nieprawidłowy lub został już użyty.",
        ErrorCode.PASSWORD_RESET_TOKEN_EXPIRED: "Link do resetu hasła wygasł. Poproś o nowy link.",
    },
    "en": {
        # AUTH
        ErrorCode.AUTH_REQUIRED: "You must be logged in.",
        ErrorCode.AUTH_INVALID_TOKEN: "Session expired or token is invalid.",

        # VALIDATION
        ErrorCode.VALIDATION_ERROR: "Invalid input.",
        ErrorCode.AGE_TOO_LOW: "You must be at least 16 years old.",
        ErrorCode.EMAIL_ALREADY_EXISTS: "This email is already taken.",
        ErrorCode.TERMS_REQUIRED: "Please accept the terms.",

        # EVENTS
        ErrorCode.EVENT_NOT_FOUND: "Event not found.",
        ErrorCode.EVENT_FULL: "This event is full.",

        # GENERIC
        ErrorCode.INTERNAL_ERROR: "Server error. Please try again.",
        ErrorCode.EVENT_NOT_PUBLISHED: "This event is not published.",
        ErrorCode.PROFILE_NOT_FOUND: "User profile not found.",
        ErrorCode.GROUP_NOT_FOUND: "Group not found.",
        ErrorCode.GROUP_LIMIT_REACHED: "You have reached the group limit for your plan.",
        ErrorCode.GROUP_CREATE_LIMIT_REACHED: "Your plan does not allow creating another group.",
        ErrorCode.GROUP_OWNER_CANNOT_LEAVE: "As the group owner, you cannot leave it. You can close it instead.",
        ErrorCode.ALREADY_JOINED: "You have already joined this event.",
        ErrorCode.NOT_JOINED: "You are not signed up for this event.",
        ErrorCode.FORBIDDEN_NOT_OWNER: "You do not have permission (not the owner).",
        ErrorCode.INVALID_EVENT_DATES: "Invalid event dates.",
        ErrorCode.INVALID_STATUS_TRANSITION: "Invalid status transition.",
        ErrorCode.INVALID_STATUS_FILTER: "Invalid status filter.",
        ErrorCode.INVALID_SORT: "Invalid sort option.",
        ErrorCode.invalid_file_type: "Invalid file type.",
        ErrorCode.file_too_large_max_5mb: "File is too large (max 5 MB).",
        ErrorCode.age_min_must_be_lte_age_max: "Minimum age must be less than or equal to maximum age.",
        ErrorCode.interest_too_long_max_40: "Interest is too long (max 40 characters).",
        ErrorCode.too_many_interests_max_20: "Too many interests (max 20).",
        ErrorCode.RATE_LIMITED: "Too many attempts. Please try again later.",

        # LOGIN
        ErrorCode.INVALID_CREDENTIALS: "Invalid email or password.",
        ErrorCode.ACCOUNT_INACTIVE: "Account is inactive.",
        ErrorCode.INSUFFICIENT_ROLE: "This account does not have access to this part of the app.",
        ErrorCode.ALREADY_SAVED: "This event is already saved.",
        ErrorCode.CANNOT_ADD_SELF: "You cannot add yourself.",
        ErrorCode.CANNOT_INVITE_SELF: "You cannot invite yourself.",
        ErrorCode.CANNOT_MESSAGE_SELF: "You cannot message yourself.",
        ErrorCode.CURRENT_PASSWORD_INVALID: "Current password is invalid.",
        ErrorCode.FRIEND_REQUEST_NOT_FOUND: "Friend request not found.",
        ErrorCode.GROUP_ACCESS_REQUIRES_MEMBERSHIP: "Access to this group requires membership.",
        ErrorCode.GROUP_INVITATION_ALREADY_PENDING: "Group invitation is already pending.",
        ErrorCode.GROUP_INVITATION_NOT_FOUND: "Group invitation not found.",
        ErrorCode.GROUP_INVITE_ONLY_FOR_FRIENDS: "You can invite only friends to the group.",
        ErrorCode.GROUP_INVITE_PLAN_REQUIRED: "Your plan does not allow group invites.",
        ErrorCode.GROUP_INVITE_REQUIRES_MEMBERSHIP: "You must be a member to invite people to this group.",
        ErrorCode.GROUP_MEMBERSHIP_REQUIRED: "This action requires group membership.",
        ErrorCode.INVALID_PLAN: "Invalid plan.",
        ErrorCode.NEW_PASSWORD_SAME_AS_CURRENT: "New password must be different from the current password.",
        ErrorCode.PASSWORD_INVALID: "Password is invalid.",
        ErrorCode.PLAN_ACTIVE_EVENT_LIMIT_REACHED: "Your plan does not allow publishing another active event.",
        ErrorCode.SAVE_NOT_FOUND: "Saved event not found.",
        ErrorCode.USER_ALREADY_IN_GROUP: "This user is already in the group.",
        ErrorCode.USER_NOT_FOUND: "User not found.",
        ErrorCode.USER_NOT_FOUND_LEGACY: "User not found.",
        ErrorCode.PASSWORD_RESET_TOKEN_INVALID: "The password reset link is invalid or has already been used.",
        ErrorCode.PASSWORD_RESET_TOKEN_EXPIRED: "The password reset link has expired. Request a new link.",
    },
}


def normalize_lang(value: str | None) -> str:
    if not value:
        return DEFAULT_LANG
    v = value.strip().lower()
    # allow "pl-PL", "en-US"
    v = v.split(",")[0].split(";")[0].strip()
    v = v.split("-")[0]
    return v if v in SUPPORTED_LANGS else DEFAULT_LANG


def message_for(code: ErrorCode, lang: str | None) -> str:
    l = normalize_lang(lang)
    return MESSAGES.get(l, MESSAGES[DEFAULT_LANG]).get(code, MESSAGES[DEFAULT_LANG][ErrorCode.INTERNAL_ERROR])
