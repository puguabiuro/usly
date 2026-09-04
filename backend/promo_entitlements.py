"""Trwałe uprawnienia wynikające z promocji."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models import PromoCampaign, PromoRedemption


def has_usly95_lifetime(db: Session, user_id: int) -> bool:
    """Sprawdza trwałe uprawnienie Premium Lifetime z aktywowanego kodu USLY95."""
    return (
        db.query(PromoRedemption.id)
        .join(
            PromoCampaign,
            PromoCampaign.id == PromoRedemption.campaign_id,
        )
        .filter(
            PromoRedemption.user_id == user_id,
            PromoRedemption.status == "activated",
            PromoCampaign.code == "USLY95",
        )
        .first()
        is not None
    )
