# backend/logger.py
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

_CONFIGURED = False

# --- Safety: mask sensitive data in logs (best-effort) ------------------------

_SENSITIVE_KEYS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
)


class SensitiveDataFilter(logging.Filter):
    """
    Best-effort masking of sensitive values in log messages.

    Works for typical patterns like:
      - "password=abc", "token: xyz"
      - {"password": "abc"} (as a string in the message)

    Note: this is not a perfect DLP system, but it prevents most accidental leaks.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            lowered = msg.lower()
            if any(k in lowered for k in _SENSITIVE_KEYS):
                record.msg = _mask_message(msg)
                record.args = ()
        except Exception:
            # Never break logging because of masking issues
            pass
        return True


def _mask_message(msg: str) -> str:
    # Simple, safe masking for common "key=value" and "key: value" patterns.
    # We avoid regex to keep it lightweight and dependency-free.
    out = msg
    for key in _SENSITIVE_KEYS:
        out = _mask_key_value(out, key)
    return out


def _mask_key_value(text: str, key: str) -> str:
    # Mask occurrences of key in various casings.
    variants = {key, key.upper(), key.capitalize()}

    for k in variants:
        # key=value or key: value
        text = _mask_after_separator(text, k, "=")
        text = _mask_after_separator(text, k, ":")

        # JSON-like: "key":"value" or "key": "value"
        text = _mask_after_separator(text, f'"{k}"', ":")

    return text



def _mask_after_separator(text: str, key: str, sep: str) -> str:
    needle = f"{key}{sep}"
    start = 0

    while True:
        idx = text.find(needle, start)
        if idx == -1:
            break

        val_start = idx + len(needle)

        # Skip spaces after separator
        while val_start < len(text) and text[val_start] == " ":
            val_start += 1

        if val_start >= len(text):
            break

        # If value starts with a quote, mask until the closing quote.
        if text[val_start] in ('"', "'"):
            quote = text[val_start]
            # find closing quote
            val_end = val_start + 1
            while val_end < len(text) and text[val_end] != quote:
                val_end += 1

            # If we found a closing quote, mask inside quotes
            if val_end < len(text) and text[val_end] == quote:
                inner_start = val_start + 1
                inner_end = val_end
                text = text[:inner_start] + "********" + text[inner_end:]
                start = inner_start + len("********") + 1  # move past masked + closing quote
                continue

        # Fallback: mask until a common delimiter or whitespace/newline
        val_end = val_start
        while val_end < len(text) and text[val_end] not in (" ", ",", ";", "\n", "\r", "}"):
            val_end += 1

        if val_end > val_start:
            text = text[:val_start] + "********" + text[val_end:]
            start = val_start + len("********")
        else:
            start = val_start

    return text



# --- Base logger config -------------------------------------------------------

DEFAULT_LEVEL = "INFO"
DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _resolve_level(level: Optional[str]) -> int:
    """
    Accepts: DEBUG / INFO / WARNING / ERROR / CRITICAL (case-insensitive)
    Falls back to DEFAULT_LEVEL if invalid / missing.
    """
    raw = (level or os.getenv("LOG_LEVEL") or DEFAULT_LEVEL).strip().upper()
    return getattr(logging, raw, logging.INFO)


def configure_logging(
    level: Optional[str] = None,
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATEFMT,
) -> None:
    """
    Configure root logging once (idempotent).
    - Logs to stdout (best for Docker/cloud).
    - Unified format (time | level | logger_name | message).
    - Adds a safety filter that masks common sensitive fields.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(_resolve_level(level))

    # Avoid duplicate handlers if something else configured logging earlier.
    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(root.level)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        handler.addFilter(SensitiveDataFilter())
        root.addHandler(handler)

    # Make common noisy libs quieter (optional, safe default).
    for noisy in ("uvicorn", "uvicorn.access", "gunicorn", "werkzeug"):
        logging.getLogger(noisy).setLevel(max(root.level, logging.INFO))

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a logger that is guaranteed to be configured.
    Usage:
        log = get_logger(__name__)
        log.info("Hello")
    """
    configure_logging()
    return logging.getLogger(name if name else "app")


def log_exception(logger: logging.Logger, msg: str, **extra) -> None:
    """
    Convenience helper for consistent error logging with stack trace.
    Example:
        try: ...
        except Exception:
            log_exception(log, "Failed to do X", user_id=user_id)
    """
    if extra:
        msg = f"{msg} | extra={extra}"
    logger.exception(msg)
