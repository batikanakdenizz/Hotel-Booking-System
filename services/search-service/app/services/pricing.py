"""Runtime 15% discount logic.

Applied at response-build time only — NEVER persisted in the Redis cache.
See Plan §3.5. Anonymous users see base prices; authenticated callers see
base * discount_rate (default 0.85).
"""
from __future__ import annotations

from decimal import Decimal


def apply_discount(base_price: Decimal, *, is_authenticated: bool, discount_rate: float = 0.85) -> tuple[Decimal, bool]:
    """Returns (effective_price, discount_applied_flag).

    Rounded to cents (matches our DECIMAL(10,2) storage).
    """
    if not is_authenticated:
        return base_price, False
    discounted = (base_price * Decimal(str(discount_rate))).quantize(Decimal("0.01"))
    return discounted, True
