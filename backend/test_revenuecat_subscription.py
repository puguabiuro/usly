"""Testy domenowego kontraktu subskrypcji RevenueCat."""

import json
import unittest
from datetime import datetime

from backend.revenuecat_subscription import (
    RevenueCatSubscriptionError,
    parse_revenuecat_subscription,
)


def make_subscription_payload():
    return {
        "object": "subscription",
        "id": "sub1ab2c3d4e5",
        "customer_id": "customer_current",
        "original_customer_id": "customer_original",
        "product_id": "prod1a2b3c4d5e",
        "current_period_ends_at": 1782864000000,
        "ends_at": 1782864000000,
        "gives_access": True,
        "pending_payment": False,
        "entitlements": {
            "object": "list",
            "items": [
                {
                    "object": "entitlement",
                    "id": "ent_premium",
                    "lookup_key": "usly_user_premium",
                    "state": "active",
                },
                {
                    "object": "entitlement",
                    "id": "ent_old",
                    "lookup_key": "usly_user_plus",
                    "state": "inactive",
                },
            ],
        },
        "status": "active",
        "environment": "production",
        "store": "play_store",
        "store_subscription_identifier": "GPA.1234-5678-9012-34567",
        "future_field": {"preserved": True},
    }


class RevenueCatSubscriptionTests(unittest.TestCase):
    def test_parses_complete_subscription(self):
        result = parse_revenuecat_subscription(
            make_subscription_payload()
        )

        self.assertEqual(result.subscription_id, "sub1ab2c3d4e5")
        self.assertEqual(result.customer_id, "customer_current")
        self.assertEqual(
            result.original_customer_id,
            "customer_original",
        )
        self.assertEqual(
            result.revenuecat_product_id,
            "prod1a2b3c4d5e",
        )
        self.assertEqual(result.environment, "production")
        self.assertEqual(result.store, "play_store")
        self.assertEqual(result.status, "active")
        self.assertTrue(result.gives_access)
        self.assertFalse(result.pending_payment)
        self.assertEqual(
            result.active_entitlement_ids,
            ("ent_premium",),
        )
        self.assertEqual(
            result.current_period_ends_at,
            datetime(2026, 7, 1, 0, 0),
        )

    def test_preserves_unknown_fields_in_stable_raw_payload(self):
        payload = make_subscription_payload()

        result = parse_revenuecat_subscription(payload)

        decoded = json.loads(result.raw_payload_json)
        self.assertEqual(
            decoded["future_field"],
            {"preserved": True},
        )
        self.assertEqual(
            result.raw_payload_json,
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    def test_accepts_null_product_and_expiration_dates(self):
        payload = make_subscription_payload()
        payload["product_id"] = None
        payload["current_period_ends_at"] = None
        payload["ends_at"] = None

        result = parse_revenuecat_subscription(payload)

        self.assertIsNone(result.revenuecat_product_id)
        self.assertIsNone(result.current_period_ends_at)
        self.assertIsNone(result.ends_at)

    def test_normalizes_numeric_store_identifier(self):
        payload = make_subscription_payload()
        payload["store_subscription_identifier"] = 12345678

        result = parse_revenuecat_subscription(payload)

        self.assertEqual(
            result.store_subscription_identifier,
            "12345678",
        )

    def test_deduplicates_active_entitlement_ids(self):
        payload = make_subscription_payload()
        payload["entitlements"]["items"].append(
            {
                "object": "entitlement",
                "id": "ent_premium",
                "lookup_key": "usly_user_premium",
                "state": "active",
            }
        )

        result = parse_revenuecat_subscription(payload)

        self.assertEqual(
            result.active_entitlement_ids,
            ("ent_premium",),
        )

    def test_rejects_invalid_entitlements_contract(self):
        payload = make_subscription_payload()
        payload["entitlements"] = {"items": "invalid"}

        with self.assertRaises(RevenueCatSubscriptionError):
            parse_revenuecat_subscription(payload)

    def test_rejects_missing_required_identifier(self):
        payload = make_subscription_payload()
        payload["id"] = ""

        with self.assertRaises(RevenueCatSubscriptionError):
            parse_revenuecat_subscription(payload)

    def test_rejects_invalid_access_flag(self):
        payload = make_subscription_payload()
        payload["gives_access"] = "true"

        with self.assertRaises(RevenueCatSubscriptionError):
            parse_revenuecat_subscription(payload)

    def test_rejects_invalid_environment(self):
        payload = make_subscription_payload()
        payload["environment"] = "development"

        with self.assertRaises(RevenueCatSubscriptionError):
            parse_revenuecat_subscription(payload)

    def test_rejects_invalid_timestamp(self):
        payload = make_subscription_payload()
        payload["ends_at"] = "1782864000000"

        with self.assertRaises(RevenueCatSubscriptionError):
            parse_revenuecat_subscription(payload)


if __name__ == "__main__":
    unittest.main()
