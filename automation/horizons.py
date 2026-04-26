from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

MIN_DAYS = 1
PRIMARY_MAX_DAYS = 7
SECONDARY_MAX_DAYS = 21
TERTIARY_MAX_DAYS = 45
TERTIARY_MIN_LIQUIDITY = 25_000
TERTIARY_MIN_VOLUME = 100_000


@dataclass(frozen=True)
class HorizonDecision:
    ok: bool
    reason: str
    bucket: str | None
    priority: int
    days_to_resolution: float | None


def horizon_decision(
    end_date: datetime | None,
    *,
    now: datetime,
    liquidity: float = 0,
    volume: float = 0,
    tertiary_min_liquidity: float = TERTIARY_MIN_LIQUIDITY,
    tertiary_min_volume: float = TERTIARY_MIN_VOLUME,
) -> HorizonDecision:
    if end_date is None:
        return HorizonDecision(False, "missing end date", None, 0, None)

    days = (end_date - now).total_seconds() / 86_400
    if days < MIN_DAYS:
        return HorizonDecision(False, f"too near resolution ({days:.1f}d < {MIN_DAYS}d)", None, 0, days)
    if days <= PRIMARY_MAX_DAYS:
        return HorizonDecision(True, f"primary fast-feedback horizon ({days:.1f}d)", "primary", 80, days)
    if days <= SECONDARY_MAX_DAYS:
        return HorizonDecision(True, f"secondary fast-feedback horizon ({days:.1f}d)", "secondary", 65, days)
    if days <= TERTIARY_MAX_DAYS:
        if liquidity >= tertiary_min_liquidity or volume >= tertiary_min_volume:
            return HorizonDecision(True, f"tertiary high-liquidity horizon ({days:.1f}d)", "tertiary", 45, days)
        return HorizonDecision(
            False,
            f"tertiary horizon lacks high-liquidity signal ({days:.1f}d, liquidity={liquidity:.0f}, volume={volume:.0f})",
            "tertiary",
            0,
            days,
        )
    return HorizonDecision(False, f"outside fast-feedback window ({days:.1f}d > {TERTIARY_MAX_DAYS}d)", None, 0, days)


def horizon_sort_key(decision: HorizonDecision, *, volume: float = 0, slug: str = "") -> tuple:
    bucket_rank = {"primary": 0, "secondary": 1, "tertiary": 2}.get(decision.bucket, 9)
    days = decision.days_to_resolution if decision.days_to_resolution is not None else 9999
    return (bucket_rank, days, -volume, slug)
