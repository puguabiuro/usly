"""Konfiguracja backendowej integracji USLY z RevenueCat.

Moduł wyłącznie odczytuje i waliduje ustawienia środowiskowe.
Nie wykonuje żadnych połączeń HTTP i nie jest jeszcze podłączony do aplikacji.
"""

from dataclasses import dataclass
import os


DEFAULT_REVENUECAT_API_V2_BASE_URL = "https://api.revenuecat.com/v2"
DEFAULT_REVENUECAT_HTTP_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class RevenueCatConfig:
    secret_api_key: str
    project_id: str
    webhook_authorization: str
    api_v2_base_url: str
    http_timeout_seconds: float

    @property
    def rest_api_configured(self) -> bool:
        return bool(self.secret_api_key and self.project_id)

    @property
    def webhook_configured(self) -> bool:
        return bool(self.webhook_authorization)


def load_revenuecat_config() -> RevenueCatConfig:
    """Ładuje konfigurację RevenueCat ze zmiennych środowiskowych."""

    timeout_raw = os.getenv(
        "REVENUECAT_HTTP_TIMEOUT_SECONDS",
        str(DEFAULT_REVENUECAT_HTTP_TIMEOUT_SECONDS),
    ).strip()

    try:
        timeout_seconds = float(timeout_raw)
    except ValueError as exc:
        raise ValueError(
            "REVENUECAT_HTTP_TIMEOUT_SECONDS musi być liczbą"
        ) from exc

    if timeout_seconds <= 0:
        raise ValueError(
            "REVENUECAT_HTTP_TIMEOUT_SECONDS musi być większe od zera"
        )

    return RevenueCatConfig(
        secret_api_key=os.getenv("REVENUECAT_SECRET_API_KEY", "").strip(),
        project_id=os.getenv("REVENUECAT_PROJECT_ID", "").strip(),
        webhook_authorization=os.getenv(
            "REVENUECAT_WEBHOOK_AUTHORIZATION",
            "",
        ).strip(),
        api_v2_base_url=os.getenv(
            "REVENUECAT_API_V2_BASE_URL",
            DEFAULT_REVENUECAT_API_V2_BASE_URL,
        ).strip().rstrip("/"),
        http_timeout_seconds=timeout_seconds,
    )
