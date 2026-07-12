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

from backend.models import RevenueCatWebhookEvent, User
from backend.revenuecat_sync import (
    RevenueCatSyncEngine,
    RevenueCatSyncResult,
    create_revenuecat_sync_engine,
)
from backend.revenuecat_webhook import RevenueCatWebhookPayload


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
        """Przetwarza jeden zwalidowany webhook RevenueCat."""

        raise NotImplementedError(
            "Procesor webhooka RevenueCat nie został jeszcze zaimplementowany"
        )
