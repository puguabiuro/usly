from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    dob: date  # yyyy-mm-dd
    role: Literal["user", "partner"]

    # LEGAL
    accept_terms: bool = False


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    status: str


# =====================
# AUTH (dopinka brakująca)
# =====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# =====================
# EVENTS (KROK 2)
# =====================

class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


def _require_tz_and_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Wymagamy datetime z timezone (offset albo Z).
    Jeśli jest timezone-aware -> normalizujemy do UTC.
    Jeśli naive -> błąd walidacji.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(
            "Datetime must include timezone (use ISO 8601 with Z or offset, e.g. 2026-02-01T18:00:00Z)"
        )
    return dt.astimezone(timezone.utc)


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=10_000)
    city: str = Field(min_length=2, max_length=80)

    start_at: datetime
    end_at: datetime

    capacity: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _validate_dates(self):
        self.start_at = _require_tz_and_to_utc(self.start_at)
        self.end_at = _require_tz_and_to_utc(self.end_at)

        if self.start_at is not None and self.end_at is not None and not (self.start_at < self.end_at):
            raise ValueError("start_at must be earlier than end_at")

        return self


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=10_000)
    city: Optional[str] = Field(default=None, min_length=2, max_length=80)

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[Literal["draft", "published", "archived"]] = None

    @model_validator(mode="after")
    def _validate_dates(self):
        self.start_at = _require_tz_and_to_utc(self.start_at)
        self.end_at = _require_tz_and_to_utc(self.end_at)

        # PATCH: walidujemy relację tylko jeśli są oba pola naraz.
        # Jeśli przyjdzie tylko jedno, porównanie zrobimy później w logice endpointu (z wartościami z DB).
        if self.start_at is not None and self.end_at is not None and not (self.start_at < self.end_at):
            raise ValueError("start_at must be earlier than end_at")

        return self


class EventOut(BaseModel):
    id: int
    partner_user_id: int

    title: str
    description: Optional[str] = None
    city: str

    start_at: datetime
    end_at: datetime

    capacity: Optional[int] = None
    status: str

    created_at: datetime
    updated_at: datetime


# =========================
# EVENTS — SCHEMAS (KROK 13)
# pricing + walidacje + normalizacja czasu
# Doklej na końcu pliku schemas.py
# =========================

from datetime import datetime, timezone
from typing import Optional, Literal

from pydantic import BaseModel, Field, model_validator, HttpUrl


EventPricingType = Literal["free", "paid_fixed", "paid_range"]
EventStatusType = Literal["draft", "published", "archived"]


def _to_utc_naive(dt: datetime) -> datetime:
    """
    Frontend może wysłać datetime z timezone (np. +01:00).
    Normalizujemy do UTC i zapisujemy jako naive (bez tzinfo),
    bo SQLite często i tak trzyma naive.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        # jeśli przyszło naive, traktujemy jako UTC (MVP)
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    city: str = Field(min_length=2, max_length=80)

    start_at: datetime
    end_at: datetime

    capacity: Optional[int] = Field(default=None, ge=1, le=100000)

    # EVENT COVER (opcjonalne MVP)
    event_cover_url: Optional[str] = Field(default=None, max_length=500)

    # PRICING
    pricing_type: EventPricingType = "free"  # free | paid_fixed | paid_range
    price_fixed: Optional[int] = Field(default=None, ge=1)  # grosze
    price_min: Optional[int] = Field(default=None, ge=1)    # grosze
    price_max: Optional[int] = Field(default=None, ge=1)    # grosze
    payment_link: Optional[HttpUrl] = None

    @model_validator(mode="after")
    def _validate_all(self):
        # czas -> UTC naive
        self.start_at = _to_utc_naive(self.start_at)
        self.end_at = _to_utc_naive(self.end_at)

        # daty
        if not (self.start_at < self.end_at):
            raise ValueError("INVALID_EVENT_DATES")

        # pricing
        if self.pricing_type == "free":
            if any([self.price_fixed, self.price_min, self.price_max]) or self.payment_link is not None:
                raise ValueError("FREE_EVENT_MUST_NOT_HAVE_PRICES_OR_LINK")

        elif self.pricing_type == "paid_fixed":
            if self.price_fixed is None:
                raise ValueError("PAID_FIXED_REQUIRES_PRICE_FIXED")
            if self.payment_link is None:
                raise ValueError("PAID_EVENT_REQUIRES_PAYMENT_LINK")
            if self.price_min is not None or self.price_max is not None:
                raise ValueError("PAID_FIXED_MUST_NOT_HAVE_RANGE")

        elif self.pricing_type == "paid_range":
            if self.price_min is None or self.price_max is None:
                raise ValueError("PAID_RANGE_REQUIRES_PRICE_MIN_MAX")
            if self.price_min > self.price_max:
                raise ValueError("PAID_RANGE_MIN_MUST_BE_LTE_MAX")
            if self.payment_link is None:
                raise ValueError("PAID_EVENT_REQUIRES_PAYMENT_LINK")
            if self.price_fixed is not None:
                raise ValueError("PAID_RANGE_MUST_NOT_HAVE_FIXED_PRICE")

        return self


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    city: Optional[str] = Field(default=None, min_length=2, max_length=80)

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    capacity: Optional[int] = Field(default=None, ge=1, le=100000)
    status: Optional[EventStatusType] = None

    # EVENT COVER (opcjonalne MVP)
    event_cover_url: Optional[str] = Field(default=None, max_length=500)

    # PRICING (w PATCH: jeśli zmieniasz pricing — podaj pricing_type)
    pricing_type: Optional[EventPricingType] = None
    price_fixed: Optional[int] = Field(default=None, ge=1)
    price_min: Optional[int] = Field(default=None, ge=1)
    price_max: Optional[int] = Field(default=None, ge=1)
    payment_link: Optional[HttpUrl] = None

    @model_validator(mode="after")
    def _validate_all(self):
        # czas -> UTC naive (tylko jeśli podany)
        if self.start_at is not None:
            self.start_at = _to_utc_naive(self.start_at)
        if self.end_at is not None:
            self.end_at = _to_utc_naive(self.end_at)

        # jeśli obie daty podane w PATCH, sprawdzamy kolejność
        if self.start_at is not None and self.end_at is not None:
            if not (self.start_at < self.end_at):
                raise ValueError("INVALID_EVENT_DATES")

        # pricing w PATCH: jeśli dotykasz cen/linku, wymagamy pricing_type
        touches_pricing_fields = any([
            self.price_fixed is not None,
            self.price_min is not None,
            self.price_max is not None,
            self.payment_link is not None,
        ])
        if touches_pricing_fields and self.pricing_type is None:
            raise ValueError("PRICING_TYPE_REQUIRED_WHEN_UPDATING_PRICING")

        # jeśli pricing_type podane — walidujemy spójność pól w payloadzie
        if self.pricing_type == "free":
            if touches_pricing_fields:
                raise ValueError("FREE_EVENT_MUST_NOT_HAVE_PRICES_OR_LINK")

        if self.pricing_type == "paid_fixed":
            if self.price_fixed is None and touches_pricing_fields:
                raise ValueError("PAID_FIXED_REQUIRES_PRICE_FIXED")
            if self.payment_link is None and touches_pricing_fields:
                raise ValueError("PAID_EVENT_REQUIRES_PAYMENT_LINK")
            if self.price_min is not None or self.price_max is not None:
                raise ValueError("PAID_FIXED_MUST_NOT_HAVE_RANGE")

        if self.pricing_type == "paid_range":
            if (self.price_min is None or self.price_max is None) and touches_pricing_fields:
                raise ValueError("PAID_RANGE_REQUIRES_PRICE_MIN_MAX")
            if self.price_min is not None and self.price_max is not None and self.price_min > self.price_max:
                raise ValueError("PAID_RANGE_MIN_MUST_BE_LTE_MAX")
            if self.payment_link is None and touches_pricing_fields:
                raise ValueError("PAID_EVENT_REQUIRES_PAYMENT_LINK")
            if self.price_fixed is not None:
                raise ValueError("PAID_RANGE_MUST_NOT_HAVE_FIXED_PRICE")

        return self


class EventOut(BaseModel):
    id: int
    partner_user_id: int

    title: str
    description: Optional[str]
    city: str

    start_at: datetime
    end_at: datetime
    capacity: Optional[int]

    status: str
    created_at: datetime
    updated_at: datetime

    # EVENT COVER (opcjonalne MVP)
    event_cover_url: Optional[str] = None

    # PRICING
    pricing_type: str
    price_fixed: Optional[int]
    price_min: Optional[int]
    price_max: Optional[int]
    payment_link: Optional[str]
