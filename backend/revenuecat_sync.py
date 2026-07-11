"""Silnik synchronizacji subskrypcji RevenueCat z planami USLY.

Moduł zawiera czystą logikę biznesową synchronizacji. Na tym etapie:

- nie wykonuje requestów HTTP,
- nie zapisuje danych w bazie,
- nie modyfikuje profili użytkowników,
- nie jest podłączony do main.py.

RevenueCatService będzie później dostarczać dane wejściowe, a ten moduł
będzie je interpretować i wyliczać końcowy plan użytkownika.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from backend.revenuecat_client import create_revenuecat_client
from backend.revenuecat_service import RevenueCatService
from backend.store_catalog import (
    PLAN_RANKS_BY_ROLE,
    get_product_by_entitlement,
)


class RevenueCatSyncError(RuntimeError):
    """Bazowy błąd silnika synchronizacji RevenueCat."""


class RevenueCatSyncDataError(RevenueCatSyncError):
    """RevenueCat zwrócił dane, których nie można bezpiecznie zinterpretować."""


@dataclass(frozen=True)
class MappedEntitlement:
    """Aktywny entitlement RevenueCat zmapowany na plan USLY."""

    entitlement_id: str
    lookup_key: str
    role: str
    plan: str
    rank: int


@dataclass(frozen=True)
class EffectivePlan:
    """Końcowy plan wyliczony dla wskazanej roli."""

    role: str
    plan: str
    rank: int
    source_entitlement_id: str | None = None
    source_entitlement_lookup_key: str | None = None


@dataclass(frozen=True)
class RevenueCatSyncResult:
    """Kompletny wynik interpretacji danych RevenueCat dla jednego konta."""

    app_user_id: str
    customer_id: str
    role: str
    effective_plan: EffectivePlan
    mapped_entitlements: tuple[MappedEntitlement, ...]
    unknown_entitlement_ids: tuple[str, ...]
    subscriptions: tuple[dict[str, Any], ...]



@dataclass
class RevenueCatSyncEngine:
    """Orkiestruje pobranie i interpretację danych RevenueCat.

    Silnik nie zapisuje danych w bazie i nie zmienia profili użytkowników.
    Zwraca wyłącznie kompletny RevenueCatSyncResult.
    """

    service: RevenueCatService

    def sync_customer(
        self,
        *,
        app_user_id: str,
        role: str,
        environment: str | None = None,
    ) -> RevenueCatSyncResult:
        """Synchronizuje jednego klienta RevenueCat z planem USLY."""

        normalized_app_user_id = normalize_required_identifier(
            app_user_id,
            "app_user_id",
        )
        normalized_role = normalize_role(role)

        customer = self.service.find_customer_by_app_user_id(
            normalized_app_user_id
        )

        customer_id = normalize_required_identifier(
            customer.get("id"),
            "customer_id",
        )

        entitlements_payload = self.service.get_entitlements()
        active_entitlements_payload = self.service.get_active_entitlements(
            customer_id
        )
        subscriptions_payload = self.service.get_subscriptions(
            customer_id,
            environment=environment,
        )

        return build_sync_result(
            app_user_id=normalized_app_user_id,
            customer_id=customer_id,
            role=normalized_role,
            entitlements_payload=entitlements_payload,
            active_entitlements_payload=active_entitlements_payload,
            subscriptions_payload=subscriptions_payload,
        )


def create_revenuecat_sync_engine() -> RevenueCatSyncEngine:
    """Tworzy produkcyjny Sync Engine z klientem konfiguracji środowiskowej."""

    client = create_revenuecat_client()
    service = RevenueCatService(client)

    return RevenueCatSyncEngine(service=service)



def normalize_role(role: str) -> str:
    """Normalizuje i waliduje rolę obsługiwaną przez system płatności."""

    normalized_role = str(role or "").strip().lower()

    if normalized_role not in PLAN_RANKS_BY_ROLE:
        raise RevenueCatSyncDataError(
            f"Nieobsługiwana rola w synchronizacji RevenueCat: {normalized_role or '<pusta>'}"
        )

    return normalized_role



def build_entitlement_lookup_map(
    entitlements_payload: dict[str, Any],
) -> dict[str, str]:
    """Buduje mapowanie wewnętrznego entitlement_id na publiczny lookup_key."""

    if not isinstance(entitlements_payload, dict):
        raise RevenueCatSyncDataError(
            "Katalog entitlementów RevenueCat musi być obiektem"
        )

    items = entitlements_payload.get("items")
    if not isinstance(items, list):
        raise RevenueCatSyncDataError(
            "Katalog entitlementów RevenueCat nie zawiera poprawnej listy items"
        )

    entitlement_lookup_map: dict[str, str] = {}

    for item in items:
        if not isinstance(item, dict):
            raise RevenueCatSyncDataError(
                "Katalog entitlementów zawiera element o nieprawidłowym typie"
            )

        entitlement_id = str(item.get("id") or "").strip()
        lookup_key = str(item.get("lookup_key") or "").strip()

        if not entitlement_id:
            raise RevenueCatSyncDataError(
                "Entitlement RevenueCat nie zawiera poprawnego id"
            )

        if not lookup_key:
            raise RevenueCatSyncDataError(
                f"Entitlement RevenueCat {entitlement_id!r} nie zawiera lookup_key"
            )

        existing_lookup_key = entitlement_lookup_map.get(entitlement_id)
        if existing_lookup_key is not None and existing_lookup_key != lookup_key:
            raise RevenueCatSyncDataError(
                (
                    f"Entitlement RevenueCat {entitlement_id!r} ma "
                    "sprzeczne wartości lookup_key"
                )
            )

        entitlement_lookup_map[entitlement_id] = lookup_key

    return entitlement_lookup_map


def map_active_entitlements(
    active_entitlements_payload: dict[str, Any],
    entitlement_lookup_map: dict[str, str],
) -> tuple[tuple[MappedEntitlement, ...], tuple[str, ...]]:
    """Mapuje aktywne entitlementy RevenueCat na zaufane plany USLY.

    Zwraca dwa zbiory:

    - poprawnie zmapowane entitlementy,
    - nieznane entitlement_id, których nie udało się przypisać do katalogu
      RevenueCat albo katalogu produktów USLY.
    """

    if not isinstance(active_entitlements_payload, dict):
        raise RevenueCatSyncDataError(
            "Aktywne entitlementy RevenueCat muszą być obiektem"
        )

    if not isinstance(entitlement_lookup_map, dict):
        raise RevenueCatSyncDataError(
            "Mapa entitlementów RevenueCat musi być słownikiem"
        )

    items = active_entitlements_payload.get("items")
    if not isinstance(items, list):
        raise RevenueCatSyncDataError(
            "Aktywne entitlementy RevenueCat nie zawierają poprawnej listy items"
        )

    mapped_entitlements: list[MappedEntitlement] = []
    unknown_entitlement_ids: list[str] = []
    seen_entitlement_ids: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            raise RevenueCatSyncDataError(
                "Lista aktywnych entitlementów zawiera element o nieprawidłowym typie"
            )

        entitlement_id = str(item.get("entitlement_id") or "").strip()

        if not entitlement_id:
            raise RevenueCatSyncDataError(
                "Aktywny entitlement RevenueCat nie zawiera entitlement_id"
            )

        if entitlement_id in seen_entitlement_ids:
            continue

        seen_entitlement_ids.add(entitlement_id)

        lookup_key = str(
            entitlement_lookup_map.get(entitlement_id) or ""
        ).strip()

        if not lookup_key:
            unknown_entitlement_ids.append(entitlement_id)
            continue

        product = get_product_by_entitlement(lookup_key)

        if product is None:
            unknown_entitlement_ids.append(entitlement_id)
            continue

        role = str(product.get("role") or "").strip()
        plan = str(product.get("plan") or "").strip()

        plan_ranks = PLAN_RANKS_BY_ROLE.get(role)
        if plan_ranks is None or plan not in plan_ranks:
            raise RevenueCatSyncDataError(
                (
                    f"Katalog USLY zawiera nieprawidłowe mapowanie "
                    f"dla entitlementu {lookup_key!r}"
                )
            )

        mapped_entitlements.append(
            MappedEntitlement(
                entitlement_id=entitlement_id,
                lookup_key=lookup_key,
                role=role,
                plan=plan,
                rank=plan_ranks[plan],
            )
        )

    mapped_entitlements.sort(
        key=lambda entitlement: (
            entitlement.role,
            entitlement.rank,
            entitlement.lookup_key,
        )
    )

    return (
        tuple(mapped_entitlements),
        tuple(unknown_entitlement_ids),
    )




def normalize_required_identifier(value: str, field_name: str) -> str:
    """Normalizuje wymagany identyfikator używany w synchronizacji."""

    normalized_value = str(value or "").strip()

    if not normalized_value:
        raise RevenueCatSyncDataError(
            f"{field_name} nie może być pusty"
        )

    return normalized_value


def extract_subscriptions(
    subscriptions_payload: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Waliduje listę subskrypcji bez interpretowania jej pól biznesowych.

    Szczegółowe mapowanie subskrypcji do StorePurchase zostanie dodane
    dopiero podczas przebudowy modelu i migracji.
    """

    if not isinstance(subscriptions_payload, dict):
        raise RevenueCatSyncDataError(
            "Subskrypcje RevenueCat muszą być obiektem"
        )

    items = subscriptions_payload.get("items")
    if not isinstance(items, list):
        raise RevenueCatSyncDataError(
            "Subskrypcje RevenueCat nie zawierają poprawnej listy items"
        )

    subscriptions: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            raise RevenueCatSyncDataError(
                "Lista subskrypcji RevenueCat zawiera element o nieprawidłowym typie"
            )

        subscriptions.append(dict(item))

    return tuple(subscriptions)


def build_sync_result(
    *,
    app_user_id: str,
    customer_id: str,
    role: str,
    entitlements_payload: dict[str, Any],
    active_entitlements_payload: dict[str, Any],
    subscriptions_payload: dict[str, Any],
) -> RevenueCatSyncResult:
    """Buduje kompletny, czysty wynik synchronizacji RevenueCat.

    Funkcja nie wykonuje requestów i nie zapisuje danych. Łączy wyłącznie
    payloady wcześniej pobrane przez RevenueCatService.
    """

    normalized_app_user_id = normalize_required_identifier(
        app_user_id,
        "app_user_id",
    )
    normalized_customer_id = normalize_required_identifier(
        customer_id,
        "customer_id",
    )
    normalized_role = normalize_role(role)

    entitlement_lookup_map = build_entitlement_lookup_map(
        entitlements_payload
    )

    mapped_entitlements, unknown_entitlement_ids = map_active_entitlements(
        active_entitlements_payload,
        entitlement_lookup_map,
    )

    effective_plan = choose_effective_plan(
        normalized_role,
        mapped_entitlements,
    )

    subscriptions = extract_subscriptions(subscriptions_payload)

    return RevenueCatSyncResult(
        app_user_id=normalized_app_user_id,
        customer_id=normalized_customer_id,
        role=normalized_role,
        effective_plan=effective_plan,
        mapped_entitlements=mapped_entitlements,
        unknown_entitlement_ids=unknown_entitlement_ids,
        subscriptions=subscriptions,
    )



def get_free_effective_plan(role: str) -> EffectivePlan:
    """Zwraca bezpieczny plan FREE dla wskazanej roli."""

    normalized_role = normalize_role(role)
    free_rank = PLAN_RANKS_BY_ROLE[normalized_role]["free"]

    return EffectivePlan(
        role=normalized_role,
        plan="free",
        rank=free_rank,
    )


def choose_effective_plan(
    role: str,
    mapped_entitlements: Iterable[MappedEntitlement],
) -> EffectivePlan:
    """Wybiera najwyższy aktywny plan należący do wskazanej roli.

    Entitlementy innej roli są ignorowane. Jeśli nie ma poprawnego aktywnego
    entitlementu dla danej roli, wynikiem jest plan FREE.
    """

    normalized_role = normalize_role(role)
    plan_ranks = PLAN_RANKS_BY_ROLE[normalized_role]
    best_entitlement: MappedEntitlement | None = None

    for entitlement in mapped_entitlements:
        if not isinstance(entitlement, MappedEntitlement):
            raise RevenueCatSyncDataError(
                "mapped_entitlements zawiera element o nieprawidłowym typie"
            )

        if entitlement.role != normalized_role:
            continue

        expected_rank = plan_ranks.get(entitlement.plan)
        if expected_rank is None:
            raise RevenueCatSyncDataError(
                f"Nieznany plan {entitlement.plan!r} dla roli {normalized_role!r}"
            )

        if entitlement.rank != expected_rank:
            raise RevenueCatSyncDataError(
                (
                    f"Niespójny ranking planu {entitlement.plan!r}: "
                    f"otrzymano {entitlement.rank}, oczekiwano {expected_rank}"
                )
            )

        if best_entitlement is None or entitlement.rank > best_entitlement.rank:
            best_entitlement = entitlement

    if best_entitlement is None:
        return get_free_effective_plan(normalized_role)

    return EffectivePlan(
        role=normalized_role,
        plan=best_entitlement.plan,
        rank=best_entitlement.rank,
        source_entitlement_id=best_entitlement.entitlement_id,
        source_entitlement_lookup_key=best_entitlement.lookup_key,
    )
