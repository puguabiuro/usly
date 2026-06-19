from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.request_id_middleware import RequestIdMiddleware
# -*- coding: utf-8 -*-

import os
import asyncio
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# --- SENTRY (optional) ---
# Enable by setting SENTRY_DSN in env (Render / local .env).
# ENV can be: local | staging | prod
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

_SENTRY_DSN = os.getenv("SENTRY_DSN")
_ENV = os.getenv("ENV", "local")
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if _SENTRY_DSN:
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        environment=_ENV,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
    )

import json
import math
import hashlib
import secrets

import pyotp
from jose import jwt

import requests
from openai import OpenAI

_openai_client = OpenAI(api_key=_OPENAI_API_KEY) if _OPENAI_API_KEY else None

def _reverse_geocode_city(lat: float, lng: float) -> str | None:
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "zoom": 10,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "usly-app"
        }

        r = requests.get(url, params=params, headers=headers, timeout=3)
        if r.status_code != 200:
            return None

        data = r.json()
        addr = data.get("address", {})

        return (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
        )
    except Exception:
        return None


def ensure_event_reminder_notifications(db, current_time=None):
    now = current_time or datetime.utcnow()
    if getattr(now, "tzinfo", None) is not None:
        now = now.replace(tzinfo=None)

    reminder_rules = [
        ("event_reminder_2d", timedelta(days=2)),
        ("event_reminder_1d", timedelta(days=1)),
    ]

    published_events = (
        db.query(Event)
        .filter(
            Event.status == "published",
            Event.start_at > now,
        )
        .all()
    )

    for event in published_events:
        event_start = event.start_at
        if getattr(event_start, "tzinfo", None) is not None:
            event_start = event_start.astimezone(timezone.utc).replace(tzinfo=None)

        signup_user_ids = {
            user_id
            for (user_id,) in (
                db.query(EventSignup.user_id)
                .filter(EventSignup.event_id == event.id)
                .all()
            )
        }

        saved_user_ids = {
            user_id
            for (user_id,) in (
                db.query(EventSave.user_id)
                .filter(EventSave.event_id == event.id)
                .all()
            )
        }

        target_user_ids = signup_user_ids | saved_user_ids

        for notif_type, delta in reminder_rules:
            if event_start is None:
                continue

            target_from = event_start - delta
            target_to = target_from + timedelta(hours=24)

            if not (target_from <= now < target_to):
                continue

            for target_user_id in target_user_ids:
                exists = (
                    db.query(UserNotification.id)
                    .filter(
                        UserNotification.user_id == target_user_id,
                        UserNotification.event_id == event.id,
                        UserNotification.type == notif_type,
                    )
                    .first()
                )

                if exists:
                    continue

                db.add(
                    UserNotification(
                        user_id=target_user_id,
                        event_id=event.id,
                        partner_user_id=event.partner_user_id,
                        type=notif_type,
                    )
                )


from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import boto3
import firebase_admin
from firebase_admin import credentials, messaging
from botocore.exceptions import ClientError
import os
import aiosmtplib
from email.message import EmailMessage

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
    File,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from backend.api_response import ok, fail
from backend.error_codes import ErrorCode
from backend.db.database import SessionLocal
from backend.models import (
    User,
    UserProfile,
    PartnerProfile,
    Event,
    EventStatus,
    AuditLog,
    EventSignup,
    UserBlock,
    EventSave,
    UserNotification,
    UserStatus,
    UserRole,
    Group,
    GroupMembership,
    Message,
    Friendship,
    GroupInvitation,
    PromoCampaign,
    PromoRedemption,
    AmbassadorRewardGrant,
    StorePurchase,
    DevicePushToken,
    PasswordResetToken,
    EmailVerificationToken,
    AiUsageLog,
)
from backend.schemas import EventCreate, EventUpdate, EventOut, PrivateMessageCreate, GroupMessageCreate, MessageOut
from backend.security import (
    hash_password,
require_role,
create_access_token,
    verify_password,
    get_current_user,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)

app = FastAPI(title="USLY API")
# Sentry middleware (enabled only when SENTRY_DSN is set)
if _SENTRY_DSN:
    app.add_middleware(SentryAsgiMiddleware)

app.add_middleware(RequestIdMiddleware)


ADMIN_LEVEL_OWNER = "owner"
ADMIN_LEVEL_OPERATIONS = "operations"
ADMIN_LEVEL_MODERATION = "moderation"
ADMIN_LEVEL_SUPPORT = "support"

ADMIN_PERMISSION_LEVELS = {
    "reports": {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS, ADMIN_LEVEL_MODERATION, ADMIN_LEVEL_SUPPORT},
    "users": {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS},
    "events": {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS},
    "plans": {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS},
    "account_status": {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS},
    "account_delete": {ADMIN_LEVEL_OWNER},
    "admin_create": {ADMIN_LEVEL_OWNER},
    "admin_manage": {ADMIN_LEVEL_OWNER},
}


def _admin_level(current_user: User) -> str:
    return (current_user.admin_level or ADMIN_LEVEL_OWNER).strip().lower() if current_user.role == "admin" else ""


def require_admin_permission(current_user: User, permission: str) -> None:
    level = _admin_level(current_user)
    allowed = ADMIN_PERMISSION_LEVELS.get(permission, {ADMIN_LEVEL_OWNER})
    if level not in allowed:
        raise HTTPException(status_code=403, detail="ADMIN_PERMISSION_DENIED")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# ---- CORS (prod: konkretna domena, bez '*') ----
# Na Render ustawisz: FRONTEND_ORIGIN=https://usly-app.onrender.com
# Lokalnie moesz ustawi: FRONTEND_ORIGIN=http://localhost:5173
frontend_origin = os.getenv("FRONTEND_ORIGIN", "")

allowed_origins = [
    "null",  # allow file:// frontend during local/mobile dev
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "capacitor://localhost",
    "ionic://localhost",
    "https://localhost",
    "https://uslyapp.pl",
    "https://www.uslyapp.pl",
    "https://usly-backend-v2.onrender.com",
]

if frontend_origin:
    allowed_origins.append(frontend_origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



USER_INTEREST_LIMITS = {
    "free": 5,
    "plus": 10,
    "premium": 20,
    "vip": None,
}

USER_TRAINER_INTEREST_LIMITS = {
    "premium": 2,
    "vip": 5,
}

PARTNER_ACTIVE_EVENT_LIMITS = {
    "free": 2,
    "pro": 5,
    "premium": None,
    "enterprise": None,
}


PARTNER_EVENT_INTEREST_TAG_LIMITS = {
    "free": 1,
    "pro": 2,
    "premium": 5,
    "enterprise": 10,
}


def _partner_event_interest_tag_limit(plan: str | None) -> int:
    safe_plan = str(plan or "free").strip().lower()
    return PARTNER_EVENT_INTEREST_TAG_LIMITS.get(safe_plan, PARTNER_EVENT_INTEREST_TAG_LIMITS["free"])


def _normalize_event_interest_tags(raw_tags, fallback_tag: str | None = None) -> list[str]:
    source = raw_tags
    if source is None:
        source = [fallback_tag] if fallback_tag else []

    if isinstance(source, str):
        source = [source]

    result = []
    seen = set()
    for item in source or []:
        tag = str(item or "").strip().lstrip("#")
        if not tag:
            continue
        if len(tag) < 2 or len(tag) > 40:
            raise HTTPException(status_code=422, detail="INVALID_EVENT_INTEREST_TAG")
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(tag)

    if not result and fallback_tag:
        fallback = str(fallback_tag or "").strip().lstrip("#")
        if fallback:
            result.append(fallback)

    if not result:
        raise HTTPException(status_code=422, detail="EVENT_INTEREST_TAG_REQUIRED")

    return result




USER_PLAN_RANKS = {
    "free": 0,
    "plus": 1,
    "premium": 2,
    "vip": 3,
}

PARTNER_PLAN_RANKS = {
    "free": 0,
    "pro": 1,
    "premium": 2,
    "enterprise": 3,
}


def _apply_plan_limits_after_downgrade(db, user: User, target_plan: str, now: datetime | None = None) -> dict:
    current_time = now or datetime.utcnow()
    safe_plan = (target_plan or "free").strip().lower()

    result = {
        "target_plan": safe_plan,
        "interests_trimmed_from": None,
        "interests_trimmed_to": None,
        "trainer_interests_trimmed_from": None,
        "trainer_interests_trimmed_to": None,
        "trainer_interests_disabled": False,
        "events_moved_to_draft": [],
    }

    if user.role == UserRole.PARTNER.value:
        event_limit = PARTNER_ACTIVE_EVENT_LIMITS.get(safe_plan, PARTNER_ACTIVE_EVENT_LIMITS["free"])
        if event_limit is None:
            return result

        now_utc = datetime.now(timezone.utc)
        published_events = (
            db.query(Event)
            .filter(Event.partner_user_id == user.id)
            .filter(Event.status == EventStatus.PUBLISHED.value)
            .filter(Event.end_at >= now_utc)
            .order_by(Event.start_at.asc(), Event.id.asc())
            .all()
        )

        keep_ids = {event.id for event in published_events[:event_limit]}
        to_draft = [event for event in published_events if event.id not in keep_ids]

        for event in to_draft:
            event.status = EventStatus.DRAFT.value
            event.updated_at = current_time
            db.add(event)
            result["events_moved_to_draft"].append(event.id)

        return result

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return result

    interest_limit = USER_INTEREST_LIMITS.get(safe_plan, USER_INTEREST_LIMITS["free"])
    interests = []
    if profile.zainteresowania_json:
        try:
            interests = json.loads(profile.zainteresowania_json) or []
        except Exception:
            interests = []

    if interest_limit is not None and len(interests) > interest_limit:
        result["interests_trimmed_from"] = len(interests)
        interests = interests[:interest_limit]
        result["interests_trimmed_to"] = len(interests)
        profile.zainteresowania_json = json.dumps(interests, ensure_ascii=False)

    trainer_limit = USER_TRAINER_INTEREST_LIMITS.get(safe_plan, 0)
    trainer_interests = []
    if profile.trainer_interests_json:
        try:
            trainer_interests = json.loads(profile.trainer_interests_json) or []
        except Exception:
            trainer_interests = []

    if trainer_limit <= 0 and trainer_interests:
        result["trainer_interests_trimmed_from"] = len(trainer_interests)
        result["trainer_interests_trimmed_to"] = 0
        result["trainer_interests_disabled"] = True
        profile.trainer_interests_json = None
    elif trainer_limit > 0 and len(trainer_interests) > trainer_limit:
        result["trainer_interests_trimmed_from"] = len(trainer_interests)
        trainer_interests = trainer_interests[:trainer_limit]
        result["trainer_interests_trimmed_to"] = len(trainer_interests)
        profile.trainer_interests_json = json.dumps(trainer_interests, ensure_ascii=False)

    profile.updated_at = current_time
    db.add(profile)
    return result


def _expire_profile_plan_if_needed(db, user: User, profile, now: datetime | None = None) -> dict | None:
    current_time = now or datetime.utcnow()
    expires_at = getattr(profile, "plan_expires_at", None)

    if not expires_at:
        return None

    compare_expires_at = expires_at
    compare_now = current_time

    if getattr(compare_expires_at, "tzinfo", None) is not None:
        compare_expires_at = compare_expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    if getattr(compare_now, "tzinfo", None) is not None:
        compare_now = compare_now.astimezone(timezone.utc).replace(tzinfo=None)

    current_plan = str(getattr(profile, "plan", None) or "free").strip().lower()
    current_status = str(getattr(profile, "plan_status", None) or "active").strip().lower()

    if current_plan == "free" or current_status == "expired" or compare_expires_at > compare_now:
        return None

    previous_plan = current_plan

    profile.plan = "free"
    profile.plan_source = "system"
    profile.plan_status = "expired"
    profile.plan_updated_at = current_time
    profile.updated_at = current_time
    db.add(profile)

    limits_result = _apply_plan_limits_after_downgrade(db, user, "free", current_time)

    db.add(AuditLog(
        user_id=user.id,
        action="plan_expired_auto_downgrade",
        details=f"previous_plan={previous_plan}; new_plan=free; expired_at={expires_at.isoformat() if expires_at else '-'}; downgrade_limits={limits_result or '-'}",
    ))

    return {
        "previous_plan": previous_plan,
        "new_plan": "free",
        "plan_status": "expired",
        "plan_expires_at": expires_at.isoformat() if expires_at else None,
        "downgrade_limits": limits_result,
    }


def _normalize_datetime_for_compare(value: datetime | None) -> datetime | None:
    if not value:
        return None
    if getattr(value, "tzinfo", None) is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _plan_expiry_notice_copy(role: str, plan: str, days_left: int, expires_at: datetime) -> tuple[str, str]:
    role_label = "Organizatora" if role == "partner" else "Towarzysza"
    date_label = expires_at.strftime("%Y-%m-%d")

    subject = f"USLY — Twój plan wygasa za {days_left} dni"
    body = (
        f"Cześć,\n\n"
        f"Twój plan {role_label} w USLY ({plan.upper()}) wygasa za {days_left} dni, czyli {date_label}.\n\n"
        "Jeśli plan nie zostanie przedłużony, po wygaśnięciu konto zostanie automatycznie przeniesione na plan FREE, "
        "a limity planu FREE zostaną zastosowane zgodnie z zasadami USLY.\n\n"
        "Dane nie zostaną usunięte, ale część płatnych możliwości może zostać ograniczona po zakończeniu planu.\n\n"
        "Zespół USLY"
    )
    return subject, body


async def _send_plan_expiry_notices(db, now: datetime | None = None) -> dict:
    current_time = now or datetime.utcnow()
    compare_now = _normalize_datetime_for_compare(current_time) or datetime.utcnow()
    sent = {"user_14d": 0, "user_7d": 0, "partner_14d": 0, "partner_7d": 0}

    rules = [
        (14, "plan_expiry_notice_14d_sent_at"),
        (7, "plan_expiry_notice_7d_sent_at"),
    ]

    profile_sets = [
        ("user", UserProfile, "user"),
        ("partner", PartnerProfile, "partner"),
    ]

    for role, model, counter_prefix in profile_sets:
        profiles = (
            db.query(model)
            .join(User, User.id == model.user_id)
            .filter(model.plan_expires_at.isnot(None))
            .filter(model.plan != "free")
            .all()
        )

        for profile in profiles:
            expires_at = _normalize_datetime_for_compare(getattr(profile, "plan_expires_at", None))
            if not expires_at:
                continue

            current_status = str(getattr(profile, "plan_status", None) or "active").strip().lower()
            if current_status in {"expired", "cancelled", "inactive"}:
                continue

            days_until_expiry = (expires_at.date() - compare_now.date()).days

            for days_left, sent_field in rules:
                if days_until_expiry != days_left:
                    continue
                if getattr(profile, sent_field, None):
                    continue

                user = db.query(User).filter(User.id == profile.user_id).first()
                if not user or not user.email:
                    continue

                plan = str(getattr(profile, "plan", None) or "paid").strip().lower()
                subject, body = _plan_expiry_notice_copy(role, plan, days_left, expires_at)

                await send_user_email(user.email, subject, body)

                setattr(profile, sent_field, current_time)
                profile.updated_at = current_time
                db.add(profile)
                db.add(AuditLog(
                    user_id=user.id,
                    action=f"plan_expiry_notice_{days_left}d_sent",
                    details=f"role={role}; plan={plan}; expires_at={expires_at.isoformat()}",
                ))
                sent[f"{counter_prefix}_{days_left}d"] += 1

    db.commit()
    return sent


def _expire_due_plans(db, now: datetime | None = None) -> dict:
    current_time = now or datetime.utcnow()
    result = {"user": 0, "partner": 0}

    profile_sets = [
        ("user", UserProfile),
        ("partner", PartnerProfile),
    ]

    for role, model in profile_sets:
        profiles = (
            db.query(model)
            .join(User, User.id == model.user_id)
            .filter(model.plan_expires_at.isnot(None))
            .filter(model.plan != "free")
            .all()
        )

        for profile in profiles:
            user = db.query(User).filter(User.id == profile.user_id).first()
            if not user:
                continue

            expired = _expire_profile_plan_if_needed(db, user, profile, current_time)
            if expired:
                result[role] += 1

    if any(result.values()):
        db.commit()

    return result


def _add_months_to_datetime(value: datetime, months: int) -> datetime:
    if months <= 0:
        return value

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1

    days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(value.day, days_in_month[month - 1])

    return value.replace(year=year, month=month, day=day)


def _grant_ambassador_rewards_if_needed(db, campaign: PromoCampaign, now: datetime | None = None) -> int:
    current_time = now or datetime.utcnow()

    if not campaign.owner_user_id:
        return 0

    if str(campaign.reward_type or "none").lower() != "vip_months":
        return 0

    threshold = int(campaign.reward_threshold or 0)
    reward_months = int(campaign.reward_value or 0)

    if threshold < 10 or reward_months <= 0:
        return 0

    paid_activations_count = (
        db.query(PromoRedemption)
        .filter(
            PromoRedemption.campaign_id == campaign.id,
            PromoRedemption.status == "activated",
        )
        .count()
    )

    reward_target_count = paid_activations_count // threshold
    if reward_target_count <= 0:
        return 0

    existing_reward_numbers = {
        reward_number
        for (reward_number,) in (
            db.query(AmbassadorRewardGrant.reward_number)
            .filter(AmbassadorRewardGrant.campaign_id == campaign.id)
            .all()
        )
    }

    owner = db.query(User).filter(User.id == campaign.owner_user_id).first()
    if not owner:
        return 0

    if owner.role == UserRole.PARTNER.value:
        owner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == owner.id).first()
        reward_plan = "premium"
    else:
        owner_profile = db.query(UserProfile).filter(UserProfile.user_id == owner.id).first()
        reward_plan = "vip"

    if not owner_profile:
        return 0

    grants_created = 0

    for reward_number in range(1, reward_target_count + 1):
        if reward_number in existing_reward_numbers:
            continue

        before = getattr(owner_profile, "plan_expires_at", None)
        base = before if before and before > current_time else current_time
        after = _add_months_to_datetime(base, reward_months)

        owner_profile.plan = reward_plan
        owner_profile.plan_source = "ambassador"
        owner_profile.plan_status = "active"
        owner_profile.plan_updated_at = current_time
        owner_profile.plan_expires_at = after
        owner_profile.updated_at = current_time

        db.add(owner_profile)
        db.add(AmbassadorRewardGrant(
            campaign_id=campaign.id,
            ambassador_user_id=owner.id,
            threshold=threshold,
            reward_number=reward_number,
            reward_months=reward_months,
            paid_activations_count=paid_activations_count,
            granted_at=current_time,
            plan_expires_at_before=before,
            plan_expires_at_after=after,
        ))
        db.add(AuditLog(
            user_id=owner.id,
            action="ambassador_reward_granted",
            details=f"campaign_id={campaign.id}; code={campaign.code}; reward_number={reward_number}; threshold={threshold}; reward_months={reward_months}; paid_activations_count={paid_activations_count}; expires_before={before.isoformat() if before else '-'}; expires_after={after.isoformat() if after else '-'}",
        ))
        grants_created += 1

    return grants_created


def _activate_reserved_promo_redemptions_after_paid_plan(db, user: User, now: datetime | None = None) -> tuple[list[int], int]:
    current_time = now or datetime.utcnow()
    activated_redemption_ids: list[int] = []
    ambassador_grants_created = 0

    if not user or not user.id:
        return activated_redemption_ids, ambassador_grants_created

    reserved_redemptions = (
        db.query(PromoRedemption)
        .join(PromoCampaign, PromoCampaign.id == PromoRedemption.campaign_id)
        .filter(
            PromoRedemption.user_id == user.id,
            PromoRedemption.status == "reserved",
            PromoCampaign.status == "active",
        )
        .all()
    )

    for redemption in reserved_redemptions:
        campaign = db.query(PromoCampaign).filter(PromoCampaign.id == redemption.campaign_id).first()
        if not campaign:
            continue
        if campaign.target_role != "both" and campaign.target_role != user.role:
            continue

        redemption.status = "activated"
        redemption.activated_at = current_time
        db.add(redemption)
        db.flush()
        activated_redemption_ids.append(redemption.id)
        ambassador_grants_created += _grant_ambassador_rewards_if_needed(db, campaign, current_time)

    return activated_redemption_ids, ambassador_grants_created



def _init_firebase_admin() -> bool:
    service_account_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
    if not service_account_b64:
        print("FIREBASE ADMIN: disabled (missing FIREBASE_SERVICE_ACCOUNT_JSON_BASE64)")
        return False

    if firebase_admin._apps:
        return True

    try:
        service_account_json = base64.b64decode(service_account_b64).decode("utf-8")
        service_account_info = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        print("FIREBASE ADMIN: initialized")
        return True
    except Exception as exc:
        print("FIREBASE ADMIN INIT ERROR:", exc)
        return False



# Healthcheck (for deploy / monitoring)

async def _plan_expiry_notice_scheduler() -> None:
    # Lightweight MVP scheduler: run once after backend startup, then once daily.
    while True:
        db = SessionLocal()
        try:
            expired_result = _expire_due_plans(db)
            if any(expired_result.values()):
                print("PLANS AUTO-DOWNGRADED:", expired_result)

            result = await _send_plan_expiry_notices(db)
            if any(result.values()):
                print("PLAN EXPIRY NOTICES SENT:", result)
        except Exception as exc:
            print("PLAN EXPIRY NOTICE SCHEDULER ERROR:", exc)
        finally:
            db.close()

        await asyncio.sleep(24 * 60 * 60)


@app.on_event("startup")
async def start_plan_expiry_notice_scheduler() -> None:
    _init_firebase_admin()
    asyncio.create_task(_plan_expiry_notice_scheduler())


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/admin/r2/health")
def admin_r2_health(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "plans")

    if not r2_enabled():
        return ok({"enabled": False})

    try:
        client = r2_client()
        client.head_bucket(Bucket=R2_BUCKET_NAME)
        return ok({
            "enabled": True,
            "bucket": R2_BUCKET_NAME,
            "public_base_url": R2_PUBLIC_BASE_URL,
        })
    except ClientError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "R2_HEALTHCHECK_FAILED",
                "message": str(exc),
            },
        )

class AdminPushTestRequest(BaseModel):
    user_id: int
    title: str = Field(default="USLY", min_length=1, max_length=80)
    body: str = Field(default="Test push notification", min_length=1, max_length=180)


@app.post("/admin/push/test")
def admin_push_test(
    payload: AdminPushTestRequest,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "plans")

    db = SessionLocal()
    try:
        token_count = (
            db.query(DevicePushToken)
            .filter(DevicePushToken.user_id == payload.user_id)
            .filter(DevicePushToken.is_active == True)
            .count()
        )
        sent = send_push_to_user(
            db,
            payload.user_id,
            payload.title,
            payload.body,
            {"type": "admin_push_test"},
        )
        return ok({"sent": sent, "token_count": token_count})
    finally:
        db.close()


@app.post("/admin/mfa/setup")
def admin_mfa_setup(
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    if _admin_level(current_user) != "owner":
        raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.role != UserRole.ADMIN.value:
            raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

        secret = _generate_mfa_secret()
        backup_codes, backup_code_hashes = _generate_mfa_backup_codes()

        user.mfa_secret = secret
        user.mfa_backup_codes_hash = json.dumps(backup_code_hashes)
        user.mfa_enabled = False
        user.mfa_enabled_at = None
        db.add(user)
        db.commit()

        label = user.admin_display_name or user.email
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            name=label,
            issuer_name="USLY Admin",
        )

        _audit(db, action="ADMIN_MFA_SETUP_STARTED", request=request, user_id=user.id, details=None)

        return ok({
            "provisioning_uri": provisioning_uri,
            "secret": secret,
            "backup_codes": backup_codes,
            "mfa_enabled": False,
        })
    finally:
        db.close()



class AdminMfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12)


class LoginMfaRequest(BaseModel):
    mfa_token: str = Field(min_length=20, max_length=1000)
    code: str = Field(min_length=6, max_length=12)


@app.post("/admin/mfa/verify")
def admin_mfa_verify(
    payload: AdminMfaVerifyRequest,
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    if _admin_level(current_user) != "owner":
        raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.role != UserRole.ADMIN.value:
            raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

        if not _verify_mfa_code(user.mfa_secret, payload.code):
            _audit(db, action="ADMIN_MFA_VERIFY_FAIL", request=request, user_id=user.id, details=None)
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        user.mfa_enabled = True
        user.mfa_enabled_at = datetime.utcnow()
        db.add(user)
        db.commit()

        _audit(db, action="ADMIN_MFA_ENABLED", request=request, user_id=user.id, details=None)

        return ok({"mfa_enabled": True})
    finally:
        db.close()


@app.post("/admin/mfa/disable")
def admin_mfa_disable(
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    if _admin_level(current_user) != "owner":
        raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.role != UserRole.ADMIN.value:
            raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes_hash = None
        user.mfa_enabled_at = None
        db.add(user)
        db.commit()

        _audit(db, action="ADMIN_MFA_DISABLED", request=request, user_id=user.id, details=None)

        return ok({"mfa_enabled": False})
    finally:
        db.close()


@app.post("/admin/mfa/backup-codes/regenerate")
def admin_mfa_regenerate_backup_codes(
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    if _admin_level(current_user) != "owner":
        raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.role != UserRole.ADMIN.value:
            raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

        if not user.mfa_enabled or not user.mfa_secret:
            raise ApiException(status_code=400, code=ErrorCode.INVALID_INPUT)

        backup_codes, backup_code_hashes = _generate_mfa_backup_codes()
        user.mfa_backup_codes_hash = json.dumps(backup_code_hashes)
        db.add(user)
        db.commit()

        _audit(db, action="ADMIN_MFA_BACKUP_CODES_REGENERATED", request=request, user_id=user.id, details=None)

        return ok({"backup_codes": backup_codes})
    finally:
        db.close()




# =========================
# MVP: JOIN EVENT
# =========================
@app.post("/events/{event_id}/join")
def join_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user", "partner")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnie
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) musi by published
        if event.status != "published":
            raise HTTPException(status_code=409, detail="EVENT_NOT_PUBLISHED")

        # 3) capacity (jeli ustawione)
        if event.capacity is not None:
            current_count = (
                db.query(EventSignup)
                .filter(EventSignup.event_id == event_id)
                .count()
            )

            if current_count >= event.capacity:
                raise HTTPException(status_code=409, detail="EVENT_FULL")

        # 4) czy user ju zapisany
        existing = (
            db.query(EventSignup)
            .filter(
                EventSignup.event_id == event_id,
                EventSignup.user_id == current_user.id,
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=409, detail="ALREADY_JOINED")

        # 5) zapis
        signup = EventSignup(
            event_id=event_id,
            user_id=current_user.id,
        )

        db.add(signup)
        db.commit()

        # 6) audit
        _audit(
            db,
            action="EVENT_JOIN",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"joined": True, "event_id": event_id})

    finally:
        db.close()
# =========================
# MVP: LEAVE EVENT
# =========================


@app.post("/events/{event_id}/save")
def save_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.status != "published":
            raise HTTPException(status_code=409, detail="EVENT_NOT_PUBLISHED")

        existing = (
            db.query(EventSave)
            .filter(
                EventSave.event_id == event_id,
                EventSave.user_id == current_user.id,
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=409, detail="ALREADY_SAVED")

        saved = EventSave(
            event_id=event_id,
            user_id=current_user.id,
        )

        db.add(saved)
        db.commit()

        _audit(
            db,
            action="EVENT_SAVE",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"saved": True, "event_id": event_id})

    finally:
        db.close()


@app.delete("/events/{event_id}/join")
def leave_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnie
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko dla published (trzymamy spjnie z join)
        if event.status != "published":
            raise HTTPException(status_code=409, detail="EVENT_NOT_PUBLISHED")

        # 3) musi istnie zapis
        signup = (
            db.query(EventSignup)
            .filter(
                EventSignup.event_id == event_id,
                EventSignup.user_id == current_user.id,
            )
            .first()
        )
        if not signup:
            raise HTTPException(status_code=409, detail="NOT_JOINED")

        # 4) usu zapis
        db.delete(signup)
        db.commit()

        # 5) audit
        _audit(
            db,
            action="EVENT_LEAVE",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"left": True, "event_id": event_id})

    finally:
        db.close()


# =========================
# Static uploads
# =========================
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads/static", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# =========================
# Cloudflare R2 media storage
# =========================
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "").strip()
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")

def r2_enabled() -> bool:
    return all([
        R2_ACCOUNT_ID,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        R2_BUCKET_NAME,
        R2_PUBLIC_BASE_URL,
    ])


def require_r2_or_allow_local_uploads() -> bool:
    if r2_enabled():
        return True

    if _ENV.strip().lower() == "prod":
        raise HTTPException(status_code=503, detail="R2_STORAGE_NOT_CONFIGURED")

    return False


def r2_client():
    if not r2_enabled():
        return None

    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_media_to_r2(key: str, content: bytes, content_type: str) -> str:
    client = r2_client()
    if not client:
        raise RuntimeError("R2 is not configured")

    client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=content_type,
    )
    return f"{R2_PUBLIC_BASE_URL}/{key}"


# =========================
# Static frontend / admin
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def _serve_frontend_index_file():
    return FileResponse(
        FRONTEND_DIR / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/", include_in_schema=False)
def serve_landing_page():
    return FileResponse(
        FRONTEND_DIR / "landing.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/regulamin", include_in_schema=False)
def serve_terms_page():
    return FileResponse(
        FRONTEND_DIR / "regulamin.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/polityka-prywatnosci", include_in_schema=False)
def serve_privacy_page():
    return FileResponse(
        FRONTEND_DIR / "polityka-prywatnosci.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/kontakt", include_in_schema=False)
def serve_contact_page():
    return FileResponse(
        FRONTEND_DIR / "kontakt.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/app", include_in_schema=False)
@app.get("/app/", include_in_schema=False)
def serve_frontend_app():
    return _serve_frontend_index_file()


@app.get("/admin.html", include_in_schema=False)
def serve_admin_html():
    return FileResponse(FRONTEND_DIR / "admin.html")

@app.get("/.well-known/assetlinks.json", include_in_schema=False)
def serve_android_assetlinks():
    android_package = os.getenv("ANDROID_PACKAGE_NAME", "com.usly.app").strip() or "com.usly.app"
    sha256_fingerprints = [
        item.strip()
        for item in os.getenv("ANDROID_SHA256_CERT_FINGERPRINTS", "").split(",")
        if item.strip()
    ]

    if not sha256_fingerprints:
        return JSONResponse([], media_type="application/json")

    return JSONResponse([
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": android_package,
                "sha256_cert_fingerprints": sha256_fingerprints,
            },
        }
    ], media_type="application/json")


@app.get("/.well-known/apple-app-site-association", include_in_schema=False)
def serve_apple_app_site_association():
    apple_team_id = os.getenv("APPLE_TEAM_ID", "").strip()
    ios_bundle_id = os.getenv("IOS_BUNDLE_ID", "com.usly.app").strip() or "com.usly.app"
    app_id = f"{apple_team_id}.{ios_bundle_id}" if apple_team_id else ""

    details = []
    if app_id:
        details.append({
            "appIDs": [app_id],
            "components": [
                {"/": "/verify-email*"},
                {"/": "/reset-password*"},
            ],
        })

    return JSONResponse({
        "applinks": {
            "details": details,
        },
    }, media_type="application/json")


@app.get("/app.js", include_in_schema=False)
def serve_app_js():
    return FileResponse(FRONTEND_DIR / "app.js")

@app.get("/api.js", include_in_schema=False)
def serve_api_js():
    return FileResponse(FRONTEND_DIR / "api.js")

@app.get("/style.css", include_in_schema=False)
def serve_style_css():
    return FileResponse(FRONTEND_DIR / "style.css")

@app.get("/admin.js", include_in_schema=False)
def serve_admin_js():
    return FileResponse(FRONTEND_DIR / "admin.js")

@app.get("/admin.css", include_in_schema=False)
def serve_admin_css():
    return FileResponse(FRONTEND_DIR / "admin.css")

@app.get("/USLY logo.png", include_in_schema=False)
def serve_usly_logo():
    return FileResponse(FRONTEND_DIR / "USLY logo.png")


# =========================
# Exceptions
# =========================
from backend.exceptions import ApiException



@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    _rid = getattr(request.state, "request_id", None)
    headers = {"x-request-id": _rid} if _rid else {}
    lang = request.headers.get("accept-language")
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content=fail(code=exc.code, message=exc.message, details=exc.details, lang=lang),
    )



from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # language from headers (same as ApiException handler)
    lang = request.headers.get("accept-language")

    # Map known HTTPException.detail strings to ErrorCode, otherwise treat as INTERNAL_ERROR
    code = ErrorCode.INTERNAL_ERROR
    if isinstance(exc.detail, str):
        try:
            code = ErrorCode(exc.detail)
        except Exception:
            code = ErrorCode.INTERNAL_ERROR

    return JSONResponse(
        status_code=exc.status_code,
        content=fail(code=code, lang=lang),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    lang = request.headers.get("accept-language")
    return JSONResponse(
        status_code=422,
        content=fail(code=ErrorCode.VALIDATION_ERROR, details=exc.errors(), lang=lang),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _rid = getattr(request.state, "request_id", None)
    headers = {"x-request-id": _rid} if _rid else {}
    lang = request.headers.get("accept-language")
    return JSONResponse(
        status_code=500,
        headers=headers,
        content=fail(code=ErrorCode.INTERNAL_ERROR, lang=lang),
    )


# =========================
# AUDIT HELPERS
# =========================
def _get_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _audit(db, *, action: str, request: Request, user_id: int | None, details: str | None = None) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip=_get_ip(request),
        user_agent=_get_user_agent(request),
        details=details,
    )
    db.add(log)
    db.commit()


def _generate_mfa_secret() -> str:
    return pyotp.random_base32()


def _verify_mfa_code(secret: str | None, code: str | None) -> bool:
    if not secret or not code:
        return False
    normalized = str(code).strip().replace(" ", "")
    if not normalized.isdigit() or len(normalized) != 6:
        return False
    return pyotp.TOTP(secret).verify(normalized, valid_window=1)


def _hash_mfa_backup_code(code: str) -> str:
    return hashlib.sha256(str(code).strip().encode("utf-8")).hexdigest()


def _generate_mfa_backup_codes(count: int = 8) -> tuple[list[str], list[str]]:
    raw_codes = [secrets.token_hex(4).upper() for _ in range(count)]
    hashed_codes = [_hash_mfa_backup_code(code) for code in raw_codes]
    return raw_codes, hashed_codes


def _consume_mfa_backup_code(user: User, code: str | None) -> bool:
    if not user or not code or not user.mfa_backup_codes_hash:
        return False
    try:
        stored_hashes = json.loads(user.mfa_backup_codes_hash)
    except Exception:
        return False
    if not isinstance(stored_hashes, list):
        return False

    code_hash = _hash_mfa_backup_code(code)
    if code_hash not in stored_hashes:
        return False

    stored_hashes.remove(code_hash)
    user.mfa_backup_codes_hash = json.dumps(stored_hashes)
    return True


def _create_mfa_challenge_token(user_id: int) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "purpose": "admin_mfa",
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_mfa_challenge_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
    if payload.get("purpose") != "admin_mfa":
        return None
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None


def _is_at_least_18(dob: date) -> bool:
    today = date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years >= 18


# =========================
# AUTH  REGISTER
# =========================
# UWAGA: RegisterRequest/RegisterResponse musz istnie w Twoim projekcie.
# Jeli masz je w innym pliku, zmie import tutaj.
from backend.schemas import RegisterRequest, RegisterResponse  # <- jeli masz gdzie indziej, podmie


@app.post("/auth/register")
@limiter.limit("3/minute")
def register(request: Request, payload: RegisterRequest):
    db = SessionLocal()
    try:
        role_value = "partner" if payload.role == "partner" else "user"

        # 18+ tylko dla Towarzysza
        if role_value == "user":
            if not payload.dob:
                raise ApiException(status_code=422, code=ErrorCode.INVALID_INPUT, message="Data urodzenia jest wymagana.")
            if not _is_at_least_18(payload.dob):
                raise ApiException(status_code=403, code=ErrorCode.AGE_TOO_LOW)

        # LEGAL — wymagane zgody
        if not payload.accept_terms or not payload.accept_privacy:
            raise ApiException(status_code=422, code=ErrorCode.TERMS_REQUIRED)

        existing = db.query(User).filter(User.email == str(payload.email)).first()
        if existing:
            raise ApiException(status_code=409, code=ErrorCode.EMAIL_ALREADY_EXISTS)

        # UWAGA: UserRole i UserStatus muszą istnieć w Twoim projekcie.
        user = User(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            dob=payload.dob,
            terms_accepted_at=datetime.utcnow(),
            terms_version="v1",
            privacy_version="v1",
            role=role_value,
            status=UserStatus.ACTIVE.value,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        try:
            import asyncio

            verify_token = str(uuid4())
            verify_row = EmailVerificationToken(
                user_id=user.id,
                token=verify_token,
                expires_at=datetime.utcnow().replace(microsecond=0) + __import__("datetime").timedelta(hours=24),
                used_at=None,
            )
            db.add(verify_row)
            db.commit()

            verify_link = _build_email_verify_link(verify_token)

            verify_subject = "USLY — potwierdź adres email"
            verify_body = (
                "Potwierdź swój adres email, aby zabezpieczyć konto USLY.\n\n"
                f"Otwórz ten link:\n{verify_link}\n\n"
                "Link jest jednorazowy i ważny przez 24 godziny.\n\n"
                "Jeśli to nie Ty zakładałaś/zakładałeś konto w USLY, zignoruj tę wiadomość albo napisz do nas:\n"
                "kontakt@uslyapp.pl"
            )

            if role_value == "partner":
                welcome_subject = "Witaj w USLY ✨"
                welcome_body = (
                    "Cieszymy się, że Twoje miejsce dołączyło do USLY.\n\n"
                    "Od teraz możesz tworzyć wydarzenia, budować społeczność wokół swojej marki i docierać do nowych osób w okolicy.\n\n"
                    "Na dobry start:\n"
                    "• uzupełnij profil miejsca\n"
                    "• dodaj pierwsze wydarzenie\n"
                    "• sprawdź możliwości promocji i planów\n\n"
                    "Jeśli potrzebujesz pomocy lub chcesz porozmawiać o pakiecie Enterprise, napisz do nas:\n"
                    "kontakt@uslyapp.pl\n\n"
                    "Do zobaczenia w USLY ✨"
                )
            else:
                welcome_subject = "Witaj w USLY ✨"
                welcome_body = (
                    "Super, że jesteś z nami.\n\n"
                    "USLY pomaga poznawać ludzi, wydarzenia i miejsca dopasowane do Twoich zainteresowań.\n\n"
                    "Na dobry start:\n"
                    "• dodaj zainteresowania\n"
                    "• uzupełnij profil\n"
                    "• stwórz swój AI Avatar\n"
                    "• odkrywaj wydarzenia i osoby w okolicy\n\n"
                    "Jeśli potrzebujesz pomocy, napisz do nas:\n"
                    "kontakt@uslyapp.pl\n\n"
                    "Miło Cię widzieć w USLY ✨"
                )

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_user_email(user.email, welcome_subject, welcome_body))
                loop.create_task(send_user_email(user.email, verify_subject, verify_body))
            except RuntimeError:
                asyncio.run(send_user_email(user.email, welcome_subject, welcome_body))
                asyncio.run(send_user_email(user.email, verify_subject, verify_body))
        except Exception as mail_error:
            print("WELCOME MAIL ERROR:", mail_error)

        return ok(
            RegisterResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                status=user.status,
            ).model_dump()
        )
    except Exception as e:
        print("REGISTER ERROR:", e)
        raise
    finally:
        db.close()


# =========================
# AUTH  VERIFY EMAIL
# =========================
def _build_email_verify_link(token: str) -> str:
    verify_link_base = os.getenv("EMAIL_VERIFY_LINK_BASE", "usly://verify-email").strip() or "usly://verify-email"
    verify_separator = "&" if "?" in verify_link_base else "?"
    return f"{verify_link_base}{verify_separator}token={token}"


def _verify_email_token(db, token: str):
    token_value = str(token or "").strip()
    if not token_value:
        raise HTTPException(status_code=400, detail="EMAIL_VERIFY_TOKEN_REQUIRED")

    verify_row = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token == token_value)
        .first()
    )

    if not verify_row or verify_row.used_at is not None:
        raise HTTPException(status_code=400, detail="EMAIL_VERIFY_TOKEN_INVALID")

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = verify_row.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at and expires_at < now_utc:
        raise HTTPException(status_code=400, detail="EMAIL_VERIFY_TOKEN_EXPIRED")

    user = db.query(User).filter(User.id == verify_row.user_id).first()
    if not user or user.status == UserStatus.DELETED.value:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    now = now_utc
    user.email_verified_at = user.email_verified_at or now
    verify_row.used_at = now

    db.add(user)
    db.add(verify_row)
    db.commit()

    return {"verified": True}


@app.post("/auth/resend-verification-email")
def resend_verification_email(current_user: User = Depends(require_role("user", "partner"))):
    if getattr(current_user, "email_verified_at", None):
        return ok({"sent": False, "already_verified": True})

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or user.status == UserStatus.DELETED.value:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        if getattr(user, "email_verified_at", None):
            return ok({"sent": False, "already_verified": True})

        now = datetime.utcnow().replace(microsecond=0)

        (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.used_at.is_(None),
            )
            .delete(synchronize_session=False)
        )

        verify_token = str(uuid4())
        verify_row = EmailVerificationToken(
            user_id=user.id,
            token=verify_token,
            expires_at=now + timedelta(hours=24),
            used_at=None,
        )
        db.add(verify_row)
        db.commit()

        verify_link = _build_email_verify_link(verify_token)
        verify_subject = "USLY — potwierdź adres email"
        verify_body = (
            "Potwierdź swój adres email, aby zabezpieczyć konto USLY.\n\n"
            f"Otwórz ten link:\n{verify_link}\n\n"
            "Link jest jednorazowy i ważny przez 24 godziny.\n\n"
            "Jeśli to nie Ty prosisz o link weryfikacyjny, zignoruj tę wiadomość albo napisz do nas:\n"
            "kontakt@uslyapp.pl"
        )

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_user_email(user.email, verify_subject, verify_body))
            except RuntimeError:
                asyncio.run(send_user_email(user.email, verify_subject, verify_body))
        except Exception as mail_error:
            print("VERIFY RESEND MAIL ERROR:", mail_error)
            raise HTTPException(status_code=500, detail="EMAIL_SEND_FAILED")

        return ok({"sent": True, "already_verified": False})
    finally:
        db.close()


@app.get("/verify-email", response_class=HTMLResponse)
def verify_email_web(token: str):
    db = SessionLocal()
    try:
        _verify_email_token(db, token)
        return HTMLResponse("""
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USLY — email potwierdzony</title>
</head>
<body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#fff7fb; color:#20131a; display:flex; min-height:100vh; align-items:center; justify-content:center; margin:0; padding:24px;">
  <main style="max-width:520px; background:white; border-radius:24px; padding:32px; box-shadow:0 18px 60px rgba(90,40,80,.14); text-align:center;">
    <h1 style="margin:0 0 12px;">Email potwierdzony ✨</h1>
    <p style="font-size:17px; line-height:1.5;">Twój adres email został potwierdzony. Możesz wrócić do aplikacji USLY.</p>
  </main>
</body>
</html>
""")
    except HTTPException as exc:
        detail = str(exc.detail or "EMAIL_VERIFY_ERROR")
        if detail == "EMAIL_VERIFY_TOKEN_EXPIRED":
            title = "Link wygasł"
            body = "Ten link weryfikacyjny stracił ważność. Wróć do aplikacji USLY i poproś o nowy link."
        elif detail == "EMAIL_VERIFY_TOKEN_INVALID":
            title = "Link jest nieważny"
            body = "Ten link został już użyty albo jest nieprawidłowy."
        else:
            title = "Nie udało się potwierdzić emaila"
            body = "Sprawdź link albo wróć do aplikacji USLY."
        return HTMLResponse(f"""
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USLY — {title}</title>
</head>
<body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#fff7fb; color:#20131a; display:flex; min-height:100vh; align-items:center; justify-content:center; margin:0; padding:24px;">
  <main style="max-width:520px; background:white; border-radius:24px; padding:32px; box-shadow:0 18px 60px rgba(90,40,80,.14); text-align:center;">
    <h1 style="margin:0 0 12px;">{title}</h1>
    <p style="font-size:17px; line-height:1.5;">{body}</p>
  </main>
</body>
</html>
""", status_code=exc.status_code)
    finally:
        db.close()


@app.get("/auth/verify-email")
def verify_email(token: str):
    db = SessionLocal()
    try:
        return ok(_verify_email_token(db, token))
    finally:
        db.close()


# =========================
# LEGAL  TERMS v1
# =========================
@app.get("/legal/terms")
def get_terms():
    return ok(
        {
            "type": "terms",
            "version": "v1",
            "content": (
                "Regulamin USLY v1\n\n"
                "1. Serwis przeznaczony jest wyłącznie dla osób, które ukończyły 18 lat.\n"
                "2. Uytkownik zobowizuje si do podawania prawdziwych danych.\n"
                "3. Szczegowe warunki korzystania zostan uzupenione.\n"
            ),
        }
    )


# =========================
# LEGAL  PRIVACY v1
# =========================
@app.get("/legal/privacy")
def get_privacy():
    return ok(
        {
            "type": "privacy",
            "version": "v1",
            "content": (
                "Polityka prywatnoci USLY v1\n\n"
                "1. Administratorem danych jest USLY (dane administratora do uzupenienia).\n"
                "2. Przetwarzamy dane w celu zaoenia i obsugi konta oraz wiadczenia usug.\n"
                "3. Podstawy prawne, odbiorcy danych, okres przechowywania i prawa uytkownika "
                "zostan doprecyzowane w wersji produkcyjnej.\n"
            ),
        }
    )


# =========================
# AUTH  LOGIN
# =========================

class CreateGroupRequest(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=600)
    interest_tag: str = Field(min_length=2, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    expected_role: str | None = None


@app.post("/auth/login")
@limiter.limit("5/minute")
def login(payload: LoginRequest, request: Request):
    db = SessionLocal()
    try:
        email = str(payload.email).strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            _audit(db, action="LOGIN_FAIL", request=request, user_id=None, details=f"email={email}")
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

         
        if user.status != UserStatus.ACTIVE.value:
            raise ApiException(status_code=403, code=ErrorCode.ACCOUNT_INACTIVE)

        if not verify_password(payload.password, user.password_hash):
            _audit(db, action="LOGIN_FAIL", request=request, user_id=user.id, details=f"email={email}")
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        if payload.expected_role and user.role != payload.expected_role:
            _audit(
                db,
                action="LOGIN_FAIL_ROLE_MISMATCH",
                request=request,
                user_id=user.id,
                details=f"email={email}, expected_role={payload.expected_role}, actual_role={user.role}",
            )
            raise ApiException(status_code=403, code=ErrorCode.INSUFFICIENT_ROLE)

        if user.role == UserRole.ADMIN.value and bool(getattr(user, "mfa_enabled", False)):
            mfa_token = _create_mfa_challenge_token(user.id)
            _audit(db, action="LOGIN_MFA_REQUIRED", request=request, user_id=user.id, details=f"email={email}")
            return ok({
                "mfa_required": True,
                "mfa_token": mfa_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "email_verified": bool(getattr(user, "email_verified_at", None)),
                    "email_verified_at": str(user.email_verified_at) if getattr(user, "email_verified_at", None) else None,
                },
            })

        access_token = create_access_token(user.id)

        _audit(db, action="LOGIN_SUCCESS", request=request, user_id=user.id, details=f"email={email}")

        return ok(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "email_verified": bool(getattr(user, "email_verified_at", None)),
                    "email_verified_at": str(user.email_verified_at) if getattr(user, "email_verified_at", None) else None,
                },
            }
        )
    finally:
        db.close()


@app.post("/auth/login/mfa")
@limiter.limit("5/minute")
def login_mfa(payload: LoginMfaRequest, request: Request):
    db = SessionLocal()
    try:
        user_id = _decode_mfa_challenge_token(payload.mfa_token)
        if not user_id:
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.role != UserRole.ADMIN.value:
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        if user.status != UserStatus.ACTIVE.value:
            raise ApiException(status_code=403, code=ErrorCode.ACCOUNT_INACTIVE)

        if not user.mfa_enabled or not user.mfa_secret:
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        used_backup_code = False
        if _verify_mfa_code(user.mfa_secret, payload.code):
            pass
        elif _consume_mfa_backup_code(user, payload.code):
            used_backup_code = True
            db.add(user)
            db.commit()
        else:
            _audit(db, action="LOGIN_MFA_FAIL", request=request, user_id=user.id, details=None)
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        access_token = create_access_token(user.id)
        _audit(
            db,
            action="LOGIN_MFA_SUCCESS",
            request=request,
            user_id=user.id,
            details="backup_code" if used_backup_code else "totp",
        )

        return ok({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "email_verified": bool(getattr(user, "email_verified_at", None)),
                "email_verified_at": str(user.email_verified_at) if getattr(user, "email_verified_at", None) else None,
            },
        })
    finally:
        db.close()


# =========================
# AUTH  LOGOUT
# =========================
@app.post("/auth/logout")
def logout(request: Request, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        _audit(db, action="LOGOUT", request=request, user_id=current_user.id, details=None)
        return ok({"ok": True})
    finally:
        db.close()


# =========================
# AUTH  /auth/me
# =========================
@app.get("/auth/me")
def auth_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "admin_display_name": current_user.admin_display_name,
        "admin_level": current_user.admin_level,
        "email_verified": bool(getattr(current_user, "email_verified_at", None)),
        "email_verified_at": str(current_user.email_verified_at) if getattr(current_user, "email_verified_at", None) else None,
    }


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# =========================
# AUTH  CHANGE PASSWORD
# =========================
@app.post("/auth/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(payload.current_password, user.password_hash):
            _audit(db, action="CHANGE_PASSWORD_FAIL", request=request, user_id=current_user.id, details="invalid_current_password")
            raise HTTPException(status_code=400, detail="CURRENT_PASSWORD_INVALID")

        if payload.current_password == payload.new_password:
            raise HTTPException(status_code=400, detail="NEW_PASSWORD_SAME_AS_CURRENT")

        user.password_hash = hash_password(payload.new_password)
        db.add(user)
        db.commit()

        _audit(db, action="CHANGE_PASSWORD_SUCCESS", request=request, user_id=current_user.id, details=None)
        return ok({"changed": True})
    finally:
        db.close()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


# =========================
# AUTH  FORGOT PASSWORD
# =========================
@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request):
    db = SessionLocal()
    try:
        email = str(payload.email).strip().lower()
        user = db.query(User).filter(User.email == email).first()

        # zawsze zwracamy ten sam wynik — nie ujawniamy, czy konto istnieje
        if not user or user.status != UserStatus.ACTIVE.value:
            _audit(db, action="FORGOT_PASSWORD_REQUEST", request=request, user_id=None, details=f"email={email}, result=ignored")
            return ok({"sent": True})

        token = str(uuid4())
        reset_row = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow().replace(microsecond=0) + __import__("datetime").timedelta(hours=1),
            used_at=None,
        )
        db.add(reset_row)
        db.commit()

        link_base = os.getenv("PASSWORD_RESET_LINK_BASE", "usly://reset-password").strip() or "usly://reset-password"
        separator = "&" if "?" in link_base else "?"
        reset_link = f"{link_base}{separator}token={token}"

        emailed = False
        email_error = None

        try:
            emailed = None
            import asyncio

            reset_subject = "USLY — reset hasła"
            reset_body = (
                "Otrzymaliśmy prośbę o reset hasła do konta USLY.\n\n"
                f"Otwórz ten link w aplikacji:\n{reset_link}\n\n"
                "Link jest jednorazowy i ważny przez 60 minut.\n\n"
                "Jeśli to nie Ty lub działanie wygląda podejrzanie, "
                "skontaktuj się z nami: kontakt@uslyapp.pl"
            )

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_user_email(user.email, reset_subject, reset_body))
                emailed = "queued"
            except RuntimeError:
                emailed = asyncio.run(send_user_email(user.email, reset_subject, reset_body))
        except Exception as e:
            email_error = str(e)

        _audit(
            db,
            action="FORGOT_PASSWORD_REQUEST",
            request=request,
            user_id=user.id,
            details=f"email={email}, token_created=1, emailed={1 if emailed else 0}, email_error={email_error or '-'}",
        )
        return ok({"sent": True})
    finally:
        db.close()


class ResetPasswordInfoRequest(BaseModel):
    token: str = Field(min_length=8, max_length=255)


# =========================
# AUTH  RESET PASSWORD INFO
# =========================
@app.post("/auth/reset-password-info")
def reset_password_info(payload: ResetPasswordInfoRequest):
    db = SessionLocal()
    try:
        token_value = str(payload.token).strip()

        reset_row = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token_value)
            .first()
        )

        if not reset_row or reset_row.used_at is not None:
            raise HTTPException(status_code=400, detail="PASSWORD_RESET_TOKEN_INVALID")

        if reset_row.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="PASSWORD_RESET_TOKEN_EXPIRED")

        user = db.query(User).filter(User.id == reset_row.user_id).first()
        if not user or user.status != UserStatus.ACTIVE.value:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        return ok({
            "email": user.email,
        })
    finally:
        db.close()


# =========================
# AUTH  RESET PASSWORD
# =========================
@app.post("/auth/reset-password")
def reset_password(payload: ResetPasswordRequest, request: Request):
    db = SessionLocal()
    try:
        token_value = str(payload.token).strip()

        reset_row = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token_value)
            .first()
        )

        if not reset_row or reset_row.used_at is not None:
            raise HTTPException(status_code=400, detail="PASSWORD_RESET_TOKEN_INVALID")

        if reset_row.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="PASSWORD_RESET_TOKEN_EXPIRED")

        user = db.query(User).filter(User.id == reset_row.user_id).first()
        if not user or user.status != UserStatus.ACTIVE.value:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        if user.password_hash and verify_password(payload.new_password, user.password_hash):
            raise HTTPException(status_code=400, detail="NEW_PASSWORD_SAME_AS_CURRENT")

        user.password_hash = hash_password(payload.new_password)
        reset_row.used_at = datetime.utcnow().replace(microsecond=0)

        db.add(user)
        db.add(reset_row)
        db.commit()

        _audit(db, action="RESET_PASSWORD_SUCCESS", request=request, user_id=user.id, details="token_used=1")
        return ok({"reset": True})
    finally:
        db.close()


# =========================
# AUTH  DELETE ACCOUNT (SOFT DELETE)
def cleanup_user_social_relations_for_soft_delete(db, user_id: int):
    owned_event_ids = [
        row[0]
        for row in db.query(Event.id).filter(Event.partner_user_id == user_id).all()
    ]

    if owned_event_ids:
        db.query(EventSignup).filter(
            EventSignup.event_id.in_(owned_event_ids)
        ).delete(synchronize_session=False)

        db.query(EventSave).filter(
            EventSave.event_id.in_(owned_event_ids)
        ).delete(synchronize_session=False)

        db.query(Event).filter(
            Event.id.in_(owned_event_ids)
        ).update(
            {
                Event.status: EventStatus.ARCHIVED.value,
                Event.updated_at: datetime.utcnow(),
            },
            synchronize_session=False,
        )

    db.query(Friendship).filter(
        (Friendship.requester_user_id == user_id)
        | (Friendship.addressee_user_id == user_id)
    ).delete(synchronize_session=False)

    affected_group_ids = [
        row[0]
        for row in db.query(GroupMembership.group_id).filter(GroupMembership.user_id == user_id).all()
    ]

    db.query(GroupMembership).filter(
        GroupMembership.user_id == user_id
    ).delete(synchronize_session=False)

    for group_id in affected_group_ids:
        count = db.query(GroupMembership).filter(GroupMembership.group_id == group_id).count()
        db.query(Group).filter(Group.id == group_id).update(
            {Group.members_count: count, Group.updated_at: datetime.utcnow()},
            synchronize_session=False,
        )

    db.query(GroupInvitation).filter(
        (GroupInvitation.inviter_user_id == user_id)
        | (GroupInvitation.invitee_user_id == user_id)
    ).delete(synchronize_session=False)

    db.query(EventSignup).filter(
        EventSignup.user_id == user_id
    ).delete(synchronize_session=False)

    db.query(EventSave).filter(
        EventSave.user_id == user_id
    ).delete(synchronize_session=False)

    db.query(UserBlock).filter(
        (UserBlock.blocker_user_id == user_id)
        | (UserBlock.blocked_user_id == user_id)
    ).delete(synchronize_session=False)

    db.query(Message).filter(
        (Message.sender_user_id == user_id)
        | (Message.recipient_user_id == user_id)
    ).delete(synchronize_session=False)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id
    ).delete(synchronize_session=False)

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id
    ).delete(synchronize_session=False)

    db.query(UserNotification).filter(
        (UserNotification.user_id == user_id)
        | (UserNotification.partner_user_id == user_id)
    ).delete(synchronize_session=False)


# =========================
@app.post("/auth/delete-account")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(payload.password, user.password_hash):
            _audit(db, action="DELETE_ACCOUNT_FAIL", request=request, user_id=current_user.id, details="invalid_password")
            raise HTTPException(status_code=400, detail="PASSWORD_INVALID")

        owned_groups = (
            db.query(Group)
            .filter(Group.creator_id == current_user.id)
            .all()
        )

        for g in owned_groups:
            db.delete(g)

        cleanup_user_social_relations_for_soft_delete(db, current_user.id)

        original_email = user.email
        safe_email = f"deleted_{user.id}_{int(datetime.utcnow().timestamp())}@deleted.usly.local"

        user.email = safe_email
        user.password_hash = None
        user.status = UserStatus.DELETED.value

        db.add(user)
        db.commit()

        try:
            import asyncio

            goodbye_subject = "USLY — Twoje konto zostało usunięte"
            goodbye_body = (
                "Potwierdzamy, że Twoje konto USLY zostało usunięte.\n\n"
                "Przykro nam, że się rozstajemy — dziękujemy, że byłaś/byłeś częścią USLY.\n\n"
                "Jeśli kiedyś zechcesz wrócić, będziemy tu dla Ciebie. "
                "A jeśli chcesz podzielić się opinią lub coś poszło nie tak, napisz do nas:\n"
                "kontakt@uslyapp.pl\n\n"
                "Do zobaczenia,\n"
                "Zespół USLY"
            )

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_user_email(original_email, goodbye_subject, goodbye_body))
            except RuntimeError:
                asyncio.run(send_user_email(original_email, goodbye_subject, goodbye_body))
        except Exception as mail_error:
            print("GOODBYE MAIL ERROR:", mail_error)

        _audit(
            db,
            action="DELETE_ACCOUNT_SUCCESS",
            request=request,
            user_id=current_user.id,
            details=f"original_email={original_email}",
        )
        return ok({"deleted": True})
    finally:
        db.close()


# =========================
# PROFILE  USER  GET /users/me
# =========================
@app.get("/users/me")
def users_me(current_user: User = Depends(require_role("user"))):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        plan_expiry_result = _expire_profile_plan_if_needed(db, current_user, profile)
        if plan_expiry_result:
            db.commit()
            db.refresh(profile)

        zainteresowania = []
        if profile.zainteresowania_json:
            try:
                zainteresowania = json.loads(profile.zainteresowania_json) or []
            except Exception:
                zainteresowania = []

        trainer_interests = []
        if profile.trainer_interests_json:
            try:
                trainer_interests = json.loads(profile.trainer_interests_json) or []
            except Exception:
                trainer_interests = []

        return ok(
            {
                "user_id": current_user.id,
                "nick": profile.nick,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "zainteresowania": zainteresowania,
                "trainer_interests": trainer_interests,
                "age_min": profile.age_min,
                "age_max": profile.age_max,
                "nearby_radius_km": profile.nearby_radius_km,
                "avatar_url": profile.avatar_url,
                "location_lat": profile.location_lat,
                "location_lng": profile.location_lng,
                "plan": profile.plan,
                "plan_source": profile.plan_source,
                "plan_status": profile.plan_status,
                "plan_updated_at": profile.plan_updated_at,
                "plan_expires_at": profile.plan_expires_at,
            }
        )
    finally:
        db.close()




@app.get("/users/nearby")
def users_nearby(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    max_distance_km: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        def calc_age(dob: date | None) -> int | None:
            if not dob:
                return None
            today = date.today()
            years = today.year - dob.year
            if (today.month, today.day) < (dob.month, dob.day):
                years -= 1
            return years

        def norm_city(v: str | None) -> str:
            return (v or "").strip().lower()

        def norm_tags(raw) -> set[str]:
            if not raw:
                return set()
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = []
            if not isinstance(raw, list):
                return set()
            return {
                str(x).strip().lower()
                for x in raw
                if str(x).strip()
            }

        my_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not my_profile:
            return ok({"items": [], "pagination": {"limit": limit, "offset": offset, "total": 0}})

        my_city = norm_city(my_profile.miasto)
        my_tags = norm_tags(my_profile.zainteresowania_json)
        my_age = calc_age(current_user.dob)
        my_pref_min = my_profile.age_min
        my_pref_max = my_profile.age_max

        rows = (
            db.query(User, UserProfile)
            .join(UserProfile, UserProfile.user_id == User.id)
            .filter(User.role == "user")
            .filter(User.status == UserStatus.ACTIVE.value)
            .filter(User.id != current_user.id)
            .order_by(UserProfile.updated_at.desc())
            .all()
        )

        if rows:
            candidate_user_ids = [user.id for user, _profile in rows]
            blocked_rows = (
                db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
                .filter(
                    ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id.in_(candidate_user_ids))) |
                    ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id.in_(candidate_user_ids)))
                )
                .all()
            )
            blocked_user_ids = {
                blocked_id if blocker_id == current_user.id else blocker_id
                for blocker_id, blocked_id in blocked_rows
            }
            rows = [(user, profile) for user, profile in rows if user.id not in blocked_user_ids]

        matched_items = []
        for user, profile in rows:
            other_city = norm_city(profile.miasto)

            # distance filter (Nearby)
            if (
                my_profile.location_lat is None
                or my_profile.location_lng is None
                or profile.location_lat is None
                or profile.location_lng is None
            ):
                continue

            dist_km = _distance_km(
                my_profile.location_lat,
                my_profile.location_lng,
                profile.location_lat,
                profile.location_lng,
            )

            user_radius = my_profile.nearby_radius_km or 25
            if dist_km > user_radius:
                continue

            other_tags = norm_tags(profile.zainteresowania_json)
            other_trainer_tags = norm_tags(profile.trainer_interests_json)
            shared_tags = sorted(my_tags & other_tags)
            shared_trainer_tags = sorted(my_tags & other_trainer_tags)

            other_age = calc_age(user.dob)
            other_pref_min = profile.age_min
            other_pref_max = profile.age_max

            if my_age is None or other_age is None:
                continue

            # ja akceptuję drugą osobę
            if my_pref_min is not None and other_age < my_pref_min:
                continue
            if my_pref_max is not None and other_age > my_pref_max:
                continue

            # druga osoba akceptuje mnie
            if other_pref_min is not None and my_age < other_pref_min:
                continue
            if other_pref_max is not None and my_age > other_pref_max:
                continue

            matched_items.append(
                {
                    "user_id": user.id,
                    "nick": profile.nick,
                    "miasto": profile.miasto,
                    "bio": profile.bio,
                    "zainteresowania": sorted(other_tags),
                    "trainer_interests": sorted(other_trainer_tags),
                    "shared_zainteresowania": shared_tags,
                    "shared_trainer_interests": shared_trainer_tags,
                    "shared_count": len(shared_tags),
                    "age": other_age,
                    "age_min": profile.age_min,
                    "age_max": profile.age_max,
                    "avatar_url": profile.avatar_url,
                    "distance_km": round(dist_km, 1),
                    "location_lat": profile.location_lat,
                    "location_lng": profile.location_lng,
                }
            )

        matched_items.sort(
            key=lambda x: (
                -int(x.get("shared_count") or 0),
                float(x.get("distance_km") or 9999),
                x.get("nick") or "",
            )
        )

        total = len(matched_items)
        items = matched_items[offset:offset + limit]

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


@app.get("/users/{user_id}")
def users_profile_by_id(
    user_id: int,
    current_user: User = Depends(require_role("user", "partner")),
):
    db = SessionLocal()
    try:
        profile_row = (
            db.query(User, UserProfile)
            .join(UserProfile, UserProfile.user_id == User.id)
            .filter(User.id == user_id)
            .filter(User.role == "user")
            .filter(User.status == UserStatus.ACTIVE.value)
            .first()
        )

        if not profile_row:
            raise HTTPException(status_code=404, detail="User not found")

        user, profile = profile_row

        viewer_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        distance_km = None
        if (
            viewer_profile
            and viewer_profile.location_lat is not None
            and viewer_profile.location_lng is not None
            and profile.location_lat is not None
            and profile.location_lng is not None
        ):
            distance_km = round(
                _distance_km(
                    viewer_profile.location_lat,
                    viewer_profile.location_lng,
                    profile.location_lat,
                    profile.location_lng,
                ),
                1,
            )

        zainteresowania = []
        if profile.zainteresowania_json:
            try:
                zainteresowania = json.loads(profile.zainteresowania_json) or []
            except Exception:
                zainteresowania = []

        trainer_interests = []
        if profile.trainer_interests_json:
            try:
                trainer_interests = json.loads(profile.trainer_interests_json) or []
            except Exception:
                trainer_interests = []

        age = None
        if user.dob:
            today = date.today()
            age = today.year - user.dob.year
            if (today.month, today.day) < (user.dob.month, user.dob.day):
                age -= 1

        return ok(
            {
                "user_id": user.id,
                "nick": profile.nick,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "zainteresowania": zainteresowania,
                "trainer_interests": trainer_interests,
                "age": age,
                "age_min": profile.age_min,
                "age_max": profile.age_max,
                "avatar_url": profile.avatar_url,
                "distance_km": distance_km,
            }
        )
    finally:
        db.close()



# =========================
# PROFILE  USER  PATCH /users/me
# =========================
class UserMePatch(BaseModel):
    nick: Optional[str] = Field(default=None)
    miasto: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=300)
    zainteresowania: Optional[List[str]] = Field(default=None)
    trainer_interests: Optional[List[str]] = Field(default=None)
    age_min: Optional[int] = Field(default=None, ge=16, le=120)
    age_max: Optional[int] = Field(default=None, ge=16, le=120)
    nearby_radius_km: Optional[int] = Field(default=None, ge=1, le=200)
    avatar_url: Optional[str] = Field(default=None)
    plan: Optional[str] = Field(default=None)
    location_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    location_lng: Optional[float] = Field(default=None, ge=-180, le=180)


def _trim(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s2 = s.strip()
    return s2 if s2 != "" else None


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@app.patch("/users/me")
def users_me_patch(
    payload: UserMePatch,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        if payload.nick is not None:
            profile.nick = _trim(payload.nick)
        if payload.miasto is not None:
            profile.miasto = _trim(payload.miasto)
        if payload.bio is not None:
            profile.bio = _trim(payload.bio)

        fields_set = payload.model_fields_set if hasattr(payload, "model_fields_set") else set()

        new_min = payload.age_min if "age_min" in fields_set else profile.age_min
        new_max = payload.age_max if "age_max" in fields_set else profile.age_max
        if new_min is not None and new_max is not None and new_min > new_max:
            raise HTTPException(status_code=422, detail="age_min_must_be_lte_age_max")

        if "age_min" in fields_set:
            profile.age_min = payload.age_min
        if "age_max" in fields_set:
            profile.age_max = payload.age_max
        if "nearby_radius_km" in fields_set and payload.nearby_radius_km is not None:
            profile.nearby_radius_km = payload.nearby_radius_km

        if payload.zainteresowania is not None:
            cleaned: list[str] = []
            for item in payload.zainteresowania:
                if item is None:
                    continue
                t = item.strip()
                if t == "":
                    continue
                if len(t) > 40:
                    raise HTTPException(status_code=422, detail="interest_too_long_max_40")
                cleaned.append(t)

            interest_limits = {
                "free": 5,
                "plus": 10,
                "premium": 20,
                "vip": None,
            }

            current_plan = (profile.plan or "free").lower()
            interest_limit = interest_limits.get(current_plan, 5)

            if interest_limit is not None and len(cleaned) > interest_limit:
                raise HTTPException(
                    status_code=422,
                    detail="too_many_interests_max_20",
                )

            profile.zainteresowania_json = json.dumps(cleaned, ensure_ascii=False)

            existing_trainer = []
            if profile.trainer_interests_json:
                try:
                    existing_trainer = json.loads(profile.trainer_interests_json) or []
                except Exception:
                    existing_trainer = []
            cleaned_lower = {x.lower() for x in cleaned}
            kept_trainer = [x for x in existing_trainer if str(x).strip().lower() in cleaned_lower]
            profile.trainer_interests_json = json.dumps(kept_trainer, ensure_ascii=False) if kept_trainer else None

        if payload.trainer_interests is not None:
            current_plan = (profile.plan or "free").lower()
            if current_plan not in {"premium", "vip"}:
                raise HTTPException(status_code=403, detail="TRAINER_INTERESTS_REQUIRE_PREMIUM_OR_VIP")

            current_interests = []
            if profile.zainteresowania_json:
                try:
                    current_interests = json.loads(profile.zainteresowania_json) or []
                except Exception:
                    current_interests = []

            interests_by_lower = {str(x).strip().lower(): str(x).strip() for x in current_interests if str(x).strip()}
            cleaned_trainer = []
            seen_trainer = set()

            for item in payload.trainer_interests:
                if item is None:
                    continue
                key = str(item).strip().lower()
                if not key:
                    continue
                if key not in interests_by_lower:
                    raise HTTPException(status_code=422, detail="TRAINER_INTEREST_MUST_BE_PROFILE_INTEREST")
                if key not in seen_trainer:
                    cleaned_trainer.append(interests_by_lower[key])
                    seen_trainer.add(key)

            trainer_limits = {
                "premium": 2,
                "vip": 5,
            }
            trainer_limit = trainer_limits.get(current_plan, 0)
            if len(cleaned_trainer) > trainer_limit:
                raise HTTPException(status_code=422, detail="TOO_MANY_TRAINER_INTERESTS")

            profile.trainer_interests_json = json.dumps(cleaned_trainer, ensure_ascii=False) if cleaned_trainer else None

        if payload.avatar_url is not None:
            profile.avatar_url = _trim(payload.avatar_url)

        if payload.plan is not None:
            requested_plan = str(payload.plan or "").strip().lower()
            if requested_plan != "free":
                raise HTTPException(status_code=403, detail="PAID_PLAN_REQUIRES_STORE_PURCHASE")
            profile.plan = "free"
            profile.plan_source = "manual"
            profile.plan_status = "active"
            profile.plan_updated_at = datetime.utcnow()
            profile.plan_expires_at = None

        # Przybliżona lokalizacja (anonimizowana)
        if payload.location_lat is not None and payload.location_lng is not None:
            lat = round(payload.location_lat, 2)
            lng = round(payload.location_lng, 2)

            profile.location_lat = lat
            profile.location_lng = lng

            city = _reverse_geocode_city(lat, lng)
            if city:
                profile.miasto = city

        profile.updated_at = datetime.utcnow()

        db.add(profile)
        db.commit()
        db.refresh(profile)

        zainteresowania = []
        if profile.zainteresowania_json:
            try:
                zainteresowania = json.loads(profile.zainteresowania_json) or []
            except Exception:
                zainteresowania = []

        trainer_interests = []
        if profile.trainer_interests_json:
            try:
                trainer_interests = json.loads(profile.trainer_interests_json) or []
            except Exception:
                trainer_interests = []

        return ok(
            {
                "user_id": current_user.id,
                "nick": profile.nick,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "zainteresowania": zainteresowania,
                "trainer_interests": trainer_interests,
                "age_min": profile.age_min,
                "age_max": profile.age_max,
                "nearby_radius_km": profile.nearby_radius_km,
                "avatar_url": profile.avatar_url,
                "location_lat": profile.location_lat,
                "location_lng": profile.location_lng,
                "plan": profile.plan,
                "plan_source": profile.plan_source,
                "plan_status": profile.plan_status,
                "plan_updated_at": profile.plan_updated_at,
            }
        )
    finally:
        db.close()


# =========================
# PROFILE  PARTNER  GET /partners/me
# =========================
@app.get("/partners/me")
def partners_me(current_user: User = Depends(require_role("partner"))):
    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        plan_expiry_result = _expire_profile_plan_if_needed(db, current_user, profile)
        if plan_expiry_result:
            db.commit()
            db.refresh(profile)

        return ok(
            {
                "user_id": current_user.id,
                "nazwa": profile.nazwa,
                "miasto": profile.miasto,
                "kategoria": profile.kategoria,
                "plan": profile.plan,
                "plan_source": profile.plan_source,
                "plan_status": profile.plan_status,
                "plan_updated_at": profile.plan_updated_at,
                "plan_expires_at": profile.plan_expires_at,
                "bio": profile.bio,
                "logo_url": profile.logo_url,
            }
        )
    finally:
        db.close()


# =========================
# PROFILE  PARTNER  PATCH /partners/me
# =========================
class PartnerMePatch(BaseModel):
    nazwa: Optional[str] = Field(default=None, max_length=120)
    miasto: Optional[str] = Field(default=None, max_length=80)
    kategoria: Optional[str] = Field(default=None, max_length=80)
    plan: Optional[str] = Field(default=None, max_length=20)
    bio: Optional[str] = Field(default=None, max_length=500)
    logo_url: Optional[str] = Field(default=None)


@app.patch("/partners/me")
def partners_me_patch(
    payload: PartnerMePatch,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        if payload.nazwa is not None:
            profile.nazwa = _trim(payload.nazwa)

        if payload.miasto is not None:
            profile.miasto = _trim(payload.miasto)

        if payload.kategoria is not None:
            profile.kategoria = _trim(payload.kategoria)

        if payload.plan is not None:
            requested_plan = _trim(payload.plan).lower()
            if requested_plan != "free":
                raise HTTPException(status_code=403, detail="PAID_PLAN_REQUIRES_STORE_PURCHASE")
            profile.plan = "free"
            profile.plan_source = "manual"
            profile.plan_status = "active"
            profile.plan_updated_at = datetime.utcnow()
            profile.plan_expires_at = None

        if payload.bio is not None:
            profile.bio = _trim(payload.bio)

        if payload.logo_url is not None:
            profile.logo_url = _trim(payload.logo_url)

        profile.updated_at = datetime.utcnow()

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return ok(
            {
                "user_id": current_user.id,
                "nazwa": profile.nazwa,
                "miasto": profile.miasto,
                "kategoria": profile.kategoria,
                "plan": profile.plan,
                "bio": profile.bio,
                "logo_url": profile.logo_url,
            }
        )
    finally:
        db.close()


# =========================
# UPLOADS (v1)  AVATAR (USER)
# POST /uploads/avatar
# =========================
AVATARS_DIR = Path("uploads") / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


@app.post("/uploads/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("user")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"

    if require_r2_or_allow_local_uploads():
        avatar_url = upload_media_to_r2(
            key=f"avatars/{filename}",
            content=content,
            content_type=file.content_type,
        )
    else:
        path = AVATARS_DIR / filename
        with open(path, "wb") as f:
            f.write(content)
        avatar_url = f"/uploads/static/avatars/{filename}"

    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        db.add(profile)
        db.commit()

        return ok({"avatar_url": avatar_url})
    finally:
        db.close()

class AiAvatarGenerateRequest(BaseModel):
    prompt: str = Field(default="", max_length=240)


AI_AVATAR_PLAN_LIMITS = {
    "free": 1,
    "plus": 5,
    "premium": 15,
    "vip": 30,
}


def _get_ai_avatar_usage(db, user_id: int, plan: str) -> dict:
    safe_plan = (plan or "free").lower()
    limit = AI_AVATAR_PLAN_LIMITS.get(safe_plan, AI_AVATAR_PLAN_LIMITS["free"])

    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    used = (
        db.query(AiUsageLog)
        .filter(AiUsageLog.user_id == user_id)
        .filter(AiUsageLog.feature == "avatar")
        .filter(AiUsageLog.created_at >= month_start)
        .count()
    )

    return {
        "plan": safe_plan,
        "limit": limit,
        "used": used,
        "remaining": max(limit - used, 0),
        "period": "monthly",
    }


@app.get("/ai/avatar/status")
def get_ai_avatar_status(
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        plan = (profile.plan if profile else "free") or "free"
        return ok(_get_ai_avatar_usage(db, current_user.id, plan))
    finally:
        db.close()



@app.post("/ai/avatar/generate")
async def generate_ai_avatar(
    payload: AiAvatarGenerateRequest,
    current_user: User = Depends(require_role("user")),
):
    if not _openai_client:
        raise HTTPException(status_code=503, detail="ai_avatar_not_configured")

    user_prompt = (payload.prompt or "").strip()
    if len(user_prompt) < 3:
        raise HTTPException(status_code=422, detail="avatar_prompt_required")

    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            profile = UserProfile(user_id=current_user.id, plan="free")
            db.add(profile)
            db.commit()
            db.refresh(profile)

        usage = _get_ai_avatar_usage(db, current_user.id, profile.plan)
        plan = usage["plan"]
        limit = usage["limit"]
        used = usage["used"]

        if used >= limit:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "ai_avatar_limit_reached",
                    "message": "Limit generowania awatarów AI w tym planie został wykorzystany.",
                    "plan": plan,
                    "limit": limit,
                    "used": used,
                },
            )

        final_prompt = (
            "Create a square illustrated profile avatar for a social/event app. "
            "Friendly, modern, polished, premium mobile app style. "
            "Do not create a realistic portrait of a real person. "
            "No text, no logo, no watermark. "
            f"User style request: {user_prompt}"
        )

        result = _openai_client.images.generate(
            model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
            prompt=final_prompt,
            size=os.getenv("OPENAI_IMAGE_SIZE", "1024x1024"),
            quality=os.getenv("OPENAI_IMAGE_QUALITY", "low"),
            n=1,
        )

        b64_image = result.data[0].b64_json
        if not b64_image:
            raise HTTPException(status_code=502, detail="ai_avatar_empty_response")

        content = base64.b64decode(b64_image)
        filename = f"ai_{current_user.id}_{uuid4().hex}.png"

        if require_r2_or_allow_local_uploads():
            avatar_url = upload_media_to_r2(
                key=f"avatars/{filename}",
                content=content,
                content_type="image/png",
            )
        else:
            path = AVATARS_DIR / filename
            with open(path, "wb") as f:
                f.write(content)
            avatar_url = f"/uploads/static/avatars/{filename}"

        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        db.add(profile)

        db.add(
            AiUsageLog(
                user_id=current_user.id,
                feature="avatar",
                plan=plan,
                created_at=datetime.utcnow(),
            )
        )

        db.commit()

        return ok(
            {
                "avatar_url": avatar_url,
                "plan": plan,
                "limit": limit,
                "used": used + 1,
                "remaining": max(limit - used - 1, 0),
            }
        )
    finally:
        db.close()



# =========================
# UPLOADS (v1)  LOGO (PARTNER)
# POST /uploads/logo
# =========================
LOGOS_DIR = Path("uploads") / "logos"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/uploads/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("partner")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"

    if require_r2_or_allow_local_uploads():
        logo_url = upload_media_to_r2(
            key=f"logos/{filename}",
            content=content,
            content_type=file.content_type,
        )
    else:
        path = LOGOS_DIR / filename
        with open(path, "wb") as f:
            f.write(content)
        logo_url = f"/uploads/static/logos/{filename}"

    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        profile.logo_url = logo_url
        profile.updated_at = datetime.utcnow()
        db.add(profile)
        db.commit()

        return ok({"logo_url": logo_url})
    finally:
        db.close()



# =========================
# PLACES SEARCH — GOOGLE PLACES PROXY
# =========================
@app.get("/partners/places/search")
def partner_search_places(
    q: str = Query(..., min_length=2, max_length=200),
    city: Optional[str] = Query(default=None, max_length=80),
    current_user: User = Depends(require_role("partner")),
):
    import json
    import os
    import ssl
    import urllib.error
    import urllib.request

    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_MAPS_API_KEY_NOT_CONFIGURED")

    query = ", ".join([part for part in [q.strip(), (city or "").strip(), "Polska"] if part])

    body = json.dumps({
        "textQuery": query,
        "languageCode": "pl",
        "regionCode": "PL",
        "maxResultCount": 5,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise HTTPException(status_code=502, detail=f"GOOGLE_PLACES_SEARCH_FAILED:{exc}")

        # Lokalny fallback dla macOS/Python, gdy certyfikaty systemowe nie są podpięte w venv.
        # Produkcyjnie na Render powinien działać standardowy SSL.
        insecure_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=insecure_context) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GOOGLE_PLACES_SEARCH_FAILED:{exc}")

    items = []
    for place in data.get("places", []) or []:
        loc = place.get("location") or {}
        display = place.get("displayName") or {}
        items.append({
            "name": display.get("text") or place.get("formattedAddress") or "Miejsce",
            "address": place.get("formattedAddress") or "",
            "lat": loc.get("latitude"),
            "lng": loc.get("longitude"),
        })

    return ok({"items": items})


# =========================
# EVENTS  CORE
# PARTNER: CREATE + UPDATE EVENT
# =========================
def _ensure_utc(dt):
    """
    SQLite czsto zwraca datetime bez tzinfo (naive). Traktujemy je jako UTC,
    eby nie byo 500 przy porwnaniach i eby logika bya spjna.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _admin_event_lifecycle_status(event: Event) -> str:
    status = str(getattr(event, "status", "") or "")
    if status in {"archived", "draft"}:
        return status
    end_at = _ensure_utc(getattr(event, "end_at", None))
    if end_at and end_at < datetime.now(timezone.utc):
        return "ended"
    return status or "published"


@app.post("/partners/events")
def partner_create_event(
    payload: EventCreate,
    current_user: User = Depends(require_role("partner")),
):
    def _to_utc_naive(dt):
        if dt is None:
            return None
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=None)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    def _to_str_or_none(v):
        if v is None:
            return None
        return str(v)

    db = SessionLocal()
    try:
        partner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
        partner_plan = str(getattr(partner_profile, "plan", None) or "free").lower()
        tag_limit = _partner_event_interest_tag_limit(partner_plan)
        interest_tags = _normalize_event_interest_tags(getattr(payload, "interest_tags", None), payload.interest_tag)

        if len(interest_tags) > tag_limit:
            raise HTTPException(status_code=422, detail="EVENT_INTEREST_TAG_LIMIT_REACHED")

        event = Event(
            partner_user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            city=payload.city,
            where=payload.where,
            address=payload.address,
            location_lat=payload.location_lat,
            location_lng=payload.location_lng,
            interest_tag=interest_tags[0],
            interest_tags_json=json.dumps(interest_tags, ensure_ascii=False),
            start_at=_to_utc_naive(payload.start_at),
            end_at=_to_utc_naive(payload.end_at),
            capacity=payload.capacity,
            event_cover_url=payload.event_cover_url,
            pricing_type=payload.pricing_type,
            price_fixed=payload.price_fixed,
            price_min=payload.price_min,
            price_max=payload.price_max,
            payment_link=_to_str_or_none(payload.payment_link),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        response_interest_tags = _normalize_event_interest_tags(
            json.loads(event.interest_tags_json) if event.interest_tags_json else None,
            event.interest_tag,
        )

        return ok(
            EventOut(
                id=event.id,
                partner_user_id=event.partner_user_id,
                title=event.title,
                description=event.description,
                city=event.city,
                where=event.where,
                address=event.address,
                location_lat=event.location_lat,
                location_lng=event.location_lng,
                interest_tag=event.interest_tag,
                interest_tags=response_interest_tags,
                start_at=event.start_at,
                end_at=event.end_at,
                capacity=event.capacity,
                status=event.status,
                created_at=event.created_at,
                updated_at=event.updated_at,
                event_cover_url=event.event_cover_url,
                pricing_type=event.pricing_type,
                price_fixed=event.price_fixed,
                price_min=event.price_min,
                price_max=event.price_max,
                payment_link=event.payment_link,
            ).model_dump()
        )
    finally:
        db.close()


@app.patch("/partners/events/{event_id}")
def partner_update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        current_start = _ensure_utc(event.start_at)
        current_end = _ensure_utc(event.end_at)
        previous_where = event.where
        previous_city = event.city

        new_start = _ensure_utc(payload.start_at) if payload.start_at is not None else current_start
        new_end = _ensure_utc(payload.end_at) if payload.end_at is not None else current_end

        if new_start is not None and new_end is not None and not (new_start < new_end):
            raise HTTPException(status_code=422, detail="INVALID_EVENT_DATES")

        def _to_utc_naive(dt):
            if dt is None:
                return None
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                return dt.replace(tzinfo=None)
            return dt.astimezone(timezone.utc).replace(tzinfo=None)

        def _to_str_or_none(v):
            if v is None:
                return None
            return str(v)

        if payload.title is not None:
            event.title = payload.title
        if payload.description is not None:
            event.description = payload.description
        if payload.city is not None:
            event.city = payload.city
        if payload.where is not None:
            event.where = payload.where
        if payload.address is not None:
            event.address = payload.address
        if payload.location_lat is not None:
            event.location_lat = payload.location_lat
        if payload.location_lng is not None:
            event.location_lng = payload.location_lng
        if getattr(payload, "interest_tags", None) is not None or payload.interest_tag is not None:
            partner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
            partner_plan = str(getattr(partner_profile, "plan", None) or "free").lower()
            tag_limit = _partner_event_interest_tag_limit(partner_plan)
            interest_tags = _normalize_event_interest_tags(getattr(payload, "interest_tags", None), payload.interest_tag or event.interest_tag)

            if len(interest_tags) > tag_limit:
                raise HTTPException(status_code=422, detail="EVENT_INTEREST_TAG_LIMIT_REACHED")

            event.interest_tag = interest_tags[0]
            event.interest_tags_json = json.dumps(interest_tags, ensure_ascii=False)
        if payload.start_at is not None:
            event.start_at = _to_utc_naive(payload.start_at)
        if payload.end_at is not None:
            event.end_at = _to_utc_naive(payload.end_at)
        if payload.capacity is not None:
            event.capacity = payload.capacity
        if payload.status is not None:
            event.status = payload.status

        if payload.event_cover_url is not None:
            event.event_cover_url = payload.event_cover_url

        if payload.pricing_type is not None:
            event.pricing_type = payload.pricing_type
        if payload.price_fixed is not None:
            event.price_fixed = payload.price_fixed
        if payload.price_min is not None:
            event.price_min = payload.price_min
        if payload.price_max is not None:
            event.price_max = payload.price_max
        if payload.payment_link is not None:
            event.payment_link = _to_str_or_none(payload.payment_link)

        event_time_changed = (
            current_start != _ensure_utc(event.start_at)
            or current_end != _ensure_utc(event.end_at)
        )
        event_location_changed = (
            previous_where != event.where
            or previous_city != event.city
        )
        event_key_details_changed = event_time_changed or event_location_changed

        event.updated_at = datetime.utcnow()

        if event_key_details_changed:
            signup_user_ids = {
                user_id
                for (user_id,) in (
                    db.query(EventSignup.user_id)
                    .filter(EventSignup.event_id == event.id)
                    .all()
                )
            }
            saved_user_ids = {
                user_id
                for (user_id,) in (
                    db.query(EventSave.user_id)
                    .filter(EventSave.event_id == event.id)
                    .all()
                )
            }
            target_user_ids = signup_user_ids | saved_user_ids

            if event_time_changed and event_location_changed:
                notification_type = "event_time_and_location_changed"
            elif event_time_changed:
                notification_type = "event_time_changed"
            else:
                notification_type = "event_location_changed"

            for target_user_id in target_user_ids:
                db.add(
                    UserNotification(
                        user_id=target_user_id,
                        event_id=event.id,
                        partner_user_id=current_user.id,
                        type=notification_type,
                    )
                )

        db.add(event)
        db.commit()
        db.refresh(event)

        response_interest_tags = _normalize_event_interest_tags(
            json.loads(event.interest_tags_json) if event.interest_tags_json else None,
            event.interest_tag,
        )

        return ok(
            EventOut(
                id=event.id,
                partner_user_id=event.partner_user_id,
                title=event.title,
                description=event.description,
                city=event.city,
                where=event.where,
                address=event.address,
                location_lat=event.location_lat,
                location_lng=event.location_lng,
                interest_tag=event.interest_tag,
                interest_tags=response_interest_tags,
                start_at=event.start_at,
                end_at=event.end_at,
                capacity=event.capacity,
                status=event.status,
                created_at=event.created_at,
                updated_at=event.updated_at,
                event_cover_url=event.event_cover_url,
                pricing_type=event.pricing_type,
                price_fixed=event.price_fixed,
                price_min=event.price_min,
                price_max=event.price_max,
                payment_link=event.payment_link,
            ).model_dump()
        )
    finally:
        db.close()


# =========================
# EVENTS  PARTNER: DELETE EVENT
# =========================
@app.delete("/partners/events/{event_id}")
def partner_delete_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        db.delete(event)
        db.commit()

        return ok({"deleted": True, "id": event_id})
    finally:
        db.close()


# =========================
# EVENTS  STATUS FLOW
# =========================
@app.post("/partners/events/{event_id}/publish")
def partner_publish_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        if event.status not in {"draft", "archived"}:
            raise HTTPException(status_code=409, detail="INVALID_STATUS_TRANSITION")

        if event.status == "archived":
            last_admin_status_log = (
                db.query(AuditLog)
                .filter(
                    AuditLog.action == "admin_update_event_status",
                    AuditLog.details.isnot(None),
                    AuditLog.details.like(f"%event_id={event.id}%"),
                )
                .order_by(AuditLog.created_at.desc())
                .first()
            )
            if last_admin_status_log and "to=archived" in (last_admin_status_log.details or ""):
                raise HTTPException(status_code=403, detail="EVENT_ARCHIVED_BY_ADMIN")

        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )
        current_plan = ((profile.plan if profile else "free") or "free").lower()

        active_limit = None
        if current_plan == "free":
            active_limit = 2
        elif current_plan == "pro":
            active_limit = 5

        now_utc = datetime.now(timezone.utc)

        if event.end_at is not None and _ensure_utc(event.end_at) < now_utc:
            raise HTTPException(status_code=409, detail="INVALID_STATUS_TRANSITION")

        if active_limit is not None:
            active_events_count = (
                db.query(Event)
                .filter(Event.partner_user_id == current_user.id)
                .filter(Event.status == "published")
                .filter(Event.end_at >= now_utc)
                .count()
            )
            if active_events_count >= active_limit:
                raise HTTPException(status_code=409, detail="PLAN_ACTIVE_EVENT_LIMIT_REACHED")

        event.status = "published"
        event.updated_at = datetime.utcnow()

        db.add(event)
        db.commit()
        db.refresh(event)

        return ok({"id": event.id, "status": event.status})
    finally:
        db.close()


@app.post("/partners/events/{event_id}/archive")
def partner_archive_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        if event.status != "published":
            raise HTTPException(status_code=409, detail="INVALID_STATUS_TRANSITION")

        event.status = "archived"
        event.updated_at = datetime.utcnow()

        db.add(event)
        db.commit()
        db.refresh(event)

        return ok({"id": event.id, "status": event.status})
    finally:
        db.close()


# =========================
# EVENTS  USER: LISTA EVENTW
# =========================
@app.get("/events")
def list_events(
    city: Optional[str] = None,
    date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        blocked_partner_ids_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id != current_user.id)) |
                ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id != current_user.id))
            )
            .all()
        )
        blocked_partner_ids = {
            blocked_user_id if blocker_user_id == current_user.id else blocker_user_id
            for blocker_user_id, blocked_user_id in blocked_partner_ids_rows
        }

        now_utc = datetime.now(timezone.utc)
        q = (
            db.query(Event)
            .filter(Event.status == "published")
            .filter(Event.end_at >= now_utc)
        )

        if blocked_partner_ids:
            q = q.filter(~Event.partner_user_id.in_(blocked_partner_ids))

        if city is not None and city.strip() != "":
            q = q.filter(Event.city == city.strip())

        if date is not None:
            start_dt = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_dt = datetime(date.year, date.month, date.day, 23, 59, 59)
            q = q.filter(Event.start_at >= start_dt)
            q = q.filter(Event.start_at <= end_dt)

        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        raw_interests = []
        if profile and profile.zainteresowania_json:
            try:
                raw_interests = json.loads(profile.zainteresowania_json) or []
            except Exception:
                raw_interests = []

        def norm_tag(value: str | None) -> str:
            if not value:
                return ""
            v = value.strip().lower()
            aliases = {
                "foto": "fotografia",
                "photo": "fotografia",
                "film": "kino",
                "movies": "kino",
                "movie": "kino",
                "tech": "ai",
                "startup": "biznes",
                "startups": "biznes",
            }
            return aliases.get(v, v)

        user_interest_set = {norm_tag(x) for x in raw_interests if x and str(x).strip()}

        events = q.all()
        scored = []

        for e in events:
            event_tags = []
            if getattr(e, "interest_tags_json", None):
                try:
                    event_tags = json.loads(e.interest_tags_json) or []
                except Exception:
                    event_tags = []
            if not event_tags:
                event_tags = [e.interest_tag]

            normalized_event_tags = {norm_tag(tag) for tag in event_tags if tag and str(tag).strip()}
            score = 1 if normalized_event_tags & user_interest_set else 0
            scored.append((score, e))

        scored.sort(key=lambda x: (-x[0], x[1].start_at, x[1].id))
        total = len(scored)
        paged = scored[offset:offset + limit]

        items = []
        for score, e in paged:
            event_tags = []
            if getattr(e, "interest_tags_json", None):
                try:
                    event_tags = json.loads(e.interest_tags_json) or []
                except Exception:
                    event_tags = []
            if not event_tags:
                event_tags = [e.interest_tag]

            partner_profile = (
                db.query(PartnerProfile)
                .filter(PartnerProfile.user_id == e.partner_user_id)
                .first()
            )

            signups_count = (
                db.query(EventSignup)
                .filter(EventSignup.event_id == e.id)
                .count()
            )
            spots_left = None
            if e.capacity is not None:
                spots_left = max(e.capacity - signups_count, 0)

            items.append(
                {
                    "id": e.id,
                    "partner_user_id": e.partner_user_id,
                    "partner_name": getattr(partner_profile, "nazwa", "") or "",
                    "partner_category": getattr(partner_profile, "kategoria", "") or "",
                    "partner_bio": getattr(partner_profile, "bio", "") or "",
                    "partner_logo_url": getattr(partner_profile, "logo_url", "") or "",
                    "partner_city": getattr(partner_profile, "miasto", "") or "",
                    "title": e.title,
                    "description": e.description,
                    "city": e.city,
                    "where": e.where,
                    "address": e.address,
                    "location_lat": e.location_lat,
                    "location_lng": e.location_lng,
                    "interest_tag": e.interest_tag,
                    "interest_tags": event_tags,
                    "start_at": e.start_at,
                    "end_at": e.end_at,
                    "capacity": e.capacity,
                    "signups_count": signups_count,
                    "spots_left": spots_left,
                    "status": e.status,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                    "event_cover_url": e.event_cover_url,
                    "pricing_type": e.pricing_type,
                    "price_fixed": e.price_fixed,
                    "price_min": e.price_min,
                    "price_max": e.price_max,
                    "payment_link": e.payment_link,
                    "_score": score,
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


# =========================
# EVENTS  USER: SZCZEGY EVENTU
# =========================
@app.get("/events/{event_id}")
def get_event_details(
    event_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .filter(Event.status == "published")
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        block_exists = (
            db.query(UserBlock)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id == event.partner_user_id)) |
                ((UserBlock.blocker_user_id == event.partner_user_id) & (UserBlock.blocked_user_id == current_user.id))
            )
            .first()
        )
        if block_exists:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        signups_count = (
            db.query(EventSignup)
            .filter(EventSignup.event_id == event.id)
            .count()
        )
        spots_left = None
        if event.capacity is not None:
            spots_left = max(event.capacity - signups_count, 0)

        event_tags = []
        if getattr(event, "interest_tags_json", None):
            try:
                event_tags = json.loads(event.interest_tags_json) or []
            except Exception:
                event_tags = []
        if not event_tags:
            event_tags = [event.interest_tag]

        return ok(
            {
                "id": event.id,
                "partner_user_id": event.partner_user_id,
            "organizer_name": getattr(partner_profile, "nazwa", None) if partner_profile else None,
            "organizer_logo_url": getattr(partner_profile, "logo_url", None) if partner_profile else None,
            "organizer_email": db.query(User).filter(User.id == event.partner_user_id).first().email if event.partner_user_id else None,
                "title": event.title,
                "description": event.description,
                "city": event.city,
                "interest_tag": event.interest_tag,
                "interest_tags": event_tags,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "capacity": event.capacity,
                "signups_count": signups_count,
                "spots_left": spots_left,
                "status": event.status,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "event_cover_url": event.event_cover_url,
                "pricing_type": event.pricing_type,
                "price_fixed": event.price_fixed,
                "price_min": event.price_min,
                "price_max": event.price_max,
                "payment_link": event.payment_link,
            }
        )
    finally:
        db.close()


# =========================
# UPLOADS (v1)  EVENT COVER (PARTNER)
# =========================
EVENT_COVERS_DIR = Path("uploads") / "event-covers"
EVENT_COVERS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/uploads/event-cover")
async def upload_event_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("partner")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"

    if require_r2_or_allow_local_uploads():
        event_cover_url = upload_media_to_r2(
            key=f"event-covers/{filename}",
            content=content,
            content_type=file.content_type,
        )
    else:
        path = EVENT_COVERS_DIR / filename
        with open(path, "wb") as f:
            f.write(content)
        event_cover_url = f"/uploads/static/event-covers/{filename}"

    return ok({"event_cover_url": event_cover_url})


# =========================
# EVENTS  PARTNER: LISTA SWOICH EVENTW
# =========================
@app.get("/partners/events")
def partner_list_events(
    status: Optional[str] = None,  # draft | published | archived
    city: Optional[str] = None,
    date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        partner_archive_cutoff = now_utc - timedelta(days=30)

        q = (
            db.query(Event)
            .filter(Event.partner_user_id == current_user.id)
            .filter(
                (Event.status == EventStatus.DRAFT.value)
                | (Event.end_at >= partner_archive_cutoff)
            )
        )

        if status is not None and status.strip() != "":
            st = status.strip()
            if st not in {"draft", "published", "archived"}:
                raise HTTPException(status_code=422, detail="INVALID_STATUS_FILTER")
            q = q.filter(Event.status == st)

        if city is not None and city.strip() != "":
            q = q.filter(Event.city == city.strip())

        if date is not None:
            start_dt = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_dt = datetime(date.year, date.month, date.day, 23, 59, 59)
            q = q.filter(Event.start_at >= start_dt)
            q = q.filter(Event.start_at <= end_dt)

        total = q.count()

        events = (
            q.order_by(Event.start_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = []
        for e in events:
            event_tags = []
            if getattr(e, "interest_tags_json", None):
                try:
                    event_tags = json.loads(e.interest_tags_json) or []
                except Exception:
                    event_tags = []
            if not event_tags:
                event_tags = [e.interest_tag]

            items.append(
                {
                    "id": e.id,
                    "partner_user_id": e.partner_user_id,
                    "title": e.title,
                    "description": e.description,
                    "city": e.city,
                    "where": e.where,
                    "address": e.address,
                    "location_lat": e.location_lat,
                    "location_lng": e.location_lng,
                    "interest_tag": e.interest_tag,
                    "interest_tags": event_tags,
                    "start_at": e.start_at,
                    "end_at": e.end_at,
                    "capacity": e.capacity,
                    "status": e.status,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                    "event_cover_url": e.event_cover_url,
                    "pricing_type": e.pricing_type,
                    "price_fixed": e.price_fixed,
                    "price_min": e.price_min,
                    "price_max": e.price_max,
                    "payment_link": e.payment_link,
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


# =========================
# EVENTS  PARTNER: SZCZEGY SWOJEGO EVENTU
# =========================
@app.get("/partners/events/{event_id}")
def partner_get_event_details(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        partner_archive_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        event_end_at = _ensure_utc(event.end_at)
        if event_end_at and event_end_at < partner_archive_cutoff:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        event_tags = []
        if getattr(event, "interest_tags_json", None):
            try:
                event_tags = json.loads(event.interest_tags_json) or []
            except Exception:
                event_tags = []
        if not event_tags:
            event_tags = [event.interest_tag]

        return ok(
            {
                "id": event.id,
                "partner_user_id": event.partner_user_id,
                "title": event.title,
                "description": event.description,
                "where": event.where,
                "city": event.city,
                "address": event.address,
                "location_lat": event.location_lat,
                "location_lng": event.location_lng,
                "interest_tag": event.interest_tag,
                "interest_tags": event_tags,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "capacity": event.capacity,
                "status": event.status,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "event_cover_url": event.event_cover_url,
                "pricing_type": event.pricing_type,
                "price_fixed": event.price_fixed,
                "price_min": event.price_min,
                "price_max": event.price_max,
                "payment_link": event.payment_link,
            }
        )
    finally:
        db.close()
# =========================
# EVENTS  USER: MOJE ZAPISY
# GET /users/me/events?limit=10&offset=0&sort=created_at_desc
# =========================


@app.delete("/events/{event_id}/save")
def unsave_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        saved = (
            db.query(EventSave)
            .filter(
                EventSave.event_id == event_id,
                EventSave.user_id == current_user.id,
            )
            .first()
        )

        if not saved:
            raise HTTPException(status_code=404, detail="SAVE_NOT_FOUND")

        db.delete(saved)
        db.commit()

        _audit(
            db,
            action="EVENT_UNSAVE",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"saved": False, "event_id": event_id})

    finally:
        db.close()




@app.get("/users/me/saved-events")
def my_saved_events(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        q = (
            db.query(EventSave, Event)
            .join(Event, Event.id == EventSave.event_id)
            .filter(EventSave.user_id == current_user.id)
            .filter(Event.status == "published")
            .order_by(EventSave.created_at.desc())
        )

        total = q.count()
        rows = q.offset(offset).limit(limit).all()

        items = []
        for saved, event in rows:
            items.append({
                "saved": {
                    "event_id": saved.event_id,
                    "created_at": saved.created_at,
                },
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "city": event.city,
                    "start_at": event.start_at,
                    "end_at": event.end_at,
                    "status": event.status,
                    "capacity": event.capacity,
                    "event_cover_url": event.event_cover_url,
                },
            })

        return ok({
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
        })
    finally:
        db.close()


@app.get("/users/me/events")
def my_event_signups(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = "created_at_desc",  # created_at_desc | created_at_asc | start_at_asc | start_at_desc
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        # sort
        if sort not in {"created_at_desc", "created_at_asc", "start_at_asc", "start_at_desc"}:
            raise HTTPException(status_code=422, detail="INVALID_SORT")

        q = (
            db.query(EventSignup, Event)
            .join(Event, Event.id == EventSignup.event_id)
            .filter(EventSignup.user_id == current_user.id)
            .filter(Event.status == "published")
        )

        total = q.count()

        # order by
        if sort == "created_at_desc":
            q = q.order_by(EventSignup.created_at.desc())
        elif sort == "created_at_asc":
            q = q.order_by(EventSignup.created_at.asc())
        elif sort == "start_at_asc":
            q = q.order_by(Event.start_at.asc())
        elif sort == "start_at_desc":
            q = q.order_by(Event.start_at.desc())

        rows = q.offset(offset).limit(limit).all()

        items = []
        for signup, event in rows:
            items.append(
                {
                    "signup": {
                        "event_id": signup.event_id,
                        "created_at": signup.created_at,
                    },
                    "event": {
                        "id": event.id,
                        "title": event.title,
                        "city": event.city,
                        "start_at": event.start_at,
                        "end_at": event.end_at,
                        "status": event.status,
                        "capacity": event.capacity,
                        "event_cover_url": event.event_cover_url,
                        "pricing_type": event.pricing_type,
                        "price_fixed": event.price_fixed,
                        "price_min": event.price_min,
                        "price_max": event.price_max,
                        "payment_link": event.payment_link,
                    },
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()
# =========================
# EVENTS  PARTNER: PARTICIPANTS
# GET /partners/events/{id}/participants?limit=10&offset=0
# =========================
@app.get("/partners/events/{event_id}/participants")
def partner_event_participants(
    event_id: int,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnie
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko waciciel
        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        partner_archive_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        event_end_at = _ensure_utc(event.end_at)
        if event_end_at and event_end_at < partner_archive_cutoff:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        blocked_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id != current_user.id)) |
                ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id != current_user.id))
            )
            .all()
        )
        blocked_user_ids = {
            blocked_user_id if blocker_user_id == current_user.id else blocker_user_id
            for blocker_user_id, blocked_user_id in blocked_rows
        }

        # 3) query zapisw + user
        q = (
            db.query(EventSignup, User)
            .join(User, User.id == EventSignup.user_id)
            .filter(EventSignup.event_id == event_id)
        )

        if blocked_user_ids:
            q = q.filter(~User.id.in_(blocked_user_ids))

        total = q.count()

        rows = (
            q.order_by(EventSignup.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for signup, user in rows:
            user_profile = (
                db.query(UserProfile)
                .filter(UserProfile.user_id == user.id)
                .first()
            )
            items.append(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nick": user_profile.nick if user_profile else None,
                    },
                    "signup": {
                        "created_at": signup.created_at,
                    },
                }
            )

        return ok(
            {
                "event_id": event_id,
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


# =========================
# EVENTS  PARTNER: OBSERVERS
# GET /partners/events/{id}/observers?limit=10&offset=0
# =========================
@app.get("/partners/events/{event_id}/observers")
def partner_event_observers(
    event_id: int,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        partner_archive_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        event_end_at = _ensure_utc(event.end_at)
        if event_end_at and event_end_at < partner_archive_cutoff:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        q = (
            db.query(EventSave, User)
            .join(User, User.id == EventSave.user_id)
            .filter(EventSave.event_id == event_id)
        )

        total = q.count()

        rows = (
            q.order_by(EventSave.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for saved, user in rows:
            user_profile = (
                db.query(UserProfile)
                .filter(UserProfile.user_id == user.id)
                .first()
            )
            items.append(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nick": user_profile.nick if user_profile else None,
                    },
                    "saved": {
                        "created_at": saved.created_at,
                    },
                }
            )

        return ok(
            {
                "event_id": event_id,
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()
# =========================
# EVENTS  PARTNER: STATS
# GET /partners/events/{id}/stats
# =========================

@app.get("/partners/dashboard/stats")
def partner_dashboard_stats(
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)

        events = (
            db.query(Event)
            .filter(Event.partner_user_id == current_user.id)
            .all()
        )

        draft_events = sum(1 for e in events if (e.status or "").lower() == "draft")

        active_events = [
            e for e in events
            if (e.status or "").lower() == "published"
            and e.end_at is not None
            and _ensure_utc(e.end_at) >= now_utc
        ]

        total_events = len(active_events)

        blocked_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id != current_user.id)) |
                ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id != current_user.id))
            )
            .all()
        )
        blocked_user_ids = {
            blocked_user_id if blocker_user_id == current_user.id else blocker_user_id
            for blocker_user_id, blocked_user_id in blocked_rows
        }

        active_event_ids = [e.id for e in active_events]
        total_signups = 0
        if active_event_ids:
            total_signups_q = (
                db.query(EventSignup)
                .filter(EventSignup.event_id.in_(active_event_ids))
            )
            if blocked_user_ids:
                total_signups_q = total_signups_q.filter(~EventSignup.user_id.in_(blocked_user_ids))
            total_signups = total_signups_q.count()

        total_capacity = 0
        free_spots = 0
        for e in active_events:
            if e.capacity is None:
                continue
            total_capacity += e.capacity
            signups_q = (
                db.query(EventSignup)
                .filter(EventSignup.event_id == e.id)
            )
            if blocked_user_ids:
                signups_q = signups_q.filter(~EventSignup.user_id.in_(blocked_user_ids))
            signups_count = signups_q.count()
            free_spots += max(e.capacity - signups_count, 0)

        return ok(
            {
                "total_events": total_events,
                "draft_events": draft_events,
                "total_signups": total_signups,
                "total_capacity": total_capacity,
                "free_spots": free_spots,
                "plan": current_user.plan if hasattr(current_user, "plan") else None,
            }
        )
    finally:
        db.close()


@app.get("/partners/events/{event_id}/stats")
def partner_event_stats(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnie
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko waciciel
        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        partner_archive_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        event_end_at = _ensure_utc(event.end_at)
        if event_end_at and event_end_at < partner_archive_cutoff:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        blocked_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id != current_user.id)) |
                ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id != current_user.id))
            )
            .all()
        )
        blocked_user_ids = {
            blocked_user_id if blocker_user_id == current_user.id else blocker_user_id
            for blocker_user_id, blocked_user_id in blocked_rows
        }

        # 3) policz zapisy
        q = (
            db.query(EventSignup)
            .filter(EventSignup.event_id == event_id)
        )

        if blocked_user_ids:
            q = q.filter(~EventSignup.user_id.in_(blocked_user_ids))

        signups_count = q.count()

        capacity = event.capacity  # moe by None
        spots_left = None
        if capacity is not None:
            spots_left = max(capacity - signups_count, 0)

        return ok(
            {
                "event_id": event_id,
                "signups_count": signups_count,
                "capacity": capacity,
                "spots_left": spots_left,
            }
        )
    finally:
        db.close()


class FriendRequestCreate(BaseModel):
    addressee_user_id: int




class GroupInvitationCreate(BaseModel):
    invitee_user_id: int


class GroupInvitationRespond(BaseModel):
    action: str = Field(pattern="^(accepted|rejected)$")


class FriendRequestRespond(BaseModel):
    action: str = Field(pattern="^(accepted|rejected)$")


class UserBlockCreate(BaseModel):
    blocked_user_id: int


class PushTokenRegisterRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    platform: str = Field(pattern="^(android|ios)$")
    device_id: str | None = Field(default=None, max_length=120)
    app_version: str | None = Field(default=None, max_length=40)


@app.post("/push/register-token")
def register_push_token(
    payload: PushTokenRegisterRequest,
    current_user: User = Depends(require_role("user", "partner")),
):
    token_value = payload.token.strip()
    if not token_value:
        raise HTTPException(status_code=400, detail="INVALID_PUSH_TOKEN")

    db = SessionLocal()
    try:
        existing = (
            db.query(DevicePushToken)
            .filter(DevicePushToken.token == token_value)
            .first()
        )

        now = datetime.utcnow()

        if existing:
            existing.user_id = current_user.id
            existing.platform = payload.platform
            existing.device_id = payload.device_id
            existing.app_version = payload.app_version
            existing.is_active = True
            existing.updated_at = now
            existing.last_seen_at = now
            token_row = existing
        else:
            token_row = DevicePushToken(
                user_id=current_user.id,
                token=token_value,
                platform=payload.platform,
                device_id=payload.device_id,
                app_version=payload.app_version,
                is_active=True,
                created_at=now,
                updated_at=now,
                last_seen_at=now,
            )
            db.add(token_row)

        db.commit()

        return ok(
            {
                "registered": True,
                "platform": token_row.platform,
            }
        )
    finally:
        db.close()


@app.post("/blocks")
def create_user_block(
    payload: UserBlockCreate,
    current_user: User = Depends(require_role("user", "partner")),
):
    db = SessionLocal()
    try:
        if payload.blocked_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="CANNOT_BLOCK_SELF")

        target = (
            db.query(User)
            .filter(User.id == payload.blocked_user_id)
            .filter(User.status == UserStatus.ACTIVE.value)
            .first()
        )
        if not target:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        existing = (
            db.query(UserBlock)
            .filter(
                UserBlock.blocker_user_id == current_user.id,
                UserBlock.blocked_user_id == payload.blocked_user_id,
            )
            .first()
        )

        blocker = current_user
        blocked = target

        def cleanup_partner_user_event_signups():
            if {blocker.role, blocked.role} != {"partner", "user"}:
                return

            partner_user_id = blocker.id if blocker.role == "partner" else blocked.id
            regular_user_id = blocker.id if blocker.role == "user" else blocked.id

            partner_event_ids = [
                event_id
                for (event_id,) in (
                    db.query(Event.id)
                    .filter(Event.partner_user_id == partner_user_id)
                    .all()
                )
            ]

            if partner_event_ids:
                (
                    db.query(EventSignup)
                    .filter(
                        EventSignup.user_id == regular_user_id,
                        EventSignup.event_id.in_(partner_event_ids),
                    )
                    .delete(synchronize_session=False)
                )

        if existing:
            cleanup_partner_user_event_signups()
            db.commit()
            return ok({
                "blocker_user_id": existing.blocker_user_id,
                "blocked_user_id": existing.blocked_user_id,
                "created_at": existing.created_at,
                "already_blocked": True,
            })

        block = UserBlock(
            blocker_user_id=current_user.id,
            blocked_user_id=payload.blocked_user_id,
        )
        db.add(block)

        (
            db.query(Friendship)
            .filter(
                ((Friendship.requester_user_id == current_user.id) & (Friendship.addressee_user_id == payload.blocked_user_id)) |
                ((Friendship.requester_user_id == payload.blocked_user_id) & (Friendship.addressee_user_id == current_user.id))
            )
            .delete(synchronize_session=False)
        )

        cleanup_partner_user_event_signups()

        db.commit()
        db.refresh(block)

        return ok({
            "blocker_user_id": block.blocker_user_id,
            "blocked_user_id": block.blocked_user_id,
            "created_at": block.created_at,
            "already_blocked": False,
        })
    finally:
        db.close()


# =========================
# AI MODERATION — TEXT MESSAGES
# =========================
def moderate_message_text_or_raise(content: str):
    text = str(content or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="message_empty")

    lowered = text.lower()
    blocked_link_markers = ["http://", "https://", "www.", ".pl", ".com", ".net", ".org"]
    if any(marker in lowered for marker in blocked_link_markers):
        raise HTTPException(status_code=422, detail="message_blocked_link")

    if not _openai_client:
        return

    try:
        response = _openai_client.responses.create(
            model=os.getenv("OPENAI_MODERATION_MODEL", "gpt-4.1-mini"),
            input=[
                {
                    "role": "system",
                    "content": (
                        "You moderate short Polish messages in a social/event app. "
                        "Return only JSON with keys: allowed:boolean, reason:string. "
                        "Block harassment, hate, sexual solicitation, threats, scams, spam, attempts to move users off-platform, and explicit content. "
                        "Allow normal friendly conversation, event planning, logistics, and mild casual language."
                    ),
                },
                {"role": "user", "content": text[:2000]},
            ],
        )
        raw = getattr(response, "output_text", "") or ""
        import json
        data = json.loads(raw)
        if data.get("allowed") is False:
            raise HTTPException(status_code=422, detail=f"message_blocked_ai:{data.get('reason') or 'policy'}")
    except HTTPException:
        raise
    except Exception as e:
        print("AI MESSAGE MODERATION ERROR:", e)
        return


# =========================
# MESSAGES — PRIVATE (MVP TESTERSKI)
# =========================
@app.post("/messages/private")
def send_private_message(
    payload: PrivateMessageCreate,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        if payload.recipient_user_id == current_user.id:
            raise HTTPException(status_code=422, detail="CANNOT_MESSAGE_SELF")

        recipient = db.query(User).filter(User.id == payload.recipient_user_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        block_exists = (
            db.query(UserBlock)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id == payload.recipient_user_id)) |
                ((UserBlock.blocker_user_id == payload.recipient_user_id) & (UserBlock.blocked_user_id == current_user.id))
            )
            .first()
        )
        if block_exists:
            raise HTTPException(status_code=403, detail="USER_BLOCKED")

        moderated_content = payload.content.strip()
        moderate_message_text_or_raise(moderated_content)

        msg = Message(
            sender_user_id=current_user.id,
            recipient_user_id=payload.recipient_user_id,
            content=moderated_content,
            is_read=False,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        return ok(
            MessageOut(
                id=msg.id,
                sender_user_id=msg.sender_user_id,
                recipient_user_id=msg.recipient_user_id,
                group_id=msg.group_id,
                content=msg.content,
                created_at=msg.created_at,
                is_read=msg.is_read,
            ).model_dump()
        )
    finally:
        db.close()


@app.get("/messages/private/{user_id}")
def list_private_messages(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        other_user = db.query(User).filter(User.id == user_id).first()
        if not other_user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        block_exists = (
            db.query(UserBlock)
            .filter(
                ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id == user_id)) |
                ((UserBlock.blocker_user_id == user_id) & (UserBlock.blocked_user_id == current_user.id))
            )
            .first()
        )
        if block_exists:
            return ok({
                "items": [],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": 0,
                },
            })

        q = db.query(Message).filter(
            Message.group_id.is_(None),
            (
                ((Message.sender_user_id == current_user.id) & (Message.recipient_user_id == user_id)) |
                ((Message.sender_user_id == user_id) & (Message.recipient_user_id == current_user.id))
            )
        )

        db.query(Message).filter(
            Message.group_id.is_(None),
            Message.sender_user_id == user_id,
            Message.recipient_user_id == current_user.id,
            Message.is_read.is_(False),
        ).update(
            {Message.is_read: True},
            synchronize_session=False,
        )
        db.commit()

        total = q.count()
        rows = (
            q.order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = [
            MessageOut(
                id=m.id,
                sender_user_id=m.sender_user_id,
                recipient_user_id=m.recipient_user_id,
                group_id=m.group_id,
                content=m.content,
                created_at=m.created_at,
                is_read=m.is_read,
            ).model_dump()
            for m in rows
        ]

        return ok({
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
        })
    finally:
        db.close()



@app.post("/messages/group")
def send_group_message(
    payload: GroupMessageCreate,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == payload.group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.group_id == payload.group_id,
                GroupMembership.user_id == current_user.id,
            )
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="GROUP_MEMBERSHIP_REQUIRED")

        moderated_content = payload.content.strip()
        moderate_message_text_or_raise(moderated_content)

        msg = Message(
            sender_user_id=current_user.id,
            group_id=payload.group_id,
            content=moderated_content,
            is_read=False,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        return ok(
            MessageOut(
                id=msg.id,
                sender_user_id=msg.sender_user_id,
                recipient_user_id=msg.recipient_user_id,
                group_id=msg.group_id,
                content=msg.content,
                created_at=msg.created_at,
                is_read=msg.is_read,
            ).model_dump()
        )
    finally:
        db.close()


@app.get("/messages/group/{group_id}")
def list_group_messages(
    group_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == current_user.id,
            )
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="GROUP_MEMBERSHIP_REQUIRED")

        q = db.query(Message).filter(
            Message.group_id == group_id,
            Message.recipient_user_id.is_(None),
        )

        blocked_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                (UserBlock.blocker_user_id == current_user.id) |
                (UserBlock.blocked_user_id == current_user.id)
            )
            .all()
        )
        blocked_user_ids = {
            blocked_id if blocker_id == current_user.id else blocker_id
            for blocker_id, blocked_id in blocked_rows
        }

        if blocked_user_ids:
            q = q.filter(~Message.sender_user_id.in_(blocked_user_ids))

        total = q.count()
        rows = (
            q.order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = [
            MessageOut(
                id=m.id,
                sender_user_id=m.sender_user_id,
                recipient_user_id=m.recipient_user_id,
                group_id=m.group_id,
                content=m.content,
                created_at=m.created_at,
                is_read=m.is_read,
            ).model_dump()
            for m in rows
        ]

        return ok({
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
        })
    finally:
        db.close()


@app.get("/messages/private")
def list_private_conversations(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        rows = (
            db.query(Message)
            .filter(
                Message.group_id.is_(None),
                (
                    (Message.sender_user_id == current_user.id) |
                    (Message.recipient_user_id == current_user.id)
                )
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .all()
        )

        latest_by_other_user_id = {}
        for m in rows:
            other_user_id = (
                m.recipient_user_id
                if m.sender_user_id == current_user.id
                else m.sender_user_id
            )
            if other_user_id is None:
                continue
            if other_user_id not in latest_by_other_user_id:
                latest_by_other_user_id[other_user_id] = m

        other_user_ids = list(latest_by_other_user_id.keys())

        if other_user_ids:
            blocked_rows = (
                db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
                .filter(
                    ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id.in_(other_user_ids))) |
                    ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id.in_(other_user_ids)))
                )
                .all()
            )
            blocked_user_ids = {
                blocked_id if blocker_id == current_user.id else blocker_id
                for blocker_id, blocked_id in blocked_rows
            }
            latest_by_other_user_id = {
                other_user_id: msg
                for other_user_id, msg in latest_by_other_user_id.items()
                if other_user_id not in blocked_user_ids
            }
            other_user_ids = list(latest_by_other_user_id.keys())

        users = (
            db.query(User)
            .filter(User.id.in_(other_user_ids))
            .all()
            if other_user_ids else []
        )
        user_profiles = (
            db.query(UserProfile)
            .filter(UserProfile.user_id.in_(other_user_ids))
            .all()
            if other_user_ids else []
        )
        partner_profiles = (
            db.query(
                PartnerProfile.user_id,
                PartnerProfile.nazwa,
                PartnerProfile.bio,
                PartnerProfile.logo_url,
                PartnerProfile.kategoria,
            )
            .filter(PartnerProfile.user_id.in_(other_user_ids))
            .all()
            if other_user_ids else []
        )

        users_by_id = {u.id: u for u in users}
        user_profiles_by_user_id = {p.user_id: p for p in user_profiles}
        partner_profiles_by_user_id = {
            row.user_id: {
                "nazwa": row.nazwa,
                "bio": row.bio,
                "logo_url": row.logo_url,
                "kategoria": row.kategoria,
            }
            for row in partner_profiles
        }

        unread_counts = {}
        unread_rows = (
            db.query(Message.recipient_user_id, Message.sender_user_id)
            .filter(
                Message.group_id.is_(None),
                Message.recipient_user_id == current_user.id,
                Message.is_read.is_(False),
            )
            .all()
        )
        for _, sender_user_id in unread_rows:
            if sender_user_id is None:
                continue
            unread_counts[sender_user_id] = unread_counts.get(sender_user_id, 0) + 1

        items = []
        for other_user_id, m in latest_by_other_user_id.items():
            other = users_by_id.get(other_user_id)
            user_profile = user_profiles_by_user_id.get(other_user_id)
            partner_profile = partner_profiles_by_user_id.get(other_user_id)

            role = getattr(other, "role", None)
            if role == "partner":
                display_name = (
                    ((partner_profile or {}).get("nazwa"))
                    or getattr(user_profile, "nick", None)
                )
            else:
                display_name = (
                    getattr(user_profile, "nick", None)
                    or ((partner_profile or {}).get("nazwa"))
                )

            fallback_name = (
                "Organizator"
                if role == "partner"
                else f"Użytkownik #{other_user_id}"
            )

            items.append({
                "other_user_id": other_user_id,
                "other_user_role": role,
                "other_user_name": (
                    display_name
                    or fallback_name
                ),
                "other_user_avatar_url": (
                    getattr(user_profile, "avatar_url", None)
                    or ((partner_profile or {}).get("logo_url"))
                    or ""
                ),
                "other_user_bio": (
                    getattr(user_profile, "bio", None)
                    or ((partner_profile or {}).get("bio"))
                    or ""
                ),
                "other_user_company": (
                    ((partner_profile or {}).get("nazwa"))
                    or ""
                ),
                "other_user_category": (
                    ((partner_profile or {}).get("kategoria"))
                    or ""
                ),
                "last_message": m.content,
                "last_message_at": m.created_at,
                "unread_count": int(unread_counts.get(other_user_id, 0)),
            })

        items.sort(
            key=lambda x: x["last_message_at"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return ok({
            "items": items[:limit],
            "pagination": {
                "limit": limit,
                "total": len(items),
            },
        })
    finally:
        db.close()




# =========================
# FRIENDSHIPS / FRIEND REQUESTS
# =========================
@app.post("/friends/requests")
def create_friend_request(
    payload: FriendRequestCreate,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        if payload.addressee_user_id == current_user.id:
            raise HTTPException(status_code=422, detail="CANNOT_ADD_SELF")

        target = db.query(User).filter(User.id == payload.addressee_user_id, User.role == "user").first()
        if not target:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        existing = db.query(Friendship).filter(
            ((Friendship.requester_user_id == current_user.id) & (Friendship.addressee_user_id == payload.addressee_user_id)) |
            ((Friendship.requester_user_id == payload.addressee_user_id) & (Friendship.addressee_user_id == current_user.id))
        ).first()

        if existing:
            return ok({
                "id": existing.id,
                "status": existing.status,
                "requester_user_id": existing.requester_user_id,
                "addressee_user_id": existing.addressee_user_id,
            })

        fr = Friendship(
            requester_user_id=current_user.id,
            addressee_user_id=payload.addressee_user_id,
            status="pending",
        )
        db.add(fr)
        db.flush()

        db.add(UserNotification(
            user_id=payload.addressee_user_id,
            partner_user_id=current_user.id,
            type="friend_request",
        ))

        db.commit()
        db.refresh(fr)

        return ok({
            "id": fr.id,
            "status": fr.status,
            "requester_user_id": fr.requester_user_id,
            "addressee_user_id": fr.addressee_user_id,
        })
    finally:
        db.close()


@app.get("/friends/requests")
def list_friend_requests(
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        incoming_rows = (
            db.query(Friendship, UserProfile)
            .join(UserProfile, UserProfile.user_id == Friendship.requester_user_id, isouter=True)
            .filter(
                Friendship.addressee_user_id == current_user.id,
                Friendship.status == "pending",
            )
            .order_by(Friendship.created_at.desc(), Friendship.id.desc())
            .all()
        )

        outgoing_rows = (
            db.query(Friendship, UserProfile)
            .join(UserProfile, UserProfile.user_id == Friendship.addressee_user_id, isouter=True)
            .filter(
                Friendship.requester_user_id == current_user.id,
                Friendship.status == "pending",
            )
            .order_by(Friendship.created_at.desc(), Friendship.id.desc())
            .all()
        )

        incoming = [
            {
                "id": fr.id,
                "status": fr.status,
                "created_at": fr.created_at.isoformat() if fr.created_at else None,
                "user": {
                    "id": fr.requester_user_id,
                    "nick": profile.nick if profile and profile.nick else "Użytkownik",
                    "city": profile.miasto if profile else "",
                    "avatar_url": profile.avatar_url if profile else "",
                },
            }
            for fr, profile in incoming_rows
        ]

        outgoing = [
            {
                "id": fr.id,
                "status": fr.status,
                "created_at": fr.created_at.isoformat() if fr.created_at else None,
                "user": {
                    "id": fr.addressee_user_id,
                    "nick": profile.nick if profile and profile.nick else "Użytkownik",
                    "city": profile.miasto if profile else "",
                    "avatar_url": profile.avatar_url if profile else "",
                },
            }
            for fr, profile in outgoing_rows
        ]

        return ok({
            "incoming": incoming,
            "outgoing": outgoing,
        })
    finally:
        db.close()




@app.get("/group-invitations")
def list_group_invitations(
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        incoming_rows = (
            db.query(GroupInvitation, Group, UserProfile)
            .join(Group, Group.id == GroupInvitation.group_id)
            .join(UserProfile, UserProfile.user_id == GroupInvitation.inviter_user_id, isouter=True)
            .filter(
                GroupInvitation.invitee_user_id == current_user.id,
                GroupInvitation.status == "pending",
            )
            .order_by(GroupInvitation.created_at.desc(), GroupInvitation.id.desc())
            .all()
        )

        outgoing_rows = (
            db.query(GroupInvitation, Group, UserProfile)
            .join(Group, Group.id == GroupInvitation.group_id)
            .join(UserProfile, UserProfile.user_id == GroupInvitation.invitee_user_id, isouter=True)
            .filter(
                GroupInvitation.inviter_user_id == current_user.id,
                GroupInvitation.status == "pending",
            )
            .order_by(GroupInvitation.created_at.desc(), GroupInvitation.id.desc())
            .all()
        )

        incoming = [
            {
                "id": inv.id,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "group": {
                    "id": group.id,
                    "title": group.title,
                    "interest_tag": group.interest_tag,
                },
                "user": {
                    "id": inv.inviter_user_id,
                    "nick": profile.nick if profile and profile.nick else "Użytkownik",
                    "city": profile.miasto if profile else "",
                    "avatar_url": profile.avatar_url if profile else "",
                },
            }
            for inv, group, profile in incoming_rows
        ]

        outgoing = [
            {
                "id": inv.id,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "group": {
                    "id": group.id,
                    "title": group.title,
                    "interest_tag": group.interest_tag,
                },
                "user": {
                    "id": inv.invitee_user_id,
                    "nick": profile.nick if profile and profile.nick else "Użytkownik",
                    "city": profile.miasto if profile else "",
                    "avatar_url": profile.avatar_url if profile else "",
                },
            }
            for inv, group, profile in outgoing_rows
        ]

        return ok({
            "incoming": incoming,
            "outgoing": outgoing,
        })
    finally:
        db.close()





@app.post("/group-invitations/{invitation_id}/respond")
def respond_group_invitation(
    invitation_id: int,
    payload: GroupInvitationRespond,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        inv = db.query(GroupInvitation).filter(
            GroupInvitation.id == invitation_id,
            GroupInvitation.invitee_user_id == current_user.id,
            GroupInvitation.status == "pending",
        ).first()

        if not inv:
            raise HTTPException(status_code=404, detail="GROUP_INVITATION_NOT_FOUND")

        if payload.action == "accepted":
            group = db.query(Group).filter(Group.id == inv.group_id).first()
            if not group:
                raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

            existing_membership = db.query(GroupMembership).filter(
                GroupMembership.user_id == current_user.id,
                GroupMembership.group_id == inv.group_id,
            ).first()

            if not existing_membership:
                membership = GroupMembership(
                    user_id=current_user.id,
                    group_id=inv.group_id,
                    role="member",
                )
                db.add(membership)
                group.members_count += 1
                db.add(group)

        inv.status = payload.action
        inv.responded_at = datetime.utcnow()
        db.add(inv)
        db.commit()
        db.refresh(inv)

        return ok({
            "id": inv.id,
            "status": inv.status,
            "group_id": inv.group_id,
        })
    finally:
        db.close()



@app.post("/friends/requests/{request_id}/respond")
def respond_friend_request(
    request_id: int,
    payload: FriendRequestRespond,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        fr = db.query(Friendship).filter(
            Friendship.id == request_id,
            Friendship.addressee_user_id == current_user.id,
            Friendship.status == "pending",
        ).first()

        if not fr:
            raise HTTPException(status_code=404, detail="FRIEND_REQUEST_NOT_FOUND")

        fr.status = payload.action
        fr.responded_at = datetime.utcnow()
        db.add(fr)
        db.commit()
        db.refresh(fr)

        return ok({
            "id": fr.id,
            "status": fr.status,
            "requester_user_id": fr.requester_user_id,
            "addressee_user_id": fr.addressee_user_id,
        })
    finally:
        db.close()


@app.get("/friends")
def list_friends(
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        rows = (
            db.query(Friendship)
            .filter(
                Friendship.status == "accepted",
                (
                    (Friendship.requester_user_id == current_user.id) |
                    (Friendship.addressee_user_id == current_user.id)
                )
            )
            .order_by(Friendship.created_at.desc(), Friendship.id.desc())
            .all()
        )

        friend_ids = [
            fr.addressee_user_id if fr.requester_user_id == current_user.id else fr.requester_user_id
            for fr in rows
        ]

        if friend_ids:
            blocked_rows = (
                db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
                .filter(
                    ((UserBlock.blocker_user_id == current_user.id) & (UserBlock.blocked_user_id.in_(friend_ids))) |
                    ((UserBlock.blocked_user_id == current_user.id) & (UserBlock.blocker_user_id.in_(friend_ids)))
                )
                .all()
            )
            blocked_friend_ids = {
                blocked_id if blocker_id == current_user.id else blocker_id
                for blocker_id, blocked_id in blocked_rows
            }
            friend_ids = [fid for fid in friend_ids if fid not in blocked_friend_ids]

        profiles = (
            db.query(UserProfile)
            .filter(UserProfile.user_id.in_(friend_ids))
            .all()
            if friend_ids else []
        )
        profiles_by_user_id = {p.user_id: p for p in profiles}

        items = []
        for fid in friend_ids:
            profile = profiles_by_user_id.get(fid)

            interests = []
            if profile and profile.zainteresowania_json:
                try:
                    interests = json.loads(profile.zainteresowania_json) or []
                except Exception:
                    interests = []

            items.append({
                "id": fid,
                "nick": profile.nick if profile and profile.nick else "Użytkownik",
                "city": profile.miasto if profile else "",
                "avatar_url": profile.avatar_url if profile else "",
                "interests": interests,
            })

        return ok({"items": items})
    finally:
        db.close()


# =========================
# GROUPS MY
# =========================

# =========================
@app.get("/groups/my")
def list_my_groups(
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        memberships = (
            db.query(GroupMembership, Group)
            .join(Group, GroupMembership.group_id == Group.id)
            .filter(GroupMembership.user_id == current_user.id)
            .all()
        )

        items = []

        for m, g in memberships:
            items.append(
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "interest_tag": g.interest_tag,
                    "members_count": g.members_count,
                    "joined_at": m.joined_at,
                    "is_creator": g.creator_id == current_user.id,
                }
            )

        return ok({"items": items})

    finally:
        db.close()


# =========================
# GROUP CREATE
# =========================
@app.post("/groups")
def create_group(
    payload: CreateGroupRequest,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            raise HTTPException(status_code=400, detail="PROFILE_NOT_FOUND")

        # limit tworzenia grup wg planu
        create_limits = {
            "free": 0,
            "plus": 1,
            "premium": 3,
            "vip": None,
        }

        limit = create_limits.get(profile.plan, 0)

        if limit is not None:
            created_count = (
                db.query(Group)
                .filter(Group.creator_id == current_user.id)
                .count()
            )

            if created_count >= limit:
                raise HTTPException(status_code=400, detail="GROUP_CREATE_LIMIT_REACHED")

        g = Group(
            creator_id=current_user.id,
            title=payload.title,
            description=payload.description,
            interest_tag=payload.interest_tag,
        )

        db.add(g)
        db.commit()
        db.refresh(g)

        # creator automatycznie dołącza
        m = GroupMembership(
            user_id=current_user.id,
            group_id=g.id,
            role="owner",
        )

        db.add(m)
        g.members_count = 1

        db.commit()

        return ok({"id": g.id})

    finally:
        db.close()

@app.get("/groups")
def list_groups(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = SessionLocal()
    try:
        q = db.query(Group)

        total = q.count()

        groups = (
            q.order_by(Group.members_count.desc(), Group.id.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = []
        for g in groups:
            items.append(
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "interest_tag": g.interest_tag,
                    "members_count": g.members_count,
                    "created_at": g.created_at,
                    "updated_at": g.updated_at,
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()



# =========================
# GROUP JOIN
# =========================
@app.post("/groups/{group_id}/join")
def join_group(
    group_id: int,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            raise HTTPException(status_code=400, detail="PROFILE_NOT_FOUND")

        # sprawdź czy już jest w grupie
        existing = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.user_id == current_user.id,
                GroupMembership.group_id == group_id,
            )
            .first()
        )

        if existing:
            return ok({"msg": "ALREADY_MEMBER"})

        # limit planu
        plan_limits = {
            "free": 1,
            "plus": 3,
            "premium": None,
            "vip": None,
        }

        limit = plan_limits.get(profile.plan, 1)

        if limit is not None:
            count = (
                db.query(GroupMembership)
                .filter(GroupMembership.user_id == current_user.id)
                .count()
            )

            if count >= limit:
                raise HTTPException(status_code=400, detail="GROUP_LIMIT_REACHED")

        m = GroupMembership(
            user_id=current_user.id,
            group_id=group_id,
        )

        db.add(m)

        (
            db.query(GroupInvitation)
            .filter(
                GroupInvitation.group_id == group_id,
                GroupInvitation.invitee_user_id == current_user.id,
                GroupInvitation.status == "pending",
            )
            .delete(synchronize_session=False)
        )

        g.members_count += 1

        db.commit()

        return ok({"joined": True})

    finally:
        db.close()



# =========================
# GROUP LEAVE
# =========================
@app.post("/groups/{group_id}/leave")
def leave_group(
    group_id: int,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.user_id == current_user.id,
                GroupMembership.group_id == group_id,
            )
            .first()
        )

        if not membership:
            return ok({"left": False, "msg": "NOT_A_MEMBER"})

        if membership.role == "owner":
            raise HTTPException(status_code=400, detail="GROUP_OWNER_CANNOT_LEAVE")

        db.delete(membership)

        if g.members_count > 0:
            g.members_count -= 1

        db.commit()

        return ok({"left": True})

    finally:
        db.close()






@app.post("/groups/{group_id}/invite")
def invite_to_group(
    group_id: int,
    payload: GroupInvitationCreate,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.user_id == current_user.id,
                GroupMembership.group_id == group_id,
            )
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="GROUP_INVITE_REQUIRES_MEMBERSHIP")

        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            raise HTTPException(status_code=400, detail="PROFILE_NOT_FOUND")

        inviter_plan = (profile.plan or "free").lower()
        if inviter_plan not in {"premium", "vip"}:
            raise HTTPException(status_code=403, detail="GROUP_INVITE_PLAN_REQUIRED")

        if payload.invitee_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="CANNOT_INVITE_SELF")

        existing_membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == payload.invitee_user_id,
            )
            .first()
        )

        if existing_membership:
            raise HTTPException(status_code=400, detail="USER_ALREADY_IN_GROUP")

        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.status == "accepted",
                (
                    ((Friendship.requester_user_id == current_user.id) & (Friendship.addressee_user_id == payload.invitee_user_id)) |
                    ((Friendship.requester_user_id == payload.invitee_user_id) & (Friendship.addressee_user_id == current_user.id))
                )
            )
            .first()
        )

        if not friendship:
            raise HTTPException(status_code=400, detail="GROUP_INVITE_ONLY_FOR_FRIENDS")

        existing = (
            db.query(GroupInvitation)
            .filter(
                GroupInvitation.group_id == group_id,
                GroupInvitation.invitee_user_id == payload.invitee_user_id,
                GroupInvitation.status == "pending",
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="GROUP_INVITATION_ALREADY_PENDING")

        inv = GroupInvitation(
            group_id=group_id,
            inviter_user_id=current_user.id,
            invitee_user_id=payload.invitee_user_id,
            status="pending",
        )
        db.add(inv)
        db.add(
            UserNotification(
                user_id=payload.invitee_user_id,
                partner_user_id=current_user.id,
                type="group_invitation",
            )
        )
        db.commit()
        db.refresh(inv)

        return ok({
            "id": inv.id,
            "status": inv.status,
        })

    finally:
        db.close()


@app.post("/groups/{group_id}/close")
def close_group(
    group_id: int,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.user_id == current_user.id,
                GroupMembership.group_id == group_id,
            )
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="GROUP_MEMBERSHIP_REQUIRED")

        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        db.delete(g)
        db.commit()

        return ok({"closed": True})

    finally:
        db.close()



@app.get("/groups/suggested")
def list_suggested_groups(
    current_user: User = Depends(require_role("user")),
    limit: int = Query(20, ge=1, le=100),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            raise HTTPException(status_code=400, detail="PROFILE_NOT_FOUND")

        raw_interests = []
        if profile.zainteresowania_json:
            try:
                raw_interests = json.loads(profile.zainteresowania_json) or []
            except Exception:
                raw_interests = []

        def norm_tag(value: str | None) -> str:
            if not value:
                return ""
            v = value.strip().lower()
            aliases = {
                "foto": "fotografia",
                "photo": "fotografia",
                "film": "kino",
                "movies": "kino",
                "movie": "kino",
                "tech": "ai",
                "startup": "biznes",
                "startups": "biznes",
            }
            return aliases.get(v, v)

        user_interest_set = {norm_tag(x) for x in raw_interests if x and str(x).strip()}
        joined_group_ids = {
            row[0]
            for row in db.query(GroupMembership.group_id)
            .filter(GroupMembership.user_id == current_user.id)
            .all()
        }

        groups = db.query(Group).all()

        scored = []
        for g in groups:
            if g.id in joined_group_ids:
                continue

            group_tag = norm_tag(g.interest_tag)
            score = 1 if group_tag and group_tag in user_interest_set else 0

            scored.append(
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "interest_tag": g.interest_tag,
                    "members_count": g.members_count,
                    "created_at": g.created_at,
                    "updated_at": g.updated_at,
                    "_score": score,
                }
            )

        scored.sort(key=lambda x: (-x["_score"], -x["members_count"], x["id"]))

        items = []
        for item in scored[:limit]:
            item.pop("_score", None)
            items.append(item)

        return ok({"items": items})
    finally:
        db.close()


@app.get("/groups/{group_id}/people")
def get_group_people(
    group_id: int,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        current_membership = (
            db.query(GroupMembership)
            .filter(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == current_user.id,
            )
            .first()
        )

        if not current_membership:
            raise HTTPException(status_code=403, detail="GROUP_ACCESS_REQUIRES_MEMBERSHIP")

        blocked_rows = (
            db.query(UserBlock.blocker_user_id, UserBlock.blocked_user_id)
            .filter(
                (UserBlock.blocker_user_id == current_user.id) |
                (UserBlock.blocked_user_id == current_user.id)
            )
            .all()
        )
        blocked_user_ids = {
            blocked_user_id if blocker_user_id == current_user.id else blocker_user_id
            for blocker_user_id, blocked_user_id in blocked_rows
        }

        member_rows = (
            db.query(GroupMembership, UserProfile)
            .join(UserProfile, UserProfile.user_id == GroupMembership.user_id, isouter=True)
            .filter(GroupMembership.group_id == group_id)
            .order_by(
                GroupMembership.user_id == g.creator_id,
                GroupMembership.joined_at.asc(),
                GroupMembership.id.asc(),
            )
            .all()
        )

        members = []
        for membership, profile in member_rows:
            if membership.user_id in blocked_user_ids:
                continue
            members.append({
                "id": membership.user_id,
                "nick": profile.nick if profile and profile.nick else "Użytkownik",
                "city": profile.miasto if profile else "",
                "avatar_url": profile.avatar_url if profile else "",
                "is_founder": membership.user_id == g.creator_id,
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            })

        invited_rows = (
            db.query(GroupInvitation, UserProfile)
            .join(UserProfile, UserProfile.user_id == GroupInvitation.invitee_user_id, isouter=True)
            .filter(
                GroupInvitation.group_id == group_id,
                GroupInvitation.status == "pending",
            )
            .order_by(GroupInvitation.created_at.desc(), GroupInvitation.id.desc())
            .all()
        )

        invited = []
        for invitation, profile in invited_rows:
            if invitation.invitee_user_id in blocked_user_ids:
                continue
            invited.append({
                "id": invitation.invitee_user_id,
                "nick": profile.nick if profile and profile.nick else "Użytkownik",
                "city": profile.miasto if profile else "",
                "avatar_url": profile.avatar_url if profile else "",
                "invitation_id": invitation.id,
                "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
            })

        return ok({
            "group_id": g.id,
            "members": members,
            "invited": invited,
        })
    finally:
        db.close()


@app.get("/groups/{group_id}")
def get_group_details(group_id: int):
    db = SessionLocal()
    try:
        g = db.query(Group).filter(Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

        return ok(
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "interest_tag": g.interest_tag,
                "members_count": g.members_count,
                "created_at": g.created_at,
                "updated_at": g.updated_at,
            }
        )
    finally:
        db.close()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    _rid = getattr(request.state, "request_id", None)
    headers = {"x-request-id": _rid} if _rid else {}
    lang = request.headers.get("accept-language")
    return JSONResponse(
        status_code=429,
        headers=headers,
        content=fail(code=ErrorCode.RATE_LIMITED, lang=lang),
    )

@app.get("/api/legal/terms_pl")
def get_terms_pl():
    return FileResponse("legal/terms_pl.md")

@app.get("/api/legal/terms_en")
def get_terms_en():
    return FileResponse("legal/terms_en.md")


# =========================

def send_push_to_user(db, user_id: int, title: str, body: str, data: dict | None = None) -> bool:
    if not firebase_admin._apps:
        return False

    tokens = (
        db.query(DevicePushToken)
        .filter(DevicePushToken.user_id == user_id)
        .filter(DevicePushToken.is_active == True)
        .all()
    )

    if not tokens:
        return False

    sent_any = False
    payload_data = {str(k): str(v) for k, v in (data or {}).items()}

    for token_row in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=payload_data,
                token=token_row.token,
            )
            messaging.send(message)
            sent_any = True
        except Exception as exc:
            print("PUSH SEND ERROR:", exc)

    return sent_any


async def send_bug_email(subject: str, body: str):
    try:
        import smtplib
        import ssl

        smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
        smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
        smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
        smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

        if not smtp_host or not smtp_user or not smtp_pass:
            print("MAIL ERROR: missing USLY SMTP config")
            return False

        msg = EmailMessage()
        msg["From"] = smtp_from
        msg["To"] = "kontakt@uslyapp.pl"
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except ssl.SSLCertVerificationError:
            context = ssl._create_unverified_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        return True
    except Exception as e:
        print("MAIL ERROR:", e)
        return False

async def send_user_email(to_email: str, subject: str, body: str):
    try:
        import smtplib
        import ssl

        to_email = str(to_email or "").strip()
        if not to_email or "@" not in to_email:
            return False

        smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
        smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
        smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
        smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

        if not smtp_host or not smtp_user or not smtp_pass:
            print("USER MAIL ERROR: missing USLY SMTP config")
            return False

        msg = EmailMessage()
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except ssl.SSLCertVerificationError:
            context = ssl._create_unverified_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        return True
    except Exception as e:
        print("USER MAIL ERROR:", e)
        return False


# ENTERPRISE CONTACT LEADS
# =========================
@app.post("/enterprise/contact")
async def submit_enterprise_contact(payload: dict):
    from pathlib import Path
    from datetime import datetime
    import json

    company = str((payload or {}).get("company") or "").strip()
    city = str((payload or {}).get("city") or "").strip()
    contact = str((payload or {}).get("contact") or "").strip()
    locations = str((payload or {}).get("locations") or "").strip()
    needs = str((payload or {}).get("needs") or "").strip()
    extra = str((payload or {}).get("extra") or "").strip()

    if not contact:
        raise HTTPException(status_code=422, detail="enterprise_contact_required")

    account_email = str((payload or {}).get("account_email") or "").strip()
    user_id = (payload or {}).get("user_id")

    now = datetime.utcnow()
    ticket = f"ENT-{now.strftime('%Y%m%d%H%M%S')}"

    lead = {
        "ticket": ticket,
        "created_at": now.isoformat(),
        "user_id": user_id,
        "email": account_email,
        "company": company,
        "city": city,
        "contact": contact,
        "locations": locations,
        "needs": needs,
        "extra": extra,
    }

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    lead_file = data_dir / "enterprise_leads.jsonl"
    with lead_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(lead, ensure_ascii=False) + "\n")

    subject = f"[USLY Enterprise] Nowe zapytanie {ticket}"
    selected_areas = locations or "—"

    body = f"""🔥 NOWE ZAPYTANIE ENTERPRISE — USLY

Ticket: {ticket}
Data: {now.strftime("%Y-%m-%d %H:%M UTC")}

━━━━━━━━━━━━━━━━━━
DANE KONTAKTOWE
━━━━━━━━━━━━━━━━━━

Firma / marka:
{company or "—"}

Miasto / zasięg:
{city or "—"}

Kontakt:
{contact or "—"}

Email konta USLY:
{account_email or "—"}

ID użytkownika:
{user_id or "—"}

━━━━━━━━━━━━━━━━━━
OBSZAR ZAINTERESOWANIA
━━━━━━━━━━━━━━━━━━

{selected_areas}

━━━━━━━━━━━━━━━━━━
WIADOMOŚĆ
━━━━━━━━━━━━━━━━━━

{needs or "—"}
"""

    import asyncio

    autoresponder_subject = "USLY — otrzymaliśmy Twoje zapytanie Enterprise"
    autoresponder_body = f"""Dziękujemy za kontakt z USLY.

Otrzymaliśmy Twoje zapytanie dotyczące pakietu Enterprise i wrócimy do Ciebie z propozycją po analizie potrzeb.

Numer zgłoszenia:
{ticket}

Wybrane obszary:
{selected_areas}

Wiadomość:
{needs or "—"}

Pozdrawiamy,
Zespół USLY
kontakt@uslyapp.pl
"""

    try:
        asyncio.create_task(send_bug_email(subject, body))

        responder_email = account_email if "@" in account_email else contact if "@" in contact else ""
        if responder_email:
            asyncio.create_task(
                send_user_email(
                    responder_email,
                    autoresponder_subject,
                    autoresponder_body,
                )
            )

        emailed = "queued"
    except Exception as e:
        emailed = False
        print("ENTERPRISE LEAD EMAIL QUEUE ERROR:", e)

    return ok({"ticket": ticket, "saved": True, "emailed": emailed})



@app.post("/contact")
async def submit_public_contact(payload: dict):
    from pathlib import Path
    from datetime import datetime
    import json
    import asyncio

    name = str((payload or {}).get("name") or "").strip()
    email = str((payload or {}).get("email") or "").strip()
    topic = str((payload or {}).get("topic") or "").strip()
    message = str((payload or {}).get("message") or "").strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="INVALID_EMAIL")

    if not topic:
        raise HTTPException(status_code=422, detail="CONTACT_TOPIC_REQUIRED")

    if not message or len(message) < 5:
        raise HTTPException(status_code=422, detail="CONTACT_MESSAGE_REQUIRED")

    now = datetime.utcnow()
    ticket = f"WEB-{now.strftime('%Y%m%d%H%M%S')}"

    entry = {
        "ticket": ticket,
        "created_at": now.isoformat(),
        "name": name,
        "email": email,
        "topic": topic,
        "message": message,
    }

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    contact_file = data_dir / "contact_messages.jsonl"
    with contact_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    subject = f"[USLY Kontakt] Nowa wiadomość {ticket}"
    body = f"""NOWA WIADOMOŚĆ ZE STRONY USLY

Ticket: {ticket}
Data: {now.strftime("%Y-%m-%d %H:%M UTC")}

Imię / nazwa:
{name or "—"}

E-mail:
{email}

Temat:
{topic}

Wiadomość:
{message}
"""

    autoresponder_subject = "USLY — Twoja wiadomość jest już u nas"
    autoresponder_body = f"""Cześć,

dziękujemy za kontakt z USLY 💜

Twoja wiadomość trafiła już do naszego zespołu i wrócimy do Ciebie tak szybko, jak będzie to możliwe.

Numer zgłoszenia:
{ticket}

Zachowaj ten numer, jeśli będziesz chciała/chciał kontynuować tę sprawę w przyszłości.

Do usłyszenia!

Zespół USLY

kontakt@uslyapp.pl
https://uslyapp.pl
"""

    try:
        asyncio.create_task(send_bug_email(subject, body))
        asyncio.create_task(send_user_email(email, autoresponder_subject, autoresponder_body))
        emailed = "queued"
    except Exception as e:
        emailed = False
        print("PUBLIC CONTACT EMAIL QUEUE ERROR:", e)

    return ok({"ticket": ticket, "saved": True, "emailed": emailed})


# FEEDBACK / BUG REPORTS
# =========================
@app.post("/feedback")
async def submit_feedback(payload: dict):
    import os
    import json
    import smtplib
    import ssl
    from pathlib import Path
    from datetime import datetime
    from email.message import EmailMessage

    bug_email_to = "kontakt@uslyapp.pl"

    message = str((payload or {}).get("message") or "").strip()
    role = str((payload or {}).get("role") or "unknown").strip() or "unknown"
    user_id = (payload or {}).get("user_id")
    email = str((payload or {}).get("email") or "—").strip() or "—"
    current_view = str((payload or {}).get("current_view") or "—").strip() or "—"

    if not message:
        return ok({
            "saved": False,
            "emailed": False,
            "ticket": None,
            "error": "EMPTY_MESSAGE",
        })

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    bug_file = data_dir / "bug_reports.jsonl"

    existing_count = 0
    if bug_file.exists():
        with bug_file.open("r", encoding="utf-8") as f:
            existing_count = sum(1 for _ in f if _.strip())

    ticket_no = existing_count + 1
    ticket = f"{ticket_no:04d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    record = {
        "ticket": ticket,
        "role": role,
        "user_id": user_id,
        "email": email,
        "current_view": current_view,
        "message": message,
        "created_at": now,
    }

    with bug_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    subject = f"[USLY BUG #{ticket}] {role.capitalize()}"
    body = (
        f"Numer: #{ticket}\n"
        f"Rola: {role.capitalize()}\n"
        f"User ID: {user_id if user_id is not None else '—'}\n"
        f"Email: {email}\n"
        f"Czas: {now}\n"
        f"Treść:\n"
        f"{message}"
    )

    smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
    smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
    smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
    smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

    emailed = False
    email_error = None

    if smtp_host and smtp_from:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = bug_email_to
            msg.set_content(body)

            context = ssl.create_default_context()
            try:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            except ssl.SSLCertVerificationError:
                fallback_context = ssl._create_unverified_context()
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=fallback_context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

            emailed = True
        except Exception as e:
            email_error = str(e)

    return ok({
        "saved": True,
        "emailed": emailed,
        "ticket": ticket,
        "email_error": email_error,
    })


# =========================
# USER REPORTS / MODERATION
# =========================
@app.post("/reports/user")
async def submit_user_report(
    payload: dict,
    current_user: User = Depends(require_role("user", "partner")),
):
    import os
    import json
    import smtplib
    import ssl
    from pathlib import Path
    from datetime import datetime
    from email.message import EmailMessage

    report_email_to = "kontakt@uslyapp.pl"

    reported_user_id = (payload or {}).get("reported_user_id")
    reason = str((payload or {}).get("reason") or "").strip()
    description = str((payload or {}).get("description") or "").strip()
    current_view = str((payload or {}).get("current_view") or "—").strip() or "—"

    allowed_reasons = {
        "spam": "Spam / scam",
        "harassment": "Nękanie lub obraźliwe treści",
        "inappropriate_profile": "Nieodpowiedni profil lub bio",
        "impersonation": "Podszywanie się",
        "other": "Inne",
    }

    if not reported_user_id:
        raise HTTPException(status_code=422, detail="REPORTED_USER_REQUIRED")

    if int(reported_user_id) == current_user.id:
        raise HTTPException(status_code=400, detail="CANNOT_REPORT_SELF")

    if reason not in allowed_reasons:
        raise HTTPException(status_code=422, detail="INVALID_REPORT_REASON")

    if len(description) > 1000:
        raise HTTPException(status_code=422, detail="REPORT_DESCRIPTION_TOO_LONG")

    db = SessionLocal()
    try:
        target = (
            db.query(User)
            .filter(User.id == int(reported_user_id))
            .filter(User.status == UserStatus.ACTIVE.value)
            .first()
        )
        if not target:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    finally:
        db.close()

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_file = data_dir / "user_reports.jsonl"

    existing_count = 0
    if report_file.exists():
        with report_file.open("r", encoding="utf-8") as f:
            existing_count = sum(1 for _ in f if _.strip())

    ticket_no = existing_count + 1
    ticket = f"UR-{ticket_no:04d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    record = {
        "ticket": ticket,
        "reporter_user_id": current_user.id,
        "reporter_role": current_user.role,
        "reported_user_id": int(reported_user_id),
        "reason": reason,
        "reason_label": allowed_reasons[reason],
        "description": description,
        "current_view": current_view,
        "created_at": now,
        "status": "new",
    }

    with report_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    subject = f"[USLY REPORT #{ticket}] {allowed_reasons[reason]}"
    body = (
        f"Numer: #{ticket}\n"
        f"Zgłaszający ID: {current_user.id}\n"
        f"Rola zgłaszającego: {current_user.role}\n"
        f"Zgłoszony user ID: {int(reported_user_id)}\n"
        f"Powód: {allowed_reasons[reason]} ({reason})\n"
        f"Widok: {current_view}\n"
        f"Czas: {now}\n\n"
        f"Opis:\n"
        f"{description or '—'}"
    )

    smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
    smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
    smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
    smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

    emailed = False
    email_error = None

    if smtp_host and smtp_from:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = report_email_to
            msg.set_content(body)

            context = ssl.create_default_context()
            try:
                server_context = context
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=server_context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            except ssl.SSLCertVerificationError:
                fallback_context = ssl._create_unverified_context()
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=fallback_context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

            emailed = True
        except Exception as e:
            email_error = str(e)

    return ok({
        "saved": True,
        "emailed": emailed,
        "ticket": ticket,
        "email_error": email_error,
    })


@app.post("/reports/event")
async def submit_event_report(
    payload: dict,
    current_user: User = Depends(require_role("user", "partner")),
):
    import os
    import json
    import smtplib
    import ssl
    from pathlib import Path
    from datetime import datetime
    from email.message import EmailMessage

    report_email_to = "kontakt@uslyapp.pl"

    event_id = (payload or {}).get("event_id")
    reason = str((payload or {}).get("reason") or "").strip()
    description = str((payload or {}).get("description") or "").strip()
    current_view = str((payload or {}).get("current_view") or "—").strip() or "—"

    allowed_reasons = {
        "spam": "Spam / scam",
        "misleading": "Fałszywe lub mylące wydarzenie",
        "inappropriate": "Nieodpowiednia treść",
        "unsafe": "Podejrzane lub niebezpieczne wydarzenie",
        "other": "Inne",
    }

    if not event_id:
        raise HTTPException(status_code=422, detail="EVENT_REQUIRED")

    if reason not in allowed_reasons:
        raise HTTPException(status_code=422, detail="INVALID_REPORT_REASON")

    if len(description) > 1000:
        raise HTTPException(status_code=422, detail="REPORT_DESCRIPTION_TOO_LONG")

    db = SessionLocal()
    try:
        event = (
            db.query(Event)
            .filter(Event.id == int(event_id))
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        event_title = getattr(event, "title", None) or getattr(event, "name", None) or f"Wydarzenie #{event_id}"
        partner_user_id = getattr(event, "partner_user_id", None)
    finally:
        db.close()

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_file = data_dir / "event_reports.jsonl"

    existing_count = 0
    if report_file.exists():
        with report_file.open("r", encoding="utf-8") as f:
            existing_count = sum(1 for _ in f if _.strip())

    ticket_no = existing_count + 1
    ticket = f"ER-{ticket_no:04d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    record = {
        "ticket": ticket,
        "reporter_user_id": current_user.id,
        "reporter_role": current_user.role,
        "event_id": int(event_id),
        "event_title": event_title,
        "partner_user_id": partner_user_id,
        "reason": reason,
        "reason_label": allowed_reasons[reason],
        "description": description,
        "current_view": current_view,
        "created_at": now,
        "status": "new",
    }

    with report_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    subject = f"[USLY EVENT REPORT #{ticket}] {allowed_reasons[reason]}"
    body = (
        f"Numer: #{ticket}\n"
        f"Zgłaszający ID: {current_user.id}\n"
        f"Rola zgłaszającego: {current_user.role}\n"
        f"Event ID: {int(event_id)}\n"
        f"Tytuł wydarzenia: {event_title}\n"
        f"Partner user ID: {partner_user_id if partner_user_id is not None else '—'}\n"
        f"Powód: {allowed_reasons[reason]} ({reason})\n"
        f"Widok: {current_view}\n"
        f"Czas: {now}\n\n"
        f"Opis:\n"
        f"{description or '—'}"
    )

    smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
    smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
    smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
    smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

    emailed = False
    email_error = None

    if smtp_host and smtp_from:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = report_email_to
            msg.set_content(body)

            context = ssl.create_default_context()
            try:
                server_context = context
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=server_context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            except ssl.SSLCertVerificationError:
                fallback_context = ssl._create_unverified_context()
                with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                    server.starttls(context=fallback_context)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

            emailed = True
        except Exception as e:
            email_error = str(e)

    return ok({
        "saved": True,
        "emailed": emailed,
        "ticket": ticket,
        "email_error": email_error,
    })



def _admin_reports_file(report_type: str):
    from pathlib import Path
    files = {
        "user": "user_reports.jsonl",
        "event": "event_reports.jsonl",
        "bug": "bug_reports.jsonl",
    }
    if report_type not in files:
        raise HTTPException(status_code=404, detail="REPORT_TYPE_NOT_FOUND")
    return Path(__file__).resolve().parent / "data" / files[report_type]


def _admin_create_user_notification(user_id: int, notification_type: str, event_id: int | None = None, partner_user_id: int | None = None):
    if not user_id or not notification_type:
        return

    db = SessionLocal()
    try:
        db.add(
            UserNotification(
                user_id=user_id,
                event_id=event_id,
                partner_user_id=partner_user_id,
                type=notification_type,
            )
        )
        db.commit()
    finally:
        db.close()


@app.post("/admin/reports/{report_type}/{ticket}/status")
def admin_update_report_status(
    report_type: str,
    ticket: str,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    import json

    require_admin_permission(current_user, "reports")

    allowed = {"new", "in_review", "pending_owner_approval", "resolved", "rejected", "archived", "accepted", "in_progress", "fixed", "not_reproducible"}
    payload = payload or {}
    new_status = str(payload.get("status") or "").strip()
    moderator_note = str(payload.get("moderator_note") or "").strip()
    moderator_message = str(payload.get("moderator_message") or "").strip()

    if new_status not in allowed:
        raise HTTPException(status_code=422, detail="INVALID_REPORT_STATUS")

    if _admin_level(current_user) in {ADMIN_LEVEL_MODERATION, ADMIN_LEVEL_SUPPORT}:
        if report_type in {"user", "event"} and new_status not in {"in_review", "rejected", "resolved", "pending_owner_approval"}:
            raise HTTPException(status_code=403, detail="OWNER_APPROVAL_REQUIRED")

    f = _admin_reports_file(report_type)
    if not f.exists():
        raise HTTPException(status_code=404, detail="REPORT_FILE_NOT_FOUND")

    rows = []
    found = None
    with f.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            if str(row.get("ticket")) == str(ticket):
                previous_status = str(row.get("status") or "new")

                if report_type in {"user", "event"}:
                    if previous_status in {"resolved", "rejected"} and new_status in {"in_review", "pending_owner_approval"}:
                        raise HTTPException(status_code=409, detail="REPORT_ALREADY_CLOSED")
                    if (
                        _admin_level(current_user) in {ADMIN_LEVEL_MODERATION, ADMIN_LEVEL_SUPPORT}
                        and previous_status == "pending_owner_approval"
                        and new_status in {"resolved", "rejected"}
                    ):
                        raise HTTPException(status_code=403, detail="OWNER_APPROVAL_ALREADY_REQUESTED")

                now = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")

                row["status"] = new_status
                row["updated_at"] = now
                row["updated_by_admin_id"] = current_user.id

                if moderator_note:
                    row["moderator_note"] = moderator_note
                if moderator_message:
                    row["moderator_message"] = moderator_message

                history = row.get("history")
                if not isinstance(history, list):
                    history = []

                history.append({
                    "at": now,
                    "admin_id": current_user.id,
                    "admin_display_name": current_user.admin_display_name or current_user.email or f"Admin #{current_user.id}",
                    "admin_level": current_user.admin_level or "admin",
                    "from_status": previous_status,
                    "to_status": new_status,
                    "moderator_note": moderator_note,
                    "moderator_message": moderator_message,
                })

                if report_type == "user" and new_status in {"in_review", "resolved", "rejected"}:
                    reporter_user_id = int(row.get("reporter_user_id") or 0)
                    if reporter_user_id:
                        _admin_create_user_notification(
                            reporter_user_id,
                            f"admin_user_report_{new_status}",
                        )

                if report_type == "event" and new_status in {"in_review", "resolved", "rejected"}:
                    reporter_user_id = int(row.get("reporter_user_id") or 0)
                    if reporter_user_id:
                        _admin_create_user_notification(
                            reporter_user_id,
                            f"admin_event_report_{new_status}",
                        )

                if report_type == "bug" and new_status in {"accepted", "in_progress", "fixed", "resolved", "not_reproducible"}:
                    bug_user_id = int(row.get("user_id") or 0)
                    if bug_user_id:
                        _admin_create_user_notification(
                            bug_user_id,
                            f"admin_bug_report_{new_status}",
                        )

                row["history"] = history
                found = row

            rows.append(row)

    if not found:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")

    with f.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    return ok({"ticket": ticket, "status": new_status, "report": found})


@app.post("/admin/reports/{report_type}/{ticket}/note")
def admin_add_report_note(
    report_type: str,
    ticket: str,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    import json

    require_admin_permission(current_user, "reports")

    note = str((payload or {}).get("note") or "").strip()
    if not note:
        raise HTTPException(status_code=422, detail="EMPTY_NOTE")

    f = _admin_reports_file(report_type)
    if not f.exists():
        raise HTTPException(status_code=404, detail="REPORT_FILE_NOT_FOUND")

    rows = []
    found = None
    with f.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            if str(row.get("ticket")) == str(ticket):
                now = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
                history = row.get("history")
                if not isinstance(history, list):
                    history = []

                history.append({
                    "type": "note",
                    "at": now,
                    "admin_id": current_user.id,
                    "admin_display_name": current_user.admin_display_name or current_user.email or f"Admin #{current_user.id}",
                    "admin_level": current_user.admin_level or "admin",
                    "note": note,
                })

                row["history"] = history
                row["updated_at"] = now
                row["updated_by_admin_id"] = current_user.id
                found = row

            rows.append(row)

    if not found:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")

    with f.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    return ok({"ticket": ticket, "report": found})


@app.post("/admin/reports/{report_type}/{ticket}/action")
def admin_add_report_action(
    report_type: str,
    ticket: str,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    import json

    require_admin_permission(current_user, "reports")

    action = str((payload or {}).get("action") or "").strip()
    label = str((payload or {}).get("label") or "").strip()

    allowed_actions = {"warning_profile", "warning_content", "warning_behavior"}
    if action not in allowed_actions:
        raise HTTPException(status_code=422, detail="INVALID_REPORT_ACTION")

    f = _admin_reports_file(report_type)
    if not f.exists():
        raise HTTPException(status_code=404, detail="REPORT_FILE_NOT_FOUND")

    rows = []
    found = None
    with f.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            if str(row.get("ticket")) == str(ticket):
                now = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
                history = row.get("history")
                if not isinstance(history, list):
                    history = []

                history.append({
                    "type": "warning",
                    "at": now,
                    "admin_id": current_user.id,
                    "admin_display_name": current_user.admin_display_name or current_user.email or f"Admin #{current_user.id}",
                    "admin_level": current_user.admin_level or "admin",
                    "action": action,
                    "label": label or action,
                })

                if report_type == "user":
                    reported_user_id = int(row.get("reported_user_id") or 0)
                    if reported_user_id:
                        _admin_create_user_notification(
                            reported_user_id,
                            f"admin_user_warning_{action}",
                        )

                row["history"] = history
                row["updated_at"] = now
                row["updated_by_admin_id"] = current_user.id
                found = row

            rows.append(row)

    if not found:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")

    with f.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    return ok({"ticket": ticket, "report": found})


@app.post("/admin/users/{user_id}/delete-account")
def admin_delete_user_account(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "account_delete")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
        if user.role == "admin":
            raise HTTPException(status_code=400, detail="CANNOT_DELETE_ADMIN")
        if user.status == UserStatus.DELETED.value:
            return ok({"deleted": True, "already_deleted": True})

        owned_groups = (
            db.query(Group)
            .filter(Group.creator_id == user.id)
            .all()
        )

        for g in owned_groups:
            db.delete(g)

        cleanup_user_social_relations_for_soft_delete(db, user.id)

        original_email = user.email
        safe_email = f"deleted_{user.id}_{int(datetime.utcnow().timestamp())}@deleted.usly.local"

        user.email = safe_email
        user.password_hash = None
        user.status = UserStatus.DELETED.value

        db.add(user)
        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_delete_user_account",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; original_email={original_email}",
            )
        )
        db.commit()

        return ok({
            "deleted": True,
            "user_id": user.id,
            "original_email": original_email,
        })
    finally:
        db.close()


@app.post("/admin/users/{user_id}/status")
def admin_update_user_status(
    user_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "account_status")

    new_status = str((payload or {}).get("status") or "").strip()
    if new_status not in {UserStatus.ACTIVE.value, UserStatus.BLOCKED.value}:
        raise HTTPException(status_code=422, detail="INVALID_USER_STATUS")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="CANNOT_MODERATE_SELF")
        if user.role == "admin" and _admin_level(current_user) != ADMIN_LEVEL_OWNER:
            raise HTTPException(status_code=400, detail="CANNOT_MODERATE_ADMIN")
        if (
            user.role == "admin"
            and (user.admin_level or "").strip().lower() == ADMIN_LEVEL_OWNER
            and new_status == UserStatus.BLOCKED.value
        ):
            active_owner_count = (
                db.query(User)
                .filter(User.role == "admin")
                .filter(User.admin_level == ADMIN_LEVEL_OWNER)
                .filter(User.status == UserStatus.ACTIVE.value)
                .count()
            )
            if active_owner_count <= 1 and user.status == UserStatus.ACTIVE.value:
                raise HTTPException(status_code=400, detail="CANNOT_BLOCK_LAST_OWNER")

        previous_status = user.status
        user.status = new_status
        db.add(user)
        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_update_user_status",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; from={previous_status}; to={new_status}",
            )
        )
        db.commit()

        return ok({"id": user.id, "status": user.status})
    finally:
        db.close()


@app.post("/admin/events/{event_id}/status")
def admin_update_event_status(
    event_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "events")

    new_status = str((payload or {}).get("status") or "").strip()
    if new_status not in {"published", "archived"}:
        raise HTTPException(status_code=422, detail="INVALID_EVENT_STATUS")

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        previous_status = event.status

        event.status = new_status
        event.updated_at = datetime.utcnow()
        db.add(event)

        db.add(
            AuditLog(
                user_id=event.partner_user_id,
                action="admin_update_event_status",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; event_id={event.id}; from={previous_status}; to={new_status}",
            )
        )

        db.commit()

        return ok({"id": event.id, "status": event.status})
    finally:
        db.close()


@app.post("/admin/users/create")
def admin_create_user_account(
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    email = str((payload or {}).get("email") or "").strip().lower()
    role = str((payload or {}).get("role") or "user").strip().lower()
    password = str((payload or {}).get("password") or "").strip()
    dob_raw = str((payload or {}).get("dob") or "").strip()
    admin_display_name = str((payload or {}).get("admin_display_name") or "").strip()
    admin_level = str((payload or {}).get("admin_level") or "").strip().lower()
    plan = str((payload or {}).get("plan") or "free").strip().lower()
    plan_source = str((payload or {}).get("plan_source") or "manual").strip().lower()
    plan_status = str((payload or {}).get("plan_status") or "active").strip().lower()

    allowed_plans = {"free", "plus", "premium", "vip", "pro", "enterprise"}
    allowed_sources = {"manual", "paid", "barter", "promo", "ambassador", "test", "system"}
    allowed_statuses = {"active", "inactive", "expired", "trial", "cancelled"}

    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="INVALID_EMAIL")
    if role not in {"user", "partner", "admin"}:
        raise HTTPException(status_code=422, detail="INVALID_ROLE")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="PASSWORD_TOO_SHORT")
    if role != "admin":
        if plan not in allowed_plans:
            raise HTTPException(status_code=422, detail="INVALID_PLAN")
        if plan_source not in allowed_sources:
            raise HTTPException(status_code=422, detail="INVALID_PLAN_SOURCE")
        if plan_status not in allowed_statuses:
            raise HTTPException(status_code=422, detail="INVALID_PLAN_STATUS")

    if role == "admin":
        require_admin_permission(current_user, "admin_create")
        if not admin_display_name:
            raise HTTPException(status_code=422, detail="ADMIN_DISPLAY_NAME_REQUIRED")
        if admin_level not in {ADMIN_LEVEL_OWNER, ADMIN_LEVEL_OPERATIONS, ADMIN_LEVEL_MODERATION, ADMIN_LEVEL_SUPPORT}:
            raise HTTPException(status_code=422, detail="INVALID_ADMIN_LEVEL")
    else:
        admin_display_name = ""
        admin_level = ""

    parsed_dob = None
    if role == "user":
        if not dob_raw:
            raise HTTPException(status_code=422, detail="DOB_REQUIRED_FOR_USER")
        try:
            parsed_dob = date.fromisoformat(dob_raw)
        except Exception:
            raise HTTPException(status_code=422, detail="INVALID_DOB")
        if not _is_at_least_18(parsed_dob):
            raise HTTPException(status_code=403, detail="AGE_TOO_LOW")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=409, detail="EMAIL_ALREADY_EXISTS")

        user = User(
            email=email,
            password_hash=hash_password(password),
            dob=parsed_dob,
            terms_accepted_at=datetime.utcnow(),
            terms_version="admin-created",
            privacy_version="admin-created",
            role=role,
            status=UserStatus.ACTIVE.value,
            admin_display_name=admin_display_name or None,
            admin_level=admin_level or None,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        if role == "user":
            db.add(UserProfile(user_id=user.id, plan=plan, plan_source=plan_source, plan_status=plan_status))
        elif role == "partner":
            db.add(PartnerProfile(user_id=user.id, plan=plan, plan_source=plan_source, plan_status=plan_status))

        token = str(uuid4())
        reset_row = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow().replace(microsecond=0) + __import__("datetime").timedelta(hours=1),
            used_at=None,
        )
        db.add(reset_row)
        db.commit()

        link_base = os.getenv("PASSWORD_RESET_LINK_BASE", "usly://reset-password").strip() or "usly://reset-password"
        separator = "&" if "?" in link_base else "?"
        reset_link = f"{link_base}{separator}token={token}"

        emailed = False
        email_error = None

        smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
        smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
        smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
        smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

        if smtp_host and smtp_from:
            try:
                import smtplib
                import ssl

                msg = EmailMessage()
                msg["Subject"] = "USLY — utworzono konto"
                msg["From"] = smtp_from
                msg["To"] = user.email
                msg.set_content(
                    "Utworzono dla Ciebie konto w USLY.\n\n"
                    "Aby ustawić własne hasło i rozpocząć korzystanie z aplikacji, otwórz poniższy link:\n"
                    f"{reset_link}\n\n"
                    "Link jest jednorazowy i będzie ważny przez 60 minut.\n"
                    "Jeśli nie spodziewałaś/spodziewałeś się tej wiadomości, skontaktuj się z supportem USLY."
                )

                context = ssl.create_default_context()
                try:
                    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                        server.starttls(context=context)
                        if smtp_user and smtp_pass:
                            server.login(smtp_user, smtp_pass)
                        server.send_message(msg)
                except ssl.SSLCertVerificationError:
                    fallback_context = ssl._create_unverified_context()
                    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                        server.starttls(context=fallback_context)
                        if smtp_user and smtp_pass:
                            server.login(smtp_user, smtp_pass)
                        server.send_message(msg)

                emailed = True
            except Exception as e:
                email_error = str(e)

        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_create_user_account",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; created_role={role}; created_admin_display_name={admin_display_name or '-'}; created_admin_level={admin_level or '-'}; plan={plan if role != 'admin' else '-'}; source={plan_source if role != 'admin' else '-'}; status={plan_status if role != 'admin' else '-'}; emailed={1 if emailed else 0}; email_error={email_error or '-'}",
            )
        )
        db.commit()

        return ok({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "plan": plan if role != "admin" else None,
            "plan_source": plan_source if role != "admin" else None,
            "plan_status": plan_status if role != "admin" else None,
            "emailed": emailed,
            "email_error": email_error,
        })
    finally:
        db.close()


@app.post("/admin/users/{user_id}/send-reset-link")
def admin_send_user_reset_link(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
):
    import smtplib
    import ssl

    require_admin_permission(current_user, "users")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(status_code=422, detail="USER_NOT_ACTIVE")

        token = str(uuid4())
        reset_row = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow().replace(microsecond=0) + __import__("datetime").timedelta(hours=1),
            used_at=None,
        )
        db.add(reset_row)
        db.commit()

        link_base = os.getenv("PASSWORD_RESET_LINK_BASE", "usly://reset-password").strip() or "usly://reset-password"
        separator = "&" if "?" in link_base else "?"
        reset_link = f"{link_base}{separator}token={token}"

        smtp_host = os.getenv("USLY_SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("USLY_SMTP_PORT", "587"))
        smtp_user = os.getenv("USLY_SMTP_USER", "").strip()
        smtp_pass = os.getenv("USLY_SMTP_PASS", "").strip()
        smtp_from = os.getenv("USLY_SMTP_FROM", "").strip() or smtp_user

        emailed = False
        email_error = None

        if smtp_host and smtp_from:
            try:
                msg = EmailMessage()
                msg["Subject"] = "USLY — reset hasła"
                msg["From"] = smtp_from
                msg["To"] = user.email
                msg.set_content(
                    "Otrzymujesz tę wiadomość, ponieważ poproszono o reset hasła do Twojego konta USLY.\n\n"
                    "Kliknij lub otwórz poniższy link, aby ustawić nowe hasło:\n"
                    f"{reset_link}\n\n"
                    "Link jest jednorazowy i będzie ważny przez 60 minut.\n"
                    "Jeśli nie prosiłaś/prosiłeś o reset hasła, skontaktuj się z supportem USLY."
                )

                context = ssl.create_default_context()
                try:
                    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                        server.starttls(context=context)
                        if smtp_user and smtp_pass:
                            server.login(smtp_user, smtp_pass)
                        server.send_message(msg)
                except ssl.SSLCertVerificationError:
                    fallback_context = ssl._create_unverified_context()
                    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                        server.starttls(context=fallback_context)
                        if smtp_user and smtp_pass:
                            server.login(smtp_user, smtp_pass)
                        server.send_message(msg)

                emailed = True
            except Exception as e:
                email_error = str(e)

        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_send_reset_link",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; emailed={1 if emailed else 0}; email_error={email_error or '-'}",
            )
        )
        db.commit()

        return ok({
            "user_id": user.id,
            "email": user.email,
            "emailed": emailed,
            "email_error": email_error,
        })
    finally:
        db.close()


@app.post("/admin/users/{user_id}/reset-password")
def admin_reset_user_password(
    user_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "users")

    new_password = str((payload or {}).get("new_password") or "").strip()

    if len(new_password) < 6:
        raise HTTPException(status_code=422, detail="PASSWORD_TOO_SHORT")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        user.password_hash = hash_password(new_password)

        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_reset_password",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}",
            )
        )

        db.add(user)
        db.commit()

        return ok({
            "user_id": user.id,
            "password_reset": True,
        })
    finally:
        db.close()


@app.post("/store/verify-purchase")
def verify_store_purchase(
    payload: dict,
    current_user: User = Depends(require_role("user", "partner")),
):
    verification_mode = os.getenv("STORE_PURCHASE_VERIFICATION_MODE", "").strip().lower()
    if verification_mode != "test":
        raise HTTPException(status_code=503, detail="STORE_VERIFICATION_NOT_CONFIGURED")

    platform = str((payload or {}).get("platform") or "").strip().lower()
    plan = str((payload or {}).get("plan") or "").strip().lower()
    product_id = str((payload or {}).get("product_id") or "").strip()
    transaction_id = str((payload or {}).get("transaction_id") or "").strip()
    original_transaction_id = str((payload or {}).get("original_transaction_id") or "").strip() or None
    purchase_token = str((payload or {}).get("purchase_token") or "").strip() or None
    environment = str((payload or {}).get("environment") or "").strip().lower() or None
    expires_at_raw = str((payload or {}).get("expires_at") or "").strip()

    if platform not in {"ios", "android"}:
        raise HTTPException(status_code=422, detail="INVALID_STORE_PLATFORM")

    if not product_id:
        raise HTTPException(status_code=422, detail="INVALID_STORE_PRODUCT_ID")

    if not transaction_id:
        raise HTTPException(status_code=422, detail="INVALID_STORE_TRANSACTION_ID")

    allowed_user_plans = {"plus", "premium", "vip"}
    allowed_partner_plans = {"pro", "premium", "enterprise"}
    allowed_plans = allowed_partner_plans if current_user.role == UserRole.PARTNER.value else allowed_user_plans

    if plan not in allowed_plans:
        raise HTTPException(status_code=422, detail="INVALID_STORE_PLAN")

    now = datetime.utcnow()
    plan_expires_at = None

    if expires_at_raw:
        try:
            plan_expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            if getattr(plan_expires_at, "tzinfo", None) is not None:
                plan_expires_at = plan_expires_at.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            raise HTTPException(status_code=422, detail="INVALID_PLAN_EXPIRES_AT")
    else:
        plan_expires_at = _add_months_to_datetime(now, 1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        if user.role == UserRole.PARTNER.value:
            profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user.id).first()
            if not profile:
                raise HTTPException(status_code=404, detail="PARTNER_PROFILE_NOT_FOUND")
        else:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile:
                raise HTTPException(status_code=404, detail="USER_PROFILE_NOT_FOUND")

        existing_purchase = (
            db.query(StorePurchase)
            .filter(
                StorePurchase.platform == platform,
                StorePurchase.transaction_id == transaction_id,
            )
            .first()
        )
        if existing_purchase:
            return ok({
                "verified": True,
                "already_verified": True,
                "mode": existing_purchase.verification_mode,
                "platform": existing_purchase.platform,
                "plan": existing_purchase.plan,
                "plan_source": "paid",
                "plan_status": "active",
                "plan_expires_at": existing_purchase.plan_expires_at.isoformat() if existing_purchase.plan_expires_at else None,
                "activated_redemption_ids": [],
                "ambassador_grants_created": 0,
            })

        profile.plan = plan
        profile.plan_source = "paid"
        profile.plan_status = "active"
        profile.plan_updated_at = now
        profile.plan_expires_at = plan_expires_at
        profile.plan_expiry_notice_14d_sent_at = None
        profile.plan_expiry_notice_7d_sent_at = None
        profile.updated_at = now
        db.add(profile)

        db.add(StorePurchase(
            user_id=user.id,
            platform=platform,
            product_id=product_id,
            transaction_id=transaction_id,
            original_transaction_id=original_transaction_id,
            purchase_token=purchase_token,
            environment=environment,
            plan=plan,
            status="verified",
            verification_mode=verification_mode,
            raw_payload=json.dumps(payload or {}, ensure_ascii=False, default=str),
            verified_at=now,
            plan_expires_at=plan_expires_at,
        ))

        activated_redemption_ids, ambassador_grants_created = _activate_reserved_promo_redemptions_after_paid_plan(db, user, now)

        if activated_redemption_ids:
            (
                db.query(PromoRedemption)
                .filter(PromoRedemption.id.in_(activated_redemption_ids))
                .update(
                    {PromoRedemption.store_transaction_id: transaction_id},
                    synchronize_session=False,
                )
            )

        db.add(AuditLog(
            user_id=user.id,
            action="store_purchase_verified_test",
            details=f"platform={platform}; plan={plan}; product_id={product_id}; transaction_id={transaction_id}; expires_at={plan_expires_at.isoformat() if plan_expires_at else '-'}; activated_redemptions={activated_redemption_ids}; ambassador_grants_created={ambassador_grants_created}",
        ))

        db.commit()

        return ok({
            "verified": True,
            "mode": verification_mode,
            "platform": platform,
            "plan": plan,
            "plan_source": "paid",
            "plan_status": "active",
            "plan_expires_at": plan_expires_at.isoformat() if plan_expires_at else None,
            "activated_redemption_ids": activated_redemption_ids,
            "ambassador_grants_created": ambassador_grants_created,
        })
    finally:
        db.close()


@app.post("/admin/users/{user_id}/plan")
def admin_update_user_plan(
    user_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "plans")

    plan = str((payload or {}).get("plan") or "").strip().lower()
    plan_source = str((payload or {}).get("plan_source") or "manual").strip().lower()
    plan_status = str((payload or {}).get("plan_status") or "active").strip().lower()
    plan_expires_at_raw = str((payload or {}).get("plan_expires_at") or "").strip()
    plan_expires_at = None

    if plan_expires_at_raw:
        try:
            plan_expires_at = datetime.fromisoformat(plan_expires_at_raw.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=422, detail="INVALID_PLAN_EXPIRES_AT")

    allowed_plans = {"free", "plus", "premium", "vip", "pro", "enterprise"}
    allowed_sources = {"manual", "paid", "barter", "promo", "ambassador", "test", "system"}
    allowed_statuses = {"active", "inactive", "expired", "trial", "cancelled"}

    if plan not in allowed_plans:
        raise HTTPException(status_code=422, detail="INVALID_PLAN")
    if plan_source not in allowed_sources:
        raise HTTPException(status_code=422, detail="INVALID_PLAN_SOURCE")
    if plan_status not in allowed_statuses:
        raise HTTPException(status_code=422, detail="INVALID_PLAN_STATUS")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        now = datetime.utcnow()
        previous_plan = "free"

        if user.role == UserRole.PARTNER.value:
            profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user.id).first()
            if not profile:
                raise HTTPException(status_code=404, detail="PARTNER_PROFILE_NOT_FOUND")
            previous_plan = (profile.plan or "free").lower()
            profile.plan = plan
            profile.plan_source = plan_source
            profile.plan_status = plan_status
            profile.plan_updated_at = now
            profile.plan_expires_at = plan_expires_at
            profile.plan_expiry_notice_14d_sent_at = None
            profile.plan_expiry_notice_7d_sent_at = None
            profile.updated_at = now
            db.add(profile)
        else:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile:
                raise HTTPException(status_code=404, detail="USER_PROFILE_NOT_FOUND")
            previous_plan = (profile.plan or "free").lower()
            profile.plan = plan
            profile.plan_source = plan_source
            profile.plan_status = plan_status
            profile.plan_updated_at = now
            profile.plan_expires_at = plan_expires_at
            profile.plan_expiry_notice_14d_sent_at = None
            profile.plan_expiry_notice_7d_sent_at = None

            if plan not in {"premium", "vip"}:
                profile.trainer_interests_json = None

            profile.updated_at = now
            db.add(profile)

        downgrade_limits_result = None
        plan_ranks = PARTNER_PLAN_RANKS if user.role == UserRole.PARTNER.value else USER_PLAN_RANKS
        previous_rank = plan_ranks.get(previous_plan, 0)
        new_rank = plan_ranks.get(plan, 0)

        if new_rank < previous_rank:
            downgrade_limits_result = _apply_plan_limits_after_downgrade(db, user, plan, now)

        ambassador_grants_created = 0
        activated_redemption_ids = []

        if plan_status == "active" and plan_source == "paid" and plan != "free":
            activated_redemption_ids, ambassador_grants_created = _activate_reserved_promo_redemptions_after_paid_plan(db, user, now)

        db.add(
            AuditLog(
                user_id=user.id,
                action="admin_update_user_plan",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; admin_level={current_user.admin_level or 'admin'}; previous_plan={previous_plan}; plan={plan}; source={plan_source}; status={plan_status}; expires_at={plan_expires_at.isoformat() if plan_expires_at else '-'}; downgrade_limits={downgrade_limits_result or '-'}; activated_redemptions={activated_redemption_ids}; ambassador_grants_created={ambassador_grants_created}",
            )
        )
        db.commit()

        return ok({
            "user_id": user.id,
            "role": user.role,
            "plan": plan,
            "plan_source": plan_source,
            "plan_status": plan_status,
            "plan_expires_at": plan_expires_at.isoformat() if plan_expires_at else None,
            "activated_redemption_ids": activated_redemption_ids,
            "ambassador_grants_created": ambassador_grants_created,
            "downgrade_limits": downgrade_limits_result,
        })
    finally:
        db.close()


@app.get("/admin/users/{user_id}/preview")
def admin_user_preview(
    user_id: int,
    ticket: str | None = None,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "reports" if ticket else "users")

    import json

    db = SessionLocal()
    try:
        row = (
            db.query(User, UserProfile)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .filter(User.id == user_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        user, profile = row
        partner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user.id).first()

        if user.role == UserRole.PARTNER.value:
            account_plan = getattr(partner_profile, "plan", None) or "free"
            account_plan_source = getattr(partner_profile, "plan_source", None) or "manual"
            account_plan_status = getattr(partner_profile, "plan_status", None) or "active"
            account_plan_updated_at = str(partner_profile.plan_updated_at) if partner_profile and partner_profile.plan_updated_at else None
            account_plan_expires_at = str(partner_profile.plan_expires_at) if partner_profile and getattr(partner_profile, "plan_expires_at", None) else None
        elif user.role == UserRole.ADMIN.value:
            account_plan = None
            account_plan_source = None
            account_plan_status = None
            account_plan_updated_at = None
            account_plan_expires_at = None
        else:
            account_plan = getattr(profile, "plan", None) if profile else "free"
            account_plan_source = getattr(profile, "plan_source", None) if profile else None
            account_plan_status = getattr(profile, "plan_status", None) if profile else None
            account_plan_updated_at = str(profile.plan_updated_at) if profile and profile.plan_updated_at else None
            account_plan_expires_at = str(profile.plan_expires_at) if profile and getattr(profile, "plan_expires_at", None) else None

        interests = []
        if profile and profile.zainteresowania_json:
            try:
                interests = json.loads(profile.zainteresowania_json) or []
            except Exception:
                interests = []

        reports_file = Path(__file__).resolve().parent / "data" / "user_reports.jsonl"
        reports_total = 0
        reports_open = 0
        selected_report = None
        if reports_file.exists():
            with reports_file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    if int(row.get("reported_user_id") or 0) == int(user_id):
                        reports_total += 1
                        if ticket and str(row.get("ticket") or "") == str(ticket):
                            selected_report = row
                        if str(row.get("status") or "new") not in {"resolved", "rejected", "archived"}:
                            reports_open += 1

        plan_history_logs = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user.id)
            .filter(AuditLog.action == "admin_update_user_plan")
            .order_by(AuditLog.created_at.desc())
            .limit(10)
            .all()
        )

        account_history_logs = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(30)
            .all()
        )

        return ok({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "reports_total": reports_total,
            "reports_open": reports_open,
            "selected_report": selected_report,
            "admin_display_name": user.admin_display_name,
            "admin_level": user.admin_level,
            "nick": getattr(partner_profile, "nazwa", None) if user.role == UserRole.PARTNER.value else (getattr(profile, "nick", None) if profile else user.admin_display_name),
            "city": getattr(partner_profile, "miasto", None) if user.role == UserRole.PARTNER.value else (getattr(profile, "city", None) if profile else None),
            "bio": getattr(partner_profile, "bio", None) if user.role == UserRole.PARTNER.value else (getattr(profile, "bio", None) if profile else None),
            "avatar_url": getattr(partner_profile, "logo_url", None) if user.role == UserRole.PARTNER.value else (getattr(profile, "avatar_url", None) if profile else None),
            "interests": interests,
            "plan": account_plan,
            "plan_source": account_plan_source,
            "plan_status": account_plan_status,
            "plan_updated_at": account_plan_updated_at,
            "plan_expires_at": account_plan_expires_at,
            "plan_history": [
                {
                    "created_at": str(log.created_at) if log.created_at else None,
                    "action": log.action,
                    "details": log.details,
                }
                for log in plan_history_logs
            ],
            "account_history": [
                {
                    "created_at": str(log.created_at) if log.created_at else None,
                    "action": log.action,
                    "details": log.details,
                }
                for log in account_history_logs
            ],
            "dob": str(user.dob) if getattr(user, "dob", None) else None,
            "created_at": str(user.created_at) if getattr(user, "created_at", None) else None,
        })
    finally:
        db.close()


@app.get("/admin/events/{event_id}/preview")
def admin_event_preview(
    event_id: int,
    ticket: str | None = None,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "reports" if ticket else "events")

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        signups_rows = db.query(EventSignup).filter(EventSignup.event_id == event.id).order_by(EventSignup.created_at.desc()).all()
        saves_rows = db.query(EventSave).filter(EventSave.event_id == event.id).order_by(EventSave.created_at.desc()).all()

        signups_count = len(signups_rows)
        saves_count = len(saves_rows)

        attendee_user_ids = list({row.user_id for row in signups_rows} | {row.user_id for row in saves_rows})
        attendee_users = {
            user.id: user
            for user in db.query(User).filter(User.id.in_(attendee_user_ids)).all()
        } if attendee_user_ids else {}
        attendee_profiles = {
            profile.user_id: profile
            for profile in db.query(UserProfile).filter(UserProfile.user_id.in_(attendee_user_ids)).all()
        } if attendee_user_ids else {}

        def _event_user_row(row):
            user = attendee_users.get(row.user_id)
            profile = attendee_profiles.get(row.user_id)
            return {
                "user_id": row.user_id,
                "email": getattr(user, "email", None),
                "status": getattr(user, "status", None),
                "nick": getattr(profile, "nick", None) if profile else None,
                "city": getattr(profile, "miasto", None) if profile else None,
                "created_at": str(row.created_at) if row.created_at else None,
            }

        signups = [_event_user_row(row) for row in signups_rows]
        saves = [_event_user_row(row) for row in saves_rows]

        partner_profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == event.partner_user_id)
            .first()
        )
        organizer_user = db.query(User).filter(User.id == event.partner_user_id).first()

        now_utc = datetime.now(timezone.utc)
        organizer_active_events = (
            db.query(Event)
            .filter(Event.partner_user_id == event.partner_user_id)
            .filter(Event.id != event.id)
            .filter(Event.status == "published")
            .filter(Event.end_at >= now_utc)
            .order_by(Event.start_at.asc())
            .limit(8)
            .all()
        )

        event_history_logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.details.isnot(None),
                AuditLog.details.like(f"%event_id={event.id}%")
            )
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )

        reports_file = Path(__file__).resolve().parent / "data" / "event_reports.jsonl"
        reports_total = 0
        reports_open = 0
        selected_report = None
        if reports_file.exists():
            with reports_file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    if int(row.get("event_id") or 0) == int(event_id):
                        reports_total += 1
                        if ticket and str(row.get("ticket") or "") == str(ticket):
                            selected_report = row
                        if str(row.get("status") or "new") not in {"resolved", "rejected", "archived"}:
                            reports_open += 1

        event_tags = []
        if getattr(event, "interest_tags_json", None):
            try:
                event_tags = json.loads(event.interest_tags_json) or []
            except Exception:
                event_tags = []
        if not event_tags and event.interest_tag:
            event_tags = [event.interest_tag]

        return ok({
            "id": event.id,
            "partner_user_id": event.partner_user_id,
            "organizer_name": getattr(partner_profile, "nazwa", None),
            "organizer_logo_url": getattr(partner_profile, "logo_url", None),
            "organizer_email": getattr(organizer_user, "email", None),
            "organizer_status": getattr(organizer_user, "status", None),
            "organizer_category": getattr(partner_profile, "kategoria", None),
            "organizer_city": getattr(partner_profile, "miasto", None),
            "organizer_bio": getattr(partner_profile, "bio", None),
            "organizer_plan": getattr(partner_profile, "plan", None),
            "organizer_active_events": [
                {
                    "id": other.id,
                    "title": other.title,
                    "city": other.city,
                    "where": getattr(other, "where", None),
                    "start_at": str(other.start_at) if other.start_at else None,
                    "end_at": str(other.end_at) if other.end_at else None,
                    "status": other.status,
                    "lifecycle_status": _admin_event_lifecycle_status(other),
                    "signups_count": db.query(EventSignup).filter(EventSignup.event_id == other.id).count(),
                    "saves_count": db.query(EventSave).filter(EventSave.event_id == other.id).count(),
                }
                for other in organizer_active_events
            ],
            "reports_total": reports_total,
            "reports_open": reports_open,
            "selected_report": selected_report,
            "title": event.title,
            "description": event.description,
            "city": event.city,
            "where": getattr(event, "where", None),
            "interest_tag": getattr(event, "interest_tag", None),
            "interest_tags": event_tags,
            "start_at": str(event.start_at) if event.start_at else None,
            "end_at": str(event.end_at) if event.end_at else None,
            "capacity": event.capacity,
            "status": event.status,
            "lifecycle_status": _admin_event_lifecycle_status(event),
            "signups_count": signups_count,
            "saves_count": saves_count,
            "signups": signups,
            "saves": saves,
            "event_history": [
                {
                    "action": log.action,
                    "details": log.details,
                    "created_at": str(log.created_at) if log.created_at else None,
                }
                for log in event_history_logs
            ],
            "created_at": str(event.created_at) if event.created_at else None,
            "updated_at": str(event.updated_at) if event.updated_at else None,
            "event_cover_url": getattr(event, "event_cover_url", None),
        })
    finally:
        db.close()


@app.get("/admin/bug-reports/{ticket}/reporter-context")
def admin_bug_reporter_context(
    ticket: str,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "reports")

    import json

    db = SessionLocal()
    try:
        reports_file = Path(__file__).resolve().parent / "data" / "bug_reports.jsonl"

        if not reports_file.exists():
            raise HTTPException(status_code=404, detail="BUG_REPORTS_NOT_FOUND")

        report = None

        with reports_file.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except Exception:
                    continue

                if str(row.get("ticket")) == str(ticket):
                    report = row
                    break

        if not report:
            raise HTTPException(status_code=404, detail="BUG_REPORT_NOT_FOUND")

        user_id = int(report.get("user_id") or 0)

        user_row = (
            db.query(User, UserProfile)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .filter(User.id == user_id)
            .first()
        )

        if not user_row:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

        user, profile = user_row

        interests = []
        if profile and profile.zainteresowania_json:
            try:
                interests = json.loads(profile.zainteresowania_json) or []
            except Exception:
                interests = []

        audit_logs = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(20)
            .all()
        )

        previous_bug_reports = []

        with reports_file.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except Exception:
                    continue

                if int(row.get("user_id") or 0) == int(user.id):
                    previous_bug_reports.append(row)

        return ok({
            "report": report,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "created_at": str(user.created_at) if user.created_at else None,
            },
            "profile": {
                "nick": getattr(profile, "nick", None) if profile else None,
                "city": getattr(profile, "city", None) if profile else None,
                "bio": getattr(profile, "bio", None) if profile else None,
                "avatar_url": getattr(profile, "avatar_url", None) if profile else None,
                "location_lat": getattr(profile, "location_lat", None) if profile else None,
                "location_lng": getattr(profile, "location_lng", None) if profile else None,
                "interests": interests,
                "updated_at": str(profile.updated_at) if profile and profile.updated_at else None,
            },
            "audit_logs": [
                {
                    "action": log.action,
                    "details": log.details,
                    "created_at": str(log.created_at) if log.created_at else None,
                    "ip": log.ip,
                }
                for log in audit_logs
            ],
            "previous_bug_reports": previous_bug_reports[::-1][:10],
        })
    finally:
        db.close()


@app.get("/admin/social-summary")
def admin_social_summary(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "dashboard")

    db = SessionLocal()
    try:
        groups_count = db.query(Group).count()
        group_memberships_count = db.query(GroupMembership).count()
        active_friendships_count = db.query(Friendship).filter(Friendship.status == "accepted").count()
        pending_friend_requests_count = db.query(Friendship).filter(Friendship.status == "pending").count()
        pending_group_invitations_count = db.query(GroupInvitation).filter(GroupInvitation.status == "pending").count()
        user_blocks_count = db.query(UserBlock).count()
        blocked_accounts_count = db.query(User).filter(User.status == UserStatus.BLOCKED.value).count()
        deleted_accounts_count = db.query(User).filter(User.status == UserStatus.DELETED.value).count()
        unverified_accounts_count = db.query(User).filter(
            User.status == UserStatus.ACTIVE.value,
            User.email_verified_at.is_(None),
        ).count()

        return ok({
            "groups_count": groups_count,
            "group_memberships_count": group_memberships_count,
            "active_friendships_count": active_friendships_count,
            "pending_friend_requests_count": pending_friend_requests_count,
            "pending_group_invitations_count": pending_group_invitations_count,
            "user_blocks_count": user_blocks_count,
            "blocked_accounts_count": blocked_accounts_count,
            "deleted_accounts_count": deleted_accounts_count,
            "unverified_accounts_count": unverified_accounts_count,
        })
    finally:
        db.close()


@app.get("/admin/staff/audit-log")
def admin_staff_audit_log(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "admin_manage")

    db = SessionLocal()
    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )

        admin_ids = [log.user_id for log in logs if log.user_id]
        admins = {
            user.id: user
            for user in db.query(User).filter(User.id.in_(admin_ids)).all()
        } if admin_ids else {}

        items = []
        for log in logs:
            actor = admins.get(log.user_id)
            items.append({
                "id": log.id,
                "created_at": str(log.created_at) if log.created_at else None,
                "action": log.action,
                "details": log.details,
                "ip": log.ip,
                "user_agent": log.user_agent,
                "admin_id": actor.id if actor else log.user_id,
                "admin_email": actor.email if actor else None,
                "admin_display_name": (actor.admin_display_name or actor.email) if actor else None,
                "admin_level": actor.admin_level if actor else None,
            })

        return ok({"items": items})
    finally:
        db.close()


@app.post("/admin/staff/{admin_id}/mfa/reset")
def admin_reset_staff_mfa(
    admin_id: int,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "admin_manage")

    db = SessionLocal()
    try:
        target = db.query(User).filter(User.id == admin_id).first()
        if not target or target.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=404, detail="ADMIN_NOT_FOUND")
        if target.id == current_user.id:
            raise HTTPException(status_code=400, detail="CANNOT_RESET_OWN_MFA_HERE")

        target.mfa_enabled = False
        target.mfa_secret = None
        target.mfa_backup_codes_hash = None
        target.mfa_enabled_at = None
        db.add(target)
        db.add(
            AuditLog(
                user_id=target.id,
                action="admin_reset_staff_mfa",
                details=f"admin_id={current_user.id}; admin_display_name={current_user.admin_display_name or current_user.email or f'Admin #{current_user.id}'}; target_admin_id={target.id}; target_admin_email={target.email}",
            )
        )
        db.commit()

        return ok({"admin_id": target.id, "mfa_enabled": False})
    finally:
        db.close()


@app.get("/admin/staff")
def admin_list_staff(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "admin_manage")

    db = SessionLocal()
    try:
        staff = (
            db.query(User)
            .filter(User.role == UserRole.ADMIN.value)
            .order_by(User.created_at.desc())
            .all()
        )

        items = []
        for user in staff:
            items.append({
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "admin_display_name": user.admin_display_name or user.email,
                "admin_level": user.admin_level or ADMIN_LEVEL_OWNER,
                "email_verified_at": str(user.email_verified_at) if getattr(user, "email_verified_at", None) else None,
                "email_verified": bool(getattr(user, "email_verified_at", None)),
                "created_at": str(user.created_at) if user.created_at else None,
            })

        return ok({"items": items})
    finally:
        db.close()


@app.get("/admin/users")
def admin_list_users(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "users")

    import json

    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .filter(User.role != UserRole.ADMIN.value)
            .order_by(User.created_at.desc())
            .all()
        )

        user_profiles = {
            profile.user_id: profile
            for profile in db.query(UserProfile).all()
        }
        partner_profiles = {
            profile.user_id: profile
            for profile in db.query(PartnerProfile).all()
        }

        user_report_stats = {}
        reports_file = Path(__file__).resolve().parent / "data" / "user_reports.jsonl"
        if reports_file.exists():
            with reports_file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue

                    reported_user_id = int(row.get("reported_user_id") or 0)
                    if not reported_user_id:
                        continue

                    stats = user_report_stats.setdefault(reported_user_id, {
                        "reports_total": 0,
                        "reports_open": 0,
                        "warnings_count": 0,
                        "moderation_decisions_count": 0,
                    })

                    status = str(row.get("status") or "new")
                    warning_type = str(row.get("warning_type") or "").strip()

                    stats["reports_total"] += 1
                    if status not in {"resolved", "rejected", "archived"}:
                        stats["reports_open"] += 1
                    if warning_type:
                        stats["warnings_count"] += 1
                    if status in {"resolved", "rejected", "archived", "pending_owner_approval"}:
                        stats["moderation_decisions_count"] += 1

        items = []
        for user in users:
            user_profile = user_profiles.get(user.id)
            partner_profile = partner_profiles.get(user.id)

            interests = []
            if user_profile and user_profile.zainteresowania_json:
                try:
                    interests = json.loads(user_profile.zainteresowania_json) or []
                except Exception:
                    interests = []

            if user.role == UserRole.PARTNER.value:
                display_name = getattr(partner_profile, "nazwa", None) or user.email
                city = getattr(partner_profile, "miasto", None)
                plan = getattr(partner_profile, "plan", None) or "free"
                plan_source = getattr(partner_profile, "plan_source", None)
                plan_status = getattr(partner_profile, "plan_status", None)
                plan_updated_at = str(partner_profile.plan_updated_at) if partner_profile and partner_profile.plan_updated_at else None
                plan_expires_at = str(partner_profile.plan_expires_at) if partner_profile and getattr(partner_profile, "plan_expires_at", None) else None
                avatar_url = getattr(partner_profile, "logo_url", None)
                bio = getattr(partner_profile, "bio", None)
            else:
                display_name = getattr(user_profile, "nick", None) or user.email
                city = getattr(user_profile, "miasto", None)
                if user.role == UserRole.ADMIN.value:
                    display_name = user.admin_display_name or user.email
                    city = None
                    plan = None
                    plan_source = None
                    plan_status = None
                    plan_updated_at = None
                    plan_expires_at = None
                    avatar_url = None
                    bio = None
                else:
                    plan = getattr(user_profile, "plan", None) or "free"
                    plan_source = getattr(user_profile, "plan_source", None) if user_profile else None
                    plan_status = getattr(user_profile, "plan_status", None) if user_profile else None
                    plan_updated_at = str(user_profile.plan_updated_at) if user_profile and user_profile.plan_updated_at else None
                    plan_expires_at = str(user_profile.plan_expires_at) if user_profile and getattr(user_profile, "plan_expires_at", None) else None
                    avatar_url = getattr(user_profile, "avatar_url", None)
                    bio = getattr(user_profile, "bio", None)

            friends_count = db.query(Friendship).filter(
                Friendship.status == "accepted",
                ((Friendship.requester_user_id == user.id) | (Friendship.addressee_user_id == user.id))
            ).count()

            blocks_count = db.query(UserBlock).filter(
                (UserBlock.blocker_user_id == user.id) | (UserBlock.blocked_user_id == user.id)
            ).count()

            groups_count = db.query(GroupMembership).filter(
                GroupMembership.user_id == user.id
            ).count()

            event_signups_count = db.query(EventSignup).filter(
                EventSignup.user_id == user.id
            ).count()

            moderation_stats = user_report_stats.get(user.id, {
                "reports_total": 0,
                "reports_open": 0,
                "warnings_count": 0,
                "moderation_decisions_count": 0,
            })

            items.append({
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "display_name": display_name,
                "admin_display_name": user.admin_display_name,
                "admin_level": user.admin_level,
                "city": city,
                "dob": str(user.dob) if getattr(user, "dob", None) else None,
                "email_verified_at": str(user.email_verified_at) if getattr(user, "email_verified_at", None) else None,
                "email_verified": bool(getattr(user, "email_verified_at", None)),
                "created_at": str(user.created_at) if user.created_at else None,
                "plan": plan,
                "plan_source": plan_source,
                "plan_status": plan_status,
                "plan_updated_at": plan_updated_at,
                "plan_expires_at": plan_expires_at,
                "avatar_url": avatar_url,
                "bio": bio,
                "interests": interests,
                "friends_count": friends_count,
                "blocks_count": blocks_count,
                "groups_count": groups_count,
                "event_signups_count": event_signups_count,
                "reports_total": moderation_stats["reports_total"],
                "reports_open": moderation_stats["reports_open"],
                "warnings_count": moderation_stats["warnings_count"],
                "moderation_decisions_count": moderation_stats["moderation_decisions_count"],
            })

        return ok({"items": items, "count": len(items)})
    finally:
        db.close()


@app.get("/admin/user-reports")
def get_admin_user_reports(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "reports")

    import json
    from pathlib import Path

    f = Path(__file__).resolve().parent / "data" / "user_reports.jsonl"
    if not f.exists():
        return {"success": True, "count": 0, "data": []}

    items = []
    with f.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                if line.strip():
                    items.append(json.loads(line))
            except Exception:
                pass

    return {"success": True, "count": len(items), "data": items[::-1]}


@app.post("/admin/events/{event_id}/notify-watchers")
def admin_notify_event_watchers(
    event_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    import json

    require_admin_permission(current_user, "events")

    payload = payload or {}
    ticket = str(payload.get("ticket") or "").strip()
    notification_type = str(payload.get("type") or "admin_event_under_review").strip()

    allowed_types = {
        "admin_event_under_review",
        "admin_event_archived",
        "admin_event_safety_notice",
    }
    if notification_type not in allowed_types:
        raise HTTPException(status_code=422, detail="INVALID_NOTIFICATION_TYPE")

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        signup_user_ids = {
            user_id
            for (user_id,) in (
                db.query(EventSignup.user_id)
                .filter(EventSignup.event_id == event.id)
                .all()
            )
        }
        saved_user_ids = {
            user_id
            for (user_id,) in (
                db.query(EventSave.user_id)
                .filter(EventSave.event_id == event.id)
                .all()
            )
        }
        target_user_ids = signup_user_ids | saved_user_ids

        for target_user_id in target_user_ids:
            db.add(
                UserNotification(
                    user_id=target_user_id,
                    event_id=event.id,
                    partner_user_id=event.partner_user_id,
                    type=notification_type,
                )
            )

        reports_file = Path(__file__).resolve().parent / "data" / "event_reports.jsonl"
        updated_report = None

        if ticket and reports_file.exists():
            rows = []
            with reports_file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue

                    if str(row.get("ticket") or "") == ticket:
                        now = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
                        history = row.get("history")
                        if not isinstance(history, list):
                            history = []

                        history.append({
                            "type": "notify_watchers",
                            "at": now,
                            "admin_id": current_user.id,
                            "admin_display_name": current_user.admin_display_name or current_user.email or f"Admin #{current_user.id}",
                            "admin_level": current_user.admin_level or "admin",
                            "notification_type": notification_type,
                            "notified_count": len(target_user_ids),
                        })

                        row["history"] = history
                        row["updated_at"] = now
                        row["updated_by_admin_id"] = current_user.id
                        updated_report = row

                    rows.append(row)

            with reports_file.open("w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")

        db.commit()

        return ok({
            "event_id": event.id,
            "ticket": ticket,
            "notification_type": notification_type,
            "notified_count": len(target_user_ids),
            "report": updated_report,
        })
    finally:
        db.close()


@app.get("/admin/events")
def admin_list_events(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "events")

    db = SessionLocal()
    try:
        events = db.query(Event).order_by(Event.created_at.desc()).all()

        partner_ids = list({ev.partner_user_id for ev in events})
        partners = {
            user.id: user
            for user in db.query(User).filter(User.id.in_(partner_ids)).all()
        } if partner_ids else {}
        partner_profiles = {
            profile.user_id: profile
            for profile in db.query(PartnerProfile).filter(PartnerProfile.user_id.in_(partner_ids)).all()
        } if partner_ids else {}

        items = []
        for ev in events:
            signups_count = db.query(EventSignup).filter(EventSignup.event_id == ev.id).count()
            saves_count = db.query(EventSave).filter(EventSave.event_id == ev.id).count()

            organizer = partners.get(ev.partner_user_id)
            organizer_profile = partner_profiles.get(ev.partner_user_id)

            event_tags = []
            if getattr(ev, "interest_tags_json", None):
                try:
                    event_tags = json.loads(ev.interest_tags_json) or []
                except Exception:
                    event_tags = []
            if not event_tags and ev.interest_tag:
                event_tags = [ev.interest_tag]

            items.append({
                "id": ev.id,
                "title": ev.title,
                "description": ev.description,
                "city": ev.city,
                "where": ev.where,
                "interest_tag": ev.interest_tag,
                "interest_tags": event_tags,
                "start_at": str(ev.start_at) if ev.start_at else None,
                "end_at": str(ev.end_at) if ev.end_at else None,
                "capacity": ev.capacity,
                "status": ev.status,
                "lifecycle_status": _admin_event_lifecycle_status(ev),
                "created_at": str(ev.created_at) if ev.created_at else None,
                "updated_at": str(ev.updated_at) if ev.updated_at else None,
                "pricing_type": getattr(ev, "pricing_type", None),
                "price_fixed": getattr(ev, "price_fixed", None),
                "price_min": getattr(ev, "price_min", None),
                "price_max": getattr(ev, "price_max", None),
                "event_cover_url": getattr(ev, "event_cover_url", None),
                "partner_user_id": ev.partner_user_id,
                "organizer_email": getattr(organizer, "email", None),
                "organizer_email_verified": bool(getattr(organizer, "email_verified_at", None)),
                "organizer_email_verified_at": str(organizer.email_verified_at) if organizer and getattr(organizer, "email_verified_at", None) else None,
                "organizer_name": getattr(organizer_profile, "nazwa", None) or getattr(organizer, "email", None),
                "organizer_status": getattr(organizer, "status", None),
                "organizer_plan": getattr(organizer_profile, "plan", None) if organizer_profile else None,
                "signups_count": signups_count,
                "saves_count": saves_count,
            })

        return ok({"items": items, "count": len(items)})
    finally:
        db.close()


@app.get("/admin/event-reports")
def get_admin_event_reports(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "reports")
    import json
    from pathlib import Path

    f = Path(__file__).resolve().parent / "data" / "event_reports.jsonl"
    if not f.exists():
        return {"success": True, "count": 0, "data": []}

    items = []
    with f.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                if line.strip():
                    items.append(json.loads(line))
            except Exception:
                pass

    return {"success": True, "count": len(items), "data": items[::-1]}


@app.get("/admin/bug-reports")
def get_bug_reports(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "reports")
    import json
    from pathlib import Path

    f = Path(__file__).resolve().parent / "data" / "bug_reports.jsonl"
    if not f.exists():
        return {"success": True, "data": []}

    items = []
    with f.open() as fh:
        for line in fh:
            try:
                items.append(json.loads(line))
            except:
                pass

    return {"success": True, "count": len(items), "data": items[::-1]}

@app.get("/users/me/notifications")
def my_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        ensure_event_reminder_notifications(db)
        db.commit()

        q = (
            db.query(UserNotification, Event)
            .outerjoin(Event, Event.id == UserNotification.event_id)
            .filter(UserNotification.user_id == current_user.id)
            .order_by(UserNotification.created_at.desc())
        )

        total = q.count()
        rows = q.offset(offset).limit(limit).all()

        items = []
        for notification, event in rows:
            items.append(
                {
                    "notification": {
                        "id": notification.id,
                        "type": notification.type,
                        "created_at": notification.created_at,
                        "read_at": notification.read_at,
                        "event_id": notification.event_id,
                        "partner_user_id": notification.partner_user_id,
                    },
                    "event": {
                        "id": event.id,
                        "title": event.title,
                        "city": event.city,
                        "where": event.where,
                        "start_at": event.start_at,
                        "end_at": event.end_at,
                        "status": event.status,
                    } if event else None,
                }
            )

        return ok({
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    finally:
        db.close()



@app.get("/admin/promo-campaigns")
def admin_list_promo_campaigns(current_user: User = Depends(require_role("admin"))):
    require_admin_permission(current_user, "plans")

    db = SessionLocal()
    try:
        campaigns = (
            db.query(PromoCampaign)
            .order_by(PromoCampaign.created_at.desc(), PromoCampaign.id.desc())
            .limit(200)
            .all()
        )

        return ok({
            "items": [
                {
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                    "owner_user_id": c.owner_user_id,
                    "target_role": c.target_role,
                    "benefit_type": c.benefit_type,
                    "benefit_value": c.benefit_value,
                    "benefit_duration_months": c.benefit_duration_months,
                    "reward_type": c.reward_type,
                    "reward_value": c.reward_value,
                    "reward_threshold": c.reward_threshold,
                    "max_uses": c.max_uses,
                    "uses_count": c.uses_count,
                    "valid_from": c.valid_from.isoformat() if c.valid_from else None,
                    "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                    "status": c.status,
                    "ios_offer_code": c.ios_offer_code,
                    "android_promo_code": c.android_promo_code,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in campaigns
            ]
        })
    finally:
        db.close()


@app.post("/admin/promo-campaigns")
def admin_create_promo_campaign(
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "plans")

    code = str((payload or {}).get("code") or "").strip().upper()
    name = str((payload or {}).get("name") or "").strip() or None
    owner_user_id = (payload or {}).get("owner_user_id")
    target_role = str((payload or {}).get("target_role") or "user").strip().lower()
    benefit_type = str((payload or {}).get("benefit_type") or "discount_percent").strip().lower()
    benefit_value = (payload or {}).get("benefit_value")
    benefit_duration_months = (payload or {}).get("benefit_duration_months")
    reward_type = str((payload or {}).get("reward_type") or "vip_months").strip().lower()
    reward_value = (payload or {}).get("reward_value")
    reward_threshold = (payload or {}).get("reward_threshold")
    max_uses = (payload or {}).get("max_uses")
    valid_until_raw = str((payload or {}).get("valid_until") or "").strip()
    note = str((payload or {}).get("note") or "").strip() or None
    ios_offer_code = str((payload or {}).get("ios_offer_code") or "").strip() or None
    android_promo_code = str((payload or {}).get("android_promo_code") or "").strip() or None

    if not code or len(code) < 3 or len(code) > 40 or not code.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="INVALID_PROMO_CODE")

    if target_role not in {"user", "partner", "both"}:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_TARGET_ROLE")

    if benefit_type not in {"discount_percent", "trial_days", "free_months", "store_offer"}:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_BENEFIT_TYPE")

    if reward_type not in {"vip_months", "none"}:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_REWARD_TYPE")

    def _optional_positive_int(value, field_name: str):
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except Exception:
            raise HTTPException(status_code=422, detail=f"INVALID_{field_name}")
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"INVALID_{field_name}")
        return parsed

    benefit_value = _optional_positive_int(benefit_value, "BENEFIT_VALUE")
    benefit_duration_months = _optional_positive_int(benefit_duration_months, "BENEFIT_DURATION_MONTHS")
    reward_value = _optional_positive_int(reward_value, "REWARD_VALUE")
    reward_threshold = _optional_positive_int(reward_threshold, "REWARD_THRESHOLD")
    if reward_type != "none" and reward_value and (reward_threshold is None or reward_threshold < 10):
        raise HTTPException(status_code=422, detail="INVALID_REWARD_THRESHOLD")
    max_uses = _optional_positive_int(max_uses, "MAX_USES")

    if benefit_type == "discount_percent" and (benefit_value is None or benefit_value < 1 or benefit_value > 90):
        raise HTTPException(status_code=422, detail="INVALID_DISCOUNT_PERCENT")

    if benefit_type == "discount_percent" and (benefit_duration_months is None or benefit_duration_months < 1 or benefit_duration_months > 12):
        raise HTTPException(status_code=422, detail="INVALID_DISCOUNT_DURATION")

    valid_until = None
    if valid_until_raw:
        try:
            valid_until = datetime.fromisoformat(valid_until_raw.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=422, detail="INVALID_VALID_UNTIL")

    db = SessionLocal()
    try:
        existing = db.query(PromoCampaign).filter(PromoCampaign.code == code).first()
        if existing:
            raise HTTPException(status_code=409, detail="PROMO_CODE_ALREADY_EXISTS")

        if owner_user_id not in (None, ""):
            try:
                owner_user_id = int(owner_user_id)
            except Exception:
                raise HTTPException(status_code=422, detail="INVALID_OWNER_USER_ID")

            owner = db.query(User).filter(User.id == owner_user_id).first()
            if not owner:
                raise HTTPException(status_code=404, detail="OWNER_USER_NOT_FOUND")
        else:
            owner_user_id = None

        now = datetime.utcnow()
        campaign = PromoCampaign(
            code=code,
            name=name,
            owner_user_id=owner_user_id,
            created_by_admin_id=current_user.id,
            target_role=target_role,
            benefit_type=benefit_type,
            benefit_value=benefit_value,
            benefit_duration_months=benefit_duration_months,
            reward_type=reward_type,
            reward_value=reward_value,
            reward_threshold=reward_threshold,
            max_uses=max_uses,
            valid_from=now,
            valid_until=valid_until,
            status="active",
            note=note,
            ios_offer_code=ios_offer_code,
            android_promo_code=android_promo_code,
            created_at=now,
            updated_at=now,
        )
        db.add(campaign)
        db.add(AuditLog(
            user_id=current_user.id,
            action="admin_create_promo_campaign",
            details=f"admin_id={current_user.id}; code={code}; owner_user_id={owner_user_id or '-'}; benefit={benefit_type}:{benefit_value}; duration_months={benefit_duration_months or '-'}; reward={reward_type}:{reward_value or '-'}; reward_threshold={reward_threshold or '-'}",
        ))
        db.commit()
        db.refresh(campaign)

        return ok({
            "id": campaign.id,
            "code": campaign.code,
            "status": campaign.status,
        })
    finally:
        db.close()


@app.patch("/admin/promo-campaigns/{campaign_id}")
def admin_update_promo_campaign(
    campaign_id: int,
    payload: dict,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "plans")

    allowed_statuses = {"active", "paused", "ended", "expired"}
    allowed_target_roles = {"user", "partner", "both"}
    allowed_benefit_types = {"discount_percent", "trial_days", "free_months", "store_offer"}
    allowed_reward_types = {"vip_months", "none"}

    def _optional_str(value):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def _optional_positive_int(value, field_name: str):
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except Exception:
            raise HTTPException(status_code=422, detail=f"INVALID_{field_name}")
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"INVALID_{field_name}")
        return parsed

    db = SessionLocal()
    try:
        campaign = db.query(PromoCampaign).filter(PromoCampaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="PROMO_CAMPAIGN_NOT_FOUND")

        data = payload or {}
        now = datetime.utcnow()
        changes = []

        if "name" in data:
            campaign.name = _optional_str(data.get("name"))
            changes.append("name")

        if "target_role" in data:
            target_role = str(data.get("target_role") or "").strip().lower()
            if target_role not in allowed_target_roles:
                raise HTTPException(status_code=422, detail="INVALID_PROMO_TARGET_ROLE")
            campaign.target_role = target_role
            changes.append("target_role")

        if "benefit_type" in data:
            benefit_type = str(data.get("benefit_type") or "").strip().lower()
            if benefit_type not in allowed_benefit_types:
                raise HTTPException(status_code=422, detail="INVALID_PROMO_BENEFIT_TYPE")
            campaign.benefit_type = benefit_type
            changes.append("benefit_type")

        if "benefit_value" in data:
            campaign.benefit_value = _optional_positive_int(data.get("benefit_value"), "BENEFIT_VALUE")
            changes.append("benefit_value")

        if "benefit_duration_months" in data:
            campaign.benefit_duration_months = _optional_positive_int(data.get("benefit_duration_months"), "BENEFIT_DURATION_MONTHS")
            changes.append("benefit_duration_months")

        if "reward_type" in data:
            reward_type = str(data.get("reward_type") or "").strip().lower()
            if reward_type not in allowed_reward_types:
                raise HTTPException(status_code=422, detail="INVALID_PROMO_REWARD_TYPE")
            campaign.reward_type = reward_type
            changes.append("reward_type")

        if "reward_value" in data:
            campaign.reward_value = _optional_positive_int(data.get("reward_value"), "REWARD_VALUE")
            changes.append("reward_value")

        if "reward_threshold" in data:
            reward_threshold = _optional_positive_int(data.get("reward_threshold"), "REWARD_THRESHOLD")
            if campaign.reward_type != "none" and campaign.reward_value and (reward_threshold is None or reward_threshold < 10):
                raise HTTPException(status_code=422, detail="INVALID_REWARD_THRESHOLD")
            campaign.reward_threshold = reward_threshold
            changes.append("reward_threshold")

        if "max_uses" in data:
            campaign.max_uses = _optional_positive_int(data.get("max_uses"), "MAX_USES")
            changes.append("max_uses")

        if "valid_until" in data:
            valid_until_raw = str(data.get("valid_until") or "").strip()
            if valid_until_raw:
                try:
                    campaign.valid_until = datetime.fromisoformat(valid_until_raw.replace("Z", "+00:00"))
                except Exception:
                    raise HTTPException(status_code=422, detail="INVALID_VALID_UNTIL")
            else:
                campaign.valid_until = None
            changes.append("valid_until")

        if "status" in data:
            status = str(data.get("status") or "").strip().lower()
            if status not in allowed_statuses:
                raise HTTPException(status_code=422, detail="INVALID_PROMO_STATUS")
            campaign.status = status
            changes.append("status")

        if "note" in data:
            campaign.note = _optional_str(data.get("note"))
            changes.append("note")

        if "ios_offer_code" in data:
            campaign.ios_offer_code = _optional_str(data.get("ios_offer_code"))
            changes.append("ios_offer_code")

        if "android_promo_code" in data:
            campaign.android_promo_code = _optional_str(data.get("android_promo_code"))
            changes.append("android_promo_code")

        if campaign.benefit_type == "discount_percent" and (campaign.benefit_value is None or campaign.benefit_value < 1 or campaign.benefit_value > 90):
            raise HTTPException(status_code=422, detail="INVALID_DISCOUNT_PERCENT")

        if campaign.benefit_type == "discount_percent" and (campaign.benefit_duration_months is None or campaign.benefit_duration_months < 1 or campaign.benefit_duration_months > 12):
            raise HTTPException(status_code=422, detail="INVALID_DISCOUNT_DURATION")

        campaign.updated_at = now
        db.add(campaign)
        db.add(AuditLog(
            user_id=current_user.id,
            action="admin_update_promo_campaign",
            details=f"admin_id={current_user.id}; campaign_id={campaign.id}; code={campaign.code}; changes={','.join(changes) or '-'}",
        ))
        db.commit()
        db.refresh(campaign)

        return ok({
            "id": campaign.id,
            "code": campaign.code,
            "status": campaign.status,
            "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        })
    finally:
        db.close()


@app.get("/promo-campaigns/validate/{code}")
def validate_promo_campaign(code: str):
    clean_code = str(code or "").strip().upper()

    if not clean_code:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_CODE")

    db = SessionLocal()
    try:
        campaign = db.query(PromoCampaign).filter(PromoCampaign.code == clean_code).first()
        now = datetime.utcnow()

        if not campaign:
            raise HTTPException(status_code=404, detail="PROMO_CODE_NOT_FOUND")

        if campaign.status != "active":
            raise HTTPException(status_code=409, detail="PROMO_CODE_INACTIVE")

        if campaign.valid_from and campaign.valid_from > now:
            raise HTTPException(status_code=409, detail="PROMO_CODE_NOT_STARTED")

        if campaign.valid_until and campaign.valid_until < now:
            raise HTTPException(status_code=410, detail="PROMO_CODE_EXPIRED")

        if campaign.max_uses is not None and campaign.uses_count >= campaign.max_uses:
            raise HTTPException(status_code=409, detail="PROMO_CODE_LIMIT_REACHED")

        return ok({
            "code": campaign.code,
            "name": campaign.name,
            "target_role": campaign.target_role,
            "benefit_type": campaign.benefit_type,
            "benefit_value": campaign.benefit_value,
            "benefit_duration_months": campaign.benefit_duration_months,
            "reward_type": campaign.reward_type,
            "reward_value": campaign.reward_value,
            "ios_offer_code": campaign.ios_offer_code,
            "android_promo_code": campaign.android_promo_code,
            "valid_from": campaign.valid_from.isoformat() if campaign.valid_from else None,
            "valid_until": campaign.valid_until.isoformat() if campaign.valid_until else None,
            "max_uses": campaign.max_uses,
            "uses_count": campaign.uses_count,
        })
    finally:
        db.close()


@app.post("/promo-campaigns/redeem")
def redeem_promo_campaign(
    payload: dict,
    current_user: User = Depends(require_role("user", "partner")),
):
    clean_code = str((payload or {}).get("code") or "").strip().upper()
    platform = str((payload or {}).get("platform") or "").strip().lower() or None

    if not clean_code:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_CODE")

    if platform and platform not in {"ios", "android", "web"}:
        raise HTTPException(status_code=422, detail="INVALID_PROMO_PLATFORM")

    db = SessionLocal()
    try:
        campaign = db.query(PromoCampaign).filter(PromoCampaign.code == clean_code).first()
        now = datetime.utcnow()

        if not campaign or campaign.status != "active":
            raise HTTPException(status_code=404, detail="PROMO_CODE_NOT_FOUND")

        if campaign.valid_until and campaign.valid_until < now:
            raise HTTPException(status_code=410, detail="PROMO_CODE_EXPIRED")

        if campaign.max_uses is not None and campaign.uses_count >= campaign.max_uses:
            raise HTTPException(status_code=409, detail="PROMO_CODE_LIMIT_REACHED")

        if campaign.target_role != "both" and campaign.target_role != current_user.role:
            raise HTTPException(status_code=403, detail="PROMO_CODE_NOT_FOR_THIS_ROLE")

        existing = (
            db.query(PromoRedemption)
            .filter(
                PromoRedemption.campaign_id == campaign.id,
                PromoRedemption.user_id == current_user.id,
            )
            .first()
        )
        if existing:
            return ok({
                "id": existing.id,
                "code": campaign.code,
                "status": existing.status,
                "already_redeemed": True,
                "benefit_type": campaign.benefit_type,
                "benefit_value": campaign.benefit_value,
                "benefit_duration_months": campaign.benefit_duration_months,
                "ios_offer_code": campaign.ios_offer_code,
                "android_promo_code": campaign.android_promo_code,
            })

        redemption = PromoRedemption(
            campaign_id=campaign.id,
            user_id=current_user.id,
            platform=platform,
            status="reserved",
            created_at=now,
        )
        campaign.uses_count = int(campaign.uses_count or 0) + 1
        campaign.updated_at = now

        db.add(redemption)
        db.add(campaign)
        db.add(AuditLog(
            user_id=current_user.id,
            action="promo_campaign_redeemed",
            details=f"code={campaign.code}; campaign_id={campaign.id}; platform={platform or '-'}; status=reserved",
        ))
        db.commit()
        db.refresh(redemption)

        return ok({
            "id": redemption.id,
            "code": campaign.code,
            "status": redemption.status,
            "already_redeemed": False,
            "benefit_type": campaign.benefit_type,
            "benefit_value": campaign.benefit_value,
            "benefit_duration_months": campaign.benefit_duration_months,
            "ios_offer_code": campaign.ios_offer_code,
            "android_promo_code": campaign.android_promo_code,
        })
    finally:
        db.close()


@app.get("/admin/promo-campaigns/{campaign_id}")
def admin_get_promo_campaign(
    campaign_id: int,
    current_user: User = Depends(require_role("admin")),
):
    require_admin_permission(current_user, "plans")

    db = SessionLocal()
    try:
        campaign = db.query(PromoCampaign).filter(PromoCampaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="PROMO_CAMPAIGN_NOT_FOUND")

        owner_user = db.query(User).filter(User.id == campaign.owner_user_id).first() if campaign.owner_user_id else None
        owner_user_profile = db.query(UserProfile).filter(UserProfile.user_id == owner_user.id).first() if owner_user and owner_user.role != UserRole.PARTNER.value else None
        owner_partner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == owner_user.id).first() if owner_user and owner_user.role == UserRole.PARTNER.value else None
        owner_profile = owner_partner_profile if owner_user and owner_user.role == UserRole.PARTNER.value else owner_user_profile
        owner_display_name = (
            getattr(owner_profile, "nick", None)
            or getattr(owner_profile, "nazwa", None)
            or (owner_user.admin_display_name if owner_user else None)
            or (owner_user.email if owner_user else None)
        )

        redemption_rows = (
            db.query(PromoRedemption, User, UserProfile, PartnerProfile)
            .join(User, User.id == PromoRedemption.user_id)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .outerjoin(PartnerProfile, PartnerProfile.user_id == User.id)
            .filter(PromoRedemption.campaign_id == campaign.id)
            .order_by(PromoRedemption.created_at.desc(), PromoRedemption.id.desc())
            .limit(300)
            .all()
        )

        redemptions = []
        paid_activations_count = 0
        paid_user_count = 0
        paid_partner_count = 0
        plan_breakdown = {}
        role_plan_breakdown = {}

        for redemption, user, user_profile, partner_profile in redemption_rows:
            profile = partner_profile if user.role == UserRole.PARTNER.value else user_profile
            plan = str(getattr(profile, "plan", None) or "free").lower()
            plan_status = str(getattr(profile, "plan_status", None) or "active").lower()
            is_paid_activation = (
                str(redemption.status or "").lower() == "activated"
                and plan_status == "active"
                and plan != "free"
            )

            if is_paid_activation:
                paid_activations_count += 1
                if user.role == UserRole.PARTNER.value:
                    paid_partner_count += 1
                else:
                    paid_user_count += 1
                plan_breakdown[plan] = plan_breakdown.get(plan, 0) + 1
                role_key = "partner" if user.role == UserRole.PARTNER.value else "user"
                role_plan_breakdown.setdefault(role_key, {})
                role_plan_breakdown[role_key][plan] = role_plan_breakdown[role_key].get(plan, 0) + 1

            display_name = (
                getattr(profile, "nick", None)
                or getattr(profile, "nazwa", None)
                or user.email
                or f"User #{user.id}"
            )

            redemptions.append({
                "id": redemption.id,
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "display_name": display_name,
                "plan": plan,
                "plan_status": plan_status,
                "platform": redemption.platform,
                "status": redemption.status,
                "store_transaction_id": redemption.store_transaction_id,
                "created_at": redemption.created_at.isoformat() if redemption.created_at else None,
                "activated_at": redemption.activated_at.isoformat() if redemption.activated_at else None,
            })

        reward_grant_rows = (
            db.query(AmbassadorRewardGrant)
            .filter(AmbassadorRewardGrant.campaign_id == campaign.id)
            .order_by(AmbassadorRewardGrant.reward_number.asc())
            .all()
        )
        reward_grants = [
            {
                "id": grant.id,
                "ambassador_user_id": grant.ambassador_user_id,
                "threshold": grant.threshold,
                "reward_number": grant.reward_number,
                "reward_months": grant.reward_months,
                "paid_activations_count": grant.paid_activations_count,
                "granted_at": grant.granted_at.isoformat() if grant.granted_at else None,
                "plan_expires_at_before": grant.plan_expires_at_before.isoformat() if grant.plan_expires_at_before else None,
                "plan_expires_at_after": grant.plan_expires_at_after.isoformat() if grant.plan_expires_at_after else None,
            }
            for grant in reward_grant_rows
        ]

        reward_threshold = int(campaign.reward_threshold or 0)
        next_reward_at = reward_threshold * ((paid_activations_count // reward_threshold) + 1) if reward_threshold >= 10 else None
        current_reward_progress = f"{paid_activations_count} / {next_reward_at}" if next_reward_at else None

        return ok({
            "campaign": {
                "id": campaign.id,
                "code": campaign.code,
                "name": campaign.name,
                "owner_user_id": campaign.owner_user_id,
                "owner_display_name": owner_display_name,
                "owner_email": owner_user.email if owner_user else None,
                "owner_role": owner_user.role if owner_user else None,
                "target_role": campaign.target_role,
                "benefit_type": campaign.benefit_type,
                "benefit_value": campaign.benefit_value,
                "benefit_duration_months": campaign.benefit_duration_months,
                "reward_type": campaign.reward_type,
                "reward_value": campaign.reward_value,
                "reward_threshold": campaign.reward_threshold,
                "max_uses": campaign.max_uses,
                "uses_count": campaign.uses_count,
                "valid_from": campaign.valid_from.isoformat() if campaign.valid_from else None,
                "valid_until": campaign.valid_until.isoformat() if campaign.valid_until else None,
                "status": campaign.status,
                "ios_offer_code": campaign.ios_offer_code,
                "android_promo_code": campaign.android_promo_code,
                "note": campaign.note,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
            },
            "stats": {
                "redemptions_count": len(redemptions),
                "paid_activations_count": paid_activations_count,
                "paid_user_count": paid_user_count,
                "paid_partner_count": paid_partner_count,
                "plan_breakdown": plan_breakdown,
                "role_plan_breakdown": role_plan_breakdown,
                "reward_grants_count": len(reward_grants),
                "reward_threshold": reward_threshold if reward_threshold >= 10 else None,
                "next_reward_at": next_reward_at,
                "current_reward_progress": current_reward_progress,
            },
            "redemptions": redemptions,
            "reward_grants": reward_grants,
        })
    finally:
        db.close()
