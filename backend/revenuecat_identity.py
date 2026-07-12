"""Tożsamość użytkownika USLY używana przez RevenueCat.

Identyfikator RevenueCat:

- jest generowany wyłącznie przez backend,
- nie zawiera danych osobowych,
- nie ujawnia wewnętrznego User.id,
- pozostaje stały przez całe życie konta,
- może być bezpiecznie używany na Androidzie i iOS.
"""

from __future__ import annotations

from uuid import uuid4


REVENUECAT_APP_USER_ID_PREFIX = "usly_usr_"
REVENUECAT_APP_USER_ID_LENGTH = len(REVENUECAT_APP_USER_ID_PREFIX) + 32


def generate_revenuecat_app_user_id() -> str:
    """Generuje nowy, nieprzewidywalny identyfikator użytkownika RevenueCat."""

    return f"{REVENUECAT_APP_USER_ID_PREFIX}{uuid4().hex}"
