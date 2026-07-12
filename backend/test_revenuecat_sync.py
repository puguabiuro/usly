"""Testy czystej logiki i orkiestracji RevenueCat Sync Engine."""

import unittest

from backend.revenuecat_sync import (
    EffectivePlan,
    MappedEntitlement,
    RevenueCatSyncDataError,
    RevenueCatSyncEngine,
    build_entitlement_lookup_map,
    build_sync_result,
    choose_effective_plan,
    map_active_entitlements,
    normalize_role,
)


class RevenueCatSyncMappingTests(unittest.TestCase):
    def test_normalize_role(self):
        self.assertEqual(normalize_role(" USER "), "user")
        self.assertEqual(normalize_role("Partner"), "partner")

        with self.assertRaises(RevenueCatSyncDataError):
            normalize_role("admin")

    def test_choose_effective_plan_returns_free_without_entitlements(self):
        self.assertEqual(
            choose_effective_plan("user", ()),
            EffectivePlan(
                role="user",
                plan="free",
                rank=0,
            ),
        )

    def test_choose_effective_plan_uses_highest_plan_for_role(self):
        mapped = (
            MappedEntitlement(
                entitlement_id="ent_plus",
                lookup_key="usly_user_plus",
                role="user",
                plan="plus",
                rank=1,
            ),
            MappedEntitlement(
                entitlement_id="ent_vip",
                lookup_key="usly_user_vip",
                role="user",
                plan="vip",
                rank=3,
            ),
            MappedEntitlement(
                entitlement_id="ent_partner",
                lookup_key="usly_partner_premium",
                role="partner",
                plan="premium",
                rank=2,
            ),
        )

        result = choose_effective_plan("user", mapped)

        self.assertEqual(result.plan, "vip")
        self.assertEqual(result.rank, 3)
        self.assertEqual(result.source_entitlement_id, "ent_vip")
        self.assertEqual(
            result.source_entitlement_lookup_key,
            "usly_user_vip",
        )

    def test_build_lookup_map_rejects_missing_lookup_key(self):
        with self.assertRaises(RevenueCatSyncDataError):
            build_entitlement_lookup_map(
                {"items": [{"id": "ent_without_lookup_key"}]}
            )

    def test_map_active_entitlements_tracks_unknown_and_duplicates(self):
        lookup_map = build_entitlement_lookup_map(
            {
                "items": [
                    {
                        "id": "ent_plus",
                        "lookup_key": "usly_user_plus",
                    },
                    {
                        "id": "ent_vip",
                        "lookup_key": "usly_user_vip",
                    },
                    {
                        "id": "ent_future",
                        "lookup_key": "usly_future_plan",
                    },
                ]
            }
        )

        mapped, unknown = map_active_entitlements(
            {
                "items": [
                    {"entitlement_id": "ent_plus"},
                    {"entitlement_id": "ent_vip"},
                    {"entitlement_id": "ent_vip"},
                    {"entitlement_id": "ent_missing"},
                    {"entitlement_id": "ent_future"},
                ]
            },
            lookup_map,
        )

        self.assertEqual(
            [item.lookup_key for item in mapped],
            [
                "usly_user_plus",
                "usly_user_vip",
            ],
        )
        self.assertEqual(
            unknown,
            (
                "ent_missing",
                "ent_future",
            ),
        )


class RevenueCatSyncResultTests(unittest.TestCase):
    def test_build_sync_result(self):
        result = build_sync_result(
            app_user_id=" user_123 ",
            customer_id=" customer_456 ",
            role=" USER ",
            entitlements_payload={
                "items": [
                    {
                        "id": "ent_premium",
                        "lookup_key": "usly_user_premium",
                    }
                ]
            },
            active_entitlements_payload={
                "items": [
                    {"entitlement_id": "ent_premium"},
                    {"entitlement_id": "ent_unknown"},
                ]
            },
            subscriptions_payload={
                "items": [
                    {
                        "object": "subscription",
                        "id": "subscription_789",
                        "customer_id": "customer_456",
                        "original_customer_id": "customer_original",
                        "product_id": "product_internal",
                        "current_period_ends_at": None,
                        "ends_at": 1782864000000,
                        "gives_access": True,
                        "pending_payment": False,
                        "entitlements": {
                            "object": "list",
                            "items": [
                                {
                                    "object": "entitlement",
                                    "id": "ent_premium",
                                    "lookup_key": (
                                        "usly_user_premium"
                                    ),
                                    "state": "active",
                                }
                            ],
                        },
                        "status": "active",
                        "environment": "production",
                        "store": "play_store",
                        "store_subscription_identifier": (
                            "GPA.1234-5678-9012-34567"
                        ),
                        "future_field": {"preserved": True},
                    }
                ]
            },
        )

        self.assertEqual(result.app_user_id, "user_123")
        self.assertEqual(result.customer_id, "customer_456")
        self.assertEqual(result.role, "user")
        self.assertEqual(result.effective_plan.plan, "premium")
        self.assertEqual(
            result.unknown_entitlement_ids,
            ("ent_unknown",),
        )
        self.assertEqual(
            result.subscriptions[0].subscription_id,
            "subscription_789",
        )
        self.assertEqual(
            result.subscriptions[0].store_subscription_identifier,
            "GPA.1234-5678-9012-34567",
        )
        self.assertIn(
            '"future_field":{"preserved":true}',
            result.subscriptions[0].raw_payload_json,
        )

    def test_build_sync_result_rejects_invalid_subscription_item(self):
        with self.assertRaises(RevenueCatSyncDataError):
            build_sync_result(
                app_user_id="user_123",
                customer_id="customer_456",
                role="user",
                entitlements_payload={"items": []},
                active_entitlements_payload={"items": []},
                subscriptions_payload={"items": ["invalid"]},
            )


class FakeRevenueCatService:
    def __init__(self):
        self.calls = []

    def find_customer_by_app_user_id(self, app_user_id):
        self.calls.append(("find_customer", app_user_id))
        return {"id": "customer_internal"}

    def get_entitlements(self):
        self.calls.append(("get_entitlements",))
        return {
            "items": [
                {
                    "id": "ent_partner_pro",
                    "lookup_key": "usly_partner_pro",
                },
                {
                    "id": "ent_partner_premium",
                    "lookup_key": "usly_partner_premium",
                },
            ]
        }

    def get_active_entitlements(self, customer_id):
        self.calls.append(("get_active_entitlements", customer_id))
        return {
            "items": [
                {"entitlement_id": "ent_partner_pro"},
                {"entitlement_id": "ent_partner_premium"},
            ]
        }

    def get_subscriptions(self, customer_id, *, environment=None):
        self.calls.append(
            ("get_subscriptions", customer_id, environment)
        )
        return {
            "items": [
                {
                    "object": "subscription",
                    "id": "subscription_internal",
                    "customer_id": customer_id,
                    "original_customer_id": "customer_original",
                    "product_id": "product_internal",
                    "current_period_ends_at": None,
                    "ends_at": None,
                    "gives_access": True,
                    "pending_payment": False,
                    "entitlements": {
                        "object": "list",
                        "items": [
                            {
                                "object": "entitlement",
                                "id": "ent_partner_premium",
                                "lookup_key": (
                                    "usly_partner_premium"
                                ),
                                "state": "active",
                            }
                        ],
                    },
                    "status": "active",
                    "environment": environment or "production",
                    "store": "play_store",
                    "store_subscription_identifier": (
                        "GPA.9999-8888-7777-66666"
                    ),
                }
            ]
        }


class RevenueCatSyncEngineTests(unittest.TestCase):
    def test_sync_customer_orchestrates_service_calls(self):
        service = FakeRevenueCatService()
        engine = RevenueCatSyncEngine(service=service)

        result = engine.sync_customer(
            app_user_id=" partner_123 ",
            role=" PARTNER ",
            environment="sandbox",
        )

        self.assertEqual(result.app_user_id, "partner_123")
        self.assertEqual(result.customer_id, "customer_internal")
        self.assertEqual(result.role, "partner")
        self.assertEqual(result.effective_plan.plan, "premium")
        self.assertEqual(result.effective_plan.rank, 2)

        self.assertEqual(
            service.calls,
            [
                ("find_customer", "partner_123"),
                ("get_entitlements",),
                (
                    "get_active_entitlements",
                    "customer_internal",
                ),
                (
                    "get_subscriptions",
                    "customer_internal",
                    "sandbox",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
