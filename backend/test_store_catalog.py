"""Testy centralnego katalogu produktów sklepowych USLY."""

import unittest

from backend.store_catalog import get_store_product_id_for_plan


class StoreProductIdForPlanTests(unittest.TestCase):
    def test_returns_user_product_id(self):
        self.assertEqual(
            get_store_product_id_for_plan("user", "premium"),
            "usly_user_premium:monthly",
        )

    def test_returns_partner_product_id(self):
        self.assertEqual(
            get_store_product_id_for_plan("partner", "pro"),
            "usly_partner_pro:monthly",
        )

    def test_returns_none_for_free_and_unknown_plan(self):
        self.assertIsNone(
            get_store_product_id_for_plan("user", "free")
        )
        self.assertIsNone(
            get_store_product_id_for_plan("user", "unknown")
        )


if __name__ == "__main__":
    unittest.main()
