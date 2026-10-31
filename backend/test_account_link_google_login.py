import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import main
from backend.models import Base, User, AccountLink, UserStatus
from backend.security import get_current_user


class LinkedGoogleLoginHTTPTests(unittest.TestCase):
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
                email="google-companion-login@example.com",
                password_hash=None,
                google_sub="google-companion-login-sub",
                role="user",
                status=UserStatus.ACTIVE.value,
            )
            organizer = User(
                email="google-organizer-login@example.com",
                password_hash=None,
                google_sub=None,
                role="partner",
                status=UserStatus.ACTIVE.value,
            )
            db.add_all([companion, organizer])
            db.flush()
            db.add(AccountLink(
                user_id=companion.id,
                partner_id=organizer.id,
            ))
            db.commit()

            self.companion_id = companion.id
            self.organizer_id = organizer.id
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

    def test_google_login_to_linked_passwordless_organizer(self):
        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["user"]["id"], self.organizer_id)
        self.assertEqual(data["user"]["role"], "partner")

        token = data["access_token"]
        self.assertTrue(token)

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(
            me.json()["id"],
            self.organizer_id,
        )

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertNotEqual(
                self.companion_rc,
                self.organizer_rc,
            )
            self.assertEqual(db.query(AccountLink).count(), 1)


    def test_google_login_rejects_missing_account_link(self):
        with self.Session() as db:
            db.query(AccountLink).delete()
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(
            response.json()["error"]["code"],
            "INSUFFICIENT_ROLE",
        )

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertEqual(db.query(AccountLink).count(), 0)


    def test_google_login_rejects_inactive_linked_organizer(self):
        with self.Session() as db:
            organizer = db.get(User, self.organizer_id)
            organizer.status = "inactive"
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(
            response.json()["error"]["code"],
            "INSUFFICIENT_ROLE",
        )

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(organizer.status, "inactive")
            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertEqual(db.query(AccountLink).count(), 1)


    def test_google_login_from_organizer_to_linked_companion(self):
        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            companion.google_sub = None
            organizer.google_sub = "google-organizer-login-sub"
            db.commit()

        claims = {
            "sub": "google-organizer-login-sub",
            "email": "google-organizer-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "user",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]

        self.assertEqual(data["user"]["id"], self.companion_id)
        self.assertEqual(data["user"]["role"], "user")

        token = data["access_token"]
        self.assertTrue(token)

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["id"], self.companion_id)
        self.assertEqual(me.json()["role"], "user")

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertIsNone(companion.google_sub)
            self.assertIsNone(companion.password_hash)
            self.assertEqual(
                organizer.google_sub,
                "google-organizer-login-sub",
            )
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertNotEqual(
                companion.revenuecat_app_user_id,
                organizer.revenuecat_app_user_id,
            )

            link = db.query(AccountLink).one()
            self.assertEqual(link.user_id, self.companion_id)
            self.assertEqual(link.partner_id, self.organizer_id)


    def test_google_login_rejects_identity_conflict(self):
        with self.Session() as db:
            db.query(AccountLink).delete()

            organizer = db.get(User, self.organizer_id)
            organizer.email = "google-companion-login@example.com"
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(
            response.json()["error"]["code"],
            "GOOGLE_ACCOUNT_CONFLICT",
        )

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertEqual(db.query(AccountLink).count(), 0)


    def test_google_login_preserves_two_independent_google_identities(self):
        with self.Session() as db:
            organizer = db.get(User, self.organizer_id)
            organizer.google_sub = "google-organizer-own-sub"
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]

        self.assertEqual(data["user"]["id"], self.organizer_id)
        self.assertEqual(data["user"]["role"], "partner")

        token = data["access_token"]
        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["id"], self.organizer_id)

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertEqual(
                organizer.google_sub,
                "google-organizer-own-sub",
            )
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertNotEqual(
                companion.revenuecat_app_user_id,
                organizer.revenuecat_app_user_id,
            )

            link = db.query(AccountLink).one()
            self.assertEqual(link.user_id, self.companion_id)
            self.assertEqual(link.partner_id, self.organizer_id)


    def test_google_login_to_linked_organizer_with_shared_email(self):
        with self.Session() as db:
            organizer = db.get(User, self.organizer_id)
            organizer.email = "google-companion-login@example.com"
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]

        self.assertEqual(data["user"]["id"], self.organizer_id)
        self.assertEqual(data["user"]["role"], "partner")

        token = data["access_token"]
        self.assertTrue(token)

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["id"], self.organizer_id)
        self.assertEqual(me.json()["role"], "partner")

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(
                companion.email,
                organizer.email,
            )
            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)
            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertNotEqual(
                companion.revenuecat_app_user_id,
                organizer.revenuecat_app_user_id,
            )

            link = db.query(AccountLink).one()
            self.assertEqual(link.user_id, self.companion_id)
            self.assertEqual(link.partner_id, self.organizer_id)


    def test_google_login_rejects_inactive_identity_owner(self):
        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            companion.status = "inactive"
            db.commit()

        claims = {
            "sub": "google-companion-login-sub",
            "email": "google-companion-login@example.com",
            "email_verified": True,
        }

        with (
            patch.dict(
                os.environ,
                {"GOOGLE_WEB_CLIENT_ID": "usly-test-client"},
            ),
            patch.object(
                main.google_id_token,
                "verify_oauth2_token",
                return_value=claims,
            ),
        ):
            response = self.client.post(
                "/auth/google",
                json={
                    "id_token": "isolated-google-login-token-123456",
                    "mode": "login",
                    "expected_role": "partner",
                },
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(
            response.json()["error"]["code"],
            "ACCOUNT_INACTIVE",
        )

        with self.Session() as db:
            companion = db.get(User, self.companion_id)
            organizer = db.get(User, self.organizer_id)

            self.assertEqual(companion.status, "inactive")
            self.assertEqual(
                companion.google_sub,
                "google-companion-login-sub",
            )
            self.assertEqual(organizer.status, UserStatus.ACTIVE.value)
            self.assertIsNone(organizer.google_sub)
            self.assertIsNone(organizer.password_hash)

            self.assertEqual(
                companion.revenuecat_app_user_id,
                self.companion_rc,
            )
            self.assertEqual(
                organizer.revenuecat_app_user_id,
                self.organizer_rc,
            )
            self.assertEqual(db.query(AccountLink).count(), 1)


if __name__ == "__main__":
    unittest.main()
