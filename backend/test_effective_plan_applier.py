"""Testy cienkiej warstwy nakładania końcowego planu na profil."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.effective_plan_applier import (
    EffectivePlanApplierError,
    apply_effective_plan,
)
from backend.models import PartnerProfile, User, UserProfile
from backend.revenuecat_sync import EffectivePlan
from backend.store_purchase_data import StorePurchaseData


class EffectivePlanApplierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.now = datetime(2026, 7, 12, 17, 30)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def create_user_with_profile(
        self,
        *,
        role: str,
        plan: str = "free",
        plan_source: str | None = None,
        plan_status: str | None = None,
        plan_expires_at: datetime | None = None,
    ):
        user = User(
            email=f"{role}-{id(self)}@example.com",
            password_hash="test",
            role=role,
            revenuecat_app_user_id=f"usly_usr_{role}_{id(self)}",
        )
        self.db.add(user)
        self.db.flush()

        profile_class = (
            PartnerProfile
            if role == "partner"
            else UserProfile
        )

        profile = profile_class(
            user_id=user.id,
            plan=plan,
            plan_source=plan_source,
            plan_status=plan_status,
            plan_expires_at=plan_expires_at,
        )
        self.db.add(profile)
        self.db.flush()

        return user, profile

    def make_effective_plan(
        self,
        *,
        role: str,
        plan: str,
    ) -> EffectivePlan:
        ranks = {
            "user": {
                "free": 0,
                "plus": 1,
                "premium": 2,
                "vip": 3,
            },
            "partner": {
                "free": 0,
                "pro": 1,
                "premium": 2,
                "enterprise": 3,
            },
        }

        if plan == "free":
            entitlement_id = None
            lookup_key = None
        else:
            entitlement_id = f"entitlement_{role}_{plan}"
            lookup_key = f"usly_{role}_{plan}"

        return EffectivePlan(
            role=role,
            plan=plan,
            rank=ranks[role][plan],
            source_entitlement_id=entitlement_id,
            source_entitlement_lookup_key=lookup_key,
        )

    def make_purchase_data(
        self,
        *,
        role: str,
        plan: str,
        gives_access: bool = True,
    ) -> StorePurchaseData:
        expires_at = self.now + timedelta(days=30)
        product_id = f"usly_{role}_{plan}:monthly"

        return StorePurchaseData(
            revenuecat_app_user_id=f"usly_usr_{role}",
            revenuecat_customer_id=f"customer_{role}",
            revenuecat_subscription_id=f"subscription_{role}_{plan}",
            revenuecat_product_id=f"rc_product_{role}_{plan}",
            revenuecat_entitlement_id=f"entitlement_{role}_{plan}",
            entitlement_lookup_key=f"usly_{role}_{plan}",
            role=role,
            plan=plan,
            platform="android",
            store="play_store",
            environment="sandbox",
            store_product_id=product_id,
            store_subscription_identifier=f"store_{role}_{plan}",
            subscription_status="active",
            gives_access=gives_access,
            pending_payment=False,
            current_period_ends_at=expires_at,
            ends_at=expires_at,
            plan_expires_at=expires_at,
            webhook_event_id=f"event_{role}_{plan}",
            webhook_event_type="INITIAL_PURCHASE",
            webhook_event_at=self.now,
            synced_at=self.now,
            raw_subscription_json="{}",
        )

    def test_applies_paid_user_plan(self) -> None:
        user, profile = self.create_user_with_profile(role="user")
        effective_plan = self.make_effective_plan(
            role="user",
            plan="plus",
        )
        purchase_data = self.make_purchase_data(
            role="user",
            plan="plus",
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=effective_plan,
            purchase_data=purchase_data,
            applied_at=self.now,
        )

        self.assertTrue(result.applied)
        self.assertFalse(result.protected_existing_plan)
        self.assertEqual(profile.plan, "plus")
        self.assertEqual(profile.plan_source, "paid")
        self.assertEqual(profile.plan_status, "active")
        self.assertEqual(
            profile.plan_expires_at,
            purchase_data.plan_expires_at,
        )
        self.assertEqual(profile.plan_updated_at, self.now)
        self.assertEqual(profile.updated_at, self.now)

    def test_applies_paid_partner_plan(self) -> None:
        user, profile = self.create_user_with_profile(role="partner")
        effective_plan = self.make_effective_plan(
            role="partner",
            plan="pro",
        )
        purchase_data = self.make_purchase_data(
            role="partner",
            plan="pro",
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=effective_plan,
            purchase_data=purchase_data,
            applied_at=self.now,
        )

        self.assertTrue(result.applied)
        self.assertEqual(profile.plan, "pro")
        self.assertEqual(profile.plan_source, "paid")
        self.assertEqual(profile.plan_status, "active")

    def test_applies_free_after_lost_store_access(self) -> None:
        user, profile = self.create_user_with_profile(
            role="user",
            plan="plus",
            plan_source="paid",
            plan_status="active",
            plan_expires_at=self.now - timedelta(minutes=1),
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=self.make_effective_plan(
                role="user",
                plan="free",
            ),
            purchase_data=None,
            applied_at=self.now,
        )

        self.assertTrue(result.applied)
        self.assertEqual(profile.plan, "free")
        self.assertEqual(profile.plan_source, "system")
        self.assertEqual(profile.plan_status, "expired")
        self.assertIsNone(profile.plan_expires_at)

    def test_preserves_active_ambassador_plan_of_equal_or_higher_rank(self) -> None:
        user, profile = self.create_user_with_profile(
            role="user",
            plan="vip",
            plan_source="ambassador",
            plan_status="active",
            plan_expires_at=self.now + timedelta(days=20),
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=self.make_effective_plan(
                role="user",
                plan="plus",
            ),
            purchase_data=self.make_purchase_data(
                role="user",
                plan="plus",
            ),
            applied_at=self.now,
        )

        self.assertFalse(result.applied)
        self.assertTrue(result.protected_existing_plan)
        self.assertEqual(profile.plan, "vip")
        self.assertEqual(profile.plan_source, "ambassador")

    def test_applies_higher_store_plan_over_lower_ambassador_plan(self) -> None:
        user, profile = self.create_user_with_profile(
            role="user",
            plan="plus",
            plan_source="ambassador",
            plan_status="active",
            plan_expires_at=self.now + timedelta(days=20),
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=self.make_effective_plan(
                role="user",
                plan="vip",
            ),
            purchase_data=self.make_purchase_data(
                role="user",
                plan="vip",
            ),
            applied_at=self.now,
        )

        self.assertTrue(result.applied)
        self.assertEqual(profile.plan, "vip")
        self.assertEqual(profile.plan_source, "paid")

    def test_preserves_active_manual_user_plan_of_equal_or_higher_rank(self) -> None:
        user, profile = self.create_user_with_profile(
            role="user",
            plan="vip",
            plan_source="manual",
            plan_status="active",
            plan_expires_at=self.now + timedelta(days=20),
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=self.make_effective_plan(
                role="user",
                plan="plus",
            ),
            purchase_data=self.make_purchase_data(
                role="user",
                plan="plus",
            ),
            applied_at=self.now,
        )

        self.assertFalse(result.applied)
        self.assertTrue(result.protected_existing_plan)
        self.assertEqual(profile.plan, "vip")
        self.assertEqual(profile.plan_source, "manual")

    def test_preserves_active_partner_enterprise(self) -> None:
        user, profile = self.create_user_with_profile(
            role="partner",
            plan="enterprise",
            plan_source="manual",
            plan_status="active",
            plan_expires_at=None,
        )

        result = apply_effective_plan(
            db=self.db,
            user=user,
            effective_plan=self.make_effective_plan(
                role="partner",
                plan="premium",
            ),
            purchase_data=self.make_purchase_data(
                role="partner",
                plan="premium",
            ),
            applied_at=self.now,
        )

        self.assertFalse(result.applied)
        self.assertTrue(result.protected_existing_plan)
        self.assertEqual(profile.plan, "enterprise")

    def test_rejects_paid_plan_without_purchase_data(self) -> None:
        user, _ = self.create_user_with_profile(role="user")

        with self.assertRaises(EffectivePlanApplierError):
            apply_effective_plan(
                db=self.db,
                user=user,
                effective_plan=self.make_effective_plan(
                    role="user",
                    plan="plus",
                ),
                purchase_data=None,
                applied_at=self.now,
            )

    def test_rejects_purchase_without_access(self) -> None:
        user, _ = self.create_user_with_profile(role="user")

        with self.assertRaises(EffectivePlanApplierError):
            apply_effective_plan(
                db=self.db,
                user=user,
                effective_plan=self.make_effective_plan(
                    role="user",
                    plan="plus",
                ),
                purchase_data=self.make_purchase_data(
                    role="user",
                    plan="plus",
                    gives_access=False,
                ),
                applied_at=self.now,
            )

    def test_rejects_role_mismatch(self) -> None:
        user, _ = self.create_user_with_profile(role="user")

        with self.assertRaises(EffectivePlanApplierError):
            apply_effective_plan(
                db=self.db,
                user=user,
                effective_plan=self.make_effective_plan(
                    role="partner",
                    plan="pro",
                ),
                purchase_data=self.make_purchase_data(
                    role="partner",
                    plan="pro",
                ),
                applied_at=self.now,
            )


if __name__ == "__main__":
    unittest.main()
