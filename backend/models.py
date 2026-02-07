from __future__ import annotations

from datetime import datetime, date
from enum import StrEnum

from sqlalchemy import String, DateTime, Date, ForeignKey, Text, CheckConstraint, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


# =====================
# ENUMY
# =====================

class UserRole(StrEnum):
    USER = "user"        # frontend: Towarzysz
    PARTNER = "partner"  # frontend: Partner
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    DELETED = "deleted"


# =====================
# USER
# =====================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    # jeśli u Ciebie dob było nullable=False, zostawiamy to bez zmian
    # (seed może nie ustawiać dob — to poprawimy później, nie teraz)
    dob: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # LEGAL – timestamp akceptacji
    terms_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # LEGAL – wersje dokumentów
    terms_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    privacy_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER.value,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


# =====================
# PROFILE — TOWARZYSZ (USER)
# tabela 1:1 z users (unikalny user_id)
# =====================

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    nick: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    miasto: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    # bio (limit 300 znaków zrobimy w walidacji requestu)
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # zainteresowania jako tekst JSON (np. ["sport","muzyka"])
    # walidacja i parsowanie będzie w schemas/endpointach
    zainteresowania_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # zakres wieku
    age_min: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )

    age_max: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


# =====================
# PROFILE — PARTNER
# tabela 1:1 z users (unikalny user_id)
# =====================

class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    nazwa: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        default=None,
    )

    miasto: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


# =====================
# AUDIT LOG
# =====================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    ip: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


# =====================
# EVENTS
# =====================

class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)

    partner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    city: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    # trzymamy UTC, frontend wysyła ISO
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # NULL = brak limitu
    capacity: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventStatus.DRAFT.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_events_end_after_start"),
        CheckConstraint("capacity IS NULL OR capacity >= 1", name="ck_events_capacity_positive"),
        Index("ix_events_status_start_at", "status", "start_at"),
        Index("ix_events_city_start_at", "city", "start_at"),
    )

    # =====================
    # PRICING (MVP)
    # =====================

    pricing_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",  # free | paid_fixed | paid_range
    )

    # ceny w groszach (np. 4900 = 49.00 PLN)
    price_fixed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    price_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    price_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    payment_link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    # =====================
    # EVENT COVER (opcjonalne MVP)
    # =====================
    event_cover_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
# =====================
# EVENT SIGNUPS (ZAPISY NA EVENT)
# =====================

class EventSignup(Base):
    __tablename__ = "event_signups"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
    Index("ix_event_signups_event_user", "event_id", "user_id"),
    # nie pozwala zapisać się 2x na ten sam event
    # (event_id,user_id) musi być unikalne
    UniqueConstraint("event_id", "user_id", name="uq_event_signups_event_user"),
    )


