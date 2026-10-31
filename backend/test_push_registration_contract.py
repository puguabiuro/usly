import unittest

from backend.push_ownership_service import decide_push_registration

from backend.push_ownership_proof import (
    create_push_ownership_proof,
    verify_push_ownership_proof,
)



class PushRegistrationContractTests(unittest.TestCase):

    def setUp(self):
        self.proof, self.proof_hash = create_push_ownership_proof()

    def test_new_token(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=None,
                requesting_user=101,
                is_active=False,
                stored_proof_hash=None,
                supplied_proof=None,
            ),
            "CREATE",
        )

    def test_same_owner_valid_proof(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=101,
                is_active=True,
                stored_proof_hash=self.proof_hash,
                supplied_proof=self.proof,
            ),
            "REFRESH_CURRENT_OWNER",
        )

    def test_other_owner_active(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=202,
                is_active=True,
                stored_proof_hash=self.proof_hash,
                supplied_proof=None,
            ),
            "DENY_OTHER_OWNER",
        )

    def test_other_owner_inactive(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=202,
                is_active=False,
                stored_proof_hash=self.proof_hash,
                supplied_proof=None,
            ),
            "DENY_OTHER_OWNER",
        )

    def test_stale_proof(self):
        old_proof, _ = create_push_ownership_proof()
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=101,
                is_active=True,
                stored_proof_hash=self.proof_hash,
                supplied_proof=old_proof,
            ),
            "DENY_INVALID_PROOF",
        )

    def test_missing_proof(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=101,
                is_active=True,
                stored_proof_hash=self.proof_hash,
                supplied_proof=None,
            ),
            "DENY_MISSING_PROOF",
        )

    def test_legacy_owner_bootstrap(self):
        self.assertEqual(
            decide_push_registration(
                existing_owner=101,
                requesting_user=101,
                is_active=True,
                stored_proof_hash=None,
                supplied_proof=None,
            ),
            "BOOTSTRAP_LEGACY_OWNER",
        )


if __name__ == "__main__":
    unittest.main()
