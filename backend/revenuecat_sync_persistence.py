"""Wspólna warstwa trwałego zastosowania wyniku RevenueCat Sync.

Moduł jest niezależny od webhooków. Może być używany zarówno przez:

- RevenueCatWebhookProcessor,
- produkcyjny endpoint POST /revenuecat/sync-me.

Nie wykonuje requestów HTTP i nie zatwierdza transakcji.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from backend.effective_plan_applier import (
    EffectivePlanApplyResult,
    apply_effective_plan,
)
from backend.models import StorePurchase, User
from backend.revenuecat_sync import RevenueCatSyncResult
from backend.store_purchase_data import (
    StorePurchaseData,
    build_store_purchase_data,
    select_subscription_for_effective_plan,
)
from backend.store_purchase_repository import StorePurchaseRepository


class RevenueCatSyncPersistenceError(RuntimeError):
    """Nie udało się trwale zastosować wyniku synchronizacji RevenueCat."""


@dataclass(frozen=True)
class RevenueCatSyncPersistenceResult:
    """Końcowy wynik trwałego zastosowania synchronizacji."""

    sync_result: RevenueCatSyncResult
    store_purchase: StorePurchase | None
    purchase_data: StorePurchaseData | None
    plan_apply_result: EffectivePlanApplyResult


@dataclass
class RevenueCatSyncPersistenceService:
    """Zapisuje zakup i stosuje końcowy plan w bieżącej transakcji."""

    db: Session

    def apply(
        self,
        *,
        user: User,
        sync_result: RevenueCatSyncResult,
        environment: str | None = None,
        store: str | None = None,
        synced_at: datetime | None = None,
        source_event_id: str | None = None,
        source_event_type: str | None = None,
        source_event_at: datetime | None = None,
    ) -> RevenueCatSyncPersistenceResult:
        """Zapisuje wynik Sync Engine i aktualizuje efektywny plan użytkownika."""

        normalized_synced_at = synced_at or datetime.utcnow()

        if not isinstance(normalized_synced_at, datetime):
            raise RevenueCatSyncPersistenceError(
                "synced_at musi być znacznikiem czasu datetime"
            )

        normalized_role = str(user.role or "").strip().lower()

        if normalized_role not in {"user", "partner"}:
            raise RevenueCatSyncPersistenceError(
                (
                    "Użytkownik ma rolę nieobsługiwaną przez płatności: "
                    f"{normalized_role or '<pusta>'}"
                )
            )

        if sync_result.role != normalized_role:
            raise RevenueCatSyncPersistenceError(
                "Rola RevenueCatSyncResult nie odpowiada roli użytkownika"
            )

        normalized_app_user_id = str(
            user.revenuecat_app_user_id or ""
        ).strip()

        if not normalized_app_user_id:
            raise RevenueCatSyncPersistenceError(
                "Użytkownik nie posiada RevenueCat App User ID"
            )

        if sync_result.app_user_id != normalized_app_user_id:
            raise RevenueCatSyncPersistenceError(
                "RevenueCatSyncResult dotyczy innego App User ID"
            )

        subscription = select_subscription_for_effective_plan(
            sync_result=sync_result,
            environment=environment,
            store=store,
        )

        purchase_data = None
        store_purchase = None

        if subscription is not None:
            purchase_data = build_store_purchase_data(
                sync_result=sync_result,
                subscription=subscription,
                synced_at=normalized_synced_at,
                source_event_id=source_event_id,
                source_event_type=source_event_type,
                source_event_at=source_event_at,
            )

            store_purchase = StorePurchaseRepository(self.db).upsert(
                user_id=user.id,
                data=purchase_data,
            )

        plan_apply_result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=sync_result.effective_plan,
            purchase_data=purchase_data,
            applied_at=normalized_synced_at,
        )

        return RevenueCatSyncPersistenceResult(
            sync_result=sync_result,
            store_purchase=store_purchase,
            purchase_data=purchase_data,
            plan_apply_result=plan_apply_result,
        )
