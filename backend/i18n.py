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
        ErrorCode.ACCOUNT_INACTIVE: "Konto jest nieaktywne.",
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
