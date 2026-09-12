import json
import unittest
from datetime import datetime, timedelta

from backend.store_entitlements import store_purchase_has_access


class PurchaseStub:
    def __init__(
        self,
        *,
        plan="plus",
        status="active",
        plan_expires_at=None,
        expires_at=None,
        revoked_at=None,
        gives_access=None,
    ):
        self.plan = plan
        self.status = status
        self.plan_expires_at = plan_expires_at
        self.expires_at = expires_at
        self.revoked_at = revoked_at
        self.raw_payload = (
            json.dumps({"gives_access": gives_access})
            if gives_access is not None
            else None
        )


class StoreEntitlementsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 12, 12, 0, 0)

    def test_paid_subscription_before_expiry_has_access(self):
        purchase = PurchaseStub(
            plan="plus",
            status="active",
            gives_access=True,
            plan_expires_at=self.now + timedelta(days=23),
        )
        self.assertTrue(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_cancelled_renewal_keeps_access_until_paid_period_ends(self):
        purchase = PurchaseStub(
            plan="plus",
            status="cancelled",
            gives_access=True,
            plan_expires_at=self.now + timedelta(days=23),
        )
        self.assertTrue(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_revenuecat_revocation_removes_access_before_expiry(self):
        purchase = PurchaseStub(
            plan="plus",
            status="cancelled",
            gives_access=False,
            plan_expires_at=self.now + timedelta(days=23),
        )
        self.assertFalse(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_expired_subscription_has_no_access(self):
        purchase = PurchaseStub(
            plan="plus",
            status="active",
            gives_access=True,
            plan_expires_at=self.now - timedelta(seconds=1),
        )
        self.assertFalse(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_revoked_purchase_has_no_access_even_before_expiry(self):
        purchase = PurchaseStub(
            plan="plus",
            status="active",
            gives_access=True,
            plan_expires_at=self.now + timedelta(days=23),
            revoked_at=self.now,
        )
        self.assertFalse(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_free_never_counts_as_paid_access(self):
        purchase = PurchaseStub(
            plan="free",
            status="active",
            gives_access=True,
            plan_expires_at=self.now + timedelta(days=23),
        )
        self.assertFalse(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_lifetime_purchase_uses_revenuecat_access(self):
        purchase = PurchaseStub(
            plan="premium",
            status="active",
            gives_access=True,
        )
        self.assertTrue(
            store_purchase_has_access(purchase, now=self.now)
        )

    def test_legacy_active_purchase_without_payload_still_works(self):
        purchase = PurchaseStub(
            plan="premium",
            status="active",
        )
        self.assertTrue(
            store_purchase_has_access(purchase, now=self.now)
        )


if __name__ == "__main__":
    unittest.main()
