from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from backend.error_codes import ErrorCode
from backend.i18n import message_for


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ApiError] = None


def ok(data: Any = None) -> dict:
    return ApiResponse(success=True, data=data, error=None).model_dump()


def fail(
    code: ErrorCode,
    message: str | None = None,
    details: Any = None,
    *,
    lang: str | None = None,
) -> dict:
    # If message explicitly provided, keep it. Otherwise use i18n catalog.
    msg = message if message is not None else message_for(code, lang)
    return ApiResponse(
        success=False,
        data=None,
        error=ApiError(code=code.value, message=msg, details=details),
    ).model_dump()
