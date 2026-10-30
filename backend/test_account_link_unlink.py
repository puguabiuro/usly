"""Izolowane testy HTTP odłączania kont USLY."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main
from backend.models import Base, User, AccountLink, UserStatus
from backend.security import create_access_token, hash_password


class AccountUnlinkHTTPTests(unittest.TestCase):
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
                email="unlink-companion@example.com",
                password_hash=hash_password("CompanionPassword123!"),
                role="user",
                status=UserStatus.ACTIVE.value,
            )
            organizer = User(
                email="unlink-organizer@example.com",
                password_hash=hash_password("OrganizerPassword123!"),
                role="partner",
                status=UserStatus.ACTIVE.value,
            )
            admin = User(
                email="unlink-admin@example.com",
                password_hash=hash_password("AdminPassword123!"),
                role="admin",
                status=UserStatus.ACTIVE.value,
            )
            db.add_all([companion, organizer, admin])
            db.flush()

            db.add(
                AccountLink(
                    user_id=companion.id,
                    partner_id=organizer.id,
                )
            )
            db.commit()

            self.companion_id = companion.id
            self.organizer_id = organizer.id
            self.admin_id = admin.id
            self.companion_rc = companion.revenuecat_app_user_id
            self.organizer_rc = organizer.revenuecat_app_user_id

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

    def unlink(self, user_id, password):
        return self.client.post(
            "/auth/account-links/unlink",
            headers={
                "Authorization": (
                    "Bearer " + create_access_token(user_id)
                )
            },
            json={
                "method": "password",
                "current_password": password,
            },
        )

    def assert_accounts_unchanged(self):
        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.status,
                UserStatus.ACTIVE.value,
            )
            self.assertEqual(
                organizer.status,
                UserStatus.ACTIVE.value,
            )
            self.assertEqual(companion.role, "user")
            self.assertEqual(organizer.role, "partner")
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertIsNotNone(companion.password_hash)
            self.assertIsNotNone(organizer.password_hash)

    def test_companion_unlinks_organizer(self):
        response = self.unlink(
            self.companion_id,
            "CompanionPassword123!",
        )
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)

        self.assert_accounts_unchanged()

    def test_organizer_unlinks_companion(self):
        response = self.unlink(
            self.organizer_id,
            "OrganizerPassword123!",
        )
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)

        self.assert_accounts_unchanged()

    def test_rejects_wrong_password(self):
        response = self.unlink(
            self.companion_id,
            "WrongPassword123!",
        )
        self.assertEqual(response.status_code, 401, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)

        self.assert_accounts_unchanged()

    def test_rejects_missing_authentication(self):
        response = self.client.post(
            "/auth/account-links/unlink",
            json={
                "method": "password",
                "current_password": "CompanionPassword123!",
            },
        )
        self.assertEqual(response.status_code, 401)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)

    def test_rejects_admin(self):
        response = self.unlink(
            self.admin_id,
            "AdminPassword123!",
        )
        self.assertEqual(response.status_code, 403, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)

    def test_rejects_when_not_linked(self):
        first = self.unlink(
            self.companion_id,
            "CompanionPassword123!",
        )
        self.assertEqual(first.status_code, 200, first.text)

        second = self.unlink(
            self.companion_id,
            "CompanionPassword123!",
        )
        self.assertEqual(second.status_code, 404, second.text)

        self.assert_accounts_unchanged()


    def _set_provider_identity(self, provider, subject):
        with self.Session() as db:
            user = db.get(User, self.companion_id)
            if provider == "google":
                user.google_sub = subject
            elif provider == "apple":
                user.apple_sub = subject
            else:
                raise ValueError("Unsupported provider")
            user.password_hash = None
            db.commit()

    def _unlink_with_payload(self, **payload):
        return self.client.post(
            "/auth/account-links/unlink",
            headers={
                "Authorization": (
                    "Bearer " + create_access_token(self.companion_id)
                )
            },
            json=payload,
        )

    def _assert_link_preserved(self):
        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 1)

    def _google_unlink(self, subject, *, invalid=False):
        import os

        with patch.dict(
            os.environ,
            {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
        ), patch.object(
            main.google_id_token,
            "verify_oauth2_token",
            side_effect=ValueError("Invalid token") if invalid else None,
            return_value=None if invalid else {"sub": subject},
        ):
            return self._unlink_with_payload(
                method="google",
                id_token="google-test-identity-token-long-enough",
            )

    def test_google_unlink_success(self):
        self._set_provider_identity("google", "google-companion-123")

        response = self._google_unlink("google-companion-123")
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)

        self.assert_accounts_unchanged_social()

    def test_google_unlink_rejects_foreign_identity(self):
        self._set_provider_identity("google", "google-companion-123")

        response = self._google_unlink("another-google-person")
        self.assertEqual(response.status_code, 401, response.text)
        self._assert_link_preserved()

    def test_google_unlink_rejects_invalid_token(self):
        self._set_provider_identity("google", "google-companion-123")

        response = self._google_unlink(
            "google-companion-123",
            invalid=True,
        )
        self.assertEqual(response.status_code, 401, response.text)
        self._assert_link_preserved()

    def _apple_unlink(self, subject, *, exchanged_subject=None):
        import os

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
            "verify_apple_identity_token",
            return_value={"sub": exchanged_subject},
        ):
            return self._unlink_with_payload(
                method="apple",
                id_token="incoming-apple-id-token-long-enough",
                nonce="test-apple-nonce-123456",
                authorization_code="test-apple-code",
            )

    def test_apple_unlink_success(self):
        self._set_provider_identity("apple", "apple-companion-123")

        response = self._apple_unlink("apple-companion-123")
        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)

        self.assert_accounts_unchanged_social()

    def test_apple_unlink_rejects_foreign_identity(self):
        self._set_provider_identity("apple", "apple-companion-123")

        response = self._apple_unlink("another-apple-person")
        self.assertEqual(response.status_code, 401, response.text)
        self._assert_link_preserved()

    def test_apple_unlink_rejects_exchanged_identity(self):
        self._set_provider_identity("apple", "apple-companion-123")

        response = self._apple_unlink(
            "apple-companion-123",
            exchanged_subject="another-apple-person",
        )
        self.assertEqual(response.status_code, 401, response.text)
        self._assert_link_preserved()

    def assert_accounts_unchanged_social(self):
        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(companion.status, UserStatus.ACTIVE.value)
            self.assertEqual(organizer.status, UserStatus.ACTIVE.value)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertIsNotNone(organizer.password_hash)


    def _assert_push_tokens_unchanged_after_unlink(self, source_role):
        from backend.models import DevicePushToken

        with self.Session() as db:
            db.add_all([
                DevicePushToken(
                    user_id=self.companion_id,
                    token="companion-device-push-token",
                    platform="android",
                    device_id="companion-device",
                    ownership_proof_hash="companion-proof-hash",
                    is_active=True,
                ),
                DevicePushToken(
                    user_id=self.organizer_id,
                    token="organizer-device-push-token",
                    platform="android",
                    device_id="organizer-device",
                    ownership_proof_hash="organizer-proof-hash",
                    is_active=True,
                ),
            ])
            db.commit()

        if source_role == "user":
            response = self.unlink(
                self.companion_id,
                "CompanionPassword123!",
            )
        else:
            response = self.unlink(
                self.organizer_id,
                "OrganizerPassword123!",
            )

        self.assertEqual(response.status_code, 200, response.text)

        with self.Session() as db:
            self.assertEqual(db.query(AccountLink).count(), 0)

            tokens = {
                item.token: item
                for item in db.query(DevicePushToken).all()
            }

            self.assertEqual(len(tokens), 2)

            companion_token = tokens["companion-device-push-token"]
            organizer_token = tokens["organizer-device-push-token"]

            self.assertEqual(
                companion_token.user_id,
                self.companion_id,
            )
            self.assertEqual(
                organizer_token.user_id,
                self.organizer_id,
            )
            self.assertTrue(companion_token.is_active)
            self.assertTrue(organizer_token.is_active)
            self.assertEqual(
                companion_token.ownership_proof_hash,
                "companion-proof-hash",
            )
            self.assertEqual(
                organizer_token.ownership_proof_hash,
                "organizer-proof-hash",
            )

        self.assert_accounts_unchanged()

    def test_unlink_from_companion_preserves_both_push_tokens(self):
        self._assert_push_tokens_unchanged_after_unlink("user")

    def test_unlink_from_organizer_preserves_both_push_tokens(self):
        self._assert_push_tokens_unchanged_after_unlink("partner")


if __name__ == "__main__":
    unittest.main()
