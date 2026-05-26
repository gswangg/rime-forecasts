from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json
from typing import Any, Iterable, Mapping

from .options import (
    OptionChainSnapshot,
    OptionQuoteFilterConfig,
    contract_quote_filter_reason,
    days_to_expiry,
    evaluate_structure_edge,
    generate_structures_for_thesis,
    model_fair_value_from_thesis,
    normalize_thesis,
)
from .timeutil import isoformat_z, parse_iso
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
    prequalification: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
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
        if self.prequalification is not None:
            payload["prequalification"] = self.prequalification
        return payload


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
    strikes: set[float] = set()
    for contract in snapshot.contracts:
        if contract.right == "call":
            calls += 1
        elif contract.right == "put":
            puts += 1
        expiries.add(contract.expiry.isoformat())
        strikes.add(contract.strike)
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
        "strikeCount": len(strikes),
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


def _parse_state_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_iso(str(value))
    except Exception:
        return None


def trigger_reasons_for_entry(
    *,
    entry: Mapping[str, Any],
    state_row: Mapping[str, Any] | None,
    current_spot: float,
    current_liquid_contracts: int,
    force: bool = False,
    now: datetime | None = None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if force:
        reasons.append("force")
    emit_first_seen = entry.get("emitOnFirstSeen", False)
    if state_row is None:
        if emit_first_seen:
            reasons.append("first_seen")
        return tuple(reasons)

    if emit_first_seen and not state_row.get("first_seen_reviewed"):
        recheck_hours = entry.get("firstSeenRecheckHours")
        last_checked = _parse_state_ts(state_row.get("first_seen_last_checked_at"))
        if recheck_hours is None or last_checked is None or now is None:
            reasons.append("first_seen")
        else:
            elapsed = (now - last_checked).total_seconds()
            if elapsed >= float(recheck_hours) * 3600:
                reasons.append("first_seen")

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
    return tuple(dict.fromkeys(reasons))


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
    prequalification: dict[str, Any] | None = None,
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
        prequalification=prequalification,
    )


def provider_sanity_check(snapshot: OptionChainSnapshot, *, spot: float, entry: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    strikes = sorted({contract.strike for contract in snapshot.contracts if contract.strike > 0})
    bid = snapshot.underlying_bid
    ask = snapshot.underlying_ask
    underlying_spread_pct = None
    if bid is None or ask is None or bid <= 0 or ask <= 0 or bid > ask:
        blockers.append("invalid underlying bid/ask")
    else:
        underlying_spread_pct = (ask - bid) / ((ask + bid) / 2)
        max_spread_pct = float(entry.get("maxUnderlyingSpreadPct", 0.03))
        if underlying_spread_pct > max_spread_pct:
            blockers.append(f"underlying spread {underlying_spread_pct:.3f} exceeds max {max_spread_pct:.3f}")

    min_contracts = int(entry.get("minOptionContracts", 4))
    if len(snapshot.contracts) < min_contracts:
        blockers.append(f"contract count {len(snapshot.contracts)} below min {min_contracts}")

    min_strikes = int(entry.get("minStrikeCount", 3))
    if len(strikes) < min_strikes:
        blockers.append(f"strike count {len(strikes)} below min {min_strikes}")

    min_strike = min(strikes) if strikes else None
    max_strike = max(strikes) if strikes else None
    max_gap_pct = float(entry.get("maxSpotStrikeGapPct", 0.35))
    if min_strike is None or max_strike is None:
        blockers.append("missing strike ladder")
    elif spot < min_strike * (1 - max_gap_pct) or spot > max_strike * (1 + max_gap_pct):
        blockers.append(f"spot {spot:.2f} outside strike ladder {min_strike:.2f}-{max_strike:.2f} with max gap {max_gap_pct:.0%}")

    max_chain_quote_age = entry.get("maxChainQuoteAgeSeconds")
    quote_age = snapshot.quote_delay_seconds
    if max_chain_quote_age is not None:
        if quote_age is None:
            blockers.append("missing chain quote timestamp")
        elif quote_age > int(max_chain_quote_age):
            blockers.append(f"chain quote age {quote_age}s exceeds max {int(max_chain_quote_age)}s")
    elif quote_age is not None and quote_age > 6 * 3600:
        warnings.append(f"chain quote age {quote_age}s exceeds 6h")

    return {
        "passes": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "metrics": {
            "spot": round(spot, 4),
            "underlyingSpreadPct": round(underlying_spread_pct, 6) if underlying_spread_pct is not None else None,
            "contractCount": len(snapshot.contracts),
            "strikeCount": len(strikes),
            "minStrike": min_strike,
            "maxStrike": max_strike,
            "quoteDelaySeconds": quote_age,
        },
    }


def directional_liquid_contracts(
    snapshot: OptionChainSnapshot,
    *,
    direction: str,
    target_price: float,
    now: datetime,
    config: OptionQuoteFilterConfig,
) -> tuple[int, int]:
    right = "call" if direction == "up" else "put"
    matching = 0
    liquid = 0
    for contract in snapshot.contracts:
        if contract.right != right:
            continue
        if direction == "up" and contract.strike > target_price:
            continue
        if direction == "down" and contract.strike < target_price:
            continue
        matching += 1
        ok, _ = contract_quote_filter_reason(contract, now=now, config=config)
        if ok:
            liquid += 1
    return liquid, matching


def _probability_margin(model_probability: float | None, breakeven_probability: float | None) -> float | None:
    if model_probability is None or breakeven_probability is None:
        return None
    return model_probability - breakeven_probability


def prequalify_candidate(
    snapshot: OptionChainSnapshot,
    candidate: SAThesisCandidate,
    *,
    entry: Mapping[str, Any],
    now: datetime,
    config: OptionQuoteFilterConfig,
) -> dict[str, Any]:
    raw_thesis = candidate.thesis_fixture["theses"][0]
    thesis = normalize_thesis(raw_thesis)
    sanity = provider_sanity_check(snapshot, spot=candidate.spot, entry=entry, now=now)
    target_price = float(raw_thesis["targetPrice"])
    liquid_directional, matching_directional = directional_liquid_contracts(
        snapshot,
        direction=candidate.direction,
        target_price=target_price,
        now=now,
        config=config,
    )
    min_directional = int(entry.get("minDirectionalLiquidContracts", entry.get("minLiquidContracts", 2)))
    directional_ok = liquid_directional >= min_directional

    structures = generate_structures_for_thesis(snapshot.contracts, thesis, now=now, config=config)
    pass_count = 0
    near_count = 0
    best: dict[str, Any] | None = None
    near_examples: list[dict[str, Any]] = []
    edge_tolerance = float(entry.get("nearPassEdgeTolerance", 0.10))
    probability_tolerance = float(entry.get("nearPassProbabilityMarginTolerance", 0.02))
    reward_risk_tolerance = float(entry.get("nearPassRewardRiskTolerance", 0.0))
    min_edge_near = max(0.0, thesis.min_edge_pct_of_risk - edge_tolerance)
    min_probability_near = max(0.0, (thesis.min_probability_margin or 0.0) - probability_tolerance)
    min_reward_risk_near = max(0.0, thesis.min_reward_risk - reward_risk_tolerance)
    high_priority = int(entry.get("priority", 55)) >= int(entry.get("nearPassMinPriority", 70))

    for structure in structures:
        model_fair, payoff_if_hit, reward_risk = model_fair_value_from_thesis(structure, thesis)
        evaluation = evaluate_structure_edge(
            structure,
            model_fair_value=model_fair,
            min_edge_pct_of_risk=thesis.min_edge_pct_of_risk,
            model_probability=thesis.target_probability,
            min_probability_margin=thesis.min_probability_margin,
            max_loss_cap=thesis.max_loss_cap,
        )
        probability_margin = _probability_margin(evaluation.model_probability, evaluation.breakeven_probability)
        max_loss_ok = structure.max_loss is not None and structure.max_loss <= thesis.max_loss_cap
        edge_ok = evaluation.edge_pct_of_risk is not None and evaluation.edge_pct_of_risk >= min_edge_near
        probability_ok = probability_margin is None or probability_margin >= min_probability_near
        reward_ok = reward_risk is not None and reward_risk >= min_reward_risk_near
        near = bool(high_priority and max_loss_ok and edge_ok and probability_ok and reward_ok)
        if evaluation.passes and reward_risk is not None and reward_risk >= thesis.min_reward_risk:
            pass_count += 1
        elif near:
            near_count += 1
            if len(near_examples) < 3:
                near_examples.append(
                    {
                        "structure": structure.to_dict(),
                        "edgePctOfRisk": evaluation.edge_pct_of_risk,
                        "probabilityMargin": round(probability_margin, 8) if probability_margin is not None else None,
                        "rewardRisk": round(reward_risk, 8) if reward_risk is not None else None,
                        "blockedReasons": list(evaluation.blocked_reasons),
                    }
                )

        score_edge = evaluation.edge_pct_of_risk if evaluation.edge_pct_of_risk is not None else -999.0
        score_margin = probability_margin if probability_margin is not None else -999.0
        score_rr = reward_risk if reward_risk is not None else -999.0
        score = (1 if evaluation.passes else 0, 1 if near else 0, score_edge, score_margin, score_rr)
        best_score = tuple(best.get("_score", ())) if best else None
        if best is None or score > best_score:
            best = {
                "_score": score,
                "structure": structure.to_dict(),
                "edgePctOfRisk": evaluation.edge_pct_of_risk,
                "probabilityMargin": round(probability_margin, 8) if probability_margin is not None else None,
                "rewardRisk": round(reward_risk, 8) if reward_risk is not None else None,
                "maxLoss": structure.max_loss,
                "maxGain": structure.max_gain,
                "blockedReasons": list(evaluation.blocked_reasons),
            }

    structure_ok = pass_count > 0 or near_count > 0
    blockers: list[str] = []
    if not sanity["passes"]:
        blockers.extend(f"provider sanity: {reason}" for reason in sanity["blockers"])
    if not directional_ok:
        blockers.append(f"directional liquid contracts {liquid_directional} below min {min_directional}")
    if not structures:
        blockers.append("no candidate structures after quote filters")
    elif not structure_ok:
        blockers.append("no passing or near-pass structure")

    if best and "_score" in best:
        best = {key: value for key, value in best.items() if key != "_score"}

    return {
        "passes": not blockers,
        "prequalified": not blockers,
        "mode": "pass" if pass_count else "near_pass" if near_count else "blocked",
        "blockers": blockers,
        "providerSanity": sanity,
        "directionalLiquidity": {
            "liquidContractCount": liquid_directional,
            "matchingContractCount": matching_directional,
            "minDirectionalLiquidContracts": min_directional,
            "passes": directional_ok,
        },
        "structureSearch": {
            "generatedStructureCount": len(structures),
            "passingStructureCount": pass_count,
            "nearPassStructureCount": near_count,
            "nearPassMinPriority": int(entry.get("nearPassMinPriority", 70)),
            "highPriorityNearPassAllowed": high_priority,
            "best": best,
            "nearExamples": near_examples,
        },
    }


def emission_requires_prequalification(entry: Mapping[str, Any], reasons: tuple[str, ...]) -> bool:
    """Return True when the scanner should refuse to emit an unqualified candidate.

    The historical name was ``first_seen_requires_prequalification`` and only
    gated first-seen triggers. Operationally that left a noise hole: when a
    sparse-chain entry crossed the ``minLiquidContracts`` floor or made a
    qualifying spot move, the scanner would still emit a paired-direction
    candidate wake even though prequalification (provider sanity, directional
    liquidity, structure search) explicitly failed.

    Broaden the gate: any non-force trigger requires prequalification by
    default. ``force`` is the operator-driven sweep escape hatch and intentionally
    bypasses the gate. ``prequalifyEmissions`` is the new opt-out flag at the
    watchlist defaults/entry level; ``prequalifyFirstSeen`` is accepted for
    backward compatibility but only controls the first-seen carve-out for legacy
    fixtures.
    """
    if "force" in reasons:
        return False
    emissions_flag = entry.get("prequalifyEmissions")
    if emissions_flag is False:
        return False
    if emissions_flag is True:
        return True
    legacy_flag = entry.get("prequalifyFirstSeen")
    if legacy_flag is False and reasons == ("first_seen",):
        return False
    return True


# Backward-compatibility alias for any consumer that imported the old name.
first_seen_requires_prequalification = emission_requires_prequalification


def update_underlying_state(
    state: dict[str, Any],
    *,
    underlying: str,
    now: datetime,
    spot: float,
    liquid_contracts: int,
    option_expiry: date | None,
    provider: str,
    first_seen_reviewed: bool | None = None,
    first_seen_checked: bool = False,
) -> None:
    underlyings = state.setdefault("underlyings", {})
    existing = underlyings.get(underlying, {}) if isinstance(underlyings.get(underlying), dict) else {}
    row = dict(existing)
    row.update(
        {
            "last_scanned_at": isoformat_z(now),
            "last_spot": round(spot, 4),
            "last_liquid_contracts": int(liquid_contracts),
            "last_option_expiry": option_expiry.isoformat() if option_expiry else None,
            "last_provider": provider,
        }
    )
    if first_seen_checked:
        row["first_seen_last_checked_at"] = isoformat_z(now)
    if first_seen_reviewed is not None:
        row["first_seen_reviewed"] = bool(first_seen_reviewed)
        if first_seen_reviewed:
            row["first_seen_reviewed_at"] = isoformat_z(now)
    underlyings[underlying] = row
