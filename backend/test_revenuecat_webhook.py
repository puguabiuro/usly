"""Testy parsera i autoryzacji webhooków RevenueCat."""

import json
import unittest

from backend.revenuecat_config import RevenueCatConfig
from backend.revenuecat_webhook import (
    RevenueCatWebhookAuthorizationError,
    RevenueCatWebhookPayloadError,
    parse_revenuecat_webhook_payload,
    validate_revenuecat_webhook_authorization,
)


def make_config(webhook_authorization: str) -> RevenueCatConfig:
    return RevenueCatConfig(
        secret_api_key="",
        project_id="",
        webhook_authorization=webhook_authorization,
        api_v2_base_url="https://api.revenuecat.com/v2",
        http_timeout_seconds=10.0,
    )


class RevenueCatWebhookAuthorizationTests(unittest.TestCase):
    def test_accepts_correct_authorization(self) -> None:
        validate_revenuecat_webhook_authorization(
            "Bearer test-secret",
            make_config("Bearer test-secret"),
        )

    def test_rejects_missing_authorization(self) -> None:
        with self.assertRaises(RevenueCatWebhookAuthorizationError):
            validate_revenuecat_webhook_authorization(
                None,
                make_config("Bearer test-secret"),
            )

    def test_rejects_incorrect_authorization(self) -> None:
        with self.assertRaises(RevenueCatWebhookAuthorizationError):
            validate_revenuecat_webhook_authorization(
                "Bearer wrong-secret",
                make_config("Bearer test-secret"),
            )

    def test_rejects_missing_configuration(self) -> None:
        with self.assertRaises(RevenueCatWebhookAuthorizationError):
            validate_revenuecat_webhook_authorization(
                "Bearer test-secret",
                make_config(""),
            )


class RevenueCatWebhookPayloadTests(unittest.TestCase):
    def test_parses_complete_payload(self) -> None:
        payload = {
            "api_version": "1.0",
            "event": {
                "id": " evt-123 ",
                "type": " INITIAL_PURCHASE ",
                "app_user_id": " user-42 ",
                "original_app_user_id": " original-user-42 ",
                "aliases": [" alias-1 ", "alias-2", "alias-1"],
                "environment": " PRODUCTION ",
                "store": " PLAY_STORE ",
                "product_id": " usly_user_plus:monthly ",
                "event_timestamp_ms": 1720000000000,
                "future_event_field": {"enabled": True},
            },
            "future_root_field": ["kept"],
        }

        parsed = parse_revenuecat_webhook_payload(payload)

        self.assertEqual(parsed.event_id, "evt-123")
        self.assertEqual(parsed.event_type, "INITIAL_PURCHASE")
        self.assertEqual(parsed.app_user_id, "user-42")
        self.assertEqual(
            parsed.original_app_user_id,
            "original-user-42",
        )
        self.assertEqual(parsed.aliases, ("alias-1", "alias-2"))
        self.assertEqual(parsed.environment, "PRODUCTION")
        self.assertEqual(parsed.store, "PLAY_STORE")
        self.assertEqual(
            parsed.product_id,
            "usly_user_plus:monthly",
        )
        self.assertEqual(
            parsed.event_timestamp_ms,
            1720000000000,
        )
        self.assertEqual(
            parsed.raw_payload["future_root_field"],
            ["kept"],
        )
        self.assertEqual(
            parsed.raw_payload["event"]["future_event_field"],
            {"enabled": True},
        )

    def test_parses_payload_without_optional_fields(self) -> None:
        parsed = parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": "evt-minimal",
                    "type": "TEST",
                }
            }
        )

        self.assertIsNone(parsed.app_user_id)
        self.assertIsNone(parsed.original_app_user_id)
        self.assertEqual(parsed.aliases, ())
        self.assertIsNone(parsed.environment)
        self.assertIsNone(parsed.store)
        self.assertIsNone(parsed.product_id)
        self.assertIsNone(parsed.event_timestamp_ms)

    def test_raw_payload_is_detached_from_input(self) -> None:
        payload = {
            "event": {
                "id": "evt-detached",
                "type": "TEST",
                "metadata": {
                    "nested": ["original"],
                },
            },
            "root_metadata": {
                "status": "original",
            },
        }

        parsed = parse_revenuecat_webhook_payload(payload)
        original_payload_json = parsed.payload_json

        payload["event"]["metadata"]["nested"].append("changed")
        payload["root_metadata"]["status"] = "changed"

        self.assertEqual(
            parsed.raw_payload["event"]["metadata"]["nested"],
            ["original"],
        )
        self.assertEqual(
            parsed.raw_payload["root_metadata"]["status"],
            "original",
        )
        self.assertEqual(
            parsed.payload_json,
            original_payload_json,
        )
        self.assertEqual(
            json.loads(parsed.payload_json),
            parsed.raw_payload,
        )

    def test_serialization_is_stable(self) -> None:
        first_json = parse_revenuecat_webhook_payload(
            {
                "z": 1,
                "event": {
                    "type": "TEST",
                    "id": "evt-json",
                },
                "a": 2,
            }
        ).payload_json

        second_json = parse_revenuecat_webhook_payload(
            {
                "a": 2,
                "event": {
                    "id": "evt-json",
                    "type": "TEST",
                },
                "z": 1,
            }
        ).payload_json

        self.assertEqual(first_json, second_json)
        self.assertEqual(
            json.loads(first_json)["event"]["id"],
            "evt-json",
        )

    def test_rejects_missing_or_invalid_event(self) -> None:
        invalid_payloads = (
            {},
            {"event": None},
            {"event": []},
            {"event": "invalid"},
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(payload)

    def test_rejects_missing_empty_or_invalid_event_id(self) -> None:
        invalid_ids = (None, "", "   ", 123, [], {})

        for event_id in invalid_ids:
            with self.subTest(event_id=event_id):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(
                        {
                            "event": {
                                "id": event_id,
                                "type": "TEST",
                            }
                        }
                    )

    def test_rejects_missing_empty_or_invalid_event_type(self) -> None:
        invalid_types = (None, "", "   ", 123, [], {})

        for event_type in invalid_types:
            with self.subTest(event_type=event_type):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(
                        {
                            "event": {
                                "id": "evt-1",
                                "type": event_type,
                            }
                        }
                    )

    def test_normalizes_and_deduplicates_aliases(self) -> None:
        parsed = parse_revenuecat_webhook_payload(
            {
                "event": {
                    "id": "evt-aliases",
                    "type": "TEST",
                    "aliases": [
                        " user-1 ",
                        "user-2",
                        "user-1",
                    ],
                }
            }
        )

        self.assertEqual(
            parsed.aliases,
            ("user-1", "user-2"),
        )

    def test_rejects_invalid_aliases(self) -> None:
        invalid_aliases = (
            "user-1",
            {},
            [""],
            [123],
        )

        for aliases in invalid_aliases:
            with self.subTest(aliases=aliases):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(
                        {
                            "event": {
                                "id": "evt-1",
                                "type": "TEST",
                                "aliases": aliases,
                            }
                        }
                    )

    def test_rejects_invalid_optional_text_fields(self) -> None:
        for field_name in (
            "app_user_id",
            "original_app_user_id",
            "environment",
            "store",
            "product_id",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(
                        {
                            "event": {
                                "id": "evt-1",
                                "type": "TEST",
                                field_name: 123,
                            }
                        }
                    )

    def test_rejects_invalid_timestamp(self) -> None:
        invalid_timestamps = (
            -1,
            True,
            1.5,
            "1720000000000",
        )

        for timestamp in invalid_timestamps:
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(RevenueCatWebhookPayloadError):
                    parse_revenuecat_webhook_payload(
                        {
                            "event": {
                                "id": "evt-1",
                                "type": "TEST",
                                "event_timestamp_ms": timestamp,
                            }
                        }
                    )


if __name__ == "__main__":
    unittest.main()
