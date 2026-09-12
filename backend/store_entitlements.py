"""Ochrona aktywnych uprawnień wynikających z zakupów sklepowych."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import StorePurchase


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _revenuecat_gives_access(purchase: StorePurchase) -> bool | None:
    """Odczytuje zapisane gives_access ze zweryfikowanego payloadu RevenueCat."""

    raw_payload = purchase.raw_payload
    if not raw_payload:
        return None

    try:
        payload = (
            json.loads(raw_payload)
            if isinstance(raw_payload, str)
            else raw_payload
        )
    except (TypeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    gives_access = payload.get("gives_access")
    if isinstance(gives_access, bool):
        return gives_access

    return None


def store_purchase_has_access(
    purchase: StorePurchase,
    *,
    now: datetime,
) -> bool:
    """Sprawdza, czy zapisany zakup nadal daje płatny dostęp."""

    if purchase.revoked_at is not None:
        return False

    plan = str(purchase.plan or "").strip().lower()
    if not plan or plan == "free":
        return False

    revenuecat_access = _revenuecat_gives_access(purchase)

    # RevenueCat jednoznacznie odebrał dostęp, np. refund/revocation.
    if revenuecat_access is False:
        return False

    expires_at = purchase.plan_expires_at or purchase.expires_at

    # Nawet stary payload z gives_access=True nie może przedłużać
    # dostępu po zapisanym końcu okresu.
    if expires_at is not None:
        return _as_utc_naive(expires_at) > _as_utc_naive(now)

    # Dla zakupu bez daty końca (np. lifetime) RevenueCat jest
    # źródłem prawdy, jeśli informacja gives_access została zapisana.
    if revenuecat_access is not None:
        return revenuecat_access

    # Fallback dla starszych rekordów bez gives_access.
    return str(purchase.status or "").strip().lower() == "active"


def get_active_store_purchase(
    db: Session,
    *,
    user_id: int,
    now: datetime,
) -> StorePurchase | None:
    """Zwraca aktywny płatny zakup użytkownika, jeśli taki istnieje."""

    purchases = (
        db.query(StorePurchase)
        .filter(StorePurchase.user_id == user_id)
        .order_by(StorePurchase.id.desc())
        .all()
    )

    for purchase in purchases:
        if store_purchase_has_access(purchase, now=now):
            return purchase

    return None
