"""Cienka warstwa persystencji zakupów sklepowych RevenueCat.

Moduł:

- przyjmuje zweryfikowany StorePurchaseData,
- wykonuje idempotentny upsert StorePurchase,
- nie oblicza planu,
- nie aktualizuje profili,
- nie wykonuje requestów HTTP,
- nie zatwierdza ani nie wycofuje transakcji.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.models import StorePurchase
from backend.store_purchase_data import StorePurchaseData


class StorePurchaseRepositoryError(RuntimeError):
    """Nie udało się bezpiecznie zapisać zakupu sklepowego."""


@dataclass
class StorePurchaseRepository:
    """Zapisuje zweryfikowane dane zakupu w bieżącej transakcji."""

    db: Session

    def upsert(
        self,
        *,
        user_id: int,
        data: StorePurchaseData,
    ) -> StorePurchase:
        """Tworzy lub aktualizuje zakup według sklepowego identyfikatora.

        Kluczem idempotencji ścieżki RevenueCat jest:

        revenuecat_subscription_id

        Pole transaction_id nadal przechowuje sklepowy
        store_subscription_identifier. Metoda wykonuje flush, ale nie commit.
        """

        if isinstance(user_id, bool) or not isinstance(user_id, int):
            raise StorePurchaseRepositoryError(
                "user_id musi być dodatnią liczbą całkowitą"
            )

        if user_id <= 0:
            raise StorePurchaseRepositoryError(
                "user_id musi być dodatnią liczbą całkowitą"
            )

        purchase = (
            self.db.query(StorePurchase)
            .filter(
                StorePurchase.revenuecat_subscription_id
                == data.revenuecat_subscription_id
            )
            .one_or_none()
        )

        if purchase is None:
            purchase = StorePurchase(
                user_id=user_id,
                platform=data.platform,
                product_id=data.store_product_id,
                transaction_id=data.store_subscription_identifier,
                original_transaction_id=None,
                purchase_token=None,
                environment=data.environment,
                revenuecat_app_user_id=data.revenuecat_app_user_id,
                revenuecat_customer_id=data.revenuecat_customer_id,
                revenuecat_subscription_id=(
                    data.revenuecat_subscription_id
                ),
                revenuecat_entitlement_id=(
                    data.revenuecat_entitlement_id
                ),
                entitlement_lookup_key=(
                    data.entitlement_lookup_key
                ),
                role=data.role,
                store=data.store,
                synced_at=data.synced_at,
                last_event_id=data.webhook_event_id,
                last_event_at=data.webhook_event_at,
                plan=data.plan,
                status=data.subscription_status,
                verification_mode="revenuecat",
                raw_payload=data.raw_subscription_json,
                verified_at=data.synced_at,
                plan_expires_at=data.plan_expires_at,
                expires_at=data.ends_at,
                revoked_at=None,
            )
            self.db.add(purchase)
        else:
            if purchase.user_id != user_id:
                raise StorePurchaseRepositoryError(
                    (
                        "Zakup sklepowy jest już przypisany do innego "
                        "użytkownika USLY"
                    )
                )

            if (
                purchase.synced_at is not None
                and data.synced_at < purchase.synced_at
            ):
                return purchase

            purchase.product_id = data.store_product_id
            purchase.transaction_id = (
                data.store_subscription_identifier
            )
            purchase.environment = data.environment
            purchase.revenuecat_app_user_id = (
                data.revenuecat_app_user_id
            )
            purchase.revenuecat_customer_id = (
                data.revenuecat_customer_id
            )
            purchase.revenuecat_subscription_id = (
                data.revenuecat_subscription_id
            )
            purchase.revenuecat_entitlement_id = (
                data.revenuecat_entitlement_id
            )
            purchase.entitlement_lookup_key = (
                data.entitlement_lookup_key
            )
            purchase.role = data.role
            purchase.store = data.store
            purchase.synced_at = data.synced_at
            purchase.last_event_id = data.webhook_event_id
            purchase.last_event_at = data.webhook_event_at
            purchase.plan = data.plan
            purchase.status = data.subscription_status
            purchase.verification_mode = "revenuecat"
            purchase.raw_payload = data.raw_subscription_json
            purchase.verified_at = data.synced_at
            purchase.plan_expires_at = data.plan_expires_at
            purchase.expires_at = data.ends_at

        self.db.flush()

        return purchase
