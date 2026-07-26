from __future__ import annotations

import os
import time
from typing import Any

import requests
from jose import JWTError, jwt


APPLE_TOKEN_AUDIENCE = "https://appleid.apple.com"

APPLE_TEAM_ID_ENV = "APPLE_TEAM_ID"
APPLE_KEY_ID_ENV = "APPLE_KEY_ID"
APPLE_PRIVATE_KEY_ENV = "APPLE_PRIVATE_KEY"


class AppleTokenExchangeError(Exception):
    """Base error for Apple server-side token operations."""


class AppleTokenExchangeNotConfiguredError(AppleTokenExchangeError):
    """Required Apple server credentials are missing or invalid."""


def _load_apple_server_credentials() -> tuple[str, str, str]:
    team_id = os.getenv(
        APPLE_TEAM_ID_ENV,
        "",
    ).strip()

    key_id = os.getenv(
        APPLE_KEY_ID_ENV,
        "",
    ).strip()

    private_key = os.getenv(
        APPLE_PRIVATE_KEY_ENV,
        "",
    ).strip()

    # Supports Render env values stored with escaped newlines.
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")

    if not team_id or not key_id or not private_key:
        raise AppleTokenExchangeNotConfiguredError(
            "Apple server credentials are not configured."
        )

    return team_id, key_id, private_key


def generate_apple_client_secret(
    client_id: str,
    *,
    lifetime_seconds: int = 300,
    now: int | None = None,
) -> str:
    client_id_value = str(client_id or "").strip()

    if not client_id_value:
        raise AppleTokenExchangeError(
            "Apple client_id is missing."
        )

    if lifetime_seconds <= 0 or lifetime_seconds > 15777000:
        raise AppleTokenExchangeError(
            "Apple client_secret lifetime is invalid."
        )

    team_id, key_id, private_key = _load_apple_server_credentials()

    issued_at = int(now if now is not None else time.time())
    expires_at = issued_at + int(lifetime_seconds)

    claims = {
        "iss": team_id,
        "iat": issued_at,
        "exp": expires_at,
        "aud": APPLE_TOKEN_AUDIENCE,
        "sub": client_id_value,
    }

    try:
        return jwt.encode(
            claims,
            private_key,
            algorithm="ES256",
            headers={
                "kid": key_id,
                "alg": "ES256",
            },
        )
    except (JWTError, ValueError, TypeError) as exc:
        raise AppleTokenExchangeNotConfiguredError(
            "Apple client_secret could not be generated."
        ) from exc

APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke"
APPLE_TOKEN_HTTP_TIMEOUT_SECONDS = 10


class AppleAuthorizationCodeError(AppleTokenExchangeError):
    """Apple authorization code could not be exchanged."""


def exchange_apple_authorization_code(
    authorization_code: str,
    *,
    client_id: str,
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    code_value = str(authorization_code or "").strip()
    client_id_value = str(client_id or "").strip()
    redirect_uri_value = str(redirect_uri or "").strip()

    if not code_value:
        raise AppleAuthorizationCodeError(
            "Apple authorization code is missing."
        )

    if not client_id_value:
        raise AppleAuthorizationCodeError(
            "Apple client_id is missing."
        )

    client_secret = generate_apple_client_secret(
        client_id_value,
    )

    request_data = {
        "grant_type": "authorization_code",
        "code": code_value,
        "client_id": client_id_value,
        "client_secret": client_secret,
    }

    if redirect_uri_value:
        request_data["redirect_uri"] = redirect_uri_value

    try:
        response = requests.post(
            APPLE_TOKEN_URL,
            data=request_data,
            timeout=APPLE_TOKEN_HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AppleAuthorizationCodeError(
            "Apple token endpoint request failed."
        ) from exc

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise AppleAuthorizationCodeError(
            "Apple token endpoint returned invalid JSON."
        ) from exc

    if response.status_code != 200:
        raise AppleAuthorizationCodeError(
            "Apple authorization code was rejected."
        )

    if not isinstance(response_payload, dict):
        raise AppleAuthorizationCodeError(
            "Apple token endpoint response is invalid."
        )

    refresh_token = str(
        response_payload.get("refresh_token") or ""
    ).strip()

    if not refresh_token:
        raise AppleAuthorizationCodeError(
            "Apple token response does not contain a refresh token."
        )

    return response_payload

class AppleTokenRevocationError(AppleTokenExchangeError):
    """Apple refresh/access token could not be revoked."""


def revoke_apple_token(
    token: str,
    *,
    client_id: str,
    token_type_hint: str = "refresh_token",
) -> None:
    token_value = str(token or "").strip()
    client_id_value = str(client_id or "").strip()
    token_type_hint_value = str(token_type_hint or "").strip()

    if not token_value:
        raise AppleTokenRevocationError(
            "Apple token to revoke is missing."
        )

    if not client_id_value:
        raise AppleTokenRevocationError(
            "Apple client_id is missing."
        )

    if token_type_hint_value not in {
        "refresh_token",
        "access_token",
    }:
        raise AppleTokenRevocationError(
            "Apple token_type_hint is invalid."
        )

    client_secret = generate_apple_client_secret(
        client_id_value,
    )

    request_data = {
        "client_id": client_id_value,
        "client_secret": client_secret,
        "token": token_value,
        "token_type_hint": token_type_hint_value,
    }

    try:
        response = requests.post(
            APPLE_REVOKE_URL,
            data=request_data,
            timeout=APPLE_TOKEN_HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AppleTokenRevocationError(
            "Apple token revocation request failed."
        ) from exc

    if response.status_code != 200:
        raise AppleTokenRevocationError(
            "Apple token revocation was rejected."
        )
