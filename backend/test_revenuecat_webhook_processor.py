"""Testy procesora webhooków RevenueCat."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import RevenueCatWebhookEvent, User
from backend.revenuecat_webhook import parse_revenuecat_webhook_payload
from backend.revenuecat_webhook_processor import (
    RevenueCatWebhookProcessingError,
    RevenueCatWebhookProcessor,
    RevenueCatWebhookUserNotFoundError,
)


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


if __name__ == "__main__":
    unittest.main()
