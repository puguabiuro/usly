"""Testy reguł własności tokenów push USLY."""

import unittest

from backend.push_ownership import (
    PushOwnershipAction as Action,
    PushOwnershipError,
    validate_push_ownership_transition as validate,
)


class PushOwnershipRulesTests(unittest.TestCase):

    def test_first_registration(self):
        self.assertTrue(validate(
            current_owner_id=None,
            requesting_user_id=101,
            action=Action.REGISTER_CURRENT_OWNER,
            authorization_verified=False,
        ))

    def test_current_owner_can_register_again(self):
        self.assertTrue(validate(
            current_owner_id=101,
            requesting_user_id=101,
            action=Action.REGISTER_CURRENT_OWNER,
            authorization_verified=False,
        ))

    def test_other_account_cannot_register_over_owner(self):
        with self.assertRaises(PushOwnershipError):
            validate(
                current_owner_id=101,
                requesting_user_id=202,
                action=Action.REGISTER_CURRENT_OWNER,
                authorization_verified=False,
            )

    def test_switch_transfer_requires_authorization(self):
        with self.assertRaises(PushOwnershipError):
            validate(
                current_owner_id=101,
                requesting_user_id=202,
                action=Action.TRANSFER_ON_ACCOUNT_SWITCH,
                authorization_verified=False,
            )

    def test_authorized_switch_transfer(self):
        self.assertTrue(validate(
            current_owner_id=101,
            requesting_user_id=202,
            action=Action.TRANSFER_ON_ACCOUNT_SWITCH,
            authorization_verified=True,
        ))

    def test_authorized_return_to_previous_profile(self):
        self.assertTrue(validate(
            current_owner_id=202,
            requesting_user_id=101,
            action=Action.TRANSFER_ON_ACCOUNT_SWITCH,
            authorization_verified=True,
        ))

    def test_new_login_transfer_requires_authorization(self):
        with self.assertRaises(PushOwnershipError):
            validate(
                current_owner_id=101,
                requesting_user_id=303,
                action=Action.TRANSFER_ON_NEW_LOGIN,
                authorization_verified=False,
            )

    def test_other_account_cannot_unregister(self):
        with self.assertRaises(PushOwnershipError):
            validate(
                current_owner_id=202,
                requesting_user_id=101,
                action=Action.UNREGISTER_CURRENT_OWNER,
                authorization_verified=False,
            )

    def test_current_owner_can_unregister(self):
        self.assertTrue(validate(
            current_owner_id=202,
            requesting_user_id=202,
            action=Action.UNREGISTER_CURRENT_OWNER,
            authorization_verified=False,
        ))


if __name__ == "__main__":
    unittest.main()
