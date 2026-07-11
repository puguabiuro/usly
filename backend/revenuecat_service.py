"""Warstwa operacji biznesowych na RevenueCat REST API v2.

Moduł zna oficjalne endpointy RevenueCat, ale nie interpretuje jeszcze
subskrypcji jako planów USLY i nie jest podłączony do aplikacji.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from backend.revenuecat_client import RevenueCatClient


class RevenueCatCustomerNotFoundError(RuntimeError):
    """Nie znaleziono klienta RevenueCat dla wskazanego App User ID."""


class RevenueCatCustomerAmbiguousError(RuntimeError):
    """Wyszukiwanie App User ID zwróciło więcej niż jednego klienta."""


@dataclass
class RevenueCatService:
    client: RevenueCatClient

    def find_customer_by_app_user_id(self, app_user_id: str) -> dict:
        """Znajduje klienta RevenueCat na podstawie stabilnego App User ID."""

        normalized_app_user_id = str(app_user_id or "").strip()
        if not normalized_app_user_id:
            raise ValueError("app_user_id nie może być pusty")

        payload = self.client.request(
            "GET",
            f"/projects/{quote(self.client.config.project_id, safe='')}/customers",
            params={
                "search": normalized_app_user_id,
                "limit": 20,
            },
        )

        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("RevenueCat zwrócił nieprawidłową listę klientów")

        if not items:
            raise RevenueCatCustomerNotFoundError(
                f"Nie znaleziono klienta RevenueCat dla {normalized_app_user_id}"
            )

        if len(items) != 1:
            raise RevenueCatCustomerAmbiguousError(
                f"RevenueCat zwrócił {len(items)} klientów dla {normalized_app_user_id}"
            )

        customer = items[0]
        if not isinstance(customer, dict) or not str(customer.get("id") or "").strip():
            raise ValueError("RevenueCat zwrócił klienta bez poprawnego customer_id")

        return customer

    def get_entitlements(self) -> dict:
        """Pobiera definicje entitlementów skonfigurowanych w projekcie."""

        return self.client.request(
            "GET",
            f"/projects/{quote(self.client.config.project_id, safe='')}/entitlements",
            params={"limit": 100},
        )

    def get_active_entitlements(self, customer_id: str) -> dict:
        """Pobiera aktywne entitlementy klienta RevenueCat."""

        normalized_customer_id = str(customer_id or "").strip()
        if not normalized_customer_id:
            raise ValueError("customer_id nie może być pusty")

        return self.client.request(
            "GET",
            (
                f"/projects/{quote(self.client.config.project_id, safe='')}"
                f"/customers/{quote(normalized_customer_id, safe='')}"
                "/active_entitlements"
            ),
            params={"limit": 100},
        )

    def get_subscriptions(
        self,
        customer_id: str,
        *,
        environment: str | None = None,
    ) -> dict:
        """Pobiera subskrypcje klienta RevenueCat."""

        normalized_customer_id = str(customer_id or "").strip()
        if not normalized_customer_id:
            raise ValueError("customer_id nie może być pusty")

        params: dict[str, object] = {"limit": 100}
        if environment is not None:
            normalized_environment = str(environment).strip().lower()
            if normalized_environment not in {"sandbox", "production"}:
                raise ValueError(
                    "environment musi mieć wartość sandbox albo production"
                )
            params["environment"] = normalized_environment

        return self.client.request(
            "GET",
            (
                f"/projects/{quote(self.client.config.project_id, safe='')}"
                f"/customers/{quote(normalized_customer_id, safe='')}"
                "/subscriptions"
            ),
            params=params,
        )
