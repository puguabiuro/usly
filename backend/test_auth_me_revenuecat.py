"""Test kontraktu RevenueCat App User ID w odpowiedzi /auth/me."""

import unittest
from types import SimpleNamespace

from backend.main import auth_me


class AuthMeRevenueCatContractTests(unittest.TestCase):
    def test_returns_backend_revenuecat_app_user_id(self) -> None:
        user = SimpleNamespace(
            id=123,
            email="test@example.com",
            role="user",
            revenuecat_app_user_id="usly_usr_0123456789abcdef0123456789abcdef",
            admin_display_name=None,
            admin_level=None,
            mfa_enabled=False,
            email_verified_at=None,
        )

        response = auth_me(current_user=user)

        self.assertIn("revenuecat_app_user_id", response)
        self.assertEqual(
            response["revenuecat_app_user_id"],
            user.revenuecat_app_user_id,
        )


if __name__ == "__main__":
    unittest.main()
