from __future__ import annotations

from datetime import datetime, date
from enum import StrEnum

from sqlalchemy import String, DateTime, Date, ForeignKey, Text, CheckConstraint, Index, Integer, UniqueConstraint, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base


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

    admin_display_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    admin_level: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
    )

    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mfa_secret: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
    )

    mfa_backup_codes_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    mfa_enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE.value,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
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

    # zainteresowania oznaczone jako trenerskie/coach, JSON subset zainteresowania_json.
    # Funkcja dostępna tylko dla planów premium/vip i egzekwowana w backendzie.
    trainer_interests_json: Mapped[str | None] = mapped_column(
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

    nearby_radius_km: Mapped[int] = mapped_column(
        nullable=False,
        default=25,
        server_default="25",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    # Przybliżona lokalizacja do funkcji "W okolicy".
    # Nie przechowujemy precyzyjnego punktu GPS użytkownika.
    location_lat: Mapped[float | None] = mapped_column(
        nullable=True,
        default=None,
    )

    location_lng: Mapped[float | None] = mapped_column(
        nullable=True,
        default=None,
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
    )

    plan_source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    plan_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    plan_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expiry_notice_14d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expiry_notice_7d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


# =====================
# AI USAGE LOG
# limity kosztowych funkcji AI, np. avatarów
# =====================

class AiUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    feature: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        Index("ix_ai_usage_user_feature_created", "user_id", "feature", "created_at"),
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

    kategoria: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
    )

    plan_source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    plan_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    plan_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expiry_notice_14d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan_expiry_notice_7d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    where: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="",
    )

    address: Mapped[str | None] = mapped_column(
        String(240),
        nullable=True,
        default=None,
    )

    location_lat: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
    )

    location_lng: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
    )

    interest_tag: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    interest_tags_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
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


# =====================
# EVENT SAVES (OBSERWOWANE EVENTY)
# =====================

class EventSave(Base):
    __tablename__ = "event_saves"

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
        Index("ix_event_saves_event_user", "event_id", "user_id"),
        UniqueConstraint("event_id", "user_id", name="uq_event_saves_event_user"),
    )


# =====================
# GROUPS
# =====================

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        default=None,
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

    interest_tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    members_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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
        CheckConstraint("members_count >= 0", name="ck_groups_members_count_non_negative"),
    )


# =====================
# GROUP MEMBERSHIPS
# =====================

class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="member",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_group_memberships_user_group"),
    )


# =====================
# MESSAGES (PRIV + GROUP) — MVP TESTERSKI
# =====================

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    sender_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # prywatna wiadomość: sender -> recipient
    recipient_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        default=None,
    )

    # grupowa wiadomość do grupy
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        default=None,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        CheckConstraint("length(content) >= 1", name="ck_messages_content_non_empty"),
        CheckConstraint(
            "(recipient_user_id IS NOT NULL AND group_id IS NULL) OR "
            "(recipient_user_id IS NULL AND group_id IS NOT NULL)",
            name="ck_messages_private_xor_group"
        ),
        Index("ix_messages_private_thread", "sender_user_id", "recipient_user_id", "created_at"),
        Index("ix_messages_group_thread", "group_id", "created_at"),
    )

# =====================
# FRIENDSHIPS / FRIEND REQUESTS
# =====================

class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True)

    requester_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    addressee_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        CheckConstraint("requester_user_id <> addressee_user_id", name="ck_friendships_no_self"),
        CheckConstraint("status IN ('pending','accepted','rejected')", name="ck_friendships_status"),
        UniqueConstraint("requester_user_id", "addressee_user_id", name="uq_friendships_requester_addressee"),
        Index("ix_friendships_addressee_status", "addressee_user_id", "status"),
        Index("ix_friendships_requester_status", "requester_user_id", "status"),
    )


class GroupInvitation(Base):
    __tablename__ = "group_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    inviter_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invitee_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        CheckConstraint("inviter_user_id <> invitee_user_id", name="ck_group_invitations_no_self"),
        CheckConstraint("status IN ('pending','accepted','rejected')", name="ck_group_invitations_status"),
        UniqueConstraint("group_id", "invitee_user_id", name="uq_group_invitations_group_invitee"),
        Index("ix_group_invitations_invitee_status", "invitee_user_id", "status"),
        Index("ix_group_invitations_inviter_status", "inviter_user_id", "status"),
    )

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        Index("ix_password_reset_tokens_user_used", "user_id", "used_at"),
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        Index("ix_email_verification_tokens_user_used", "user_id", "used_at"),
    )


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)

    blocker_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    blocked_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        CheckConstraint("blocker_user_id <> blocked_user_id", name="ck_user_blocks_no_self"),
        UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_user_blocks_blocker_blocked"),
        Index("ix_user_blocks_blocker_created", "blocker_user_id", "created_at"),
        Index("ix_user_blocks_blocked_created", "blocked_user_id", "created_at"),
    )


# =====================
# USER NOTIFICATIONS (MVP)
# =====================

class UserNotification(Base):
    __tablename__ = "user_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    partner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )



# =====================
# DEVICE PUSH TOKENS
# =====================

class DevicePushToken(Base):
    __tablename__ = "device_push_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    device_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        default=None,
    )

    app_version: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        default=None,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        Index("ix_device_push_tokens_user_active", "user_id", "is_active"),
        Index("ix_device_push_tokens_platform_active", "platform", "is_active"),
    )

# =====================
# PROMO / AMBASSADOR CODES
# =====================

class PromoCampaign(Base):
    __tablename__ = "promo_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        default=None,
    )

    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
    )

    benefit_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="discount_percent",
    )

    benefit_value: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    benefit_duration_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    reward_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
    )

    reward_value: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    reward_threshold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    uses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    ios_offer_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    android_promo_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_promo_campaigns_status_valid", "status", "valid_until"),
        Index("ix_promo_campaigns_owner_status", "owner_user_id", "status"),
    )


class PromoRedemption(Base):
    __tablename__ = "promo_redemptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("promo_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    platform: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="reserved",
        index=True,
    )

    store_transaction_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", name="uq_promo_redemptions_campaign_user"),
        Index("ix_promo_redemptions_user_status", "user_id", "status"),
        Index("ix_promo_redemptions_campaign_status", "campaign_id", "status"),
    )

class AmbassadorRewardGrant(Base):
    __tablename__ = "ambassador_reward_grants"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(ForeignKey("promo_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    ambassador_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_months: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_activations_count: Mapped[int] = mapped_column(Integer, nullable=False)

    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    plan_expires_at_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    plan_expires_at_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    __table_args__ = (
        UniqueConstraint("campaign_id", "reward_number", name="uq_ambassador_reward_campaign_number"),
        Index("ix_ambassador_rewards_user_campaign", "ambassador_user_id", "campaign_id"),
    )


class RevenueCatWebhookEvent(Base):
    """Trwały rejestr webhooków RevenueCat.

    Tabela służy do:

    - deduplikacji ponownie dostarczonych zdarzeń,
    - audytu przetwarzania webhooków,
    - diagnostyki błędów,
    - kontrolowanego retry.
    """

    __tablename__ = "revenuecat_webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        unique=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    app_user_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    revenuecat_customer_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    environment: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="received",
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    payload_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        Index(
            "ix_revenuecat_webhook_events_status_received",
            "status",
            "received_at",
        ),
        Index(
            "ix_revenuecat_webhook_events_app_user_status",
            "app_user_id",
            "status",
        ),
    )


class StorePurchase(Base):
    __tablename__ = "store_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    product_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    original_transaction_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    purchase_token: Mapped[str | None] = mapped_column(
        String(260),
        nullable=True,
        default=None,
        index=True,
    )

    environment: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
    )

    revenuecat_app_user_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    revenuecat_customer_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    revenuecat_subscription_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    revenuecat_entitlement_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    entitlement_lookup_key: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        default=None,
        index=True,
    )

    role: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        index=True,
    )

    store: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
        index=True,
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    last_event_id: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
        default=None,
        index=True,
    )

    last_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    plan: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="verified",
        index=True,
    )

    verification_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="test",
    )

    raw_payload: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        UniqueConstraint("platform", "transaction_id", name="uq_store_purchases_platform_transaction"),
        Index("ix_store_purchases_user_status", "user_id", "status"),
    )

