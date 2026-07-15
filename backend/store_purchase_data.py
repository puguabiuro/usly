"""Domenowy kontrakt danych zakupu sklepowego RevenueCat.

Moduł łączy zweryfikowane dane z:

- RevenueCat Sync Engine,
- subskrypcji RevenueCat API v2,
- webhooka RevenueCat.

Moduł:

- nie korzysta z SQLAlchemy,
- nie zapisuje danych do bazy,
- nie zmienia profili ani planów użytkowników,
- nie wykonuje requestów HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.revenuecat_subscription import RevenueCatSubscription
from backend.revenuecat_sync import RevenueCatSyncResult
from backend.revenuecat_webhook import RevenueCatWebhookPayload
from backend.store_catalog import get_store_product_id_for_plan


class StorePurchaseDataError(RuntimeError):
    """Nie udało się bezpiecznie zbudować danych StorePurchase."""


@dataclass(frozen=True)
class StorePurchaseData:
    """Komplet zweryfikowanych danych do późniejszego zapisu w bazie."""

    revenuecat_app_user_id: str
    revenuecat_customer_id: str
    revenuecat_subscription_id: str
    revenuecat_product_id: str | None

    revenuecat_entitlement_id: str | None
    entitlement_lookup_key: str | None

    role: str
    plan: str

    platform: str
    store: str
    environment: str

    store_product_id: str
    store_subscription_identifier: str

    subscription_status: str
    gives_access: bool
    pending_payment: bool

    current_period_ends_at: datetime | None
    ends_at: datetime | None
    plan_expires_at: datetime | None

    webhook_event_id: str | None
    webhook_event_type: str | None
    webhook_event_at: datetime | None

    synced_at: datetime
    raw_subscription_json: str


def select_subscription_for_effective_plan(
    *,
    sync_result: RevenueCatSyncResult,
    webhook_payload: RevenueCatWebhookPayload | None = None,
    environment: str | None = None,
    store: str | None = None,
) -> RevenueCatSubscription | None:
    """Wybiera subskrypcję odpowiadającą końcowemu planowi użytkownika.

    Filtry środowiska i sklepu mogą pochodzić z webhooka albo bezpośrednio
    z produkcyjnej synchronizacji konta. Funkcja nie wymaga webhooka.
    """

    source_entitlement_id = (
        sync_result.effective_plan.source_entitlement_id
    )

    if source_entitlement_id is None:
        if sync_result.effective_plan.plan != "free":
            raise StorePurchaseDataError(
                "Płatny plan nie zawiera źródłowego entitlement_id"
            )
        return None

    normalized_environment = str(environment or "").strip().lower()
    normalized_store = str(store or "").strip().lower()

    if webhook_payload is not None:
        webhook_environment = str(
            webhook_payload.environment or ""
        ).strip().lower()
        webhook_store = str(
            webhook_payload.store or ""
        ).strip().lower()

        if (
            normalized_environment
            and webhook_environment
            and normalized_environment != webhook_environment
        ):
            raise StorePurchaseDataError(
                "Przekazane środowisko jest niespójne z webhookiem"
            )

        if (
            normalized_store
            and webhook_store
            and normalized_store != webhook_store
        ):
            raise StorePurchaseDataError(
                "Przekazany sklep jest niespójny z webhookiem"
            )

        normalized_environment = (
            normalized_environment or webhook_environment
        )
        normalized_store = normalized_store or webhook_store

    candidates: list[RevenueCatSubscription] = []

    for subscription in sync_result.subscriptions:
        if subscription.customer_id != sync_result.customer_id:
            continue

        if not subscription.gives_access:
            continue

        if (
            source_entitlement_id
            not in subscription.active_entitlement_ids
        ):
            continue

        if (
            normalized_environment
            and subscription.environment != normalized_environment
        ):
            continue

        if normalized_store and subscription.store != normalized_store:
            continue

        candidates.append(subscription)

    if not candidates:
        raise StorePurchaseDataError(
            (
                "Nie znaleziono aktywnej subskrypcji RevenueCat "
                "odpowiadającej końcowemu planowi"
            )
        )

    candidates.sort(
        key=lambda subscription: (
            subscription.current_period_ends_at
            or subscription.ends_at
            or datetime.min,
            subscription.subscription_id,
        ),
        reverse=True,
    )

    return candidates[0]


def build_store_purchase_data(
    *,
    sync_result: RevenueCatSyncResult,
    subscription: RevenueCatSubscription,
    webhook_payload: RevenueCatWebhookPayload | None = None,
    synced_at: datetime | None = None,
    source_event_id: str | None = None,
    source_event_type: str | None = None,
    source_event_at: datetime | None = None,
) -> StorePurchaseData:
    """Buduje spójny kontrakt danych późniejszego StorePurchase.

    Dane zdarzenia są opcjonalne. Webhook może je dostarczyć, ale produkcyjna
    synchronizacja konta nie musi tworzyć ani udawać webhooka.
    """

    if subscription.customer_id != sync_result.customer_id:
        raise StorePurchaseDataError(
            "Subskrypcja RevenueCat należy do innego customer_id"
        )

    normalized_source_event_id = (
        str(source_event_id).strip()
        if source_event_id is not None
        else None
    )
    normalized_source_event_type = (
        str(source_event_type).strip()
        if source_event_type is not None
        else None
    )
    normalized_source_event_at = source_event_at

    if (
        normalized_source_event_at is not None
        and not isinstance(normalized_source_event_at, datetime)
    ):
        raise StorePurchaseDataError(
            "source_event_at musi być znacznikiem czasu datetime albo null"
        )

    if webhook_payload is not None:
        webhook_app_user_id = str(
            webhook_payload.app_user_id or ""
        ).strip()

        if (
            webhook_app_user_id
            and webhook_app_user_id != sync_result.app_user_id
        ):
            raise StorePurchaseDataError(
                "Webhook RevenueCat dotyczy innego App User ID"
            )

        webhook_environment = str(
            webhook_payload.environment or ""
        ).strip().lower()

        if (
            webhook_environment
            and webhook_environment != subscription.environment
        ):
            raise StorePurchaseDataError(
                "Środowisko webhooka i subskrypcji RevenueCat jest niespójne"
            )

        webhook_store = str(
            webhook_payload.store or ""
        ).strip().lower()

        if webhook_store and webhook_store != subscription.store:
            raise StorePurchaseDataError(
                "Sklep webhooka i subskrypcji RevenueCat jest niespójny"
            )

        webhook_event_id = str(
            webhook_payload.event_id or ""
        ).strip()
        webhook_event_type = str(
            webhook_payload.event_type or ""
        ).strip()
        webhook_event_at = _milliseconds_to_datetime(
            webhook_payload.event_timestamp_ms
        )

        if (
            normalized_source_event_id
            and webhook_event_id
            and normalized_source_event_id != webhook_event_id
        ):
            raise StorePurchaseDataError(
                "source_event_id jest niespójne z webhookiem"
            )

        if (
            normalized_source_event_type
            and webhook_event_type
            and normalized_source_event_type != webhook_event_type
        ):
            raise StorePurchaseDataError(
                "source_event_type jest niespójne z webhookiem"
            )

        if (
            normalized_source_event_at is not None
            and webhook_event_at is not None
            and normalized_source_event_at != webhook_event_at
        ):
            raise StorePurchaseDataError(
                "source_event_at jest niespójne z webhookiem"
            )

        normalized_source_event_id = (
            normalized_source_event_id
            or webhook_event_id
            or None
        )
        normalized_source_event_type = (
            normalized_source_event_type
            or webhook_event_type
            or None
        )
        normalized_source_event_at = (
            normalized_source_event_at
            if normalized_source_event_at is not None
            else webhook_event_at
        )

    platform_by_store = {
        "play_store": "android",
        "app_store": "ios",
    }

    platform = platform_by_store.get(subscription.store)

    if platform is None:
        raise StorePurchaseDataError(
            (
                "Nieobsługiwany sklep subskrypcji RevenueCat: "
                f"{subscription.store!r}"
            )
        )

    normalized_synced_at = synced_at or datetime.utcnow()

    if not isinstance(normalized_synced_at, datetime):
        raise StorePurchaseDataError(
            "synced_at musi być znacznikiem czasu datetime"
        )

    effective_plan = sync_result.effective_plan

    canonical_store_product_id = get_store_product_id_for_plan(
        sync_result.role,
        effective_plan.plan,
    )

    if canonical_store_product_id is None:
        raise StorePurchaseDataError(
            (
                "Brak sklepowego product_id dla końcowego planu "
                f"{sync_result.role!r}/{effective_plan.plan!r}"
            )
        )

    if webhook_payload is not None:
        webhook_product_id = str(
            webhook_payload.product_id or ""
        ).strip()

        if (
            webhook_product_id
            and webhook_product_id != canonical_store_product_id
        ):
            raise StorePurchaseDataError(
                (
                    "Product ID webhooka nie odpowiada końcowemu "
                    "planowi wyliczonemu przez RevenueCat"
                )
            )

    plan_expires_at = (
        subscription.current_period_ends_at
        or subscription.ends_at
    )

    return StorePurchaseData(
        revenuecat_app_user_id=sync_result.app_user_id,
        revenuecat_customer_id=sync_result.customer_id,
        revenuecat_subscription_id=subscription.subscription_id,
        revenuecat_product_id=subscription.revenuecat_product_id,
        revenuecat_entitlement_id=(
            effective_plan.source_entitlement_id
        ),
        entitlement_lookup_key=(
            effective_plan.source_entitlement_lookup_key
        ),
        role=sync_result.role,
        plan=effective_plan.plan,
        platform=platform,
        store=subscription.store,
        environment=subscription.environment,
        store_product_id=canonical_store_product_id,
        store_subscription_identifier=(
            subscription.store_subscription_identifier
        ),
        subscription_status=subscription.status,
        gives_access=subscription.gives_access,
        pending_payment=subscription.pending_payment,
        current_period_ends_at=(
            subscription.current_period_ends_at
        ),
        ends_at=subscription.ends_at,
        plan_expires_at=plan_expires_at,
        webhook_event_id=normalized_source_event_id,
        webhook_event_type=normalized_source_event_type,
        webhook_event_at=normalized_source_event_at,
        synced_at=normalized_synced_at,
        raw_subscription_json=subscription.raw_payload_json,
    )


def _milliseconds_to_datetime(
    value: int | None,
) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise StorePurchaseDataError(
            "Timestamp webhooka musi zawierać milisekundy Unix albo null"
        )

    if value < 0:
        raise StorePurchaseDataError(
            "Timestamp webhooka nie może być ujemny"
        )

    try:
        return datetime.utcfromtimestamp(value / 1000)
    except (OverflowError, OSError, ValueError) as exc:
        raise StorePurchaseDataError(
            "Timestamp webhooka jest nieprawidłowy"
        ) from exc
