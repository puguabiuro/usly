import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.database import Base
from backend.models import DevicePushToken, User, UserRole, UserStatus
from backend.security import create_access_token
from backend import main


class PushRegistrationHTTPTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        with self.Session() as db:
            a = User(
                email="push-a@example.test",
                role=UserRole.USER.value,
                status=UserStatus.ACTIVE.value,
            )
            b = User(
                email="push-b@example.test",
                role=UserRole.PARTNER.value,
                status=UserStatus.ACTIVE.value,
            )
            db.add_all([a, b])
            db.commit()
            self.a_id = a.id
            self.b_id = b.id

        self.patches = [
            patch.object(main, "SessionLocal", self.Session),
            patch("backend.security.SessionLocal", self.Session),
        ]
        for item in self.patches:
            item.start()

        self.client = TestClient(main.app)
        self.token = "USLY_PUSH_HTTP_" + "X" * 40

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()

    def headers(self, user_id):
        return {
            "Authorization": f"Bearer {create_access_token(user_id)}"
        }

    def register(self, user_id, proof=None):
        payload = {
            "token": self.token,
            "platform": "android",
            "language": "pl",
        }
        if proof is not None:
            payload["push_ownership_proof"] = proof

        return self.client.post(
            "/push/register-token",
            headers=self.headers(user_id),
            json=payload,
        )

    def unregister(self, user_id, proof=None):
        payload = {"token": self.token}
        if proof is not None:
            payload["push_ownership_proof"] = proof

        return self.client.post(
            "/push/unregister-token",
            headers=self.headers(user_id),
            json=payload,
        )

    @staticmethod
    def data(response):
        body = response.json()
        return body.get("data", body)

    def test_new_token(self):
        response = self.register(self.a_id)
        self.assertEqual(response.status_code, 200, response.text)
        proof = self.data(response)["push_ownership_proof"]
        self.assertTrue(proof)

        with self.Session() as db:
            row = db.query(DevicePushToken).filter_by(
                token=self.token
            ).one()
            self.assertEqual(row.user_id, self.a_id)
            self.assertTrue(row.is_active)

    def test_valid_proof_refresh(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)
        proof = self.data(first)["push_ownership_proof"]
        response = self.register(self.a_id, proof)
        self.assertEqual(response.status_code, 200, response.text)

    def test_missing_proof_denied(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)
        response = self.register(self.a_id)
        self.assertEqual(response.status_code, 409)

    def test_other_owner_denied(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)
        response = self.register(self.b_id)
        self.assertEqual(response.status_code, 409)

    def test_unregister_proof(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)
        proof = self.data(first)["push_ownership_proof"]

        denied = self.unregister(self.a_id)
        self.assertEqual(denied.status_code, 409)

        accepted = self.unregister(self.a_id, proof)
        self.assertEqual(accepted.status_code, 200, accepted.text)

        with self.Session() as db:
            row = db.query(DevicePushToken).filter_by(
                token=self.token
            ).one()
            self.assertFalse(row.is_active)

    def test_inactive_other_owner_denied(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)
        proof = self.data(first)["push_ownership_proof"]

        unregistered = self.unregister(self.a_id, proof)
        self.assertEqual(unregistered.status_code, 200, unregistered.text)

        response = self.register(self.b_id)
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
