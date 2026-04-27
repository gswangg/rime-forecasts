from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .horizons import HorizonDecision, horizon_decision
from .timeutil import parse_iso

POLYMARKET_MARKET_URL = "https://polymarket.com/market/{slug}"


@dataclass(frozen=True)
class PolymarketMarket:
    id: str
    slug: str
    question: str
    url: str
    active: bool
    closed: bool
    end_date: datetime | None
    outcomes: tuple[str, ...]
    outcome_prices: tuple[float, ...]
    yes_price: float | None
    best_bid: float | None
    best_ask: float | None
    last_trade_price: float | None
    liquidity: float
    volume: float
    raw: dict[str, Any]

    @property
    def is_binary_yes_no(self) -> bool:
        if len(self.outcomes) != 2:
            return False
        normalized = tuple(o.strip().lower() for o in self.outcomes)
        return normalized in (("yes", "no"), ("no", "yes"))

    @property
    def inferred_resolution(self) -> str | None:
        if not self.closed or self.yes_price is None:
            return None
        if self.yes_price >= 0.99:
            return "YES"
        if self.yes_price <= 0.01:
            return "NO"
        return "MKT"


def _decode_jsonish(value: Any, default: list[Any]) -> list[Any]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return list(default)
        return decoded if isinstance(decoded, list) else list(default)
    if isinstance(value, list):
        return value
    return list(default)


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _float_or_zero(value: Any) -> float:
    parsed = _float_or_none(value)
    return parsed if parsed is not None else 0.0


def normalize_market(raw: dict[str, Any]) -> PolymarketMarket:
    outcomes_raw = _decode_jsonish(raw.get("outcomes"), [])
    prices_raw = _decode_jsonish(raw.get("outcomePrices") or raw.get("outcome_prices"), [])
    outcomes = tuple(str(o) for o in outcomes_raw)
    outcome_prices = tuple(p for p in (_float_or_none(p) for p in prices_raw) if p is not None)

    yes_price = None
    if outcomes and outcome_prices:
        normalized_outcomes = [o.strip().lower() for o in outcomes]
        try:
            yes_index = normalized_outcomes.index("yes")
            yes_price = outcome_prices[yes_index]
        except (ValueError, IndexError):
            yes_price = outcome_prices[0]

    end_raw = raw.get("endDate") or raw.get("endDateIso")
    end_date = None
    if end_raw:
        try:
            end_date = parse_iso(str(end_raw))
        except ValueError:
            end_date = None

    slug = str(raw.get("slug") or "").strip()
    return PolymarketMarket(
        id=str(raw.get("id") or raw.get("conditionId") or slug),
        slug=slug,
        question=str(raw.get("question") or raw.get("title") or slug),
        url=POLYMARKET_MARKET_URL.format(slug=slug) if slug else "https://polymarket.com/",
        active=bool(raw.get("active", False)),
        closed=bool(raw.get("closed", False)),
        end_date=end_date,
        outcomes=outcomes,
        outcome_prices=outcome_prices,
        yes_price=yes_price,
        best_bid=_float_or_none(raw.get("bestBid")),
        best_ask=_float_or_none(raw.get("bestAsk")),
        last_trade_price=_float_or_none(raw.get("lastTradePrice")),
        liquidity=_float_or_zero(raw.get("liquidityNum", raw.get("liquidity"))),
        volume=_float_or_zero(raw.get("volumeNum", raw.get("volume"))),
        raw=raw,
    )


def candidate_horizon(market: PolymarketMarket, *, now: datetime) -> HorizonDecision:
    return horizon_decision(market.end_date, now=now, liquidity=market.liquidity, volume=market.volume)


def is_generic_team_match_market(question: str) -> bool:
    normalized = " ".join(question.strip().split())
    patterns = (
        r"^Will .+ vs\. .+ end in a draw\?$",
        r"^Will .+ win on \d{4}-\d{2}-\d{2}\?$",
    )
    return any(re.match(pattern, normalized) for pattern in patterns)


def candidate_filter_reason(
    market: PolymarketMarket,
    *,
    now: datetime,
    min_liquidity: float = 5_000,
    min_volume: float = 10_000,
    min_real_volume: float = 1_000,
    min_price: float = 0.05,
    max_price: float = 0.95,
    max_spread: float = 0.10,
) -> tuple[bool, str]:
    if not market.slug:
        return False, "missing slug"
    if not market.active or market.closed:
        return False, "not active or already closed"
    if not market.is_binary_yes_no:
        return False, "not binary YES/NO"
    if market.yes_price is None:
        return False, "missing YES price"
    if market.yes_price < min_price or market.yes_price > max_price:
        return False, f"YES price outside candidate band ({market.yes_price:.3f})"
    if market.best_bid is None or market.best_ask is None:
        return False, "missing actionable bid/ask"
    if not (0 < market.best_bid < 1 and 0 < market.best_ask < 1 and market.best_bid <= market.best_ask):
        return False, f"bid/ask not actionable ({market.best_bid}/{market.best_ask})"
    if market.best_ask - market.best_bid > max_spread:
        return False, f"spread too wide ({(market.best_ask - market.best_bid) * 100:.1f}pp)"
    if market.volume < min_real_volume:
        return False, f"real volume below threshold ({market.volume:.0f} < {min_real_volume:.0f})"
    if market.liquidity < min_liquidity and market.volume < min_volume:
        return False, f"liquidity/volume below threshold ({market.liquidity:.0f}/{market.volume:.0f})"
    if is_generic_team_match_market(market.question):
        return False, "generic team-match sports market without model edge"
    horizon = candidate_horizon(market, now=now)
    if not horizon.ok:
        return False, horizon.reason
    return True, horizon.reason


def market_payload(market: PolymarketMarket) -> dict[str, Any]:
    return {
        "id": market.id,
        "slug": market.slug,
        "question": market.question,
        "url": market.url,
        "active": market.active,
        "closed": market.closed,
        "endDate": market.end_date.isoformat().replace("+00:00", "Z") if market.end_date else None,
        "yesPrice": market.yes_price,
        "bestBid": market.best_bid,
        "bestAsk": market.best_ask,
        "lastTradePrice": market.last_trade_price,
        "liquidity": market.liquidity,
        "volume": market.volume,
        "outcomes": list(market.outcomes),
        "outcomePrices": list(market.outcome_prices),
        "inferredResolution": market.inferred_resolution,
    }
