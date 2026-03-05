from __future__ import annotations

from dataclasses import dataclass

from backend.error_codes import ErrorCode


@dataclass
class ApiException(Exception):
    status_code: int
    code: ErrorCode
    message: str | None = None
    details: object | None = None
