"""Centralny katalog produktów sklepowych USLY.

Ten moduł definiuje zaufane mapowanie identyfikatorów produktów sklepowych
na entitlement, rolę oraz plan w USLY.

Moduł nie jest jeszcze podłączony do istniejącego flow płatności.
"""

from typing import Any


USER_PLAN_RANKS = {
    "free": 0,
    "plus": 1,
    "premium": 2,
    "vip": 3,
}

PARTNER_PLAN_RANKS = {
    "free": 0,
    "pro": 1,
    "premium": 2,
    "enterprise": 3,
}

PLAN_RANKS_BY_ROLE = {
    "user": USER_PLAN_RANKS,
    "partner": PARTNER_PLAN_RANKS,
}


STORE_PRODUCTS = {
    "usly_user_plus:monthly": {
        "entitlement": "usly_user_plus",
        "role": "user",
        "plan": "plus",
    },
    "usly_user_premium:monthly": {
        "entitlement": "usly_user_premium",
        "role": "user",
        "plan": "premium",
    },
    "usly_user_vip:monthly": {
        "entitlement": "usly_user_vip",
        "role": "user",
        "plan": "vip",
    },
    "usly_partner_pro:monthly": {
        "entitlement": "usly_partner_pro",
        "role": "partner",
        "plan": "pro",
    },
    "usly_partner_premium:monthly": {
        "entitlement": "usly_partner_premium",
        "role": "partner",
        "plan": "premium",
    },
}


def get_store_product(product_id: str) -> dict[str, Any] | None:
    """Zwraca zaufaną definicję produktu albo None dla nieznanego ID."""

    normalized_product_id = str(product_id or "").strip()
    return STORE_PRODUCTS.get(normalized_product_id)


PRODUCT_BY_ENTITLEMENT = {
    product["entitlement"]: product
    for product in STORE_PRODUCTS.values()
}

PRODUCT_BY_ROLE_AND_PLAN = {
    (product["role"], product["plan"]): product
    for product in STORE_PRODUCTS.values()
}


def get_product_by_entitlement(entitlement: str) -> dict[str, Any] | None:
    """Zwraca definicję produktu na podstawie entitlement."""
    return PRODUCT_BY_ENTITLEMENT.get(str(entitlement or "").strip())


def get_product_for_plan(role: str, plan: str) -> dict[str, Any] | None:
    """Zwraca definicję produktu dla roli i planu."""
    return PRODUCT_BY_ROLE_AND_PLAN.get(
        (str(role or "").strip(), str(plan or "").strip())
    )


def is_product_valid_for_role(product_id: str, role: str) -> bool:
    """Sprawdza, czy produkt należy do wskazanej roli."""
    product = get_store_product(product_id)
    return bool(product and product["role"] == str(role or "").strip())

