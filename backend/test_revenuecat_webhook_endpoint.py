"""Testy endpointu POST /revenuecat/webhook."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.main import revenuecat_webhook
from backend.revenuecat_config import RevenueCatConfig
from backend.revenuecat_webhook_processor import (
    RevenueCatWebhookProcessResult,
)


class FakeRequest:
    def __init__(
        self,
        *,
        authorization: str | None,
        payload,
        json_error: Exception | None = None,
    ) -> None:
        self.headers = {}

        if authorization is not None:
            self.headers["authorization"] = authorization

        self._payload = payload
        self._json_error = json_error

    async def json(self):
        if self._json_error is not None:
            raise self._json_error

        return self._payload


class FakeSession:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


class ControlledProcessor:
    result = None
    error = None
    created_with_db = None
    received_payload = None

    def __init__(self, *, db) -> None:
        type(self).created_with_db = db

    def process(self, payload):
        type(self).received_payload = payload

        if type(self).error is not None:
            raise type(self).error

        return type(self).result


class RevenueCatWebhookEndpointTests(
    unittest.IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.config = RevenueCatConfig(
            secret_api_key="secret-api-key",
            project_id="project-id",
            webhook_authorization="Bearer webhook-secret",
            api_v2_base_url="https://api.revenuecat.com/v2",
            http_timeout_seconds=10.0,
        )

        self.payload = {
            "event": {
                "id": "evt-endpoint-1",
                "type": "INITIAL_PURCHASE",
                "app_user_id": (
                    "usly_usr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                ),
                "environment": "SANDBOX",
                "store": "PLAY_STORE",
                "product_id": "usly_user_plus:monthly",
            }
        }

        ControlledProcessor.result = None
        ControlledProcessor.error = None
        ControlledProcessor.created_with_db = None
        ControlledProcessor.received_payload = None

    async def test_rejects_invalid_authorization_before_opening_session(
        self,
    ) -> None:
        request = FakeRequest(
            authorization="Bearer wrong-secret",
            payload=self.payload,
        )

        with patch(
            "backend.main.load_revenuecat_config",
            return_value=self.config,
        ), patch("backend.main.SessionLocal") as session_local:
            with self.assertRaises(HTTPException) as context:
                await revenuecat_webhook(request)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_WEBHOOK_UNAUTHORIZED",
        )
        session_local.assert_not_called()

    async def test_rejects_invalid_json_before_opening_session(
        self,
    ) -> None:
        request = FakeRequest(
            authorization="Bearer webhook-secret",
            payload=None,
            json_error=ValueError("invalid json"),
        )

        with patch(
            "backend.main.load_revenuecat_config",
            return_value=self.config,
        ), patch("backend.main.SessionLocal") as session_local:
            with self.assertRaises(HTTPException) as context:
                await revenuecat_webhook(request)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_WEBHOOK_INVALID_JSON",
        )
        session_local.assert_not_called()

    async def test_commits_successful_webhook(self) -> None:
        session = FakeSession()
        request = FakeRequest(
            authorization="Bearer webhook-secret",
            payload=self.payload,
        )

        ControlledProcessor.result = RevenueCatWebhookProcessResult(
            event_id="evt-endpoint-1",
            status="processed",
            duplicate=False,
            webhook_event_db_id=1,
            app_user_id=(
                "usly_usr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ),
            revenuecat_customer_id="customer-endpoint-1",
            role="user",
            effective_plan="plus",
        )

        with patch(
            "backend.main.load_revenuecat_config",
            return_value=self.config,
        ), patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.RevenueCatWebhookProcessor",
            ControlledProcessor,
        ):
            response = await revenuecat_webhook(request)

        self.assertEqual(session.commit_calls, 1)
        self.assertEqual(session.rollback_calls, 0)
        self.assertEqual(session.close_calls, 1)
        self.assertIs(ControlledProcessor.created_with_db, session)
        self.assertEqual(
            ControlledProcessor.received_payload.event_id,
            "evt-endpoint-1",
        )
        self.assertIsNotNone(response)

    async def test_commits_failed_status_and_returns_502(self) -> None:
        session = FakeSession()
        request = FakeRequest(
            authorization="Bearer webhook-secret",
            payload=self.payload,
        )

        ControlledProcessor.result = RevenueCatWebhookProcessResult(
            event_id="evt-endpoint-1",
            status="failed",
            duplicate=False,
            webhook_event_db_id=1,
            app_user_id=(
                "usly_usr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ),
            revenuecat_customer_id=None,
            role=None,
            effective_plan=None,
        )

        with patch(
            "backend.main.load_revenuecat_config",
            return_value=self.config,
        ), patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.RevenueCatWebhookProcessor",
            ControlledProcessor,
        ):
            with self.assertRaises(HTTPException) as context:
                await revenuecat_webhook(request)

        self.assertEqual(context.exception.status_code, 502)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_WEBHOOK_PROCESSING_FAILED",
        )
        self.assertEqual(session.commit_calls, 1)
        self.assertEqual(session.rollback_calls, 0)
        self.assertEqual(session.close_calls, 1)

    async def test_rolls_back_unexpected_processing_error(self) -> None:
        session = FakeSession()
        request = FakeRequest(
            authorization="Bearer webhook-secret",
            payload=self.payload,
        )

        ControlledProcessor.error = RuntimeError(
            "unexpected processing error"
        )

        with patch(
            "backend.main.load_revenuecat_config",
            return_value=self.config,
        ), patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.RevenueCatWebhookProcessor",
            ControlledProcessor,
        ):
            with self.assertRaises(HTTPException) as context:
                await revenuecat_webhook(request)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_WEBHOOK_INTERNAL_ERROR",
        )
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
