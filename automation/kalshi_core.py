from __future__ import annotations

from datetime import datetime
from typing import Any

from .horizons import horizon_sort_key
from .kalshi import KalshiMarket, candidate_filter_reason, candidate_horizon, market_payload
from .state import default_state as _default_state
from .timeutil import isoformat_z
from .wake import build_wake_event, safe_part

SOURCE = "rime-forecasts/kalshi-daemon"


def default_state() -> dict[str, Any]:
    return _default_state()


def _stamp(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def _event_id(event_type: str, ticker: str, now: datetime) -> str:
    return safe_part("-".join(["rime", "kalshi", event_type.replace("_", "-"), safe_part(ticker, max_len=55), _stamp(now)]), max_len=120)


def _candidate_prompt(market: KalshiMarket, horizon) -> str:
    return (
        f"Evaluate this Kalshi {horizon.bucket} fast-feedback candidate ({horizon.days_to_resolution:.1f}d to close) "
        "against drive-prompt.md v3. If it clears the edge/confidence/economics bar, write the prediction file and update scorecard/journal. "
        "If it does not clear, acknowledge with wake_done and a concise skip outcome. "
        f"Market: {market.title} — {market.url}"
    )


def _candidate_event(market: KalshiMarket, *, now: datetime, session_id: str) -> dict[str, Any]:
    horizon = candidate_horizon(market, now=now)
    return build_wake_event(
        event_id=_event_id("candidate_found", market.ticker, now),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="candidate_found",
        priority=horizon.priority,
        prompt=_candidate_prompt(market, horizon),
        payload={
            "venue": "Kalshi",
            "market": market_payload(market),
            "horizon": {
                "bucket": horizon.bucket,
                "daysToResolution": horizon.days_to_resolution,
                "reason": horizon.reason,
                "priority": horizon.priority,
            },
            "dedupeKey": f"candidate:kalshi:{market.ticker}",
        },
        source=SOURCE,
    )


def generate_events(
    *,
    markets: list[KalshiMarket],
    state: dict[str, Any],
    now: datetime,
    session_id: str,
    max_candidate_events: int = 3,
    max_events: int = 10,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    candidate_markets = sorted(
        markets,
        key=lambda market: horizon_sort_key(candidate_horizon(market, now=now), volume=market.volume, slug=market.ticker),
    )
    for market in candidate_markets:
        if len(events) >= max_events or len(events) >= max_candidate_events:
            break
        if market.ticker in state.get("candidate_events", {}):
            continue
        ok, _reason = candidate_filter_reason(market, now=now)
        if not ok:
            continue
        events.append(_candidate_event(market, now=now, session_id=session_id))
    return events


def mark_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now: datetime) -> None:
    emitted_at = isoformat_z(now)
    state.setdefault("candidate_events", {})
    state.setdefault("emitted_events", {})
    for event in events:
        payload = event.get("payload", {})
        market = payload.get("market", {})
        ticker = market.get("ticker")
        dedupe_key = payload.get("dedupeKey") or f"event:{event['id']}"
        state["emitted_events"][dedupe_key] = {"event_id": event["id"], "emitted_at": emitted_at}
        if event.get("type") == "candidate_found" and ticker:
            state["candidate_events"][ticker] = {"event_id": event["id"], "emitted_at": emitted_at}
