"""Izolowane testy HTTP przełączania kont USLY."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.database import Base
from backend.models import User, UserRole, UserStatus, AccountLink
from backend.security import create_access_token
from backend import main


class AccountLinkHTTPTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(connection, record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()

        self.companion = User(
            email=f"http-companion-{id(self)}@example.test",
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
        )
        self.organizer = User(
            email=f"http-organizer-{id(self)}@example.test",
            role=UserRole.PARTNER.value,
            status=UserStatus.ACTIVE.value,
        )

        self.db.add_all([self.companion, self.organizer])
        self.db.commit()

        self.companion_id = self.companion.id
        self.organizer_id = self.organizer.id

        # Oba moduły korzystają z tej samej bazy testowej.
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

        self.db.rollback()
        self.db.close()

    def headers(self, user_id):
        return {
            "Authorization": f"Bearer {create_access_token(user_id)}"
        }

    def link_accounts(self):
        self.db.add(
            AccountLink(
                user_id=self.companion_id,
                partner_id=self.organizer_id,
            )
        )
        self.db.commit()

    def switch(self, source_id, target_id):
        return self.client.post(
            "/auth/account-links/switch",
            headers=self.headers(source_id),
            json={"target_user_id": target_id},
        )

    def test_requires_authentication(self):
        response = self.client.post(
            "/auth/account-links/switch",
            json={"target_user_id": self.organizer_id},
        )
        self.assertEqual(response.status_code, 401)

    def test_rejects_unlinked_account(self):
        response = self.switch(
            self.companion_id,
            self.organizer_id,
        )
        self.assertEqual(response.status_code, 403)

    def test_switch_companion_to_organizer(self):
        self.link_accounts()

        response = self.switch(
            self.companion_id,
            self.organizer_id,
        )
        self.assertEqual(response.status_code, 200, response.text)

        payload = response.json()
        data = payload.get("data", payload)

        token = data["access_token"]

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(me.status_code, 200, me.text)

        me_payload = me.json()
        me_data = me_payload.get("data", me_payload)

        self.assertEqual(me_data["id"], self.organizer_id)

    def test_switch_organizer_to_companion(self):
        self.link_accounts()

        response = self.switch(
            self.organizer_id,
            self.companion_id,
        )
        self.assertEqual(response.status_code, 200, response.text)

        payload = response.json()
        data = payload.get("data", payload)

        token = data["access_token"]

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(me.status_code, 200, me.text)

        me_payload = me.json()
        me_data = me_payload.get("data", me_payload)

        self.assertEqual(me_data["id"], self.companion_id)


    def test_rejects_foreign_account_when_already_linked(self):
        self.link_accounts()

        foreign_organizer = User(
            email=f"foreign-organizer-{id(self)}@example.test",
            role=UserRole.PARTNER.value,
            status=UserStatus.ACTIVE.value,
        )
        self.db.add(foreign_organizer)
        self.db.commit()

        response = self.switch(
            self.companion_id,
            foreign_organizer.id,
        )

        self.assertEqual(response.status_code, 403, response.text)

        # Prawidłowe powiązanie musi pozostać nienaruszone.
        valid_response = self.switch(
            self.companion_id,
            self.organizer_id,
        )
        self.assertEqual(
            valid_response.status_code,
            200,
            valid_response.text,
        )


if __name__ == "__main__":
    unittest.main()
