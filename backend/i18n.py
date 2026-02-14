from __future__ import annotations

from typing import Dict

from error_codes import ErrorCode

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
