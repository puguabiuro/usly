"""Izolowane testy regresyjne łączenia kont USLY."""

import os
import unittest
from unittest.mock import patch

from jose import jwt
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Testy nie wymagają sekretu środowiska produkcyjnego.
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "usly-account-links-isolated-test-secret-2026",
)

from backend.db.database import Base
from backend.models import (
    AccountLink,
    AccountLinkProofUse,
    AuditLog,
    User,
    UserRole,
    UserStatus,
)
from backend.account_link_service import (
    create_account_link,
    create_verified_account_link,
)
from backend.account_link_proof import (
    create_account_link_proof,
    verify_account_link_proof,
)
from backend.exceptions import ApiException


class AccountLinkRegressionTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        for table in (
            User.__table__,
            AccountLink.__table__,
            AccountLinkProofUse.__table__,
            AuditLog.__table__,
        ):
            table.create(self.engine, checkfirst=True)

        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.companion = self.make_user("user")
        self.organizer = self.make_user("partner")
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def make_user(self, role, status=None):
        user = User(
            email=f"account-link-{role}-{self.db.query(User).count()}@example.test",
            role=role,
            status=status or UserStatus.ACTIVE.value,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def test_valid_account_link(self):
        link = create_account_link(
            self.db,
            companion_user_id=self.companion.id,
            organizer_user_id=self.organizer.id,
        )
        self.db.commit()

        self.assertEqual(link.user_id, self.companion.id)
        self.assertEqual(link.partner_id, self.organizer.id)
        self.assertEqual(self.db.query(AccountLink).count(), 1)

    def test_cannot_link_same_account(self):
        with self.assertRaises(ApiException):
            create_account_link(
                self.db,
                companion_user_id=self.companion.id,
                organizer_user_id=self.companion.id,
            )

    def test_rejects_wrong_roles(self):
        with self.assertRaises(ApiException):
            create_account_link(
                self.db,
                companion_user_id=self.organizer.id,
                organizer_user_id=self.companion.id,
            )

    def test_rejects_inactive_account(self):
        self.organizer.status = "inactive"
        self.db.flush()

        with self.assertRaises(ApiException):
            create_account_link(
                self.db,
                companion_user_id=self.companion.id,
                organizer_user_id=self.organizer.id,
            )

    def test_rejects_duplicate_link(self):
        create_account_link(
            self.db,
            companion_user_id=self.companion.id,
            organizer_user_id=self.organizer.id,
        )
        self.db.commit()

        with self.assertRaises(ApiException):
            create_account_link(
                self.db,
                companion_user_id=self.companion.id,
                organizer_user_id=self.organizer.id,
            )

    def test_rejects_link_to_another_organizer(self):
        second_organizer = self.make_user("partner")
        self.db.commit()

        create_account_link(
            self.db,
            companion_user_id=self.companion.id,
            organizer_user_id=self.organizer.id,
        )
        self.db.commit()

        with self.assertRaises(ApiException):
            create_account_link(
                self.db,
                companion_user_id=self.companion.id,
                organizer_user_id=second_organizer.id,
            )

    def test_proof_is_bound_to_initiator(self):
        proof = create_account_link_proof(
            user_id=self.organizer.id,
            initiating_user_id=self.companion.id,
        )

        with self.assertRaises(ApiException):
            verify_account_link_proof(
                proof,
                initiating_user_id=self.organizer.id,
            )

    def test_valid_proof_links_accounts(self):
        proof = create_account_link_proof(
            user_id=self.organizer.id,
            initiating_user_id=self.companion.id,
        )

        link = create_verified_account_link(
            self.db,
            initiating_user_id=self.companion.id,
            proof=proof,
        )

        self.assertEqual(link.user_id, self.companion.id)
        self.assertEqual(link.partner_id, self.organizer.id)
        self.assertEqual(self.db.query(AccountLinkProofUse).count(), 1)

    def test_proof_cannot_be_reused(self):
        proof = create_account_link_proof(
            user_id=self.organizer.id,
            initiating_user_id=self.companion.id,
        )

        create_verified_account_link(
            self.db,
            initiating_user_id=self.companion.id,
            proof=proof,
        )

        with self.assertRaises(ApiException):
            create_verified_account_link(
                self.db,
                initiating_user_id=self.companion.id,
                proof=proof,
            )

        self.assertEqual(self.db.query(AccountLinkProofUse).count(), 1)

    def test_invalid_proof_is_rejected(self):
        with self.assertRaises(ApiException):
            verify_account_link_proof(
                "not-a-valid-proof",
                initiating_user_id=self.companion.id,
            )


class AccountSwitchEndpointTests(unittest.TestCase):
    """Testy rzeczywistej funkcji endpointu z izolowaną sesją."""

    setUp = AccountLinkRegressionTests.setUp
    tearDown = AccountLinkRegressionTests.tearDown
    make_user = AccountLinkRegressionTests.make_user

    def set_up_endpoint(self):
        from backend import main
        self.main = main


    def switch(self, source, target_id):
        from unittest.mock import patch
        self.set_up_endpoint()

        payload = self.main.AccountLinkSwitchRequest(
            target_user_id=target_id,
        )

        with (
            patch.object(
                self.main,
                "SessionLocal",
                return_value=self.Session(),
            ),
            patch.object(self.main, "_audit"),
        ):
            from starlette.requests import Request

            request = Request({
                "type": "http",
                "method": "POST",
                "path": "/auth/account-links/switch",
                "headers": [],
                "client": ("127.0.0.1", 12345),
                "scheme": "http",
                "server": ("testserver", 80),
                "query_string": b"",
            })

            return self.main.switch_linked_account.__wrapped__(
                request=request,
                payload=payload,
                current_user=source,
            )

    def assert_switch_token(self, response, expected_user_id):
        from backend.security import JWT_SECRET_KEY, JWT_ALGORITHM
        from jose import jwt

        # Odczyt odpowiedzi zgodnie z formatem ok() w aplikacji.
        if hasattr(response, "body"):
            import json
            response = json.loads(response.body)

        self.assertIsInstance(response, dict)

        data = response.get("data", response)
        self.assertIsInstance(data, dict)

        token = data["access_token"]
        claims = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        self.assertEqual(claims["sub"], str(expected_user_id))
        self.assertEqual(data["user"]["id"], expected_user_id)

    def link_accounts(self):
        create_account_link(
            self.db,
            companion_user_id=self.companion.id,
            organizer_user_id=self.organizer.id,
        )
        self.db.commit()

    def test_switch_companion_to_organizer(self):
        self.link_accounts()

        response = self.switch(
            self.companion,
            self.organizer.id,
        )

        self.assert_switch_token(response, self.organizer.id)

    def test_switch_organizer_to_companion(self):
        self.link_accounts()

        response = self.switch(
            self.organizer,
            self.companion.id,
        )

        self.assert_switch_token(response, self.companion.id)

    def test_switch_rejects_unlinked_account(self):
        with self.assertRaises(ApiException):
            self.switch(
                self.companion,
                self.organizer.id,
            )

    def test_switch_rejects_same_role(self):
        second_companion = self.make_user("user")
        self.db.commit()

        with self.assertRaises(ApiException):
            self.switch(
                self.companion,
                second_companion.id,
            )

    def test_switch_rejects_inactive_target(self):
        self.link_accounts()
        self.organizer.status = "inactive"
        self.db.commit()

        with self.assertRaises(ApiException):
            self.switch(
                self.companion,
                self.organizer.id,
            )

    def test_switch_rejects_self(self):
        with self.assertRaises(ApiException):
            self.switch(
                self.companion,
                self.companion.id,
            )


if __name__ == "__main__":
    unittest.main()
