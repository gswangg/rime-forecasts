from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .clv import due_clv_checkpoints
from .horizons import horizon_sort_key
from .polymarket import PolymarketMarket, candidate_filter_reason, candidate_group_key, candidate_horizon, market_payload
from .reasoning import PredictionWatch, watch_payload
from .state import default_state as _default_state
from .timeutil import isoformat_z, parse_iso
from .wake import build_wake_event, safe_part

SOURCE = "rime-forecasts/polymarket-daemon"


def default_state() -> dict[str, Any]:
    return _default_state()


def _stamp(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def _event_id(event_type: str, slug: str, now: datetime, extra: str | None = None) -> str:
    parts = ["rime", event_type.replace("_", "-"), safe_part(slug, max_len=50)]
    if extra:
        parts.append(safe_part(extra, max_len=20))
    parts.append(_stamp(now))
    return safe_part("-".join(parts), max_len=120)


def _clv_values(watch: PredictionWatch, market: PolymarketMarket | None) -> dict[str, Any]:
    if watch.price_at_writing is None or market is None or market.yes_price is None:
        return {"clvPp": None, "rawYesMovePp": None, "direction": "unknown"}

    raw_yes_move = round((market.yes_price - watch.price_at_writing) * 100, 2)
    if watch.prediction is None:
        return {"clvPp": raw_yes_move, "rawYesMovePp": raw_yes_move, "direction": "raw_yes"}

    edge = watch.prediction - watch.price_at_writing
    if edge > 0:
        # We were above-market YES; a higher YES price is favorable.
        return {"clvPp": raw_yes_move, "rawYesMovePp": raw_yes_move, "direction": "toward_yes"}
    if edge < 0:
        # We were below-market YES / effectively NO; a lower YES price is favorable.
        return {"clvPp": round(-raw_yes_move, 2), "rawYesMovePp": raw_yes_move, "direction": "toward_no"}
    return {"clvPp": raw_yes_move, "rawYesMovePp": raw_yes_move, "direction": "no_edge"}


def _candidate_prompt(market: PolymarketMarket, horizon) -> str:
    return (
        f"Evaluate this Polymarket {horizon.bucket} fast-feedback candidate ({horizon.days_to_resolution:.1f}d to resolution) "
        "against drive-prompt.md v3. If it clears the edge/confidence/economics bar, write the prediction file and update scorecard/journal. "
        "If it does not clear, acknowledge with wake_done and a concise skip outcome. "
        f"Market: {market.question} — {market.url}"
    )


def _price_move_prompt(watch: PredictionWatch, market: PolymarketMarket, move_pp: float) -> str:
    direction = "up" if move_pp > 0 else "down"
    return (
        f"Polymarket watched market moved {abs(move_pp):.1f}pp {direction}: {watch.title}. "
        "Review whether this changes CLV, thesis, or resolution-watch notes; update repo if needed, then call wake_done. "
        f"Market: {market.url}"
    )


def _clv_prompt(watch: PredictionWatch, checkpoint: str, clv_pp: float | None) -> str:
    clv_text = "unknown CLV" if clv_pp is None else f"{clv_pp:+.1f}pp CLV"
    return (
        f"CLV checkpoint {checkpoint} is due for {watch.title} ({clv_text}). "
        "Record fast-feedback learning if useful, update scorecard/ledger if appropriate, then call wake_done."
    )


def _resolution_prompt(watch: PredictionWatch, market: PolymarketMarket) -> str:
    resolution = market.inferred_resolution or "unknown"
    return (
        f"Polymarket watched market appears resolved/closed ({resolution}): {watch.title}. "
        "Check the market, append the Resolution section if final, update scorecard, commit if substantive, then call wake_done. "
        f"Market: {market.url}"
    )


def _candidate_event(
    market: PolymarketMarket,
    *,
    now: datetime,
    session_id: str,
    group_key: str,
    sibling_markets: list[PolymarketMarket],
) -> dict[str, Any]:
    horizon = candidate_horizon(market, now=now)
    return build_wake_event(
        event_id=_event_id("candidate_found", market.slug, now),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="candidate_found",
        priority=horizon.priority,
        prompt=_candidate_prompt(market, horizon),
        payload={
            "market": market_payload(market),
            "siblingMarkets": [market_payload(sibling) for sibling in sibling_markets],
            "candidateGroupKey": group_key,
            "horizon": {
                "bucket": horizon.bucket,
                "daysToResolution": horizon.days_to_resolution,
                "reason": horizon.reason,
                "priority": horizon.priority,
            },
            "dedupeKey": f"candidate:{group_key}",
        },
        source=SOURCE,
    )


def _price_moved_event(
    watch: PredictionWatch,
    market: PolymarketMarket,
    *,
    previous_price: float,
    move_pp: float,
    now: datetime,
    session_id: str,
) -> dict[str, Any]:
    return build_wake_event(
        event_id=_event_id("price_moved", market.slug, now),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="price_moved",
        priority=60,
        prompt=_price_move_prompt(watch, market, move_pp),
        payload={
            "watch": watch_payload(watch),
            "market": market_payload(market),
            "previousPrice": previous_price,
            "currentPrice": market.yes_price,
            "movePp": round(move_pp, 2),
            "dedupeKey": f"price:{market.slug}:{previous_price:.4f}->{market.yes_price:.4f}",
        },
        source=SOURCE,
    )


def _clv_event(
    watch: PredictionWatch,
    checkpoint: str,
    market: PolymarketMarket | None,
    *,
    now: datetime,
    session_id: str,
) -> dict[str, Any]:
    clv_values = _clv_values(watch, market)
    clv = clv_values["clvPp"]
    return build_wake_event(
        event_id=_event_id("clv_checkpoint_due", watch.slug, now, checkpoint),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="clv_checkpoint_due",
        priority=40,
        prompt=_clv_prompt(watch, checkpoint, clv),
        payload={
            "watch": watch_payload(watch),
            "checkpoint": checkpoint,
            "market": market_payload(market) if market else None,
            "priceAtWriting": watch.price_at_writing,
            "currentPrice": market.yes_price if market else None,
            "clvPp": clv,
            "rawYesMovePp": clv_values["rawYesMovePp"],
            "clvDirection": clv_values["direction"],
            "dedupeKey": f"clv:{watch.key}:{checkpoint}",
        },
        source=SOURCE,
    )


def _resolution_event(watch: PredictionWatch, market: PolymarketMarket, *, now: datetime, session_id: str) -> dict[str, Any]:
    return build_wake_event(
        event_id=_event_id("resolution_changed", market.slug, now),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="resolution_changed",
        priority=90,
        prompt=_resolution_prompt(watch, market),
        payload={
            "watch": watch_payload(watch),
            "market": market_payload(market),
            "resolution": market.inferred_resolution,
            "dedupeKey": f"resolution:{market.slug}",
        },
        source=SOURCE,
    )


def generate_events(
    *,
    markets: list[PolymarketMarket],
    watches: list[PredictionWatch],
    state: dict[str, Any],
    now: datetime,
    session_id: str,
    price_move_threshold: float = 0.05,
    price_move_cooldown_sec: int = 7200,
    price_move_cooldown_override: float = 0.15,
    price_move_reversal_band: float = 0.05,
    price_move_max_spread: float = 0.20,
    price_move_wide_spread_override: float = 0.25,
    max_candidate_events: int = 3,
    max_events: int = 10,
) -> list[dict[str, Any]]:
    markets_by_slug = {market.slug: market for market in markets if market.slug}
    watch_by_slug = {watch.slug: watch for watch in watches}
    watch_slugs = set(watch_by_slug)
    events: list[dict[str, Any]] = []

    # Resolutions first: final feedback beats discovery.
    for watch in watches:
        if len(events) >= max_events:
            return events
        market = markets_by_slug.get(watch.slug)
        if not market or not market.closed:
            continue
        if watch.slug in state.get("resolution_events", {}):
            continue
        events.append(_resolution_event(watch, market, now=now, session_id=session_id))

    # Price moves on watched markets.
    for watch in watches:
        if len(events) >= max_events:
            return events
        market = markets_by_slug.get(watch.slug)
        if not market or market.yes_price is None:
            continue
        if market.best_bid is None or market.best_ask is None:
            continue
        if not (0 < market.best_bid <= market.best_ask < 1):
            continue
        previous = state.get("last_prices", {}).get(watch.slug, {}).get("price")
        if previous is None:
            continue
        move = market.yes_price - float(previous)
        if abs(move) >= price_move_threshold:
            if (
                market.best_ask - market.best_bid > price_move_max_spread
                and abs(move) < price_move_wide_spread_override
            ):
                continue
            last_alert = state.get("last_price_move_events", {}).get(watch.slug, {})
            if last_alert.get("emitted_at") and last_alert.get("price") is not None:
                alert_time = parse_iso(last_alert["emitted_at"])
                alert_price = float(last_alert["price"])
                recent_alert = now - alert_time < timedelta(seconds=price_move_cooldown_sec)
                move_since_alert = market.yes_price - alert_price
                previous_alert_price = last_alert.get("previous_price")
                if recent_alert and previous_alert_price is not None:
                    last_alert_move = alert_price - float(previous_alert_price)
                    reversed_last_alert = last_alert_move * move_since_alert < 0
                    returned_near_pre_alert = abs(market.yes_price - float(previous_alert_price)) <= price_move_reversal_band
                    if reversed_last_alert and returned_near_pre_alert:
                        continue
                if recent_alert and abs(move_since_alert) < price_move_cooldown_override:
                    continue
            events.append(
                _price_moved_event(
                    watch,
                    market,
                    previous_price=float(previous),
                    move_pp=move * 100,
                    now=now,
                    session_id=session_id,
                )
            )

    # Fast feedback checkpoints.
    for due in due_clv_checkpoints(watches, state, now=now):
        if len(events) >= max_events:
            return events
        market = markets_by_slug.get(due.watch.slug)
        events.append(_clv_event(due.watch, due.checkpoint, market, now=now, session_id=session_id))

    # Candidate discovery last, capped separately to avoid inbox floods.
    candidate_count = 0
    grouped_markets: dict[str, list[PolymarketMarket]] = {}
    for market in markets:
        if market.slug:
            grouped_markets.setdefault(candidate_group_key(market), []).append(market)

    emitted_candidate_groups: set[str] = set()
    state_candidate_events = state.get("candidate_events", {})
    state_candidate_groups = set(state.get("candidate_event_groups", {}))
    for group_key, group in grouped_markets.items():
        if any(market.slug in state_candidate_events for market in group):
            state_candidate_groups.add(group_key)

    candidate_markets = sorted(
        markets,
        key=lambda market: horizon_sort_key(candidate_horizon(market, now=now), volume=market.volume, slug=market.slug),
    )
    for market in candidate_markets:
        if len(events) >= max_events or candidate_count >= max_candidate_events:
            break
        if market.slug in watch_slugs:
            continue
        if market.slug in state_candidate_events:
            continue
        group_key = candidate_group_key(market)
        if group_key in emitted_candidate_groups or group_key in state_candidate_groups:
            continue
        ok, _reason = candidate_filter_reason(market, now=now)
        if not ok:
            continue
        sibling_markets = sorted(
            (
                sibling
                for sibling in grouped_markets.get(group_key, [market])
                if sibling.slug and sibling.active and not sibling.closed and sibling.is_binary_yes_no and sibling.yes_price is not None
            ),
            key=lambda sibling: sibling.slug,
        )
        events.append(_candidate_event(market, now=now, session_id=session_id, group_key=group_key, sibling_markets=sibling_markets))
        emitted_candidate_groups.add(group_key)
        candidate_count += 1

    return events


def mark_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now: datetime) -> None:
    emitted_at = isoformat_z(now)
    state.setdefault("candidate_events", {})
    state.setdefault("candidate_event_groups", {})
    state.setdefault("last_prices", {})
    state.setdefault("price_move_events", {})
    state.setdefault("last_price_move_events", {})
    state.setdefault("clv_checkpoints", {})
    state.setdefault("resolution_events", {})
    state.setdefault("emitted_events", {})

    for event in events:
        payload = event.get("payload", {})
        dedupe_key = payload.get("dedupeKey") or f"event:{event['id']}"
        state["emitted_events"][dedupe_key] = {"event_id": event["id"], "emitted_at": emitted_at}

        event_type = event.get("type")
        market = payload.get("market") or {}
        slug = market.get("slug") or payload.get("watch", {}).get("slug")

        if event_type == "candidate_found" and slug:
            state["candidate_events"][slug] = {"event_id": event["id"], "emitted_at": emitted_at}
            group_key = payload.get("candidateGroupKey")
            if group_key:
                state["candidate_event_groups"][group_key] = {"event_id": event["id"], "emitted_at": emitted_at, "slug": slug}
        elif event_type == "price_moved" and slug:
            state["price_move_events"][dedupe_key] = {"event_id": event["id"], "emitted_at": emitted_at}
            if market.get("yesPrice") is not None:
                state["last_price_move_events"][slug] = {
                    "event_id": event["id"],
                    "emitted_at": emitted_at,
                    "price": market.get("yesPrice"),
                    "previous_price": payload.get("previousPrice"),
                    "move_pp": payload.get("movePp"),
                }
        elif event_type == "clv_checkpoint_due":
            watch = payload.get("watch", {})
            checkpoint = payload.get("checkpoint")
            key = f"{watch.get('reasoningPath', '').split('/')[-1]}:{watch.get('slug')}"
            if checkpoint and watch.get("slug"):
                state["clv_checkpoints"].setdefault(key, {})[checkpoint] = {
                    "event_id": event["id"],
                    "emitted_at": emitted_at,
                    "clv_pp": payload.get("clvPp"),
                }
        elif event_type == "resolution_changed" and slug:
            state["resolution_events"][slug] = {
                "event_id": event["id"],
                "emitted_at": emitted_at,
                "resolution": payload.get("resolution"),
            }

        if slug and market.get("yesPrice") is not None:
            state["last_prices"][slug] = {"price": market.get("yesPrice"), "observed_at": emitted_at}


def observe_watched_prices(state: dict[str, Any], markets: list[PolymarketMarket], watches: list[PredictionWatch], *, now: datetime) -> None:
    """Update last-price baselines after generation/writes.

    This prevents the first observation of a watch from generating a spurious price_moved event,
    while allowing future polls to detect moves from the last seen daemon price.
    """
    markets_by_slug = {market.slug: market for market in markets if market.slug}
    state.setdefault("last_prices", {})
    observed_at = isoformat_z(now)
    for watch in watches:
        market = markets_by_slug.get(watch.slug)
        if market and market.yes_price is not None:
            state["last_prices"][watch.slug] = {"price": market.yes_price, "observed_at": observed_at}
