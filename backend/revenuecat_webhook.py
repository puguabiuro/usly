"""Parser i kontrakt webhooków RevenueCat.

Moduł odpowiada wyłącznie za:

- autoryzację webhooka,
- walidację payloadu,
- normalizację danych wejściowych,
- przygotowanie stabilnego obiektu dla dalszego procesora.

Na tym etapie moduł:

- nie zapisuje danych do bazy,
- nie wywołuje Sync Engine,
- nie jest podłączony do main.py.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import secrets
from typing import Any

from backend.revenuecat_config import RevenueCatConfig


class RevenueCatWebhookError(RuntimeError):
    """Bazowy błąd obsługi webhooków RevenueCat."""


class RevenueCatWebhookAuthorizationError(RevenueCatWebhookError):
    """Niepoprawna autoryzacja webhooka RevenueCat."""


class RevenueCatWebhookPayloadError(RevenueCatWebhookError):
    """Nieprawidłowy payload webhooka RevenueCat."""


@dataclass(frozen=True)
class RevenueCatWebhookPayload:
    """Znormalizowany kontrakt wejściowy webhooka RevenueCat."""

    event_id: str
    event_type: str
    app_user_id: str | None
    original_app_user_id: str | None
    aliases: tuple[str, ...]
    environment: str | None
    store: str | None
    product_id: str | None
    event_timestamp_ms: int | None
    raw_payload: dict[str, Any]
    payload_json: str


def validate_revenuecat_webhook_authorization(
    provided_authorization: str | None,
    config: RevenueCatConfig,
) -> None:
    """Weryfikuje nagłówek autoryzacyjny webhooka w stałym czasie."""

    expected_authorization = str(config.webhook_authorization or "").strip()

    if not expected_authorization:
        raise RevenueCatWebhookAuthorizationError(
            "Autoryzacja webhooka RevenueCat nie jest skonfigurowana"
        )

    normalized_authorization = str(provided_authorization or "").strip()

    if not normalized_authorization:
        raise RevenueCatWebhookAuthorizationError(
            "Brak autoryzacji webhooka RevenueCat"
        )

    if not secrets.compare_digest(
        normalized_authorization,
        expected_authorization,
    ):
        raise RevenueCatWebhookAuthorizationError(
            "Niepoprawna autoryzacja webhooka RevenueCat"
        )


def normalize_required_webhook_identifier(
    value: Any,
    field_name: str,
) -> str:
    """Normalizuje wymagany, niepusty identyfikator tekstowy."""

    if not isinstance(value, str):
        raise RevenueCatWebhookPayloadError(
            f"Pole {field_name} musi być tekstem"
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise RevenueCatWebhookPayloadError(
            f"Pole {field_name} nie może być puste"
        )

    return normalized_value


def normalize_optional_webhook_text(
    value: Any,
    field_name: str,
) -> str | None:
    """Normalizuje opcjonalne pole tekstowe webhooka."""

    if value is None:
        return None

    if not isinstance(value, str):
        raise RevenueCatWebhookPayloadError(
            f"Pole {field_name} musi być tekstem albo null"
        )

    normalized_value = value.strip()
    return normalized_value or None


def normalize_webhook_aliases(value: Any) -> tuple[str, ...]:
    """Normalizuje opcjonalną listę aliasów App User ID."""

    if value is None:
        return ()

    if not isinstance(value, list):
        raise RevenueCatWebhookPayloadError(
            "Pole event.aliases musi być listą albo null"
        )

    normalized_aliases: list[str] = []
    seen_aliases: set[str] = set()

    for index, alias in enumerate(value):
        normalized_alias = normalize_required_webhook_identifier(
            alias,
            f"event.aliases[{index}]",
        )

        if normalized_alias not in seen_aliases:
            normalized_aliases.append(normalized_alias)
            seen_aliases.add(normalized_alias)

    return tuple(normalized_aliases)


def normalize_webhook_timestamp_ms(
    value: Any,
    field_name: str,
) -> int | None:
    """Normalizuje opcjonalny znacznik czasu wyrażony w milisekundach."""

    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise RevenueCatWebhookPayloadError(
            f"Pole {field_name} musi być liczbą całkowitą albo null"
        )

    if value < 0:
        raise RevenueCatWebhookPayloadError(
            f"Pole {field_name} nie może być ujemne"
        )

    return value


def serialize_revenuecat_webhook_payload(
    payload: dict[str, Any],
) -> str:
    """Serializuje pełny payload webhooka do stabilnego JSON."""

    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise RevenueCatWebhookPayloadError(
            "Payload webhooka RevenueCat nie może zostać zapisany jako JSON"
        ) from exc


def parse_revenuecat_webhook_payload(
    payload: Any,
) -> RevenueCatWebhookPayload:
    """Waliduje i normalizuje payload webhooka RevenueCat."""

    if not isinstance(payload, dict):
        raise RevenueCatWebhookPayloadError(
            "Payload webhooka RevenueCat musi być obiektem"
        )

    event = payload.get("event")

    if not isinstance(event, dict):
        raise RevenueCatWebhookPayloadError(
            "Payload webhooka RevenueCat nie zawiera poprawnego obiektu event"
        )

    event_id = normalize_required_webhook_identifier(
        event.get("id"),
        "event.id",
    )
    event_type = normalize_required_webhook_identifier(
        event.get("type"),
        "event.type",
    )

    app_user_id = normalize_optional_webhook_text(
        event.get("app_user_id"),
        "event.app_user_id",
    )
    original_app_user_id = normalize_optional_webhook_text(
        event.get("original_app_user_id"),
        "event.original_app_user_id",
    )
    aliases = normalize_webhook_aliases(event.get("aliases"))
    environment = normalize_optional_webhook_text(
        event.get("environment"),
        "event.environment",
    )
    store = normalize_optional_webhook_text(
        event.get("store"),
        "event.store",
    )
    product_id = normalize_optional_webhook_text(
        event.get("product_id"),
        "event.product_id",
    )
    event_timestamp_ms = normalize_webhook_timestamp_ms(
        event.get("event_timestamp_ms"),
        "event.event_timestamp_ms",
    )

    payload_json = serialize_revenuecat_webhook_payload(payload)

    try:
        raw_payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise RevenueCatWebhookPayloadError(
            "Zserializowany payload webhooka RevenueCat jest nieprawidłowy"
        ) from exc

    if not isinstance(raw_payload, dict):
        raise RevenueCatWebhookPayloadError(
            "Zserializowany payload webhooka RevenueCat nie jest obiektem"
        )

    return RevenueCatWebhookPayload(
        event_id=event_id,
        event_type=event_type,
        app_user_id=app_user_id,
        original_app_user_id=original_app_user_id,
        aliases=aliases,
        environment=environment,
        store=store,
        product_id=product_id,
        event_timestamp_ms=event_timestamp_ms,
        raw_payload=raw_payload,
        payload_json=payload_json,
    )
