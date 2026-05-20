from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json
from typing import Any, Iterable, Mapping

from .options import OptionChainSnapshot, OptionQuoteFilterConfig, contract_quote_filter_reason, days_to_expiry
from .timeutil import isoformat_z
from .wake import safe_part

DEFAULT_STRATEGY = "situational-awareness-ai-stack"
SOURCE = "rime-forecasts/sa-thesis-scan"


@dataclass(frozen=True)
class SAThesisCandidate:
    candidate_id: str
    dedupe_key: str
    underlying: str
    theme: str
    direction: str
    trigger_reasons: tuple[str, ...]
    spot: float
    option_expiry: date
    days_to_expiry: int
    chain_summary: dict[str, Any]
    thesis_fixture: dict[str, Any]
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidateId": self.candidate_id,
            "dedupeKey": self.dedupe_key,
            "underlying": self.underlying,
            "theme": self.theme,
            "direction": self.direction,
            "triggerReasons": list(self.trigger_reasons),
            "spot": self.spot,
            "optionExpiry": self.option_expiry.isoformat(),
            "daysToExpiry": self.days_to_expiry,
            "chainSummary": self.chain_summary,
            "thesisFixture": self.thesis_fixture,
            "priority": self.priority,
        }


def load_watchlist(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("SA watchlist must be a JSON object")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("SA watchlist requires entries[]")
    defaults = data.get("defaults", {})
    if defaults is not None and not isinstance(defaults, dict):
        raise ValueError("SA watchlist defaults must be an object")
    data.setdefault("strategy", DEFAULT_STRATEGY)
    data.setdefault("defaults", {})
    return data


def merged_entry(defaults: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(entry)
    return merged


def entry_enabled(entry: Mapping[str, Any]) -> bool:
    return entry.get("enabled", True) is not False and entry.get("active", True) is not False


def select_expiry(
    expiries: Iterable[date],
    *,
    now: datetime,
    target_days: int,
    min_days_to_expiry: int,
    max_days_to_expiry: int,
) -> date | None:
    choices = []
    for expiry in expiries:
        dte = days_to_expiry(expiry, now=now)
        if min_days_to_expiry <= dte <= max_days_to_expiry:
            choices.append((abs(dte - target_days), dte, expiry))
    if not choices:
        return None
    return sorted(choices)[0][2]


def spot_mid(snapshot: OptionChainSnapshot) -> float | None:
    mid = snapshot.underlying_mid
    if mid is not None:
        return mid
    prices = []
    for contract in snapshot.contracts:
        if contract.underlying_bid is not None and contract.underlying_ask is not None and contract.underlying_bid <= contract.underlying_ask:
            prices.append((contract.underlying_bid + contract.underlying_ask) / 2)
    if not prices:
        return None
    return sum(prices) / len(prices)


def quote_config_from_entry(entry: Mapping[str, Any]) -> OptionQuoteFilterConfig:
    def f(name: str, default: float) -> float:
        value = entry.get(name)
        return float(value) if value is not None else default

    def i(name: str, default: int) -> int:
        value = entry.get(name)
        return int(value) if value is not None else default

    return OptionQuoteFilterConfig(
        allow_underlyings=(str(entry.get("underlying", "")).upper(),),
        min_days_to_expiry=i("minDaysToExpiry", 1),
        max_days_to_expiry=i("maxDaysToExpiry", 60),
        min_volume=f("minVolume", 100.0),
        min_open_interest=f("minOpenInterest", 500.0),
        min_premium=f("minPremium", 0.05),
        max_single_leg_abs_spread=f("maxSingleLegAbsSpread", 0.05),
        max_single_leg_spread_pct_of_mid=f("maxSingleLegSpreadPctOfMid", 0.15),
        max_quote_age_seconds=i("maxQuoteAgeSeconds", 0) or None,
    )


def chain_summary(snapshot: OptionChainSnapshot, *, now: datetime, config: OptionQuoteFilterConfig) -> dict[str, Any]:
    liquid = []
    calls = 0
    puts = 0
    expiries: set[str] = set()
    for contract in snapshot.contracts:
        if contract.right == "call":
            calls += 1
        elif contract.right == "put":
            puts += 1
        expiries.add(contract.expiry.isoformat())
        ok, _ = contract_quote_filter_reason(contract, now=now, config=config)
        if ok:
            liquid.append(contract)
    return {
        "provider": snapshot.provider,
        "quoteTs": isoformat_z(snapshot.quote_ts) if snapshot.quote_ts else None,
        "quoteDelaySeconds": snapshot.quote_delay_seconds,
        "underlyingBid": snapshot.underlying_bid,
        "underlyingAsk": snapshot.underlying_ask,
        "contractCount": len(snapshot.contracts),
        "callCount": calls,
        "putCount": puts,
        "expiryCount": len(expiries),
        "liquidContractCount": len(liquid),
        "liquidCallCount": sum(1 for c in liquid if c.right == "call"),
        "liquidPutCount": sum(1 for c in liquid if c.right == "put"),
        "minStrike": min((c.strike for c in snapshot.contracts), default=None),
        "maxStrike": max((c.strike for c in snapshot.contracts), default=None),
    }


def _direction_value(value: Any, direction: str, default: float) -> float:
    if isinstance(value, Mapping):
        raw = value.get(direction)
        if raw is None:
            raw = value.get(direction.lower())
        if raw is None:
            raw = value.get("default")
    else:
        raw = value
    if raw is None:
        return default
    return float(raw)


def entry_directions(entry: Mapping[str, Any]) -> tuple[str, ...]:
    raw = entry.get("directions") or entry.get("direction") or ("up",)
    values = (raw,) if isinstance(raw, str) else tuple(raw)
    directions: list[str] = []
    for value in values:
        text = str(value).strip().lower()
        if text not in {"up", "down"}:
            raise ValueError(f"unsupported SA thesis direction: {text!r}")
        directions.append(text)
    return tuple(dict.fromkeys(directions))


def target_price_for_direction(spot: float, entry: Mapping[str, Any], direction: str) -> float:
    move = _direction_value(entry.get("targetMovePct"), direction, 0.20)
    target = spot * (1 + move) if direction == "up" else spot * (1 - move)
    return round(target, 2)


def target_probability_for_direction(entry: Mapping[str, Any], direction: str) -> float:
    return _direction_value(entry.get("targetProbability"), direction, 0.25)


def trigger_reasons_for_entry(
    *,
    entry: Mapping[str, Any],
    state_row: Mapping[str, Any] | None,
    current_spot: float,
    current_liquid_contracts: int,
    force: bool = False,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if force:
        reasons.append("force")
    if state_row is None:
        if entry.get("emitOnFirstSeen", False):
            reasons.append("first_seen")
        return tuple(reasons)

    min_liquid = int(entry.get("minLiquidContracts", 2))
    previous_liquid = int(state_row.get("last_liquid_contracts", 0) or 0)
    if previous_liquid < min_liquid <= current_liquid_contracts:
        reasons.append(f"liquidity_crossed_{min_liquid}")

    previous_spot = state_row.get("last_spot")
    trigger_pct = float(entry.get("spotMoveTriggerPct", 0.12))
    if previous_spot is not None:
        previous_spot = float(previous_spot)
        if previous_spot > 0:
            move = current_spot / previous_spot - 1
            if abs(move) >= trigger_pct:
                reasons.append(f"spot_move_{move:+.1%}")
    return tuple(reasons)


def build_candidate(
    *,
    strategy: str,
    entry: Mapping[str, Any],
    direction: str,
    now: datetime,
    spot: float,
    option_expiry: date,
    chain_summary: dict[str, Any],
    trigger_reasons: tuple[str, ...],
) -> SAThesisCandidate:
    underlying = str(entry.get("underlying") or "").upper()
    if not underlying:
        raise ValueError("SA watchlist entry missing underlying")
    theme = str(entry.get("theme") or "uncategorized")
    target_price = target_price_for_direction(spot, entry, direction)
    target_probability = target_probability_for_direction(entry, direction)
    if not 0 < target_probability < 1:
        raise ValueError(f"target probability for {underlying} {direction} must be inside (0, 1)")

    thesis_id = safe_part(
        f"sa-{underlying.lower()}-{theme}-{direction}-{option_expiry.isoformat()}-{target_price}",
        max_len=90,
    )
    candidate_id = safe_part(f"{thesis_id}-{now.strftime('%Y%m%dT%H%M%SZ')}", max_len=115)
    catalyst = str(entry.get("catalyst") or f"{theme} catalyst/repricing window")
    mechanism = str(entry.get("mechanism") or entry.get("thesis") or f"{underlying} {theme} thesis")
    falsifier = str(entry.get("falsifier") or "thesis mechanism fails or option chain prices the move fully")
    planned_exit = str(entry.get("plannedExit") or "first liquid post-catalyst mark; otherwise close before expiry week")
    event_date = entry.get("eventDate") or entry.get("event_date") or entry.get("catalystDate") or entry.get("catalyst_date") or option_expiry.isoformat()
    allowed_structures = entry.get("allowedStructures") or ["debit_vertical"]

    thesis = {
        "id": thesis_id,
        "active": False,
        "direction": direction,
        "targetPrice": target_price,
        "targetProbability": target_probability,
        "eventDate": event_date,
        "optionExpiry": option_expiry.isoformat(),
        "maxLossCap": float(entry.get("maxLossCap", 200.0)),
        "minRewardRisk": float(entry.get("minRewardRisk", 3.0)),
        "minEdgePctOfRisk": float(entry.get("minEdgePctOfRisk", 0.30)),
        "minProbabilityMargin": float(entry.get("minProbabilityMargin", 0.08)),
        "allowedStructures": list(allowed_structures),
        "thesis": f"{mechanism} Direction: {direction}; target {target_price} from spot {round(spot, 2)}.",
        "catalyst": catalyst,
        "plannedExit": planned_exit,
        "falsifier": falsifier,
    }
    fixture = {
        "active": False,
        "underlying": underlying,
        "strategy": strategy,
        "generatedAt": isoformat_z(now),
        "source": SOURCE,
        "theme": theme,
        "notes": "Generated inactive thesis candidate. Promote manually only after review.",
        "theses": [thesis],
    }
    dte = days_to_expiry(option_expiry, now=now)
    dedupe_key = f"sa_thesis:{underlying}:{theme}:{direction}:{option_expiry.isoformat()}:{round(target_price, 2)}"
    return SAThesisCandidate(
        candidate_id=candidate_id,
        dedupe_key=dedupe_key,
        underlying=underlying,
        theme=theme,
        direction=direction,
        trigger_reasons=trigger_reasons,
        spot=round(spot, 4),
        option_expiry=option_expiry,
        days_to_expiry=dte,
        chain_summary=chain_summary,
        thesis_fixture=fixture,
        priority=int(entry.get("priority", 55)),
    )


def update_underlying_state(
    state: dict[str, Any],
    *,
    underlying: str,
    now: datetime,
    spot: float,
    liquid_contracts: int,
    option_expiry: date | None,
    provider: str,
) -> None:
    underlyings = state.setdefault("underlyings", {})
    underlyings[underlying] = {
        "last_scanned_at": isoformat_z(now),
        "last_spot": round(spot, 4),
        "last_liquid_contracts": int(liquid_contracts),
        "last_option_expiry": option_expiry.isoformat() if option_expiry else None,
        "last_provider": provider,
    }
