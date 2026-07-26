import time
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from jose.utils import base64url_encode

from backend.apple_auth import (
    APPLE_ISSUER,
    AppleAuthKeyError,
    AppleAuthTokenError,
    verify_apple_identity_token,
)


IOS_AUDIENCE = "com.usly.app"
WEB_AUDIENCE = "com.usly.app.signin"
TEST_KID = "usly-test-apple-key"


def _rsa_public_jwk(private_key, kid=TEST_KID):
    numbers = private_key.public_key().public_numbers()

    exponent = numbers.e.to_bytes(
        (numbers.e.bit_length() + 7) // 8,
        "big",
    )
    modulus = numbers.n.to_bytes(
        (numbers.n.bit_length() + 7) // 8,
        "big",
    )

    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": base64url_encode(modulus).decode("ascii"),
        "e": base64url_encode(exponent).decode("ascii"),
    }


class AppleIdentityTokenVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.public_jwk = _rsa_public_jwk(cls.private_key)

    def make_token(
        self,
        *,
        audience=IOS_AUDIENCE,
        subject="apple-user-123",
        nonce=None,
        issuer=APPLE_ISSUER,
        kid=TEST_KID,
        expires_in=300,
    ):
        claims = {
            "iss": issuer,
            "aud": audience,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
            "sub": subject,
            "email": "apple-test@example.com",
            "email_verified": "true",
        }

        if nonce is not None:
            claims["nonce"] = nonce

        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        return jwt.encode(
            claims,
            private_key_pem,
            algorithm="RS256",
            headers={"kid": kid},
        )

    def verify_with_mocked_jwks(
        self,
        token,
        *,
        allowed_audiences=(IOS_AUDIENCE, WEB_AUDIENCE),
        expected_nonce=None,
    ):
        with patch(
            "backend.apple_auth._fetch_apple_jwks",
            return_value=[self.public_jwk],
        ):
            return verify_apple_identity_token(
                token,
                allowed_audiences=allowed_audiences,
                expected_nonce=expected_nonce,
            )

    def test_accepts_valid_ios_audience(self):
        token = self.make_token(audience=IOS_AUDIENCE)

        claims = self.verify_with_mocked_jwks(token)

        self.assertEqual(claims["sub"], "apple-user-123")
        self.assertEqual(claims["aud"], IOS_AUDIENCE)

    def test_accepts_valid_web_audience(self):
        token = self.make_token(audience=WEB_AUDIENCE)

        claims = self.verify_with_mocked_jwks(token)

        self.assertEqual(claims["aud"], WEB_AUDIENCE)

    def test_rejects_invalid_audience(self):
        token = self.make_token(audience="com.invalid.app")

        with self.assertRaises(AppleAuthTokenError):
            self.verify_with_mocked_jwks(token)

    def test_accepts_matching_nonce(self):
        token = self.make_token(nonce="nonce-123")

        claims = self.verify_with_mocked_jwks(
            token,
            expected_nonce="nonce-123",
        )

        self.assertEqual(claims["nonce"], "nonce-123")

    def test_rejects_wrong_nonce(self):
        token = self.make_token(nonce="nonce-from-token")

        with self.assertRaises(AppleAuthTokenError):
            self.verify_with_mocked_jwks(
                token,
                expected_nonce="different-nonce",
            )

    def test_rejects_missing_subject(self):
        token = self.make_token(subject="")

        with self.assertRaises(AppleAuthTokenError):
            self.verify_with_mocked_jwks(token)

    def test_rejects_expired_token(self):
        token = self.make_token(expires_in=-60)

        with self.assertRaises(AppleAuthTokenError):
            self.verify_with_mocked_jwks(token)

    def test_rejects_invalid_issuer(self):
        token = self.make_token(
            issuer="https://example.invalid",
        )

        with self.assertRaises(AppleAuthTokenError):
            self.verify_with_mocked_jwks(token)

    def test_rejects_unknown_kid_after_refresh_attempt(self):
        token = self.make_token(kid="unknown-kid")

        with patch(
            "backend.apple_auth._fetch_apple_jwks",
            return_value=[self.public_jwk],
        ) as mocked_fetch:
            with self.assertRaises(AppleAuthKeyError):
                verify_apple_identity_token(
                    token,
                    allowed_audiences=(IOS_AUDIENCE, WEB_AUDIENCE),
                )

        self.assertEqual(mocked_fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
