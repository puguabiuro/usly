"""Izolowane testy HTTP tworzenia połączonego profilu USLY."""

import unittest
import os
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main
from backend.models import Base, User, AccountLink, UserStatus
from backend.security import create_access_token, hash_password


class CreateLinkedProfileHTTPTests(unittest.TestCase):
    def setUp(self):
        main.limiter.reset()

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        with self.Session() as db:
            companion = User(
                email="create-companion@example.com",
                password_hash=hash_password("CurrentPassword123!"),
                role="user",
                status=UserStatus.ACTIVE.value,
            )
            organizer = User(
                email="create-organizer@example.com",
                password_hash=hash_password("CurrentPassword123!"),
                role="partner",
                status=UserStatus.ACTIVE.value,
            )
            db.add_all([companion, organizer])
            db.commit()
            self.companion_id = companion.id
            self.organizer_id = organizer.id

        self.patches = [
            patch.object(main, "SessionLocal", self.Session),
            patch("backend.security.SessionLocal", self.Session),
            patch.object(main, "_audit"),
        ]

        for item in self.patches:
            item.start()

        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()

    def create_profile(self, user_id, **changes):
        payload = {
            "email": "new-linked@example.com",
            "current_password": "CurrentPassword123!",
            "new_password": "NewPassword123!",
            "dob": "1995-06-15",
            "accept_terms": True,
            "accept_privacy": True,
        }
        payload.update(changes)

        return self.client.post(
            "/auth/account-links/create-profile",
            headers={
                "Authorization": (
                    "Bearer " + create_access_token(user_id)
                )
            },
            json=payload,
        )

    def test_companion_creates_organizer(self):
        response = self.create_profile(self.companion_id)
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            created = db.query(User).filter(
                User.email == "new-linked@example.com"
            ).one()
            link = db.query(AccountLink).one()
            self.assertEqual(created.role, "partner")
            self.assertEqual(link.user_id, self.companion_id)
            self.assertEqual(link.partner_id, created.id)

    def test_created_profile_has_separate_revenuecat_identity(self):
        response = self.create_profile(self.companion_id)
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            companion = db.query(User).filter(
                User.id == self.companion_id
            ).one()

            organizer = db.query(User).filter(
                User.email == "new-linked@example.com"
            ).one()

            self.assertEqual(companion.role, "user")
            self.assertEqual(organizer.role, "partner")
            self.assertNotEqual(companion.id, organizer.id)

            companion_rc = companion.revenuecat_app_user_id
            organizer_rc = organizer.revenuecat_app_user_id

            self.assertIsNotNone(companion_rc)
            self.assertIsNotNone(organizer_rc)
            self.assertNotEqual(companion_rc, organizer_rc)

            for app_user_id in (companion_rc, organizer_rc):
                self.assertRegex(
                    app_user_id,
                    r"^usly_usr_[0-9a-f]{32}$",
                )

    def test_organizer_creates_companion(self):
        response = self.create_profile(self.organizer_id)
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            created = db.query(User).filter(
                User.email == "new-linked@example.com"
            ).one()
            link = db.query(AccountLink).one()
            self.assertEqual(created.role, "user")
            self.assertEqual(str(created.dob), "1995-06-15")
            self.assertEqual(link.user_id, created.id)
            self.assertEqual(link.partner_id, self.organizer_id)

    def test_rejects_invalid_current_password(self):
        response = self.create_profile(
            self.companion_id,
            current_password="IncorrectPassword123!",
        )
        self.assertEqual(response.status_code, 401, response.text)

    def test_rejects_missing_terms(self):
        response = self.create_profile(
            self.companion_id,
            accept_terms=False,
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_rejects_second_linked_profile(self):
        first = self.create_profile(self.companion_id)
        self.assertEqual(first.status_code, 200, first.text)

        second = self.create_profile(
            self.companion_id,
            email="another-linked@example.com",
        )
        self.assertEqual(second.status_code, 409, second.text)

    def test_rejects_existing_email_for_target_role(self):
        response = self.create_profile(
            self.companion_id,
            email="create-organizer@example.com",
        )
        self.assertEqual(response.status_code, 409, response.text)


    def _set_companion_google_sub(self, value):
        with self.Session() as db:
            user = db.get(User, self.companion_id)
            user.google_sub = value
            user.password_hash = None
            db.commit()

    def _assert_no_new_profile(self):
        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)
            self.assertEqual(db.query(User).count(), 2)

    def test_google_reauth_success(self):
        self._set_companion_google_sub("google-companion-123")

        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            return_value={"sub": "google-companion-123"},
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                method="google",
                id_token="valid-google-id-token-for-test",
            )

        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)
            self.assertEqual(db.query(User).count(), 3)

    def test_google_creates_passwordless_linked_organizer(self):
        self._set_companion_google_sub("google-companion-123")

        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            return_value={"sub": "google-companion-123"},
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                new_password=None,
                method="google",
                id_token="valid-google-id-token-for-test",
            )

        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            created = db.query(User).filter(
                User.email == "new-linked@example.com"
            ).one()

            self.assertEqual(created.role, "partner")
            self.assertIsNone(created.password_hash)
            self.assertIsNone(created.google_sub)
            self.assertNotEqual(
                companion.revenuecat_app_user_id,
                created.revenuecat_app_user_id,
            )

            link = db.query(AccountLink).one()
            self.assertEqual(link.user_id, companion.id)
            self.assertEqual(link.partner_id, created.id)

    def test_google_reauth_rejects_different_sub(self):
        self._set_companion_google_sub("google-companion-123")

        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            return_value={"sub": "different-google-user"},
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                method="google",
                id_token="different-google-id-token",
            )

        self.assertEqual(response.status_code, 401, response.text)
        self._assert_no_new_profile()

    def test_google_reauth_rejects_invalid_token(self):
        self._set_companion_google_sub("google-companion-123")

        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            side_effect=ValueError("Invalid token"),
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                method="google",
                id_token="invalid-google-id-token",
            )

        self.assertEqual(response.status_code, 401, response.text)
        self._assert_no_new_profile()

    def test_google_reauth_rejects_unlinked_provider(self):
        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            return_value={"sub": "google-companion-123"},
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                method="google",
                id_token="valid-google-id-token-for-test",
            )

        self.assertNotEqual(response.status_code, 200, response.text)
        self._assert_no_new_profile()


    def _set_companion_apple_sub(self, value):
        with self.Session() as db:
            user = db.get(User, self.companion_id)
            user.apple_sub = value
            user.password_hash = None
            db.commit()

    def _apple_create_profile(self, *, subject, exchanged_subject=None):
        from backend.apple_auth import AppleAuthError

        if exchanged_subject is None:
            exchanged_subject = subject

        with patch.dict(
            os.environ,
            {"APPLE_IOS_CLIENT_ID": "test.apple.client"},
        ), patch.object(
            main,
            "_verify_apple_auth_identity",
            return_value={
                "apple_sub": subject,
                "email": None,
                "email_verified": False,
                "audience": "test.apple.client",
            },
        ), patch.object(
            main,
            "exchange_apple_authorization_code",
            return_value={
                "id_token": "exchanged-apple-id-token",
                "refresh_token": "test-apple-refresh-token",
            },
        ), patch.object(
            main,
            "encrypt_secret",
            return_value="encrypted-test-refresh-token",
        ), patch.object(
            main,
            "verify_apple_identity_token",
            return_value={"sub": exchanged_subject},
        ):
            return self.create_profile(
                self.companion_id,
                current_password=None,
                method="apple",
                id_token="incoming-apple-id-token-long-enough",
                nonce="test-apple-nonce-123456",
                authorization_code="test-apple-code",
            )

    def test_apple_reauth_success(self):
        from backend.models import AppleAuthCredential

        self._set_companion_apple_sub("apple-companion-123")

        response = self._apple_create_profile(
            subject="apple-companion-123",
        )

        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)
            self.assertEqual(db.query(User).count(), 3)
            self.assertEqual(db.query(AppleAuthCredential).count(), 0)

            created = db.query(User).filter(
                User.email == "new-linked@example.com"
            ).one()

            self.assertIsNone(created.apple_sub)

    def test_apple_reauth_rejects_different_sub(self):
        self._set_companion_apple_sub("apple-companion-123")

        response = self._apple_create_profile(
            subject="different-apple-user",
        )

        self.assertEqual(response.status_code, 401, response.text)
        self._assert_no_new_profile()

    def test_apple_reauth_rejects_invalid_token(self):
        from backend.apple_auth import AppleAuthError

        self._set_companion_apple_sub("apple-companion-123")

        with patch.dict(
            os.environ,
            {"APPLE_IOS_CLIENT_ID": "test.apple.client"},
        ), patch.object(
            main,
            "_verify_apple_auth_identity",
            side_effect=AppleAuthError("invalid"),
        ):
            response = self.create_profile(
                self.companion_id,
                current_password=None,
                method="apple",
                id_token="invalid-apple-id-token-long-enough",
                nonce="test-apple-nonce-123456",
                authorization_code="test-apple-code",
            )

        self.assertNotEqual(response.status_code, 200, response.text)
        self._assert_no_new_profile()

    def test_apple_reauth_rejects_exchanged_subject(self):
        self._set_companion_apple_sub("apple-companion-123")

        response = self._apple_create_profile(
            subject="apple-companion-123",
            exchanged_subject="different-apple-user",
        )

        self.assertEqual(response.status_code, 401, response.text)
        self._assert_no_new_profile()

    def test_apple_reauth_rejects_unlinked_provider(self):
        response = self._apple_create_profile(
            subject="apple-companion-123",
        )

        self.assertNotEqual(response.status_code, 200, response.text)
        self._assert_no_new_profile()


if __name__ == "__main__":
    unittest.main()
