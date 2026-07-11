"""Klient REST API RevenueCat.

Na tym etapie moduł przygotowuje wyłącznie konfigurację klienta.
Nie wykonuje jeszcze żadnych połączeń HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from backend.revenuecat_config import (
    RevenueCatConfig,
    load_revenuecat_config,
)


class RevenueCatError(RuntimeError):
    """Bazowy błąd integracji RevenueCat."""


class RevenueCatConfigurationError(RevenueCatError):
    """Brak lub nieprawidłowa konfiguracja RevenueCat."""


class RevenueCatRequestError(RevenueCatError):
    """Błąd sieciowy albo odpowiedź HTTP z błędem."""


class RevenueCatResponseError(RevenueCatError):
    """Nieprawidłowa odpowiedź zwrócona przez RevenueCat."""


@dataclass
class RevenueCatClient:
    config: RevenueCatConfig

    @property
    def default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.secret_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(self.default_headers)
        return session

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        """Wykonuje autoryzowany request do RevenueCat REST API."""

        if not self.config.rest_api_configured:
            raise RevenueCatConfigurationError(
                "RevenueCat REST API nie jest skonfigurowane"
            )

        normalized_path = "/" + str(path or "").strip().lstrip("/")
        url = f"{self.config.api_v2_base_url}{normalized_path}"
        session = self.create_session()

        try:
            response = session.request(
                method=str(method or "").strip().upper(),
                url=url,
                params=params,
                json=json_body,
                timeout=self.config.http_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RevenueCatRequestError(
                "Nie udało się wykonać requestu do RevenueCat"
            ) from exc
        finally:
            session.close()

        try:
            payload = response.json()
        except ValueError as exc:
            raise RevenueCatResponseError(
                "RevenueCat zwrócił nieprawidłową odpowiedź JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise RevenueCatResponseError(
                "RevenueCat zwrócił nieoczekiwany format odpowiedzi"
            )

        return payload


def create_revenuecat_client() -> RevenueCatClient:
    """Tworzy klienta RevenueCat na podstawie konfiguracji środowiskowej."""
    return RevenueCatClient(load_revenuecat_config())
