from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .horizons import HorizonDecision, horizon_decision
from .timeutil import parse_iso

KALSHI_MARKET_URL = "https://kalshi.com/markets/{ticker}"


@dataclass(frozen=True)
class KalshiMarket:
    ticker: str
    event_ticker: str | None
    title: str
    url: str
    status: str
    market_type: str | None
    close_time: datetime | None
    expiration_time: datetime | None
    yes_bid: float | None
    yes_ask: float | None
    last_price: float | None
    yes_price: float | None
    liquidity: float
    volume: float
    open_interest: float
    category: str | None
    raw: dict[str, Any]

    @property
    def active(self) -> bool:
        return self.status.lower() in {"active", "open"}


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


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _float_or_none(value)
        if parsed is not None:
            return parsed
    return None


def _price_from_market(raw: dict[str, Any]) -> tuple[float | None, float | None, float | None, float | None]:
    bid = _first_float(raw.get("yes_bid_dollars"), raw.get("yes_bid"))
    ask = _first_float(raw.get("yes_ask_dollars"), raw.get("yes_ask"))
    last = _first_float(raw.get("last_price_dollars"), raw.get("last_price"), raw.get("previous_price_dollars"))

    # Integer cent fields, when present, are 0-100. Dollar fields are 0-1 strings.
    if bid is not None and bid > 1:
        bid = bid / 100
    if ask is not None and ask > 1:
        ask = ask / 100
    if last is not None and last > 1:
        last = last / 100

    yes_price = None
    if bid is not None and ask is not None and 0 < bid < 1 and 0 < ask < 1 and bid <= ask:
        yes_price = (bid + ask) / 2
    elif last is not None and 0 < last < 1:
        yes_price = last
    elif ask is not None and 0 < ask < 1:
        yes_price = ask
    elif bid is not None and 0 < bid < 1:
        yes_price = bid
    return bid, ask, last, yes_price


def normalize_market(raw: dict[str, Any]) -> KalshiMarket:
    ticker = str(raw.get("ticker") or "").strip()
    close_raw = raw.get("close_time") or raw.get("latest_expiration_time") or raw.get("expiration_time")
    expiration_raw = raw.get("expiration_time") or raw.get("latest_expiration_time") or raw.get("close_time")
    close_time = None
    expiration_time = None
    if close_raw:
        try:
            close_time = parse_iso(str(close_raw))
        except ValueError:
            close_time = None
    if expiration_raw:
        try:
            expiration_time = parse_iso(str(expiration_raw))
        except ValueError:
            expiration_time = None

    bid, ask, last, yes_price = _price_from_market(raw)
    volume = max(
        _float_or_zero(raw.get("volume_dollars")),
        _float_or_zero(raw.get("volume")),
        _float_or_zero(raw.get("volume_fp")),
        _float_or_zero(raw.get("volume_24h_fp")),
    )
    liquidity = max(
        _float_or_zero(raw.get("liquidity_dollars")),
        _float_or_zero(raw.get("liquidity")),
        _float_or_zero(raw.get("open_interest_fp")),
    )
    open_interest = _float_or_zero(raw.get("open_interest_fp"))

    return KalshiMarket(
        ticker=ticker,
        event_ticker=raw.get("event_ticker"),
        title=str(raw.get("title") or raw.get("subtitle") or ticker),
        url=KALSHI_MARKET_URL.format(ticker=ticker) if ticker else "https://kalshi.com/markets",
        status=str(raw.get("status") or ""),
        market_type=raw.get("market_type"),
        close_time=close_time,
        expiration_time=expiration_time,
        yes_bid=bid,
        yes_ask=ask,
        last_price=last,
        yes_price=yes_price,
        liquidity=liquidity,
        volume=volume,
        open_interest=open_interest,
        category=raw.get("category"),
        raw=raw,
    )


def candidate_horizon(market: KalshiMarket, *, now: datetime) -> HorizonDecision:
    return horizon_decision(market.close_time or market.expiration_time, now=now, liquidity=market.liquidity, volume=market.volume)


def candidate_filter_reason(
    market: KalshiMarket,
    *,
    now: datetime,
    min_liquidity: float = 5_000,
    min_volume: float = 10_000,
    min_real_volume: float = 1_000,
    min_price: float = 0.05,
    max_price: float = 0.95,
    max_spread: float = 0.20,
) -> tuple[bool, str]:
    if not market.ticker:
        return False, "missing ticker"
    if not market.active:
        return False, "not active/open"
    if market.market_type and market.market_type.lower() != "binary":
        return False, "not binary"
    if market.yes_price is None:
        return False, "missing YES price"
    if market.yes_price < min_price or market.yes_price > max_price:
        return False, f"YES price outside candidate band ({market.yes_price:.3f})"
    if market.yes_bid is None or market.yes_ask is None:
        return False, "missing actionable bid/ask"
    if not (0 < market.yes_bid < 1 and 0 < market.yes_ask < 1 and market.yes_bid <= market.yes_ask):
        return False, f"bid/ask not actionable ({market.yes_bid}/{market.yes_ask})"
    if market.yes_ask - market.yes_bid > max_spread:
        return False, f"spread too wide ({(market.yes_ask - market.yes_bid) * 100:.1f}pp)"
    if market.volume < min_real_volume:
        return False, f"real volume below threshold ({market.volume:.0f} < {min_real_volume:.0f})"
    if market.liquidity < min_liquidity and market.volume < min_volume:
        return False, f"liquidity/volume below threshold ({market.liquidity:.0f}/{market.volume:.0f})"
    horizon = candidate_horizon(market, now=now)
    if not horizon.ok:
        return False, horizon.reason
    return True, horizon.reason


def market_payload(market: KalshiMarket) -> dict[str, Any]:
    return {
        "ticker": market.ticker,
        "eventTicker": market.event_ticker,
        "title": market.title,
        "url": market.url,
        "status": market.status,
        "marketType": market.market_type,
        "closeTime": market.close_time.isoformat().replace("+00:00", "Z") if market.close_time else None,
        "expirationTime": market.expiration_time.isoformat().replace("+00:00", "Z") if market.expiration_time else None,
        "yesPrice": market.yes_price,
        "yesBid": market.yes_bid,
        "yesAsk": market.yes_ask,
        "lastPrice": market.last_price,
        "liquidity": market.liquidity,
        "volume": market.volume,
        "openInterest": market.open_interest,
        "category": market.category,
    }
