"""Nakładanie końcowego planu RevenueCat na profil użytkownika USLY.

Moduł:

- nie wykonuje requestów HTTP,
- nie zapisuje StorePurchase,
- nie parsuje webhooków,
- nie wykonuje commit ani rollback,
- aktualizuje wyłącznie UserProfile albo PartnerProfile.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import PartnerProfile, User, UserProfile
from backend.revenuecat_sync import EffectivePlan
from backend.store_purchase_data import StorePurchaseData


class EffectivePlanApplierError(RuntimeError):
    """Nie udało się bezpiecznie zastosować końcowego planu."""


@dataclass(frozen=True)
class EffectivePlanApplyResult:
    """Wynik zastosowania albo zachowania planu profilu."""

    profile_type: str
    previous_plan: str
    effective_plan: str
    applied: bool
    protected_existing_plan: bool


_PROTECTED_PLAN_SOURCES = {
    "ambassador",
    "barter",
    "manual",
    "promo",
}

_USER_PLAN_RANKS = {
    "free": 0,
    "plus": 1,
    "premium": 2,
    "vip": 3,
}

_PARTNER_PLAN_RANKS = {
    "free": 0,
    "pro": 1,
    "premium": 2,
    "enterprise": 3,
}


def apply_effective_plan(
    *,
    db: Session,
    user: User,
    effective_plan: EffectivePlan,
    purchase_data: StorePurchaseData | None,
    applied_at: datetime,
) -> EffectivePlanApplyResult:
    """Stosuje plan RevenueCat albo zachowuje ważny plan spoza sklepu."""

    if not isinstance(db, Session):
        raise EffectivePlanApplierError(
            "db musi być aktywną sesją SQLAlchemy"
        )

    if not user or not getattr(user, "id", None):
        raise EffectivePlanApplierError(
            "user musi być zapisanym użytkownikiem"
        )

    if not isinstance(applied_at, datetime):
        raise EffectivePlanApplierError(
            "applied_at musi być znacznikiem czasu datetime"
        )

    role = str(getattr(user, "role", "") or "").strip().lower()
    effective_role = str(effective_plan.role or "").strip().lower()
    effective_plan_name = str(effective_plan.plan or "").strip().lower()

    if role != effective_role:
        raise EffectivePlanApplierError(
            "Rola użytkownika nie odpowiada roli Effective Plan"
        )

    if role == "partner":
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == user.id)
            .first()
        )
        profile_type = "partner"
        ranks = _PARTNER_PLAN_RANKS
    elif role == "user":
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user.id)
            .first()
        )
        profile_type = "user"
        ranks = _USER_PLAN_RANKS
    else:
        raise EffectivePlanApplierError(
            f"Nieobsługiwana rola użytkownika: {role!r}"
        )

    if profile is None:
        raise EffectivePlanApplierError(
            f"Nie znaleziono profilu dla roli {role!r}"
        )

    if effective_plan_name not in ranks:
        raise EffectivePlanApplierError(
            (
                "Effective Plan zawiera nieobsługiwany plan "
                f"{effective_plan_name!r} dla roli {role!r}"
            )
        )

    previous_plan = str(profile.plan or "free").strip().lower()
    previous_source = str(profile.plan_source or "").strip().lower()
    previous_status = str(profile.plan_status or "active").strip().lower()

    existing_plan_updated_at = getattr(
        profile,
        "plan_updated_at",
        None,
    )

    if (
        isinstance(existing_plan_updated_at, datetime)
        and _as_utc_naive(applied_at)
        < _as_utc_naive(existing_plan_updated_at)
    ):
        return EffectivePlanApplyResult(
            profile_type=profile_type,
            previous_plan=previous_plan,
            effective_plan=previous_plan,
            applied=False,
            protected_existing_plan=False,
        )

    if _should_preserve_existing_plan(
        role=role,
        current_plan=previous_plan,
        current_source=previous_source,
        current_status=previous_status,
        current_expires_at=profile.plan_expires_at,
        effective_plan=effective_plan_name,
        applied_at=applied_at,
    ):
        return EffectivePlanApplyResult(
            profile_type=profile_type,
            previous_plan=previous_plan,
            effective_plan=previous_plan,
            applied=False,
            protected_existing_plan=True,
        )

    if effective_plan_name == "free":
        if purchase_data is not None:
            raise EffectivePlanApplierError(
                "Plan free nie może otrzymać StorePurchaseData"
            )

        profile.plan = "free"
        profile.plan_source = "system"
        profile.plan_status = "expired"
        profile.plan_expires_at = None
    else:
        if purchase_data is None:
            raise EffectivePlanApplierError(
                "Płatny Effective Plan wymaga StorePurchaseData"
            )

        if purchase_data.role != role:
            raise EffectivePlanApplierError(
                "Rola StorePurchaseData nie odpowiada roli użytkownika"
            )

        if purchase_data.plan != effective_plan_name:
            raise EffectivePlanApplierError(
                "Plan StorePurchaseData nie odpowiada Effective Plan"
            )

        if not purchase_data.gives_access:
            raise EffectivePlanApplierError(
                "StorePurchaseData nie potwierdza dostępu do planu"
            )

        profile.plan = effective_plan_name
        profile.plan_source = "paid"
        profile.plan_status = "active"
        profile.plan_expires_at = purchase_data.plan_expires_at

    profile.plan_updated_at = applied_at
    profile.plan_expiry_notice_14d_sent_at = None
    profile.plan_expiry_notice_7d_sent_at = None
    profile.updated_at = applied_at

    db.add(profile)
    db.flush()

    return EffectivePlanApplyResult(
        profile_type=profile_type,
        previous_plan=previous_plan,
        effective_plan=effective_plan_name,
        applied=True,
        protected_existing_plan=False,
    )


def _should_preserve_existing_plan(
    *,
    role: str,
    current_plan: str,
    current_source: str,
    current_status: str,
    current_expires_at: datetime | None,
    effective_plan: str,
    applied_at: datetime,
) -> bool:
    """Chroni ważne plany spoza RevenueCat przed automatycznym nadpisaniem."""

    if role == "partner" and current_plan == "enterprise":
        return _is_current_plan_active(
            current_status=current_status,
            current_expires_at=current_expires_at,
            applied_at=applied_at,
        )

    if current_source not in _PROTECTED_PLAN_SOURCES:
        return False

    if current_plan == "free":
        return False

    if not _is_current_plan_active(
        current_status=current_status,
        current_expires_at=current_expires_at,
        applied_at=applied_at,
    ):
        return False

    ranks = (
        _PARTNER_PLAN_RANKS
        if role == "partner"
        else _USER_PLAN_RANKS
    )

    return ranks.get(current_plan, 0) >= ranks.get(effective_plan, 0)


def _is_current_plan_active(
    *,
    current_status: str,
    current_expires_at: datetime | None,
    applied_at: datetime,
) -> bool:
    if current_status not in {"active", "trial"}:
        return False

    if current_expires_at is None:
        return True

    expires_at = _as_utc_naive(current_expires_at)
    current_time = _as_utc_naive(applied_at)

    return expires_at > current_time


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value

    return value.astimezone(timezone.utc).replace(tzinfo=None)
