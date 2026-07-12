"""Testy tożsamości użytkownika USLY dla RevenueCat."""

import re
import unittest

from backend.revenuecat_identity import (
    REVENUECAT_APP_USER_ID_LENGTH,
    REVENUECAT_APP_USER_ID_PREFIX,
    generate_revenuecat_app_user_id,
)


class RevenueCatIdentityTests(unittest.TestCase):
    def test_generates_expected_identifier_format(self) -> None:
        app_user_id = generate_revenuecat_app_user_id()

        self.assertEqual(len(app_user_id), REVENUECAT_APP_USER_ID_LENGTH)
        self.assertTrue(
            app_user_id.startswith(REVENUECAT_APP_USER_ID_PREFIX)
        )
        self.assertRegex(
            app_user_id,
            re.compile(r"^usly_usr_[0-9a-f]{32}$"),
        )

    def test_generates_unique_identifiers(self) -> None:
        identifiers = {
            generate_revenuecat_app_user_id()
            for _ in range(1000)
        }

        self.assertEqual(len(identifiers), 1000)

    def test_identifier_contains_no_hyphens_or_whitespace(self) -> None:
        app_user_id = generate_revenuecat_app_user_id()

        self.assertNotIn("-", app_user_id)
        self.assertFalse(any(character.isspace() for character in app_user_id))


if __name__ == "__main__":
    unittest.main()
