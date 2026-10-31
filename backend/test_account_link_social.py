"""Isolated security tests for Google account-link proof issuance."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.account_link_proof import verify_account_link_proof
from backend.account_link_social import authenticate_second_account_with_google
from backend.exceptions import ApiException
from backend.models import User, UserStatus


class GoogleAccountLinkTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        User.__table__.create(self.engine)
        self.db = Session(self.engine)

        self.companion = User(
            email="companion@example.test",
            role="user",
            status=UserStatus.ACTIVE.value,
            google_sub="google-companion",
        )
        self.organizer = User(
            email="organizer@example.test",
            role="partner",
            status=UserStatus.ACTIVE.value,
            google_sub="google-organizer",
        )
        self.db.add_all([self.companion, self.organizer])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_companion_can_prove_organizer(self):
        proof = authenticate_second_account_with_google(
            self.db,
            initiating_user=self.companion,
            google_sub="google-organizer",
        )
        target_id, proof_id = verify_account_link_proof(
            proof,
            initiating_user_id=self.companion.id,
        )
        self.assertEqual(target_id, self.organizer.id)
        self.assertEqual(len(proof_id), 64)

    def test_organizer_can_prove_companion(self):
        proof = authenticate_second_account_with_google(
            self.db,
            initiating_user=self.organizer,
            google_sub="google-companion",
        )
        target_id, _ = verify_account_link_proof(
            proof,
            initiating_user_id=self.organizer.id,
        )
        self.assertEqual(target_id, self.companion.id)

    def test_rejects_same_role(self):
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="google-companion",
            )

    def test_rejects_unknown_identity(self):
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="unknown-google-sub",
            )

    def test_rejects_empty_identity(self):
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="",
            )

    def test_rejects_inactive_second_account(self):
        self.organizer.status = UserStatus.DELETED.value
        self.db.commit()
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="google-organizer",
            )

    def test_rejects_inactive_initiator(self):
        self.companion.status = UserStatus.DELETED.value
        self.db.commit()
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="google-organizer",
            )

    def test_rejects_admin_initiator(self):
        self.companion.role = "admin"
        self.db.commit()
        with self.assertRaises(ApiException):
            authenticate_second_account_with_google(
                self.db,
                initiating_user=self.companion,
                google_sub="google-organizer",
            )

    def test_proof_is_bound_to_initiator(self):
        proof = authenticate_second_account_with_google(
            self.db,
            initiating_user=self.companion,
            google_sub="google-organizer",
        )
        with self.assertRaises(ApiException):
            verify_account_link_proof(
                proof,
                initiating_user_id=self.organizer.id,
            )


if __name__ == "__main__":
    unittest.main()
