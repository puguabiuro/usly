"""HTTP security tests for Google account-link proof."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main
from backend.account_link_proof import verify_account_link_proof
from backend.models import Base, User, UserStatus
from backend.security import create_access_token


class GoogleAccountLinkHTTPTests(unittest.TestCase):

    def setUp(self):
        # Izolacja licznika SlowAPI między przypadkami testowymi.
        # Produkcyjny limit endpointu pozostaje bez zmian.
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
                email="google-http-companion@example.test",
                role="user",
                status=UserStatus.ACTIVE.value,
                google_sub="google-http-companion",
            )
            organizer = User(
                email="google-http-organizer@example.test",
                role="partner",
                status=UserStatus.ACTIVE.value,
                google_sub="google-http-organizer",
            )
            db.add_all([companion, organizer])
            db.commit()
            self.companion_id = companion.id
            self.organizer_id = organizer.id

        self.client = TestClient(main.app)
        self.db_patch = patch.object(
            main, "SessionLocal", self.session_factory
        )
        self.security_db_patch = patch(
            "backend.security.SessionLocal", self.session_factory
        )
        self.env_patch = patch.dict(
            os.environ, {"GOOGLE_WEB_CLIENT_ID": "test-client-id"}
        )

        self.db_patch.start()
        self.security_db_patch.start()
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.security_db_patch.stop()
        self.db_patch.stop()
        self.client.close()
        self.engine.dispose()

    def request_proof(self, user_id=None):
        headers = {}
        if user_id is not None:
            headers["Authorization"] = (
                "Bearer " + create_access_token(user_id)
            )

        return self.client.post(
            "/auth/account-links/google-proof",
            headers=headers,
            json={"id_token": "mock-google-token"},
        )

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_valid_opposite_role(self, verify):
        verify.return_value = {"sub": "google-http-organizer"}

        response = self.request_proof(self.companion_id)
        self.assertEqual(response.status_code, 200, response.text)

        proof = response.json()["data"]["proof"]
        target_id, _ = verify_account_link_proof(
            proof,
            initiating_user_id=self.companion_id,
        )
        self.assertEqual(target_id, self.organizer_id)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_reverse_direction(self, verify):
        verify.return_value = {"sub": "google-http-companion"}

        response = self.request_proof(self.organizer_id)
        self.assertEqual(response.status_code, 200, response.text)

        proof = response.json()["data"]["proof"]
        target_id, _ = verify_account_link_proof(
            proof,
            initiating_user_id=self.organizer_id,
        )
        self.assertEqual(target_id, self.companion_id)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_rejects_invalid_google_token(self, verify):
        verify.side_effect = ValueError("Invalid Google token")

        response = self.request_proof(self.companion_id)
        self.assertEqual(response.status_code, 401, response.text)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_rejects_wrong_identity(self, verify):
        verify.return_value = {"sub": "unknown-google-identity"}

        response = self.request_proof(self.companion_id)
        self.assertEqual(response.status_code, 401, response.text)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_rejects_same_role(self, verify):
        verify.return_value = {"sub": "google-http-companion"}

        response = self.request_proof(self.companion_id)
        self.assertNotEqual(response.status_code, 200, response.text)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_requires_authenticated_initiator(self, verify):
        verify.return_value = {"sub": "google-http-organizer"}

        response = self.request_proof()
        self.assertIn(response.status_code, (401, 403), response.text)

    @patch.object(main.google_id_token, "verify_oauth2_token")
    def test_rejects_inactive_target(self, verify):
        with self.session_factory() as db:
            organizer = db.get(User, self.organizer_id)
            organizer.status = UserStatus.DELETED.value
            db.commit()

        verify.return_value = {"sub": "google-http-organizer"}

        response = self.request_proof(self.companion_id)
        self.assertEqual(response.status_code, 403, response.text)


if __name__ == "__main__":
    unittest.main()
