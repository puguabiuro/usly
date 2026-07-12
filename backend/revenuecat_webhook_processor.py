"""Procesor webhooków RevenueCat.

Moduł będzie odpowiadać za:

- trwałą rejestrację zdarzenia webhookowego,
- idempotentną obsługę duplikatów,
- kontrolowane przejścia statusów,
- uruchomienie RevenueCat Sync Engine,
- zapis wyniku synchronizacji,
- aktualizację końcowego planu użytkownika.

Na tym etapie zawiera wyłącznie kontrakt procesora i wynik przetwarzania.
Nie jest jeszcze podłączony do main.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.effective_plan_applier import (
    EffectivePlanApplyResult,
    apply_effective_plan,
)
from backend.models import RevenueCatWebhookEvent, StorePurchase, User
from backend.revenuecat_sync import (
    RevenueCatSyncEngine,
    RevenueCatSyncResult,
    create_revenuecat_sync_engine,
)
from backend.revenuecat_webhook import RevenueCatWebhookPayload
from backend.store_purchase_data import (
    build_store_purchase_data,
    select_subscription_for_effective_plan,
)
from backend.store_purchase_repository import StorePurchaseRepository


class RevenueCatWebhookProcessorError(RuntimeError):
    """Bazowy błąd procesora webhooków RevenueCat."""


class RevenueCatWebhookProcessingError(RevenueCatWebhookProcessorError):
    """Webhook został zarejestrowany, ale jego przetwarzanie nie powiodło się."""


class RevenueCatWebhookUserNotFoundError(RevenueCatWebhookProcessorError):
    """Nie znaleziono konta USLY odpowiadającego App User ID."""


@dataclass(frozen=True)
class RevenueCatWebhookProcessResult:
    """Końcowy wynik obsługi jednego webhooka RevenueCat."""

    event_id: str
    status: str
    duplicate: bool
    webhook_event_db_id: int | None
    app_user_id: str | None
    revenuecat_customer_id: str | None
    role: str | None
    effective_plan: str | None


@dataclass(frozen=True)
class RevenueCatWebhookPersistenceResult:
    """Wynik trwałego zastosowania synchronizacji RevenueCat."""

    sync_result: RevenueCatSyncResult
    store_purchase: StorePurchase | None
    plan_apply_result: EffectivePlanApplyResult


@dataclass
class RevenueCatWebhookProcessor:
    """Orkiestruje trwałe i idempotentne przetwarzanie webhooka."""

    db: Session
    sync_engine: RevenueCatSyncEngine = field(
        default_factory=create_revenuecat_sync_engine
    )

    def find_user_by_app_user_id(
        self,
        app_user_id: str | None,
    ) -> User:
        """Odnajduje konto USLY po stałym identyfikatorze RevenueCat."""

        normalized_app_user_id = str(app_user_id or "").strip()

        if not normalized_app_user_id:
            raise RevenueCatWebhookUserNotFoundError(
                "Webhook RevenueCat nie zawiera App User ID"
            )

        user = (
            self.db.query(User)
            .filter(
                User.revenuecat_app_user_id == normalized_app_user_id
            )
            .one_or_none()
        )

        if user is None:
            raise RevenueCatWebhookUserNotFoundError(
                (
                    "Nie znaleziono użytkownika USLY dla RevenueCat "
                    f"App User ID {normalized_app_user_id!r}"
                )
            )

        return user

    def resolve_sync_role(
        self,
        user: User,
    ) -> str:
        """Zwraca rolę obsługiwaną przez subskrypcje sklepowe."""

        normalized_role = str(user.role or "").strip().lower()

        if normalized_role not in {"user", "partner"}:
            raise RevenueCatWebhookProcessingError(
                (
                    "Użytkownik RevenueCat ma rolę nieobsługiwaną "
                    f"przez subskrypcje sklepowe: {normalized_role or '<pusta>'}"
                )
            )

        return normalized_role

    def sync_user_from_webhook(
        self,
        *,
        user: User,
        payload: RevenueCatWebhookPayload,
    ) -> RevenueCatSyncResult:
        """Uruchamia RevenueCat Sync Engine dla odnalezionego konta USLY."""

        role = self.resolve_sync_role(user)

        return self.sync_engine.sync_customer(
            app_user_id=user.revenuecat_app_user_id,
            role=role,
            environment=payload.environment,
        )

    def persist_sync_result(
        self,
        *,
        user: User,
        payload: RevenueCatWebhookPayload,
        sync_result: RevenueCatSyncResult,
        synced_at: datetime,
    ) -> RevenueCatWebhookPersistenceResult:
        """Zapisuje zakup i stosuje końcowy plan w bieżącej transakcji."""

        if not isinstance(synced_at, datetime):
            raise RevenueCatWebhookProcessingError(
                "synced_at musi być znacznikiem czasu datetime"
            )

        role = self.resolve_sync_role(user)

        if sync_result.role != role:
            raise RevenueCatWebhookProcessingError(
                "Rola RevenueCatSyncResult nie odpowiada roli użytkownika"
            )

        store_purchase = None
        purchase_data = None

        subscription = select_subscription_for_effective_plan(
            sync_result=sync_result,
            webhook_payload=payload,
        )

        if subscription is not None:
            purchase_data = build_store_purchase_data(
                sync_result=sync_result,
                subscription=subscription,
                webhook_payload=payload,
                synced_at=synced_at,
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
            applied_at=synced_at,
        )

        return RevenueCatWebhookPersistenceResult(
            sync_result=sync_result,
            store_purchase=store_purchase,
            plan_apply_result=plan_apply_result,
        )

    def register_event(
        self,
        payload: RevenueCatWebhookPayload,
    ) -> tuple[RevenueCatWebhookEvent, bool]:
        """Rejestruje webhook albo zwraca istniejący duplikat.

        Zwracana wartość bool oznacza, czy zdarzenie było już wcześniej
        zarejestrowane. Metoda wykonuje flush, ale nie zatwierdza transakcji.
        """

        webhook_event = RevenueCatWebhookEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            app_user_id=payload.app_user_id,
            environment=payload.environment,
            status="received",
            payload_json=payload.payload_json,
            retry_count=0,
        )

        try:
            with self.db.begin_nested():
                self.db.add(webhook_event)
                self.db.flush()
        except IntegrityError as exc:
            existing_event = (
                self.db.query(RevenueCatWebhookEvent)
                .filter(
                    RevenueCatWebhookEvent.event_id == payload.event_id
                )
                .one_or_none()
            )

            if existing_event is None:
                raise RevenueCatWebhookProcessingError(
                    "Nie udało się odczytać zdublowanego zdarzenia webhooka"
                ) from exc

            return existing_event, True

        return webhook_event, False

    def start_processing(
        self,
        webhook_event: RevenueCatWebhookEvent,
    ) -> RevenueCatWebhookEvent:
        """Rozpoczyna pierwsze przetwarzanie zarejestrowanego webhooka."""

        if webhook_event.status != "received":
            raise RevenueCatWebhookProcessingError(
                (
                    "Nie można rozpocząć pierwszego przetwarzania webhooka "
                    f"ze statusem {webhook_event.status!r}"
                )
            )

        webhook_event.status = "processing"
        webhook_event.processing_started_at = datetime.utcnow()
        webhook_event.error_message = None

        self.db.flush()

        return webhook_event

    def mark_processed(
        self,
        webhook_event: RevenueCatWebhookEvent,
    ) -> RevenueCatWebhookEvent:
        """Kończy poprawne przetwarzanie webhooka."""

        if webhook_event.status != "processing":
            raise RevenueCatWebhookProcessingError(
                (
                    "Nie można zakończyć przetwarzania webhooka "
                    f"ze statusem {webhook_event.status!r}"
                )
            )

        webhook_event.status = "processed"
        webhook_event.processed_at = datetime.utcnow()

        self.db.flush()

        return webhook_event

    def mark_failed(
        self,
        webhook_event: RevenueCatWebhookEvent,
        error_message: str,
    ) -> RevenueCatWebhookEvent:
        """Kończy nieudane przetwarzanie webhooka."""

        if webhook_event.status != "processing":
            raise RevenueCatWebhookProcessingError(
                (
                    "Nie można oznaczyć przetwarzania webhooka jako błędne "
                    f"ze statusem {webhook_event.status!r}"
                )
            )

        normalized_error_message = error_message.strip()

        if not normalized_error_message:
            raise RevenueCatWebhookProcessingError(
                "Komunikat błędu webhooka nie może być pusty"
            )

        webhook_event.status = "failed"
        webhook_event.error_message = normalized_error_message
        webhook_event.processed_at = None

        self.db.flush()

        return webhook_event

    def retry_processing(
        self,
        webhook_event: RevenueCatWebhookEvent,
    ) -> RevenueCatWebhookEvent:
        """Rozpoczyna kontrolowane ponowienie nieudanego webhooka."""

        if webhook_event.status != "failed":
            raise RevenueCatWebhookProcessingError(
                (
                    "Nie można ponowić przetwarzania webhooka "
                    f"ze statusem {webhook_event.status!r}"
                )
            )

        retry_started_at = datetime.utcnow()

        webhook_event.status = "processing"
        webhook_event.retry_count += 1
        webhook_event.last_retry_at = retry_started_at
        webhook_event.processing_started_at = retry_started_at
        webhook_event.processed_at = None
        webhook_event.error_message = None

        self.db.flush()

        return webhook_event

    def process(
        self,
        payload: RevenueCatWebhookPayload,
    ) -> RevenueCatWebhookProcessResult:
        """Przetwarza jeden zwalidowany webhook RevenueCat.

        Metoda wykonuje flush, ale nie wykonuje commit ani rollback.
        Warstwa wyżej kontroluje ostateczne zatwierdzenie transakcji.
        """

        webhook_event, duplicate = self.register_event(payload)

        if duplicate and webhook_event.status in {
            "processed",
            "processing",
        }:
            return RevenueCatWebhookProcessResult(
                event_id=webhook_event.event_id,
                status=webhook_event.status,
                duplicate=True,
                webhook_event_db_id=webhook_event.id,
                app_user_id=webhook_event.app_user_id,
                revenuecat_customer_id=None,
                role=None,
                effective_plan=None,
            )

        if webhook_event.status == "failed":
            self.retry_processing(webhook_event)
        elif webhook_event.status == "received":
            self.start_processing(webhook_event)
        else:
            raise RevenueCatWebhookProcessingError(
                (
                    "Webhook ma nieobsługiwany status przed "
                    f"przetwarzaniem: {webhook_event.status!r}"
                )
            )

        user = None
        sync_result = None

        try:
            user = self.find_user_by_app_user_id(payload.app_user_id)

            sync_result = self.sync_user_from_webhook(
                user=user,
                payload=payload,
            )

            synced_at = datetime.utcnow()

            with self.db.begin_nested():
                self.persist_sync_result(
                    user=user,
                    payload=payload,
                    sync_result=sync_result,
                    synced_at=synced_at,
                )

                self.mark_processed(webhook_event)

            return RevenueCatWebhookProcessResult(
                event_id=webhook_event.event_id,
                status=webhook_event.status,
                duplicate=duplicate,
                webhook_event_db_id=webhook_event.id,
                app_user_id=user.revenuecat_app_user_id,
                revenuecat_customer_id=sync_result.customer_id,
                role=sync_result.role,
                effective_plan=sync_result.effective_plan.plan,
            )

        except Exception as exc:
            error_message = (
                f"{type(exc).__name__}: {str(exc).strip() or 'unknown error'}"
            )

            if webhook_event.status == "processing":
                self.mark_failed(
                    webhook_event,
                    error_message,
                )

            return RevenueCatWebhookProcessResult(
                event_id=webhook_event.event_id,
                status=webhook_event.status,
                duplicate=duplicate,
                webhook_event_db_id=webhook_event.id,
                app_user_id=(
                    user.revenuecat_app_user_id
                    if user is not None
                    else payload.app_user_id
                ),
                revenuecat_customer_id=(
                    sync_result.customer_id
                    if sync_result is not None
                    else None
                ),
                role=(
                    sync_result.role
                    if sync_result is not None
                    else None
                ),
                effective_plan=(
                    sync_result.effective_plan.plan
                    if sync_result is not None
                    else None
                ),
            )
