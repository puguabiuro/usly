"""Testy procesora webhooków RevenueCat."""

import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.models import (
    RevenueCatWebhookEvent,
    StorePurchase,
    User,
    UserProfile,
)
from backend.revenuecat_subscription import RevenueCatSubscription
from backend.revenuecat_sync import (
    EffectivePlan,
    RevenueCatSyncResult,
)
from backend.revenuecat_webhook import parse_revenuecat_webhook_payload
from backend.revenuecat_webhook_processor import (
    RevenueCatWebhookProcessingError,
    RevenueCatWebhookProcessor,
    RevenueCatWebhookUserNotFoundError,
)




class FakeRevenueCatSyncEngine:
    def __init__(self) -> None:
        self.calls = []
        self.result = object()

    def sync_customer(
        self,
        *,
        app_user_id,
        role,
        environment=None,
    ):
        self.calls.append(
            {
                "app_user_id": app_user_id,
                "role": role,
                "environment": environment,
            }
        )
        return self.result


class RevenueCatWebhookProcessorRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        User.__table__.create(bind=self.engine)
        RevenueCatWebhookEvent.__table__.create(bind=self.engine)
        self.db = self.Session()
        self.processor = RevenueCatWebhookProcessor(db=self.db)

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        self.engine.dispose()

    def make_payload(
        self,
        *,
        event_id: str = "evt-1",
        event_type: str = "TEST",
    ):
        return parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": event_id,
                    "type": event_type,
                    "app_user_id": "user-42",
                    "environment": "SANDBOX",
                }
            }
        )

    def test_finds_user_by_revenuecat_app_user_id(self) -> None:
        user = User(
            email="revenuecat-user@usly.local",
            password_hash="test",
            role="user",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_0123456789abcdef0123456789abcdef"
            ),
        )
        self.db.add(user)
        self.db.flush()

        found_user = self.processor.find_user_by_app_user_id(
            "  usly_usr_0123456789abcdef0123456789abcdef  "
        )

        self.assertEqual(found_user.id, user.id)
        self.assertEqual(found_user.email, user.email)

    def test_resolves_user_sync_role(self) -> None:
        user = User(
            email="sync-user-role@usly.local",
            password_hash="test",
            role=" USER ",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_11111111111111111111111111111111"
            ),
        )

        self.assertEqual(
            self.processor.resolve_sync_role(user),
            "user",
        )

    def test_resolves_partner_sync_role(self) -> None:
        user = User(
            email="sync-partner-role@usly.local",
            password_hash="test",
            role="PARTNER",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_22222222222222222222222222222222"
            ),
        )

        self.assertEqual(
            self.processor.resolve_sync_role(user),
            "partner",
        )

    def test_rejects_admin_sync_role(self) -> None:
        user = User(
            email="sync-admin-role@usly.local",
            password_hash="test",
            role="admin",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_33333333333333333333333333333333"
            ),
        )

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.resolve_sync_role(user)

    def test_syncs_user_from_webhook_with_trusted_identity(self) -> None:
        fake_sync_engine = FakeRevenueCatSyncEngine()
        processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=fake_sync_engine,
        )
        user = User(
            email="sync-webhook-user@usly.local",
            password_hash="test",
            role=" USER ",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_77777777777777777777777777777777"
            ),
        )
        payload = parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": "evt-sync-user",
                    "type": "RENEWAL",
                    "app_user_id": (
                        "usly_usr_77777777777777777777777777777777"
                    ),
                    "environment": "SANDBOX",
                }
            }
        )

        result = processor.sync_user_from_webhook(
            user=user,
            payload=payload,
        )

        self.assertIs(result, fake_sync_engine.result)
        self.assertEqual(
            fake_sync_engine.calls,
            [
                {
                    "app_user_id": (
                        "usly_usr_77777777777777777777777777777777"
                    ),
                    "role": "user",
                    "environment": "SANDBOX",
                }
            ],
        )

    def test_rejects_unknown_revenuecat_app_user_id(self) -> None:
        with self.assertRaises(RevenueCatWebhookUserNotFoundError):
            self.processor.find_user_by_app_user_id(
                "usly_usr_ffffffffffffffffffffffffffffffff"
            )

    def test_rejects_missing_revenuecat_app_user_id(self) -> None:
        for app_user_id in (None, "", "   "):
            with self.subTest(app_user_id=app_user_id):
                with self.assertRaises(
                    RevenueCatWebhookUserNotFoundError
                ):
                    self.processor.find_user_by_app_user_id(app_user_id)

    def test_registers_new_event(self) -> None:
        payload = self.make_payload()

        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)
        self.assertIsNotNone(event.id)
        self.assertEqual(event.event_id, "evt-1")
        self.assertEqual(event.event_type, "TEST")
        self.assertEqual(event.app_user_id, "user-42")
        self.assertEqual(event.environment, "SANDBOX")
        self.assertEqual(event.status, "received")
        self.assertEqual(event.retry_count, 0)
        self.assertEqual(event.payload_json, payload.payload_json)

    def test_returns_existing_event_for_duplicate_event_id(self) -> None:
        payload = self.make_payload()

        first_event, first_duplicate = self.processor.register_event(payload)
        second_event, second_duplicate = self.processor.register_event(payload)

        self.assertFalse(first_duplicate)
        self.assertTrue(second_duplicate)
        self.assertEqual(second_event.id, first_event.id)
        self.assertEqual(second_event.event_id, first_event.event_id)
        self.assertEqual(
            self.db.query(RevenueCatWebhookEvent).count(),
            1,
        )

    def test_session_remains_usable_after_duplicate_conflict(self) -> None:
        payload = self.make_payload()

        self.processor.register_event(payload)
        self.processor.register_event(payload)

        events = (
            self.db.query(RevenueCatWebhookEvent)
            .order_by(RevenueCatWebhookEvent.id.asc())
            .all()
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_id, "evt-1")

    def test_registers_different_event_ids_separately(self) -> None:
        first_payload = self.make_payload(event_id="evt-1")
        second_payload = self.make_payload(event_id="evt-2")

        first_event, first_duplicate = self.processor.register_event(
            first_payload
        )
        second_event, second_duplicate = self.processor.register_event(
            second_payload
        )

        self.assertFalse(first_duplicate)
        self.assertFalse(second_duplicate)
        self.assertNotEqual(first_event.id, second_event.id)
        self.assertEqual(
            self.db.query(RevenueCatWebhookEvent).count(),
            2,
        )

    def test_starts_first_processing(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        event.error_message = "stary błąd"
        before_start = datetime.utcnow()

        started_event = self.processor.start_processing(event)

        after_start = datetime.utcnow()

        self.assertEqual(started_event.status, "processing")
        self.assertIsNotNone(started_event.processing_started_at)
        self.assertGreaterEqual(
            started_event.processing_started_at,
            before_start,
        )
        self.assertLessEqual(
            started_event.processing_started_at,
            after_start,
        )
        self.assertIsNone(started_event.error_message)
        self.assertEqual(started_event.retry_count, 0)

    def test_rejects_start_processing_for_non_received_status(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.start_processing(event)

    def test_marks_processing_event_as_processed(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)
        before_processed = datetime.utcnow()

        processed_event = self.processor.mark_processed(event)

        after_processed = datetime.utcnow()

        self.assertEqual(processed_event.status, "processed")
        self.assertIsNotNone(processed_event.processed_at)
        self.assertGreaterEqual(
            processed_event.processed_at,
            before_processed,
        )
        self.assertLessEqual(
            processed_event.processed_at,
            after_processed,
        )
        self.assertEqual(processed_event.retry_count, 0)

    def test_rejects_mark_processed_for_non_processing_status(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.mark_processed(event)

    def test_marks_processing_event_as_failed(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)

        failed_event = self.processor.mark_failed(
            event,
            "  RevenueCat API timeout  ",
        )

        self.assertEqual(failed_event.status, "failed")
        self.assertEqual(
            failed_event.error_message,
            "RevenueCat API timeout",
        )
        self.assertIsNone(failed_event.processed_at)
        self.assertEqual(failed_event.retry_count, 0)

    def test_rejects_mark_failed_for_non_processing_status(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.mark_failed(event, "RevenueCat API timeout")

    def test_rejects_empty_failure_message(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.mark_failed(event, "   ")

        self.assertEqual(event.status, "processing")
        self.assertIsNone(event.error_message)

    def test_retries_failed_event(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)
        self.processor.mark_failed(event, "RevenueCat API timeout")

        before_retry = datetime.utcnow()

        retried_event = self.processor.retry_processing(event)

        after_retry = datetime.utcnow()

        self.assertEqual(retried_event.status, "processing")
        self.assertEqual(retried_event.retry_count, 1)
        self.assertIsNotNone(retried_event.last_retry_at)
        self.assertIsNotNone(retried_event.processing_started_at)
        self.assertGreaterEqual(
            retried_event.last_retry_at,
            before_retry,
        )
        self.assertLessEqual(
            retried_event.last_retry_at,
            after_retry,
        )
        self.assertEqual(
            retried_event.processing_started_at,
            retried_event.last_retry_at,
        )
        self.assertIsNone(retried_event.error_message)
        self.assertIsNone(retried_event.processed_at)

    def test_increments_retry_count_for_each_retry(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        self.processor.start_processing(event)
        self.processor.mark_failed(event, "pierwszy błąd")
        self.processor.retry_processing(event)
        self.processor.mark_failed(event, "drugi błąd")

        retried_event = self.processor.retry_processing(event)

        self.assertEqual(retried_event.status, "processing")
        self.assertEqual(retried_event.retry_count, 2)
        self.assertIsNone(retried_event.error_message)

    def test_rejects_retry_for_non_failed_status(self) -> None:
        payload = self.make_payload()
        event, duplicate = self.processor.register_event(payload)

        self.assertFalse(duplicate)

        with self.assertRaises(RevenueCatWebhookProcessingError):
            self.processor.retry_processing(event)

        self.assertEqual(event.status, "received")
        self.assertEqual(event.retry_count, 0)
        self.assertIsNone(event.last_retry_at)



class RevenueCatWebhookProcessorPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        self.db = self.Session()
        self.processor = RevenueCatWebhookProcessor(db=self.db)
        self.now = datetime(2026, 7, 12, 18, 30)

        self.user = User(
            email="persist-sync-user@usly.local",
            password_hash="test",
            role="user",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_88888888888888888888888888888888"
            ),
        )
        self.db.add(self.user)
        self.db.flush()

        self.profile = UserProfile(
            user_id=self.user.id,
            plan="free",
            plan_source="manual",
            plan_status="active",
        )
        self.db.add(self.profile)
        self.db.flush()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        self.engine.dispose()

    def make_payload(
        self,
        *,
        event_id: str,
        event_type: str,
        product_id: str | None,
    ):
        event = {
            "id": event_id,
            "type": event_type,
            "app_user_id": self.user.revenuecat_app_user_id,
            "environment": "SANDBOX",
            "store": "PLAY_STORE",
        }

        if product_id is not None:
            event["product_id"] = product_id

        return parse_revenuecat_webhook_payload({"event": event})

    def make_paid_sync_result(self) -> RevenueCatSyncResult:
        expires_at = self.now + timedelta(days=30)

        subscription = RevenueCatSubscription(
            subscription_id="subscription_user_plus",
            customer_id="customer_user_1",
            original_customer_id="customer_user_1",
            revenuecat_product_id="rc_product_user_plus",
            store_subscription_identifier="store_order_user_plus",
            environment="sandbox",
            store="play_store",
            status="active",
            gives_access=True,
            pending_payment=False,
            active_entitlement_ids=("entitlement_user_plus",),
            current_period_ends_at=expires_at,
            ends_at=expires_at,
            raw_payload_json='{"id":"subscription_user_plus"}',
        )

        effective_plan = EffectivePlan(
            role="user",
            plan="plus",
            rank=1,
            source_entitlement_id="entitlement_user_plus",
            source_entitlement_lookup_key="usly_user_plus",
        )

        return RevenueCatSyncResult(
            app_user_id=self.user.revenuecat_app_user_id,
            customer_id="customer_user_1",
            role="user",
            effective_plan=effective_plan,
            mapped_entitlements=(),
            unknown_entitlement_ids=(),
            subscriptions=(subscription,),
        )

    def make_free_sync_result(self) -> RevenueCatSyncResult:
        return RevenueCatSyncResult(
            app_user_id=self.user.revenuecat_app_user_id,
            customer_id="customer_user_1",
            role="user",
            effective_plan=EffectivePlan(
                role="user",
                plan="free",
                rank=0,
                source_entitlement_id=None,
                source_entitlement_lookup_key=None,
            ),
            mapped_entitlements=(),
            unknown_entitlement_ids=(),
            subscriptions=(),
        )

    def test_persists_paid_purchase_and_applies_user_plan(self) -> None:
        payload = self.make_payload(
            event_id="evt-paid-persist",
            event_type="INITIAL_PURCHASE",
            product_id="usly_user_plus:monthly",
        )
        sync_result = self.make_paid_sync_result()

        result = self.processor.persist_sync_result(
            user=self.user,
            payload=payload,
            sync_result=sync_result,
            synced_at=self.now,
        )

        self.assertIs(result.sync_result, sync_result)
        self.assertIsNotNone(result.store_purchase)
        self.assertTrue(result.plan_apply_result.applied)

        purchase = self.db.query(StorePurchase).one()
        self.assertEqual(purchase.user_id, self.user.id)
        self.assertEqual(
            purchase.revenuecat_subscription_id,
            "subscription_user_plus",
        )
        self.assertEqual(purchase.plan, "plus")

        self.assertEqual(self.profile.plan, "plus")
        self.assertEqual(self.profile.plan_source, "paid")
        self.assertEqual(self.profile.plan_status, "active")
        self.assertEqual(
            self.profile.plan_expires_at,
            self.now + timedelta(days=30),
        )

    def test_does_not_apply_older_free_sync_after_newer_paid_sync(self) -> None:
        newer_time = self.now + timedelta(hours=2)

        paid_payload = self.make_payload(
            event_id="evt-newer-paid",
            event_type="RENEWAL",
            product_id="usly_user_plus:monthly",
        )

        self.processor.persist_sync_result(
            user=self.user,
            payload=paid_payload,
            sync_result=self.make_paid_sync_result(),
            synced_at=newer_time,
        )

        free_payload = self.make_payload(
            event_id="evt-older-free",
            event_type="EXPIRATION",
            product_id=None,
        )

        result = self.processor.persist_sync_result(
            user=self.user,
            payload=free_payload,
            sync_result=self.make_free_sync_result(),
            synced_at=self.now,
        )

        self.assertFalse(result.plan_apply_result.applied)
        self.assertEqual(self.profile.plan, "plus")
        self.assertEqual(self.profile.plan_source, "paid")
        self.assertEqual(self.profile.plan_status, "active")
        self.assertEqual(self.db.query(StorePurchase).count(), 1)

    def test_applies_free_without_creating_store_purchase(self) -> None:
        self.profile.plan = "plus"
        self.profile.plan_source = "paid"
        self.profile.plan_status = "active"
        self.profile.plan_expires_at = self.now - timedelta(minutes=1)
        self.db.flush()

        payload = self.make_payload(
            event_id="evt-expired-persist",
            event_type="EXPIRATION",
            product_id=None,
        )
        sync_result = self.make_free_sync_result()

        result = self.processor.persist_sync_result(
            user=self.user,
            payload=payload,
            sync_result=sync_result,
            synced_at=self.now,
        )

        self.assertIsNone(result.store_purchase)
        self.assertTrue(result.plan_apply_result.applied)
        self.assertEqual(self.db.query(StorePurchase).count(), 0)
        self.assertEqual(self.profile.plan, "free")
        self.assertEqual(self.profile.plan_source, "system")
        self.assertEqual(self.profile.plan_status, "expired")
        self.assertIsNone(self.profile.plan_expires_at)


class ControlledRevenueCatSyncEngine:
    def __init__(
        self,
        *,
        result=None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = []

    def sync_customer(
        self,
        *,
        app_user_id,
        role,
        environment=None,
    ):
        self.calls.append(
            {
                "app_user_id": app_user_id,
                "role": role,
                "environment": environment,
            }
        )

        if self.error is not None:
            raise self.error

        return self.result


class RevenueCatWebhookProcessorProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        self.db = self.Session()
        self.now = datetime(2026, 7, 12, 19, 30)

        self.user = User(
            email="process-user@usly.local",
            password_hash="test",
            role="user",
            status="active",
            revenuecat_app_user_id=(
                "usly_usr_99999999999999999999999999999999"
            ),
        )
        self.db.add(self.user)
        self.db.flush()

        self.profile = UserProfile(
            user_id=self.user.id,
            plan="free",
            plan_source="manual",
            plan_status="active",
        )
        self.db.add(self.profile)
        self.db.flush()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        self.engine.dispose()

    def make_payload(
        self,
        *,
        event_id: str = "evt-process-paid",
    ):
        return parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": event_id,
                    "type": "INITIAL_PURCHASE",
                    "app_user_id": self.user.revenuecat_app_user_id,
                    "environment": "SANDBOX",
                    "store": "PLAY_STORE",
                    "product_id": "usly_user_plus:monthly",
                }
            }
        )

    def make_sync_result(self) -> RevenueCatSyncResult:
        expires_at = self.now + timedelta(days=30)

        subscription = RevenueCatSubscription(
            subscription_id="subscription_process_plus",
            customer_id="customer_process_1",
            original_customer_id="customer_process_1",
            revenuecat_product_id="rc_product_process_plus",
            store_subscription_identifier="store_process_plus",
            environment="sandbox",
            store="play_store",
            status="active",
            gives_access=True,
            pending_payment=False,
            active_entitlement_ids=("entitlement_process_plus",),
            current_period_ends_at=expires_at,
            ends_at=expires_at,
            raw_payload_json='{"id":"subscription_process_plus"}',
        )

        return RevenueCatSyncResult(
            app_user_id=self.user.revenuecat_app_user_id,
            customer_id="customer_process_1",
            role="user",
            effective_plan=EffectivePlan(
                role="user",
                plan="plus",
                rank=1,
                source_entitlement_id="entitlement_process_plus",
                source_entitlement_lookup_key="usly_user_plus",
            ),
            mapped_entitlements=(),
            unknown_entitlement_ids=(),
            subscriptions=(subscription,),
        )

    def test_processes_paid_webhook_end_to_end(self) -> None:
        sync_result = self.make_sync_result()
        sync_engine = ControlledRevenueCatSyncEngine(
            result=sync_result,
        )
        processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=sync_engine,
        )

        result = processor.process(self.make_payload())

        self.assertEqual(result.status, "processed")
        self.assertFalse(result.duplicate)
        self.assertEqual(result.effective_plan, "plus")
        self.assertEqual(result.role, "user")
        self.assertEqual(
            result.revenuecat_customer_id,
            "customer_process_1",
        )

        event = self.db.query(RevenueCatWebhookEvent).one()
        self.assertEqual(event.status, "processed")
        self.assertIsNotNone(event.processing_started_at)
        self.assertIsNotNone(event.processed_at)
        self.assertIsNone(event.error_message)

        self.assertEqual(self.db.query(StorePurchase).count(), 1)
        self.assertEqual(self.profile.plan, "plus")
        self.assertEqual(self.profile.plan_source, "paid")
        self.assertEqual(self.profile.plan_status, "active")

    def test_returns_processed_duplicate_without_second_purchase(self) -> None:
        sync_engine = ControlledRevenueCatSyncEngine(
            result=self.make_sync_result(),
        )
        processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=sync_engine,
        )
        payload = self.make_payload(
            event_id="evt-process-duplicate",
        )

        first_result = processor.process(payload)
        second_result = processor.process(payload)

        self.assertEqual(first_result.status, "processed")
        self.assertEqual(second_result.status, "processed")
        self.assertTrue(second_result.duplicate)
        self.assertEqual(self.db.query(StorePurchase).count(), 1)
        self.assertEqual(
            self.db.query(RevenueCatWebhookEvent).count(),
            1,
        )
        self.assertEqual(len(sync_engine.calls), 1)

    def test_failure_does_not_leave_partial_store_purchase(self) -> None:
        self.db.delete(self.profile)
        self.db.flush()

        processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=ControlledRevenueCatSyncEngine(
                result=self.make_sync_result(),
            ),
        )

        result = processor.process(
            self.make_payload(event_id="evt-process-partial-failure")
        )

        self.assertEqual(result.status, "failed")

        event = self.db.query(RevenueCatWebhookEvent).one()
        self.assertEqual(event.status, "failed")
        self.assertIn(
            "EffectivePlanApplierError",
            event.error_message,
        )

        self.assertEqual(
            self.db.query(StorePurchase).count(),
            0,
        )

    def test_marks_webhook_failed_when_sync_raises(self) -> None:
        sync_engine = ControlledRevenueCatSyncEngine(
            error=RuntimeError("RevenueCat unavailable"),
        )
        processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=sync_engine,
        )

        result = processor.process(
            self.make_payload(event_id="evt-process-failed")
        )

        self.assertEqual(result.status, "failed")
        self.assertFalse(result.duplicate)

        event = self.db.query(RevenueCatWebhookEvent).one()
        self.assertEqual(event.status, "failed")
        self.assertIn("RuntimeError", event.error_message)
        self.assertIn("RevenueCat unavailable", event.error_message)
        self.assertEqual(self.db.query(StorePurchase).count(), 0)
        self.assertEqual(self.profile.plan, "free")

    def test_retries_failed_webhook_and_processes_it(self) -> None:
        payload = self.make_payload(
            event_id="evt-process-retry",
        )

        failing_engine = ControlledRevenueCatSyncEngine(
            error=RuntimeError("temporary failure"),
        )
        failing_processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=failing_engine,
        )

        first_result = failing_processor.process(payload)
        self.assertEqual(first_result.status, "failed")

        successful_engine = ControlledRevenueCatSyncEngine(
            result=self.make_sync_result(),
        )
        successful_processor = RevenueCatWebhookProcessor(
            db=self.db,
            sync_engine=successful_engine,
        )

        second_result = successful_processor.process(payload)

        self.assertEqual(second_result.status, "processed")
        self.assertTrue(second_result.duplicate)

        event = self.db.query(RevenueCatWebhookEvent).one()
        self.assertEqual(event.status, "processed")
        self.assertEqual(event.retry_count, 1)
        self.assertIsNotNone(event.last_retry_at)
        self.assertIsNone(event.error_message)

        self.assertEqual(self.db.query(StorePurchase).count(), 1)
        self.assertEqual(self.profile.plan, "plus")
        self.assertEqual(len(successful_engine.calls), 1)

if __name__ == "__main__":
    unittest.main()
