"""Testy trwałego uprawnienia Premium Lifetime z kodu USLY95."""

from __future__ import annotations

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.promo_entitlements import has_usly95_lifetime
from backend.models import PromoCampaign, PromoRedemption, User


class Usly95LifetimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.user = User(
            email=f"usly95-{id(self)}@example.com",
            password_hash="test",
            role="user",
            revenuecat_app_user_id=f"usly_usr_usly95_{id(self)}",
        )
        self.db.add(self.user)
        self.db.flush()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def create_campaign(self, *, code: str) -> PromoCampaign:
        campaign = PromoCampaign(
            code=code,
            name=f"Test {code}",
            target_role="user",
            benefit_type="discount_percent",
            status="active",
            uses_count=0,
        )
        self.db.add(campaign)
        self.db.flush()
        return campaign

    def create_redemption(
        self,
        *,
        campaign: PromoCampaign,
        status: str,
    ) -> None:
        redemption = PromoRedemption(
            campaign_id=campaign.id,
            user_id=self.user.id,
            platform="ios",
            status=status,
            created_at=datetime(2026, 9, 4, 12, 0),
            activated_at=(
                datetime(2026, 9, 4, 12, 0)
                if status == "activated"
                else None
            ),
        )
        self.db.add(redemption)
        self.db.flush()

    def test_activated_usly95_grants_lifetime(self) -> None:
        campaign = self.create_campaign(code="USLY95")
        self.create_redemption(
            campaign=campaign,
            status="activated",
        )

        self.assertTrue(
            has_usly95_lifetime(
                self.db,
                self.user.id,
            )
        )

    def test_reserved_usly95_does_not_grant_lifetime(self) -> None:
        campaign = self.create_campaign(code="USLY95")
        self.create_redemption(
            campaign=campaign,
            status="reserved",
        )

        self.assertFalse(
            has_usly95_lifetime(
                self.db,
                self.user.id,
            )
        )

    def test_other_activated_campaign_does_not_grant_lifetime(self) -> None:
        campaign = self.create_campaign(code="OTHER95")
        self.create_redemption(
            campaign=campaign,
            status="activated",
        )

        self.assertFalse(
            has_usly95_lifetime(
                self.db,
                self.user.id,
            )
        )


if __name__ == "__main__":
    unittest.main()
