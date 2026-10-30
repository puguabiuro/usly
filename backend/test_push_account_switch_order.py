"""Testy kolejności i własności tokenu push po zmianie kontraktu."""

import unittest

from backend.test_push_registration_http import PushRegistrationHTTPTests


class PushAccountSwitchOrderTests(PushRegistrationHTTPTests):
    """Testy HTTP z prawdziwą logiką rejestracji i izolowaną SQLite."""

    def test_delayed_old_registration_cannot_reclaim_token(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)

        proof = self.data(first)["push_ownership_proof"]
        self.assertTrue(proof)

        from backend.push_ownership_service import transfer_push_token

        with self.Session() as db:
            rotated = transfer_push_token(
                db,
                token=self.token,
                source_user_id=self.a_id,
                target_user_id=self.b_id,
                current_proof=proof,
                transfer_authorized=True,
            )
            db.commit()

        self.assertTrue(rotated)

        delayed = self.register(self.a_id, proof)
        self.assertEqual(delayed.status_code, 409, delayed.text)

        refreshed = self.register(self.b_id, rotated)
        self.assertEqual(refreshed.status_code, 200, refreshed.text)

    def test_authorized_transfer_a_b_a(self):
        first = self.register(self.a_id)
        self.assertEqual(first.status_code, 200, first.text)

        proof_a = self.data(first)["push_ownership_proof"]

        from backend.push_ownership_service import transfer_push_token
        from backend.models import DevicePushToken

        with self.Session() as db:
            proof_b = transfer_push_token(
                db,
                token=self.token,
                source_user_id=self.a_id,
                target_user_id=self.b_id,
                current_proof=proof_a,
                transfer_authorized=True,
            )
            db.commit()

        with self.Session() as db:
            new_proof_a = transfer_push_token(
                db,
                token=self.token,
                source_user_id=self.b_id,
                target_user_id=self.a_id,
                current_proof=proof_b,
                transfer_authorized=True,
            )
            db.commit()

        self.assertTrue(new_proof_a)
        self.assertNotEqual(proof_a, new_proof_a)

        with self.Session() as db:
            row = db.query(DevicePushToken).filter_by(
                token=self.token
            ).one()
            self.assertEqual(row.user_id, self.a_id)
            self.assertTrue(row.is_active)

        refreshed = self.register(self.a_id, new_proof_a)
        self.assertEqual(refreshed.status_code, 200, refreshed.text)


if __name__ == "__main__":
    unittest.main()
