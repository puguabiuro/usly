"""Domenowy kontrakt subskrypcji RevenueCat API v2.

Moduł:

- nie wykonuje requestów HTTP,
- nie zapisuje danych w bazie,
- nie modyfikuje planów użytkowników,
- przekształca surowy obiekt subskrypcji RevenueCat w bezpieczny,
  niemutowalny model domenowy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class RevenueCatSubscriptionError(RuntimeError):
    """Nie udało się bezpiecznie zinterpretować subskrypcji RevenueCat."""


@dataclass(frozen=True)
class RevenueCatSubscription:
    """Zwalidowana subskrypcja otrzymana z RevenueCat API v2."""

    subscription_id: str
    customer_id: str
    original_customer_id: str
    revenuecat_product_id: str | None
    store_subscription_identifier: str
    environment: str
    store: str
    status: str
    gives_access: bool
    pending_payment: bool
    active_entitlement_ids: tuple[str, ...]
    current_period_ends_at: datetime | None
    ends_at: datetime | None
    raw_payload_json: str


def parse_revenuecat_subscription(
    payload: dict[str, Any],
) -> RevenueCatSubscription:
    """Waliduje pojedynczy obiekt subskrypcji RevenueCat API v2."""

    if not isinstance(payload, dict):
        raise RevenueCatSubscriptionError(
            "Subskrypcja RevenueCat musi być obiektem"
        )

    object_type = _required_string(payload.get("object"), "object")
    if object_type != "subscription":
        raise RevenueCatSubscriptionError(
            "Obiekt RevenueCat nie jest subskrypcją"
        )

    subscription_id = _required_string(payload.get("id"), "id")
    customer_id = _required_string(
        payload.get("customer_id"),
        "customer_id",
    )
    original_customer_id = _required_string(
        payload.get("original_customer_id"),
        "original_customer_id",
    )

    revenuecat_product_id = _optional_string(payload.get("product_id"))

    store_subscription_identifier = _required_identifier(
        payload.get("store_subscription_identifier"),
        "store_subscription_identifier",
    )

    environment = _required_string(
        payload.get("environment"),
        "environment",
    ).lower()
    if environment not in {"sandbox", "production"}:
        raise RevenueCatSubscriptionError(
            "environment musi mieć wartość sandbox albo production"
        )

    store = _required_string(payload.get("store"), "store").lower()
    status = _required_string(payload.get("status"), "status").lower()

    gives_access = _required_bool(
        payload.get("gives_access"),
        "gives_access",
    )
    pending_payment = _required_bool(
        payload.get("pending_payment"),
        "pending_payment",
    )

    active_entitlement_ids = _parse_active_entitlement_ids(
        payload.get("entitlements")
    )

    current_period_ends_at = _milliseconds_to_datetime(
        payload.get("current_period_ends_at"),
        "current_period_ends_at",
    )
    ends_at = _milliseconds_to_datetime(
        payload.get("ends_at"),
        "ends_at",
    )

    raw_payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return RevenueCatSubscription(
        subscription_id=subscription_id,
        customer_id=customer_id,
        original_customer_id=original_customer_id,
        revenuecat_product_id=revenuecat_product_id,
        store_subscription_identifier=store_subscription_identifier,
        environment=environment,
        store=store,
        status=status,
        gives_access=gives_access,
        pending_payment=pending_payment,
        active_entitlement_ids=active_entitlement_ids,
        current_period_ends_at=current_period_ends_at,
        ends_at=ends_at,
        raw_payload_json=raw_payload_json,
    )


def _parse_active_entitlement_ids(
    value: Any,
) -> tuple[str, ...]:
    if not isinstance(value, dict):
        raise RevenueCatSubscriptionError(
            "Pole entitlements musi być obiektem"
        )

    items = value.get("items")

    if not isinstance(items, list):
        raise RevenueCatSubscriptionError(
            "Pole entitlements.items musi być listą"
        )

    active_ids: list[str] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise RevenueCatSubscriptionError(
                (
                    "Element entitlements.items"
                    f"[{index}] musi być obiektem"
                )
            )

        entitlement_id = _required_string(
            item.get("id"),
            f"entitlements.items[{index}].id",
        )
        state = _required_string(
            item.get("state"),
            f"entitlements.items[{index}].state",
        ).lower()

        if state == "active" and entitlement_id not in seen_ids:
            active_ids.append(entitlement_id)
            seen_ids.add(entitlement_id)

    return tuple(active_ids)


def _required_string(value: Any, field_name: str) -> str:
    normalized_value = str(value or "").strip()

    if not normalized_value:
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} nie może być puste"
        )

    return normalized_value


def _optional_string(value: Any) -> str | None:
    normalized_value = str(value or "").strip()
    return normalized_value or None


def _required_identifier(value: Any, field_name: str) -> str:
    if isinstance(value, bool) or value is None:
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} nie może być puste"
        )

    normalized_value = str(value).strip()

    if not normalized_value:
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} nie może być puste"
        )

    return normalized_value


def _required_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} musi być wartością logiczną"
        )

    return value


def _milliseconds_to_datetime(
    value: Any,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} musi zawierać milisekundy Unix albo null"
        )

    if value < 0:
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} nie może być ujemne"
        )

    try:
        return datetime.utcfromtimestamp(value / 1000)
    except (OverflowError, OSError, ValueError) as exc:
        raise RevenueCatSubscriptionError(
            f"Pole {field_name} zawiera nieprawidłowy timestamp"
        ) from exc
