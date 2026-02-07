from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from error_codes import ErrorCode


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ApiError] = None


_ERROR_MESSAGES: dict[ErrorCode, str] = {
    # --- AUTH ---
    ErrorCode.AUTH_REQUIRED: "Wymagana autoryzacja.",
    ErrorCode.AUTH_INVALID_TOKEN: "Nieprawidłowy token.",

    # --- VALIDATION ---
    ErrorCode.VALIDATION_ERROR: "Błąd walidacji danych.",
    ErrorCode.AGE_TOO_LOW: "Musisz mieć co najmniej 16 lat.",
    ErrorCode.EMAIL_ALREADY_EXISTS: "Email jest już zajęty.",
    ErrorCode.TERMS_REQUIRED: "Musisz zaakceptować regulamin i politykę prywatności.",

    # --- EVENTS ---
    ErrorCode.EVENT_NOT_FOUND: "Nie znaleziono wydarzenia.",
    ErrorCode.EVENT_FULL: "Wydarzenie jest pełne.",

    # --- GENERIC ---
    ErrorCode.INTERNAL_ERROR: "Wystąpił nieoczekiwany błąd serwera.",
}


def ok(data: Any = None) -> dict:
    return ApiResponse(success=True, data=data, error=None).model_dump()


def fail(code: ErrorCode, message: str | None = None, details: Any = None) -> dict:
    msg = message if message is not None else _ERROR_MESSAGES.get(code, "Wystąpił błąd.")
    return ApiResponse(
        success=False,
        data=None,
        error=ApiError(code=code.value, message=msg, details=details),
    ).model_dump()
