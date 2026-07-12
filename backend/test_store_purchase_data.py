"""Testy domenowego kontraktu StorePurchaseData."""

import unittest
from datetime import datetime

from backend.revenuecat_subscription import RevenueCatSubscription
from backend.revenuecat_sync import (
    EffectivePlan,
    RevenueCatSyncResult,
)
from backend.revenuecat_webhook import (
    parse_revenuecat_webhook_payload,
)
from backend.store_purchase_data import (
    StorePurchaseDataError,
    build_store_purchase_data,
    select_subscription_for_effective_plan,
)


def make_subscription(
    *,
    customer_id="customer_123",
    store="play_store",
    environment="production",
    gives_access=True,
):
    return RevenueCatSubscription(
        subscription_id="subscription_123",
        customer_id=customer_id,
        original_customer_id="customer_original",
        revenuecat_product_id="product_internal",
        store_subscription_identifier=(
            "GPA.1234-5678-9012-34567"
        ),
        environment=environment,
        store=store,
        status="active" if gives_access else "expired",
        gives_access=gives_access,
        pending_payment=False,
        active_entitlement_ids=("entitlement_internal",),
        current_period_ends_at=datetime(2026, 8, 20, 12, 0),
        ends_at=datetime(2026, 8, 20, 12, 0),
        raw_payload_json='{"id":"subscription_123"}',
    )


def make_sync_result(
    *,
    app_user_id="usly_usr_123",
    customer_id="customer_123",
    role="user",
    plan="premium",
):
    return RevenueCatSyncResult(
        app_user_id=app_user_id,
        customer_id=customer_id,
        role=role,
        effective_plan=EffectivePlan(
            role=role,
            plan=plan,
            rank=2,
            source_entitlement_id="entitlement_internal",
            source_entitlement_lookup_key=(
                "usly_user_premium"
            ),
        ),
        mapped_entitlements=(),
        unknown_entitlement_ids=(),
        subscriptions=(),
    )


def make_webhook(
    *,
    app_user_id="usly_usr_123",
    environment="PRODUCTION",
    store="PLAY_STORE",
):
    return parse_revenuecat_webhook_payload(
        {
            "event": {
                "id": "event_123",
                "type": "RENEWAL",
                "app_user_id": app_user_id,
                "environment": environment,
                "store": store,
                "product_id": "usly_user_premium:monthly",
                "event_timestamp_ms": 1780315200000,
            }
        }
    )


class StorePurchaseDataTests(unittest.TestCase):
    def test_selects_subscription_for_effective_plan(self):
        matching = make_subscription()
        unrelated = RevenueCatSubscription(
            subscription_id="subscription_unrelated",
            customer_id="customer_123",
            original_customer_id="customer_original",
            revenuecat_product_id="product_unrelated",
            store_subscription_identifier="GPA.UNRELATED",
            environment="production",
            store="play_store",
            status="active",
            gives_access=True,
            pending_payment=False,
            active_entitlement_ids=("entitlement_other",),
            current_period_ends_at=datetime(2026, 9, 20, 12, 0),
            ends_at=datetime(2026, 9, 20, 12, 0),
            raw_payload_json='{"id":"subscription_unrelated"}',
        )
        sync_result = make_sync_result()
        sync_result = RevenueCatSyncResult(
            app_user_id=sync_result.app_user_id,
            customer_id=sync_result.customer_id,
            role=sync_result.role,
            effective_plan=sync_result.effective_plan,
            mapped_entitlements=sync_result.mapped_entitlements,
            unknown_entitlement_ids=(
                sync_result.unknown_entitlement_ids
            ),
            subscriptions=(unrelated, matching),
        )

        selected = select_subscription_for_effective_plan(
            sync_result=sync_result,
            webhook_payload=make_webhook(),
        )

        self.assertIs(selected, matching)

    def test_selects_latest_matching_subscription(self):
        older = make_subscription()
        newer = RevenueCatSubscription(
            subscription_id="subscription_newer",
            customer_id="customer_123",
            original_customer_id="customer_original",
            revenuecat_product_id="product_newer",
            store_subscription_identifier="GPA.NEWER",
            environment="production",
            store="play_store",
            status="active",
            gives_access=True,
            pending_payment=False,
            active_entitlement_ids=("entitlement_internal",),
            current_period_ends_at=datetime(2026, 9, 20, 12, 0),
            ends_at=datetime(2026, 9, 20, 12, 0),
            raw_payload_json='{"id":"subscription_newer"}',
        )
        base = make_sync_result()
        sync_result = RevenueCatSyncResult(
            app_user_id=base.app_user_id,
            customer_id=base.customer_id,
            role=base.role,
            effective_plan=base.effective_plan,
            mapped_entitlements=base.mapped_entitlements,
            unknown_entitlement_ids=base.unknown_entitlement_ids,
            subscriptions=(older, newer),
        )

        selected = select_subscription_for_effective_plan(
            sync_result=sync_result,
            webhook_payload=make_webhook(),
        )

        self.assertIs(selected, newer)

    def test_returns_none_for_free_effective_plan(self):
        sync_result = make_sync_result(plan="free")
        sync_result = RevenueCatSyncResult(
            app_user_id=sync_result.app_user_id,
            customer_id=sync_result.customer_id,
            role=sync_result.role,
            effective_plan=EffectivePlan(
                role="user",
                plan="free",
                rank=0,
            ),
            mapped_entitlements=(),
            unknown_entitlement_ids=(),
            subscriptions=(),
        )

        selected = select_subscription_for_effective_plan(
            sync_result=sync_result,
            webhook_payload=make_webhook(),
        )

        self.assertIsNone(selected)

    def test_rejects_missing_matching_subscription(self):
        base = make_sync_result()
        sync_result = RevenueCatSyncResult(
            app_user_id=base.app_user_id,
            customer_id=base.customer_id,
            role=base.role,
            effective_plan=base.effective_plan,
            mapped_entitlements=base.mapped_entitlements,
            unknown_entitlement_ids=base.unknown_entitlement_ids,
            subscriptions=(
                make_subscription(gives_access=False),
            ),
        )

        with self.assertRaises(StorePurchaseDataError):
            select_subscription_for_effective_plan(
                sync_result=sync_result,
                webhook_payload=make_webhook(),
            )

    def test_builds_complete_android_purchase_data(self):
        synced_at = datetime(2026, 7, 12, 14, 30)

        result = build_store_purchase_data(
            sync_result=make_sync_result(),
            subscription=make_subscription(),
            webhook_payload=make_webhook(),
            synced_at=synced_at,
        )

        self.assertEqual(result.platform, "android")
        self.assertEqual(result.store, "play_store")
        self.assertEqual(result.environment, "production")
        self.assertEqual(result.role, "user")
        self.assertEqual(result.plan, "premium")
        self.assertEqual(
            result.store_product_id,
            "usly_user_premium:monthly",
        )
        self.assertEqual(
            result.revenuecat_product_id,
            "product_internal",
        )
        self.assertEqual(
            result.revenuecat_subscription_id,
            "subscription_123",
        )
        self.assertEqual(
            result.entitlement_lookup_key,
            "usly_user_premium",
        )
        self.assertTrue(result.gives_access)
        self.assertEqual(result.synced_at, synced_at)
        self.assertIsNotNone(result.webhook_event_at)

    def test_uses_catalog_product_id_when_webhook_omits_it(self):
        webhook = parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": "event-no-product",
                    "type": "RENEWAL",
                    "app_user_id": "usly_usr_123",
                    "environment": "PRODUCTION",
                    "store": "PLAY_STORE",
                    "event_timestamp_ms": 1780315200000,
                }
            }
        )

        result = build_store_purchase_data(
            sync_result=make_sync_result(),
            subscription=make_subscription(),
            webhook_payload=webhook,
        )

        self.assertEqual(
            result.store_product_id,
            "usly_user_premium:monthly",
        )

    def test_rejects_webhook_product_inconsistent_with_plan(self):
        webhook = parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": "event-wrong-product",
                    "type": "PRODUCT_CHANGE",
                    "app_user_id": "usly_usr_123",
                    "environment": "PRODUCTION",
                    "store": "PLAY_STORE",
                    "product_id": "usly_user_plus:monthly",
                    "event_timestamp_ms": 1780315200000,
                }
            }
        )

        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(
                    plan="premium"
                ),
                subscription=make_subscription(),
                webhook_payload=webhook,
            )

    def test_maps_app_store_to_ios(self):
        result = build_store_purchase_data(
            sync_result=make_sync_result(),
            subscription=make_subscription(store="app_store"),
            webhook_payload=make_webhook(store="APP_STORE"),
        )

        self.assertEqual(result.platform, "ios")

    def test_uses_subscription_expiration_for_plan(self):
        result = build_store_purchase_data(
            sync_result=make_sync_result(),
            subscription=make_subscription(),
            webhook_payload=make_webhook(),
        )

        self.assertEqual(
            result.plan_expires_at,
            datetime(2026, 8, 20, 12, 0),
        )

    def test_rejects_different_customer(self):
        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(
                    customer_id="customer_other"
                ),
                subscription=make_subscription(),
                webhook_payload=make_webhook(),
            )

    def test_rejects_different_app_user_id(self):
        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(),
                subscription=make_subscription(),
                webhook_payload=make_webhook(
                    app_user_id="usly_usr_other"
                ),
            )

    def test_rejects_different_environment(self):
        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(),
                subscription=make_subscription(
                    environment="sandbox"
                ),
                webhook_payload=make_webhook(
                    environment="PRODUCTION"
                ),
            )

    def test_rejects_different_store(self):
        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(),
                subscription=make_subscription(
                    store="app_store"
                ),
                webhook_payload=make_webhook(
                    store="PLAY_STORE"
                ),
            )

    def test_rejects_unsupported_store(self):
        subscription = make_subscription(store="stripe")

        with self.assertRaises(StorePurchaseDataError):
            build_store_purchase_data(
                sync_result=make_sync_result(),
                subscription=subscription,
                webhook_payload=make_webhook(store=None),
            )


if __name__ == "__main__":
    unittest.main()
