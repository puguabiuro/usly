"""HTTP security tests for Apple account-link proof."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main
from backend.account_link_proof import verify_account_link_proof
from backend.models import Base, User, UserStatus, AppleAuthCredential
from backend.security import create_access_token


class AppleAccountLinkHTTPTests(unittest.TestCase):

    def setUp(self):
        main.limiter.reset()

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        with self.session_factory() as db:
            companion = User(
                email="apple-http-companion@example.test",
                role="user",
                status=UserStatus.ACTIVE.value,
                apple_sub="apple-http-companion",
            )
            organizer = User(
                email="apple-http-organizer@example.test",
                role="partner",
                status=UserStatus.ACTIVE.value,
                apple_sub="apple-http-organizer",
            )
            db.add_all([companion, organizer])
            db.commit()
            self.companion_id = companion.id
            self.organizer_id = organizer.id

        self.patches = [
            patch.object(main, "SessionLocal", self.session_factory),
            patch("backend.security.SessionLocal", self.session_factory),
            patch.dict(
                os.environ,
                {"APPLE_IOS_CLIENT_ID": "test.apple.client"},
            ),
            patch.object(
                main,
                "_verify_apple_auth_identity",
                return_value={
                    "apple_sub": "apple-http-organizer",
                    "email": None,
                    "email_verified": False,
                    "audience": "test.apple.client",
                },
            ),
            patch.object(
                main,
                "_exchange_apple_code_for_identity",
                return_value=(
                    "test.apple.client",
                    {
                        "id_token": "exchanged-apple-token",
                        "refresh_token": "unused-refresh-token",
                    },
                ),
            ),
            patch.object(
                main,
                "verify_apple_identity_token",
                return_value={"sub": "apple-http-organizer"},
            ),
        ]

        for item in self.patches:
            item.start()

        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()

    def request_proof(self, authenticated=True):
        headers = {}
        if authenticated:
            headers["Authorization"] = (
                "Bearer " + create_access_token(self.companion_id)
            )

        return self.client.post(
            "/auth/account-links/apple-proof",
            headers=headers,
            json={
                "id_token": "incoming-apple-token-long-enough",
                "nonce": "test-apple-nonce-123456",
                "authorization_code": "test-apple-code",
            },
        )

    def test_valid_opposite_role(self):
        response = self.request_proof()
        self.assertEqual(response.status_code, 200, response.text)

        proof = response.json()["data"]["proof"]
        target_id, _ = verify_account_link_proof(
            proof,
            initiating_user_id=self.companion_id,
        )
        self.assertEqual(target_id, self.organizer_id)

    def test_rejects_mismatched_apple_subject(self):
        with patch.object(
            main,
            "verify_apple_identity_token",
            return_value={"sub": "different-apple-person"},
        ):
            response = self.request_proof()

        self.assertEqual(response.status_code, 401, response.text)

    def test_rejects_missing_exchanged_identity_token(self):
        with patch.object(
            main,
            "_exchange_apple_code_for_identity",
            return_value=(
                "test.apple.client",
                {"refresh_token": "unused-refresh-token"},
            ),
        ):
            response = self.request_proof()

        self.assertEqual(response.status_code, 401, response.text)

    def test_rejects_invalid_exchanged_identity_token(self):
        from backend.apple_auth import AppleAuthError

        with patch.object(
            main,
            "verify_apple_identity_token",
            side_effect=AppleAuthError("invalid"),
        ):
            response = self.request_proof()

        self.assertEqual(response.status_code, 401, response.text)

    def test_rejects_failed_code_exchange(self):
        from backend.exceptions import ApiException
        from backend.error_codes import ErrorCode

        with patch.object(
            main,
            "_exchange_apple_code_for_identity",
            side_effect=ApiException(
                status_code=401,
                code=ErrorCode.INVALID_CREDENTIALS,
            ),
        ):
            response = self.request_proof()

        self.assertEqual(response.status_code, 401, response.text)

    def test_requires_authenticated_initiator(self):
        response = self.request_proof(authenticated=False)
        self.assertIn(response.status_code, (401, 403), response.text)

    def test_rejects_unknown_second_account(self):
        with patch.object(
            main,
            "_verify_apple_auth_identity",
            return_value={
                "apple_sub": "unknown-apple-person",
                "email": None,
                "email_verified": False,
                "audience": "test.apple.client",
            },
        ), patch.object(
            main,
            "verify_apple_identity_token",
            return_value={"sub": "unknown-apple-person"},
        ):
            response = self.request_proof()

        self.assertEqual(response.status_code, 401, response.text)

    def test_does_not_store_second_account_credentials(self):
        response = self.request_proof()
        self.assertEqual(response.status_code, 200, response.text)

        with self.session_factory() as db:
            count = db.query(AppleAuthCredential).count()
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
