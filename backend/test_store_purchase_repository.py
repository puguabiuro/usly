"""Testy cienkiej warstwy zapisu StorePurchase."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.models import StorePurchase, User
from backend.store_purchase_data import StorePurchaseData
from backend.store_purchase_repository import (
    StorePurchaseRepository,
    StorePurchaseRepositoryError,
)


class StorePurchaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.user = User(
            email="repository-user@example.com",
            password_hash="test",
            role="user",
            revenuecat_app_user_id="usly_usr_repository",
        )
        self.db.add(self.user)
        self.db.flush()

        self.repository = StorePurchaseRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def make_data(
        self,
        *,
        plan: str = "plus",
        status: str = "active",
        event_id: str = "event_1",
        synced_at: datetime | None = None,
    ) -> StorePurchaseData:
        timestamp = synced_at or datetime(2026, 7, 12, 16, 30)
        expires_at = timestamp + timedelta(days=30)

        return StorePurchaseData(
            revenuecat_app_user_id="usly_usr_repository",
            revenuecat_customer_id="customer_1",
            revenuecat_subscription_id="subscription_1",
            revenuecat_product_id="rc_product_1",
            revenuecat_entitlement_id="entitlement_plus",
            entitlement_lookup_key="usly_user_plus",
            role="user",
            plan=plan,
            platform="android",
            store="play_store",
            environment="sandbox",
            store_product_id="usly_user_plus:monthly",
            store_subscription_identifier="store_subscription_1",
            subscription_status=status,
            gives_access=True,
            pending_payment=False,
            current_period_ends_at=expires_at,
            ends_at=expires_at,
            plan_expires_at=expires_at,
            webhook_event_id=event_id,
            webhook_event_type="RENEWAL",
            webhook_event_at=timestamp,
            synced_at=timestamp,
            raw_subscription_json='{"id":"subscription_1"}',
        )

    def test_creates_store_purchase(self) -> None:
        data = self.make_data()

        purchase = self.repository.upsert(
            user_id=self.user.id,
            data=data,
        )

        self.assertIsNotNone(purchase.id)
        self.assertEqual(purchase.user_id, self.user.id)
        self.assertEqual(purchase.platform, "android")
        self.assertEqual(
            purchase.transaction_id,
            "store_subscription_1",
        )
        self.assertEqual(
            purchase.revenuecat_subscription_id,
            "subscription_1",
        )
        self.assertEqual(purchase.product_id, "usly_user_plus:monthly")
        self.assertEqual(purchase.verification_mode, "revenuecat")
        self.assertEqual(purchase.last_event_id, "event_1")
        self.assertEqual(
            self.db.query(StorePurchase).count(),
            1,
        )

    def test_updates_latest_store_transaction_identifier(self) -> None:
        first = self.make_data()

        renewed_values = {
            **first.__dict__,
            "store_subscription_identifier": "store_subscription_renewal_2",
            "webhook_event_id": "event_renewal_2",
            "synced_at": datetime(2026, 7, 13, 16, 30),
        }
        renewed = StorePurchaseData(**renewed_values)

        first_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=first,
        )
        renewed_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=renewed,
        )

        self.assertEqual(first_purchase.id, renewed_purchase.id)
        self.assertEqual(
            renewed_purchase.revenuecat_subscription_id,
            "subscription_1",
        )
        self.assertEqual(
            renewed_purchase.transaction_id,
            "store_subscription_renewal_2",
        )
        self.assertEqual(
            renewed_purchase.last_event_id,
            "event_renewal_2",
        )
        self.assertEqual(
            self.db.query(StorePurchase).count(),
            1,
        )

    def test_updates_existing_store_purchase(self) -> None:
        first = self.make_data()
        later_time = datetime(2026, 7, 13, 10, 0)
        second = self.make_data(
            plan="premium",
            status="renewed",
            event_id="event_2",
            synced_at=later_time,
        )

        first_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=first,
        )
        second_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=second,
        )

        self.assertEqual(first_purchase.id, second_purchase.id)
        self.assertEqual(second_purchase.plan, "premium")
        self.assertEqual(second_purchase.status, "renewed")
        self.assertEqual(second_purchase.last_event_id, "event_2")
        self.assertEqual(second_purchase.synced_at, later_time)
        self.assertEqual(
            self.db.query(StorePurchase).count(),
            1,
        )

    def test_does_not_overwrite_newer_purchase_with_older_sync(self) -> None:
        newer_time = datetime(2026, 7, 14, 12, 0)
        older_time = datetime(2026, 7, 13, 12, 0)

        newer = self.make_data(
            plan="premium",
            status="active",
            event_id="event_newer",
            synced_at=newer_time,
        )
        older = self.make_data(
            plan="plus",
            status="expired",
            event_id="event_older",
            synced_at=older_time,
        )

        first_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=newer,
        )
        second_purchase = self.repository.upsert(
            user_id=self.user.id,
            data=older,
        )

        self.assertEqual(first_purchase.id, second_purchase.id)
        self.assertEqual(second_purchase.plan, "premium")
        self.assertEqual(second_purchase.status, "active")
        self.assertEqual(second_purchase.last_event_id, "event_newer")
        self.assertEqual(second_purchase.synced_at, newer_time)
        self.assertEqual(
            self.db.query(StorePurchase).count(),
            1,
        )

    def test_rejects_purchase_owned_by_different_user(self) -> None:
        other_user = User(
            email="repository-other@example.com",
            password_hash="test",
            role="user",
            revenuecat_app_user_id="usly_usr_repository_other",
        )
        self.db.add(other_user)
        self.db.flush()

        data = self.make_data()

        self.repository.upsert(
            user_id=self.user.id,
            data=data,
        )

        with self.assertRaises(StorePurchaseRepositoryError):
            self.repository.upsert(
                user_id=other_user.id,
                data=data,
            )

    def test_rejects_invalid_user_id(self) -> None:
        with self.assertRaises(StorePurchaseRepositoryError):
            self.repository.upsert(
                user_id=0,
                data=self.make_data(),
            )


if __name__ == "__main__":
    unittest.main()
