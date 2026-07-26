from __future__ import annotations

import time
from threading import Lock
from typing import Any, Iterable

import requests
from jose import JWTError, jwk, jwt


APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_JWKS_CACHE_TTL_SECONDS = 6 * 60 * 60
APPLE_JWKS_HTTP_TIMEOUT_SECONDS = 5


class AppleAuthError(Exception):
    """Base error for Apple identity-token verification."""


class AppleAuthKeyError(AppleAuthError):
    """Apple public signing key could not be resolved."""


class AppleAuthTokenError(AppleAuthError):
    """Apple identity token is invalid."""


_jwks_cache: dict[str, Any] = {
    "fetched_at": 0.0,
    "keys": [],
}
_jwks_lock = Lock()


def _fetch_apple_jwks(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    now = time.monotonic()

    with _jwks_lock:
        cached_keys = _jwks_cache.get("keys") or []
        fetched_at = float(_jwks_cache.get("fetched_at") or 0.0)

        if (
            not force_refresh
            and cached_keys
            and now - fetched_at < APPLE_JWKS_CACHE_TTL_SECONDS
        ):
            return list(cached_keys)

        try:
            response = requests.get(
                APPLE_JWKS_URL,
                timeout=APPLE_JWKS_HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise AppleAuthKeyError(
                "Could not fetch Apple public signing keys."
            ) from exc

        keys = payload.get("keys") if isinstance(payload, dict) else None

        if not isinstance(keys, list) or not keys:
            raise AppleAuthKeyError(
                "Apple public signing keys response is invalid."
            )

        normalized_keys = [
            key
            for key in keys
            if isinstance(key, dict)
            and isinstance(key.get("kid"), str)
            and key.get("kid")
        ]

        if not normalized_keys:
            raise AppleAuthKeyError(
                "Apple public signing keys response contains no usable keys."
            )

        _jwks_cache["keys"] = normalized_keys
        _jwks_cache["fetched_at"] = now

        return list(normalized_keys)


def _find_apple_signing_key(kid: str) -> dict[str, Any]:
    for force_refresh in (False, True):
        keys = _fetch_apple_jwks(force_refresh=force_refresh)

        for key in keys:
            if key.get("kid") == kid:
                return key

    raise AppleAuthKeyError(
        "No matching Apple public signing key was found."
    )


def _normalize_audiences(audiences: Iterable[str]) -> set[str]:
    return {
        str(audience).strip()
        for audience in audiences
        if str(audience).strip()
    }


def verify_apple_identity_token(
    identity_token: str,
    *,
    allowed_audiences: Iterable[str],
    expected_nonce: str | None = None,
) -> dict[str, Any]:
    token = str(identity_token or "").strip()

    if not token:
        raise AppleAuthTokenError("Apple identity token is missing.")

    audiences = _normalize_audiences(allowed_audiences)

    if not audiences:
        raise AppleAuthTokenError(
            "No allowed Apple audiences were configured."
        )

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AppleAuthTokenError(
            "Apple identity token header is invalid."
        ) from exc

    kid = str(header.get("kid") or "").strip()
    algorithm = str(header.get("alg") or "").strip()

    if not kid or algorithm != "RS256":
        raise AppleAuthTokenError(
            "Apple identity token uses an invalid signing header."
        )

    signing_jwk = _find_apple_signing_key(kid)

    try:
        signing_key = jwk.construct(signing_jwk, algorithm="RS256")
        public_key_pem = signing_key.to_pem()

        claims = jwt.decode(
            token,
            public_key_pem,
            algorithms=["RS256"],
            issuer=APPLE_ISSUER,
            options={
                "verify_aud": False,
                "verify_exp": True,
                "verify_signature": True,
            },
        )
    except (JWTError, ValueError, TypeError) as exc:
        raise AppleAuthTokenError(
            "Apple identity token verification failed."
        ) from exc

    audience_claim = claims.get("aud")

    if isinstance(audience_claim, str):
        token_audiences = {audience_claim}
    elif isinstance(audience_claim, list):
        token_audiences = {
            str(value)
            for value in audience_claim
            if isinstance(value, str)
        }
    else:
        token_audiences = set()

    if not token_audiences.intersection(audiences):
        raise AppleAuthTokenError(
            "Apple identity token audience is invalid."
        )

    subject = str(claims.get("sub") or "").strip()

    if not subject:
        raise AppleAuthTokenError(
            "Apple identity token subject is missing."
        )

    if expected_nonce is not None:
        expected_nonce_value = str(expected_nonce).strip()
        token_nonce = str(claims.get("nonce") or "").strip()

        if not expected_nonce_value or token_nonce != expected_nonce_value:
            raise AppleAuthTokenError(
                "Apple identity token nonce is invalid."
            )

    return claims
