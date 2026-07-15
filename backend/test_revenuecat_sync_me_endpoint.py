"""Testy endpointu POST /revenuecat/sync-me."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.main import revenuecat_sync_me
from backend.revenuecat_sync import (
    EffectivePlan,
    RevenueCatSyncError,
    RevenueCatSyncResult,
)
from backend.revenuecat_sync_persistence import (
    RevenueCatSyncPersistenceError,
    RevenueCatSyncPersistenceResult,
)


class FakeQuery:
    def __init__(self, user) -> None:
        self.user = user

    def filter(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self.user


class FakeSession:
    def __init__(self, user) -> None:
        self.user = user
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def query(self, model):
        return FakeQuery(self.user)

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


class ControlledSyncEngine:
    result = None
    error = None
    received_app_user_id = None
    received_role = None
    received_environment = None

    def sync_customer(
        self,
        *,
        app_user_id,
        role,
        environment=None,
    ):
        type(self).received_app_user_id = app_user_id
        type(self).received_role = role
        type(self).received_environment = environment

        if type(self).error is not None:
            raise type(self).error

        return type(self).result


class ControlledPersistenceService:
    result = None
    error = None
    created_with_db = None
    received_user = None
    received_sync_result = None

    def __init__(self, db) -> None:
        type(self).created_with_db = db

    def apply(
        self,
        *,
        user,
        sync_result,
        environment=None,
        store=None,
        synced_at=None,
        source_event_id=None,
        source_event_type=None,
        source_event_at=None,
    ):
        type(self).received_user = user
        type(self).received_sync_result = sync_result

        if type(self).error is not None:
            raise type(self).error

        return type(self).result


class RevenueCatSyncMeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = SimpleNamespace(
            id=123,
            role="user",
            revenuecat_app_user_id=(
                "usly_usr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ),
        )

        self.sync_result = RevenueCatSyncResult(
            app_user_id=self.user.revenuecat_app_user_id,
            customer_id="customer-sync-me-1",
            role="user",
            effective_plan=EffectivePlan(
                role="user",
                plan="premium",
                rank=2,
                source_entitlement_id="entitlement-premium",
                source_entitlement_lookup_key="usly_user_premium",
            ),
            mapped_entitlements=(),
            unknown_entitlement_ids=(),
            subscriptions=(),
        )

        ControlledSyncEngine.result = self.sync_result
        ControlledSyncEngine.error = None
        ControlledSyncEngine.received_app_user_id = None
        ControlledSyncEngine.received_role = None
        ControlledSyncEngine.received_environment = None

        ControlledPersistenceService.result = (
            RevenueCatSyncPersistenceResult(
                sync_result=self.sync_result,
                store_purchase=SimpleNamespace(id=321),
                purchase_data=None,
                plan_apply_result=SimpleNamespace(),
            )
        )
        ControlledPersistenceService.error = None
        ControlledPersistenceService.created_with_db = None
        ControlledPersistenceService.received_user = None
        ControlledPersistenceService.received_sync_result = None

    def test_commits_successful_sync_and_returns_effective_plan(
        self,
    ) -> None:
        session = FakeSession(self.user)

        with patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.create_revenuecat_sync_engine",
            return_value=ControlledSyncEngine(),
        ), patch(
            "backend.main.RevenueCatSyncPersistenceService",
            ControlledPersistenceService,
        ):
            response = revenuecat_sync_me(
                current_user=self.user,
            )

        self.assertEqual(session.commit_calls, 1)
        self.assertEqual(session.rollback_calls, 0)
        self.assertEqual(session.close_calls, 1)
        self.assertEqual(
            ControlledSyncEngine.received_app_user_id,
            self.user.revenuecat_app_user_id,
        )
        self.assertEqual(
            ControlledSyncEngine.received_role,
            "user",
        )
        self.assertIs(
            ControlledPersistenceService.created_with_db,
            session,
        )
        self.assertIs(
            ControlledPersistenceService.received_user,
            self.user,
        )
        self.assertIs(
            ControlledPersistenceService.received_sync_result,
            self.sync_result,
        )
        self.assertIsNotNone(response)

    def test_rejects_missing_revenuecat_app_user_id(self) -> None:
        self.user.revenuecat_app_user_id = None
        session = FakeSession(self.user)

        with patch(
            "backend.main.SessionLocal",
            return_value=session,
        ):
            with self.assertRaises(HTTPException) as context:
                revenuecat_sync_me(
                    current_user=self.user,
                )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_APP_USER_ID_MISSING",
        )
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)

    def test_returns_404_when_user_is_missing(self) -> None:
        session = FakeSession(None)

        with patch(
            "backend.main.SessionLocal",
            return_value=session,
        ):
            with self.assertRaises(HTTPException) as context:
                revenuecat_sync_me(
                    current_user=self.user,
                )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(
            context.exception.detail,
            "USER_NOT_FOUND",
        )
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)

    def test_rolls_back_revenuecat_sync_error(self) -> None:
        session = FakeSession(self.user)
        ControlledSyncEngine.error = RevenueCatSyncError(
            "sync failed"
        )

        with patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.create_revenuecat_sync_engine",
            return_value=ControlledSyncEngine(),
        ):
            with self.assertRaises(HTTPException) as context:
                revenuecat_sync_me(
                    current_user=self.user,
                )

        self.assertEqual(context.exception.status_code, 502)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_SYNC_FAILED",
        )
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)

    def test_rolls_back_persistence_error(self) -> None:
        session = FakeSession(self.user)
        ControlledPersistenceService.error = (
            RevenueCatSyncPersistenceError(
                "persistence failed"
            )
        )

        with patch(
            "backend.main.SessionLocal",
            return_value=session,
        ), patch(
            "backend.main.create_revenuecat_sync_engine",
            return_value=ControlledSyncEngine(),
        ), patch(
            "backend.main.RevenueCatSyncPersistenceService",
            ControlledPersistenceService,
        ):
            with self.assertRaises(HTTPException) as context:
                revenuecat_sync_me(
                    current_user=self.user,
                )

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "REVENUECAT_SYNC_PERSISTENCE_FAILED",
        )
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
