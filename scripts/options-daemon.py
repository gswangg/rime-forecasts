#!/usr/bin/env python3
"""Shadow-only listed-options opportunity daemon for rime-forecasts.

v0.1 is fixture-driven. A fixture supplies an option chain plus thesis-derived
candidate structures/fair values. The daemon applies quote-quality filters,
builds capped-risk structures, evaluates edge after executable bid/ask, and
emits/prints options_signal_candidate events for model review.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_WAKE_ROOT, require_session_id
from automation.options import (
    OptionChainProvider,
    OptionContract,
    OptionOpportunity,
    OptionQuoteFilterConfig,
    OptionStructure,
    atm_straddle_implied_move,
    build_credit_vertical,
    build_debit_vertical,
    build_long_option,
    contract_quote_filter_reason,
    days_to_expiry,
    evaluate_structure_edge,
    find_opportunities_for_thesis,
    generate_structures_for_thesis,
    model_fair_value_from_thesis,
    normalize_thesis,
    option_structure_label,
    option_ticket_from_event,
    parse_option_chain_snapshot,
    target_move_pct_from_spot,
    write_option_ticket,
)
from automation.options_providers import TradierOptionProvider
from automation.state import save_state
from automation.timeutil import isoformat_z, parse_iso, utcnow
from automation.wake import build_wake_event, safe_part, write_wake_event

SOURCE = "rime-forecasts/options-daemon"
DEFAULT_STATE_PATH = Path("automation/state/options-daemon.json")


class OptionsDaemonError(ValueError):
    pass


def load_fixture(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OptionsDaemonError("options fixture must be a JSON object")
    signals = data.get("signals", [])
    if not isinstance(signals, list):
        raise OptionsDaemonError("options fixture signals must be a list")
    theses = data.get("theses", [])
    if not isinstance(theses, list):
        raise OptionsDaemonError("options fixture theses must be a list")
    has_chain = "chain" in data or "contracts" in data
    has_provider_theses = bool(data.get("underlying") and theses)
    if not has_chain and not has_provider_theses:
        raise OptionsDaemonError("options fixture requires chain/contracts or underlying plus theses[] for provider-backed loading")
    data.setdefault("_fixturePath", str(path))
    return data


def load_fixtures(paths: list[Path] | None = None, fixture_dir: Path | None = None) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for path in paths or []:
        fixtures.append(load_fixture(path))
    if fixture_dir:
        if not fixture_dir.exists():
            raise OptionsDaemonError(f"fixture directory does not exist: {fixture_dir}")
        for path in sorted(fixture_dir.glob("*.json")):
            fixtures.append(load_fixture(path))
    return fixtures


def load_options_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"emitted_signals": {}, "clv_events": {}, "exit_events": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    state = data if isinstance(data, dict) else {}
    state.setdefault("emitted_signals", {})
    state.setdefault("clv_events", {})
    state.setdefault("exit_events", {})
    state.setdefault("thesis_refresh_events", {})
    state.setdefault("thesis_refresh_status", {})
    return state


def _contract_by_symbol(contracts: tuple[OptionContract, ...]) -> dict[str, OptionContract]:
    return {contract.symbol: contract for contract in contracts}


def build_provider(name: str | None) -> OptionChainProvider | None:
    if not name:
        return None
    normalized = name.strip().lower()
    if normalized == "tradier":
        return TradierOptionProvider.from_env()
    raise OptionsDaemonError(f"unsupported options provider: {name!r}")


def is_active(row: dict[str, Any]) -> bool:
    return row.get("active", True) is not False and row.get("enabled", True) is not False


def thesis_expiry_value(row: dict[str, Any]) -> Any:
    return (
        row.get("optionExpiry")
        or row.get("option_expiry")
        or row.get("targetExpiry")
        or row.get("target_expiry")
        or row.get("expiry")
        or row.get("eventDate")
        or row.get("event_date")
    )


def materialize_provider_fixture(fixture: dict[str, Any], provider: OptionChainProvider | None) -> dict[str, Any]:
    if "chain" in fixture or "contracts" in fixture:
        return fixture
    if provider is None:
        raise OptionsDaemonError("provider-backed thesis fixture requires --provider")
    underlying = str(fixture.get("underlying") or "").upper()
    if not underlying:
        raise OptionsDaemonError("provider-backed thesis fixture requires underlying")
    expiries: set[Any] = set()
    for row in fixture.get("theses", []):
        if isinstance(row, dict) and is_active(row):
            expiry = thesis_expiry_value(row)
            if expiry:
                expiries.add(expiry)
    chains = []
    if expiries:
        for expiry_raw in sorted(expiries):
            expiry = parse_iso(str(expiry_raw) + "T00:00:00Z").date() if "T" not in str(expiry_raw) else parse_iso(str(expiry_raw)).date()
            chains.append(provider.fetch_chain(underlying, expiry))
    else:
        chains.append(provider.fetch_chain(underlying))
    contracts = []
    quote_ts = None
    underlying_bid = None
    underlying_ask = None
    for chain in chains:
        quote_ts = quote_ts or chain.quote_ts
        underlying_bid = underlying_bid if underlying_bid is not None else chain.underlying_bid
        underlying_ask = underlying_ask if underlying_ask is not None else chain.underlying_ask
        contracts.extend(contract.to_dict() for contract in chain.contracts)
    materialized = dict(fixture)
    materialized["chain"] = {
        "underlying": underlying,
        "provider": provider.provider,
        "quote_ts": isoformat_z(quote_ts) if quote_ts is not None else None,
        "underlying_bid": underlying_bid,
        "underlying_ask": underlying_ask,
        "contracts": contracts,
        "raw": {"source": "provider", "provider": provider.provider, "fixturePath": fixture.get("_fixturePath")},
    }
    return materialized


def _get_contract(symbols: dict[str, OptionContract], symbol: str | None, field: str) -> OptionContract:
    if not symbol:
        raise OptionsDaemonError(f"signal missing {field} symbol")
    try:
        return symbols[str(symbol)]
    except KeyError as exc:
        raise OptionsDaemonError(f"unknown option symbol for {field}: {symbol}") from exc


def build_structure_from_signal(signal: dict[str, Any], symbols: dict[str, OptionContract]) -> OptionStructure:
    structure_type = str(signal.get("structure") or signal.get("structureType") or "").strip().lower()
    if structure_type in {"long_call", "long_put", "long"}:
        contract = _get_contract(symbols, signal.get("contract") or signal.get("symbol"), "contract")
        structure = build_long_option(contract)
        if structure_type == "long_call" and structure.right != "call":
            raise OptionsDaemonError("long_call signal referenced a put contract")
        if structure_type == "long_put" and structure.right != "put":
            raise OptionsDaemonError("long_put signal referenced a call contract")
        return structure
    if structure_type == "debit_vertical":
        long_contract = _get_contract(symbols, signal.get("long") or signal.get("longSymbol"), "long")
        short_contract = _get_contract(symbols, signal.get("short") or signal.get("shortSymbol"), "short")
        return build_debit_vertical(long_contract, short_contract)
    if structure_type == "credit_vertical":
        short_contract = _get_contract(symbols, signal.get("short") or signal.get("shortSymbol"), "short")
        long_contract = _get_contract(symbols, signal.get("long") or signal.get("longSymbol"), "long")
        return build_credit_vertical(short_contract, long_contract)
    raise OptionsDaemonError(f"unsupported option structure: {structure_type!r}")


def _structure_leg_part(structure: OptionStructure) -> str:
    return "-".join(f"{leg.quantity}:{leg.contract.symbol}" for leg in structure.legs)


def _signal_id(signal: dict[str, Any], structure: OptionStructure) -> str:
    explicit = signal.get("id") or signal.get("signalId")
    if explicit:
        return safe_part(str(explicit), max_len=80)
    return safe_part(f"{structure.underlying}:{structure.structure_type}:{_structure_leg_part(structure)}", max_len=80)


def _opportunity_signal_id(opportunity: OptionOpportunity) -> str:
    return safe_part(f"{opportunity.thesis.id}:{opportunity.structure.structure_type}:{_structure_leg_part(opportunity.structure)}", max_len=80)


def _event_id(signal_id: str, now) -> str:
    return safe_part(f"rime-options-signal-{signal_id}-{now.strftime('%Y%m%dT%H%M%SZ')}", max_len=120)


def _prompt(signal: dict[str, Any], structure: OptionStructure, edge_pct: float | None) -> str:
    edge_text = "unknown edge" if edge_pct is None else f"{edge_pct * 100:.1f}% of max risk model edge"
    thesis = str(signal.get("thesis") or "fixture thesis")
    return (
        f"Evaluate this shadow options candidate for {structure.underlying} ({structure.structure_type}, {edge_text}). "
        "Use automation/OPTIONS_SPEC.md. If useful, update options-ledger.md/journal; no live order. "
        f"Thesis: {thesis}"
    )


def _opportunity_prompt(opportunity: OptionOpportunity) -> str:
    edge_pct = opportunity.evaluation.edge_pct_of_risk
    edge_text = "unknown edge" if edge_pct is None else f"{edge_pct * 100:.1f}% of max risk model edge"
    return (
        f"Evaluate this generated shadow options candidate for {opportunity.structure.underlying} "
        f"({opportunity.structure.structure_type}, {edge_text}, reward/risk {opportunity.reward_risk}). "
        "Use automation/OPTIONS_SPEC.md. If useful, update options-ledger.md/journal; no live order. "
        f"Thesis: {opportunity.thesis.thesis}"
    )


def _signal_payload(signal: dict[str, Any], structure: OptionStructure, evaluation, leg_filter_reasons: list[dict[str, Any]]) -> dict[str, Any]:
    signal_id = _signal_id(signal, structure)
    return {
        "signalId": signal_id,
        "underlying": structure.underlying,
        "sourceMode": "signal",
        "structure": structure.to_dict(),
        "evaluation": evaluation.to_dict(),
        "thesis": signal.get("thesis"),
        "catalyst": signal.get("catalyst"),
        "plannedExit": signal.get("plannedExit"),
        "falsifier": signal.get("falsifier"),
        "relatedMarkets": signal.get("relatedMarkets", []),
        "legFilterReasons": leg_filter_reasons,
        "dedupeKey": f"options_signal:{signal_id}",
    }


def _tape_context(snapshot, thesis, *, now) -> dict[str, Any] | None:
    """Build a compact tape/positioning context for a thesis review.

    Surfaces ATM-straddle implied move, target move, and the
    target/implied ratio so reviewers can sanity-check whether the
    thesis's directional target exceeds what the option chain is
    pricing as a one-sigma move to expiry.
    """
    if snapshot is None:
        return None
    spot = snapshot.underlying_mid
    if spot is None or spot <= 0:
        return None
    expiry = thesis.option_expiry or thesis.event_date
    dte = days_to_expiry(expiry, now=now) if expiry is not None else None
    implied = atm_straddle_implied_move(snapshot, expiry=expiry, spot=spot)
    target_move = target_move_pct_from_spot(direction=thesis.direction, target_price=thesis.target_price, spot=spot)
    implied_pct = implied.get("impliedMovePct") if isinstance(implied, dict) else None
    ratio = None
    if target_move is not None and implied_pct and implied_pct > 0:
        ratio = target_move / implied_pct
    spread_pct = None
    if snapshot.underlying_bid and snapshot.underlying_ask and snapshot.underlying_bid > 0:
        spread_pct = (snapshot.underlying_ask - snapshot.underlying_bid) / ((snapshot.underlying_ask + snapshot.underlying_bid) / 2)
    return {
        "spot": round(spot, 6),
        "underlyingBid": snapshot.underlying_bid,
        "underlyingAsk": snapshot.underlying_ask,
        "underlyingSpreadPct": round(spread_pct, 8) if spread_pct is not None else None,
        "quoteTs": isoformat_z(snapshot.quote_ts) if snapshot.quote_ts is not None else None,
        "quoteDelaySeconds": snapshot.quote_delay_seconds,
        "daysToExpiry": dte,
        "chainImpliedMoveToExpiry": implied,
        "targetMovePct": round(target_move, 8) if target_move is not None else None,
        "targetMoveVsImpliedRatio": round(ratio, 6) if ratio is not None else None,
        "reviewerNote": (
            "target move exceeds implied move; print/event surprise must clear vol-crush hurdle"
            if ratio is not None and ratio > 1.0
            else (
                "target move inside implied move; option chain already prices this directional outcome inside its distribution"
                if ratio is not None and ratio <= 1.0
                else None
            )
        ),
    }


def _opportunity_payload(
    opportunity: OptionOpportunity,
    leg_filter_reasons: list[dict[str, Any]],
    tape_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signal_id = _opportunity_signal_id(opportunity)
    payload = {
        "signalId": signal_id,
        "underlying": opportunity.structure.underlying,
        "sourceMode": "thesis_search",
        "thesis": opportunity.thesis.to_dict(),
        "structure": opportunity.structure.to_dict(),
        "evaluation": opportunity.evaluation.to_dict(),
        "modelPayoffIfHit": opportunity.model_payoff_if_hit,
        "rewardRisk": opportunity.reward_risk,
        "score": opportunity.score,
        "catalyst": opportunity.thesis.catalyst,
        "plannedExit": opportunity.thesis.planned_exit,
        "falsifier": opportunity.thesis.falsifier,
        "legFilterReasons": leg_filter_reasons,
        "dedupeKey": f"options_signal:{signal_id}",
    }
    if tape_context is not None:
        payload["tapeContext"] = tape_context
    return payload


def _leg_filter_reasons(structure: OptionStructure, *, now, config: OptionQuoteFilterConfig) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    for leg in structure.legs:
        ok, reason = contract_quote_filter_reason(leg.contract, now=now, config=config)
        reasons.append({"symbol": leg.contract.symbol, "ok": ok, "reason": reason})
    return reasons


def generate_options_events(
    *,
    fixture: dict[str, Any],
    now,
    session_id: str,
    state: dict[str, Any],
    config: OptionQuoteFilterConfig,
    min_edge_pct_of_risk: float,
    min_probability_margin: float | None,
    max_loss_cap: float | None,
    max_events: int,
    max_signals_per_thesis: int = 1,
    thesis_ids_with_open_paper: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chain_raw = fixture.get("chain", fixture)
    snapshot = parse_option_chain_snapshot(chain_raw)
    symbols = _contract_by_symbol(snapshot.contracts)
    events: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    cap_per_thesis = max(1, int(max_signals_per_thesis))
    open_paper_ids = thesis_ids_with_open_paper or set()
    fixture_allow_multi = bool(fixture.get("allowMultiplePaperPositions", False))

    for raw_thesis in fixture.get("theses", []):
        if len(events) >= max_events:
            break
        if not isinstance(raw_thesis, dict):
            rejections.append({"thesis": raw_thesis, "reason": "thesis must be an object"})
            continue
        if not is_active(raw_thesis):
            rejections.append({"thesisId": raw_thesis.get("id"), "reason": "inactive thesis"})
            continue
        try:
            thesis = normalize_thesis(raw_thesis)
            opportunities = find_opportunities_for_thesis(snapshot.contracts, thesis, now=now, config=config)
        except Exception as exc:
            rejections.append({"thesis": raw_thesis.get("id") if isinstance(raw_thesis, dict) else None, "reason": str(exc)})
            continue
        # Cross-poll thesis dedup: skip emission when a paper_open ticket already
        # exists for this thesis, unless the fixture/thesis explicitly opts into
        # holding multiple paper positions on the same thesis simultaneously.
        allow_multi = fixture_allow_multi or bool(raw_thesis.get("allowMultiplePaperPositions", False))
        if thesis.id in open_paper_ids and not allow_multi:
            rejections.append({
                "thesisId": thesis.id,
                "reason": "paper_open position already exists for this thesis; cross-poll dedup",
                "openPaperThesisId": thesis.id,
            })
            continue
        if not opportunities:
            rejections.append({"thesisId": thesis.id, "reason": "no generated structure passed gates"})
            continue
        emitted_for_thesis = 0
        skipped_alternative_count = 0
        skipped_alternative_examples: list[dict[str, Any]] = []
        for opportunity in opportunities[: max(0, max_events - len(events))]:
            signal_id = _opportunity_signal_id(opportunity)
            if signal_id in state.get("emitted_signals", {}):
                rejections.append({"signalId": signal_id, "reason": "already emitted"})
                continue
            if emitted_for_thesis >= cap_per_thesis:
                skipped_alternative_count += 1
                if len(skipped_alternative_examples) < 3:
                    skipped_alternative_examples.append(
                        {
                            "signalId": signal_id,
                            "structureType": opportunity.structure.structure_type,
                            "edgePctOfRisk": opportunity.evaluation.edge_pct_of_risk,
                            "rewardRisk": opportunity.reward_risk,
                            "maxLoss": opportunity.structure.max_loss,
                        }
                    )
                continue
            leg_reasons = _leg_filter_reasons(opportunity.structure, now=now, config=config)
            tape_ctx = _tape_context(snapshot, opportunity.thesis, now=now)
            payload = _opportunity_payload(opportunity, leg_reasons, tape_context=tape_ctx)
            payload["perThesisCap"] = cap_per_thesis
            event = build_wake_event(
                event_id=_event_id(signal_id, now),
                session_id=session_id,
                ts=isoformat_z(now),
                event_type="options_signal_candidate",
                priority=65,
                prompt=_opportunity_prompt(opportunity),
                payload=payload,
                source=SOURCE,
            )
            events.append(event)
            emitted_for_thesis += 1
            if len(events) >= max_events:
                break
        if skipped_alternative_count:
            rejections.append(
                {
                    "thesisId": thesis.id,
                    "reason": f"per-thesis cap {cap_per_thesis} reached; suppressed {skipped_alternative_count} alternative structure(s)",
                    "perThesisCap": cap_per_thesis,
                    "suppressedAlternatives": skipped_alternative_examples,
                }
            )

    for raw_signal in fixture.get("signals", []):
        if len(events) >= max_events:
            break
        if not isinstance(raw_signal, dict):
            rejections.append({"signal": raw_signal, "reason": "signal must be an object"})
            continue
        if not is_active(raw_signal):
            rejections.append({"signalId": raw_signal.get("id") or raw_signal.get("signalId"), "reason": "inactive signal"})
            continue
        try:
            structure = build_structure_from_signal(raw_signal, symbols)
            signal_id = _signal_id(raw_signal, structure)
        except Exception as exc:
            rejections.append({"signal": raw_signal.get("id") if isinstance(raw_signal, dict) else None, "reason": str(exc)})
            continue

        if signal_id in state.get("emitted_signals", {}):
            rejections.append({"signalId": signal_id, "reason": "already emitted"})
            continue

        leg_reasons = _leg_filter_reasons(structure, now=now, config=config)
        if not all(row["ok"] for row in leg_reasons):
            rejections.append({"signalId": signal_id, "reason": "leg quote filter failed", "legFilterReasons": leg_reasons})
            continue

        model_fair = raw_signal.get("modelFairValue", raw_signal.get("model_fair_value"))
        if model_fair is None:
            rejections.append({"signalId": signal_id, "reason": "missing modelFairValue"})
            continue
        try:
            model_fair_value = float(model_fair)
            model_probability = raw_signal.get("modelProbability", raw_signal.get("model_probability"))
            evaluation = evaluate_structure_edge(
                structure,
                model_fair_value=model_fair_value,
                min_edge_pct_of_risk=float(raw_signal.get("minEdgePctOfRisk", min_edge_pct_of_risk)),
                model_probability=float(model_probability) if model_probability is not None else None,
                min_probability_margin=(
                    float(raw_signal.get("minProbabilityMargin"))
                    if raw_signal.get("minProbabilityMargin") is not None
                    else min_probability_margin
                ),
                max_loss_cap=float(raw_signal.get("maxLossCap")) if raw_signal.get("maxLossCap") is not None else max_loss_cap,
            )
        except Exception as exc:
            rejections.append({"signalId": signal_id, "reason": str(exc)})
            continue

        if not evaluation.passes:
            rejections.append({"signalId": signal_id, "reason": "edge gate failed", "blockedReasons": list(evaluation.blocked_reasons)})
            continue

        payload = _signal_payload(raw_signal, structure, evaluation, leg_reasons)
        event = build_wake_event(
            event_id=_event_id(signal_id, now),
            session_id=session_id,
            ts=isoformat_z(now),
            event_type="options_signal_candidate",
            priority=65,
            prompt=_prompt(raw_signal, structure, evaluation.edge_pct_of_risk),
            payload=payload,
            source=SOURCE,
        )
        events.append(event)

    return events, rejections


def mark_options_events_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now) -> None:
    emitted = state.setdefault("emitted_signals", {})
    for event in events:
        signal_id = event.get("payload", {}).get("signalId")
        if signal_id:
            emitted[signal_id] = {"emitted_at": isoformat_z(now), "event_id": event.get("id")}


def is_thesis_search_fixture(fixture: dict[str, Any]) -> bool:
    return fixture.get("strategy") == "situational-awareness-ai-stack" or fixture.get("source") == "rime-forecasts/sa-thesis-scan"


def paper_open_thesis_ids(ticket_dir: Path) -> set[str]:
    """Return the set of thesis_id values that currently have a paper_open ticket.

    Used as the cross-poll dedupe gate: when a thesis already has a live shadow
    paper position, the daemon should not emit additional options_signal_candidate
    wakes for the same thesis on subsequent polls just because a different strike
    pair newly passes gates.
    """
    if not ticket_dir.exists():
        return set()
    open_ids: set[str] = set()
    for path in ticket_dir.glob("*.json"):
        try:
            ticket = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(ticket, dict):
            continue
        if str(ticket.get("status") or "") != "paper_open":
            continue
        thesis_block = ticket.get("thesis") if isinstance(ticket.get("thesis"), dict) else {}
        thesis_id = thesis_block.get("id")
        if thesis_id:
            open_ids.add(str(thesis_id))
            continue
        # Fall back to parsing thesis_id out of signal_id ("<thesis_id>:<...>")
        signal_id = str(ticket.get("signal_id") or "")
        if signal_id and ":" in signal_id:
            open_ids.add(signal_id.split(":", 1)[0])
    return open_ids


def _parse_optional_ts(value: Any):
    if not value:
        return None
    try:
        return parse_iso(str(value))
    except Exception:
        return None


def _fixture_review_anchor(fixture: dict[str, Any], raw_thesis: dict[str, Any]):
    return (
        _parse_optional_ts(raw_thesis.get("reviewedAt"))
        or _parse_optional_ts(fixture.get("reviewedAt"))
        or _parse_optional_ts(fixture.get("generatedAt"))
    )


def _snapshot_spot(snapshot) -> float | None:
    return snapshot.underlying_mid


def _chain_liquidity_summary(snapshot, *, now, config: OptionQuoteFilterConfig) -> dict[str, Any]:
    liquid = []
    calls = 0
    puts = 0
    for contract in snapshot.contracts:
        if contract.right == "call":
            calls += 1
        elif contract.right == "put":
            puts += 1
        ok, _ = contract_quote_filter_reason(contract, now=now, config=config)
        if ok:
            liquid.append(contract)
    return {
        "provider": snapshot.provider,
        "quoteTs": isoformat_z(snapshot.quote_ts) if snapshot.quote_ts is not None else None,
        "quoteDelaySeconds": snapshot.quote_delay_seconds,
        "underlyingBid": snapshot.underlying_bid,
        "underlyingAsk": snapshot.underlying_ask,
        "contractCount": len(snapshot.contracts),
        "callCount": calls,
        "putCount": puts,
        "liquidContractCount": len(liquid),
        "liquidCallCount": sum(1 for contract in liquid if contract.right == "call"),
        "liquidPutCount": sum(1 for contract in liquid if contract.right == "put"),
        "minStrike": min((contract.strike for contract in snapshot.contracts), default=None),
        "maxStrike": max((contract.strike for contract in snapshot.contracts), default=None),
    }


def _target_distance_pct(thesis, spot: float | None) -> float | None:
    if spot is None or spot <= 0:
        return None
    if thesis.direction == "up":
        return thesis.target_price / spot - 1
    return spot / thesis.target_price - 1


def _best_structure_diagnostic(snapshot, thesis, *, now, config: OptionQuoteFilterConfig) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    passing = 0
    generated = 0
    for structure in generate_structures_for_thesis(snapshot.contracts, thesis, now=now, config=config):
        generated += 1
        model_fair, payoff_if_hit, reward_risk = model_fair_value_from_thesis(structure, thesis)
        evaluation = evaluate_structure_edge(
            structure,
            model_fair_value=model_fair,
            min_edge_pct_of_risk=thesis.min_edge_pct_of_risk,
            model_probability=thesis.target_probability,
            min_probability_margin=thesis.min_probability_margin,
            max_loss_cap=thesis.max_loss_cap,
        )
        passes = evaluation.passes and reward_risk is not None and reward_risk >= thesis.min_reward_risk
        if passes:
            passing += 1
        probability_margin = None
        if evaluation.model_probability is not None and evaluation.breakeven_probability is not None:
            probability_margin = evaluation.model_probability - evaluation.breakeven_probability
        blocked = list(evaluation.blocked_reasons)
        if reward_risk is None or reward_risk < thesis.min_reward_risk:
            blocked.append(f"reward/risk {reward_risk if reward_risk is not None else 'unknown'} below min {thesis.min_reward_risk:.3f}")
        score = (
            1 if passes else 0,
            evaluation.edge_pct_of_risk if evaluation.edge_pct_of_risk is not None else -999.0,
            probability_margin if probability_margin is not None else -999.0,
            reward_risk if reward_risk is not None else -999.0,
        )
        if best is None or score > best["_score"]:
            best = {
                "_score": score,
                "structure": structure.to_dict(),
                "passes": passes,
                "edgePctOfRisk": evaluation.edge_pct_of_risk,
                "probabilityMargin": round(probability_margin, 8) if probability_margin is not None else None,
                "rewardRisk": round(reward_risk, 8) if reward_risk is not None else None,
                "modelFairValue": evaluation.model_fair_value,
                "blockedReasons": blocked,
            }
    if best is not None:
        best = {key: value for key, value in best.items() if key != "_score"}
    return {"generatedStructureCount": generated, "passingStructureCount": passing, "best": best}


def _thesis_has_emitted_signal(state: dict[str, Any], thesis_id: str) -> bool:
    return any(thesis_id in str(signal_id) for signal_id in state.get("emitted_signals", {}))


def _thesis_refresh_event_id(thesis_id: str, reasons: list[str], now) -> str:
    reason_part = safe_part("-".join(reasons) or "review", max_len=32)
    return safe_part(f"rime-options-thesis-refresh-{thesis_id}-{reason_part}-{now.strftime('%Y%m%dT%H%M%SZ')}", max_len=120)


def _thesis_refresh_prompt(payload: dict[str, Any]) -> str:
    thesis = payload.get("thesis", {}) if isinstance(payload.get("thesis"), dict) else {}
    reasons = ", ".join(payload.get("reasons", []))
    return (
        f"Options thesis refresh due for {payload.get('underlying')} {thesis.get('id')} ({reasons}). "
        "Reassess the active search fixture against current market conditions, thesis/falsifier, liquidity, and structure-search diagnostics. "
        "If still valid, update reviewedAt/notes if useful; if invalid, deactivate the thesis fixture. Do not place live orders."
    )


def _mark_thesis_refresh_status(
    state: dict[str, Any],
    *,
    thesis_id: str,
    now,
    spot: float | None,
    liquid_contracts: int,
    passing_structures: int,
    provider: str,
) -> None:
    status = state.setdefault("thesis_refresh_status", {}).setdefault(thesis_id, {})
    status.update(
        {
            "last_checked_at": isoformat_z(now),
            "last_spot": spot,
            "last_liquid_contracts": liquid_contracts,
            "last_passing_structure_count": passing_structures,
            "last_provider": provider,
        }
    )


def generate_thesis_refresh_events(
    *,
    fixture: dict[str, Any],
    now,
    session_id: str,
    state: dict[str, Any],
    config: OptionQuoteFilterConfig,
    max_events: int,
    refresh_days: int = 7,
    no_signal_days: int | None = None,
    expiry_review_days: int = 7,
    spot_move_pct: float = 0.08,
    liquidity_drop_pct: float = 0.50,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if max_events <= 0 or not is_thesis_search_fixture(fixture):
        return [], []
    snapshot = parse_option_chain_snapshot(fixture.get("chain", fixture))
    spot = _snapshot_spot(snapshot)
    liquidity = _chain_liquidity_summary(snapshot, now=now, config=config)
    liquid_contracts = int(liquidity["liquidContractCount"])
    no_signal_days = refresh_days if no_signal_days is None else no_signal_days
    events: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    refresh_state = state.setdefault("thesis_refresh_status", {})
    emitted_state = state.setdefault("thesis_refresh_events", {})

    for raw_thesis in fixture.get("theses", []):
        if len(events) >= max_events:
            break
        if not isinstance(raw_thesis, dict):
            rejections.append({"thesis": raw_thesis, "reason": "thesis must be an object"})
            continue
        if not is_active(raw_thesis):
            continue
        try:
            thesis = normalize_thesis(raw_thesis)
        except Exception as exc:
            rejections.append({"thesis": raw_thesis.get("id"), "reason": str(exc)})
            continue
        diagnostic = _best_structure_diagnostic(snapshot, thesis, now=now, config=config)
        status = refresh_state.get(thesis.id, {}) if isinstance(refresh_state.get(thesis.id), dict) else {}
        reasons: list[str] = []
        expiry = thesis.option_expiry or thesis.event_date
        dte = days_to_expiry(expiry, now=now) if expiry is not None else None
        if dte is not None and dte <= expiry_review_days:
            reasons.append(f"expiry_within_{expiry_review_days}d")
        anchor = _fixture_review_anchor(fixture, raw_thesis)
        if anchor is not None:
            age_days = (now - anchor).total_seconds() / 86400
            if age_days >= refresh_days:
                reasons.append(f"review_stale_{refresh_days}d")
            if not _thesis_has_emitted_signal(state, thesis.id) and age_days >= no_signal_days:
                reasons.append(f"no_signal_{no_signal_days}d")
        last_spot = status.get("last_spot")
        spot_move = None
        if spot is not None and last_spot:
            try:
                previous_spot = float(last_spot)
                if previous_spot > 0:
                    spot_move = spot / previous_spot - 1
                    if abs(spot_move) >= spot_move_pct:
                        reasons.append(f"spot_move_{spot_move:+.1%}")
            except Exception:
                pass
        last_liquid = status.get("last_liquid_contracts")
        liquidity_change = None
        if last_liquid:
            try:
                previous_liquid = int(last_liquid)
                if previous_liquid > 0:
                    liquidity_change = liquid_contracts / previous_liquid - 1
                    if liquidity_change <= -abs(liquidity_drop_pct):
                        reasons.append(f"liquidity_drop_{liquidity_change:+.0%}")
            except Exception:
                pass
        previous_passing = int(status.get("last_passing_structure_count", 0) or 0)
        current_passing = int(diagnostic["passingStructureCount"])
        if status:
            if previous_passing == 0 and current_passing > 0:
                reasons.append("structure_now_passes")
            if previous_passing > 0 and current_passing == 0:
                reasons.append("structure_no_longer_passes")

        _mark_thesis_refresh_status(
            state,
            thesis_id=thesis.id,
            now=now,
            spot=spot,
            liquid_contracts=liquid_contracts,
            passing_structures=current_passing,
            provider=snapshot.provider,
        )
        if not reasons:
            continue
        reasons = list(dict.fromkeys(reasons))
        dedupe_key = f"options_thesis_refresh:{thesis.id}:{now.date().isoformat()}:{','.join(reasons)}"
        if dedupe_key in emitted_state:
            rejections.append({"thesisId": thesis.id, "reason": "refresh already emitted", "dedupeKey": dedupe_key})
            continue
        tape_ctx = _tape_context(snapshot, thesis, now=now)
        payload = {
            "thesisId": thesis.id,
            "underlying": snapshot.underlying,
            "fixturePath": fixture.get("_fixturePath"),
            "reasons": reasons,
            "thesis": thesis.to_dict(),
            "reviewedAt": raw_thesis.get("reviewedAt") or fixture.get("reviewedAt"),
            "currentMarket": {
                "spot": spot,
                "targetDistancePct": round(_target_distance_pct(thesis, spot), 8) if _target_distance_pct(thesis, spot) is not None else None,
                "spotMoveSinceLastCheckPct": round(spot_move, 8) if spot_move is not None else None,
                "liquidityChangeSinceLastCheckPct": round(liquidity_change, 8) if liquidity_change is not None else None,
                "daysToExpiry": dte,
                "liquidity": liquidity,
            },
            "tapeContext": tape_ctx,
            "structureSearch": diagnostic,
            "dedupeKey": dedupe_key,
        }
        event = build_wake_event(
            event_id=_thesis_refresh_event_id(thesis.id, reasons, now),
            session_id=session_id,
            ts=isoformat_z(now),
            event_type="options_thesis_refresh_due",
            priority=70 if dte is not None and dte <= 2 else 55,
            prompt=_thesis_refresh_prompt(payload),
            payload=payload,
            source=SOURCE,
        )
        events.append(event)
    return events, rejections


def mark_thesis_refresh_events_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now) -> None:
    emitted = state.setdefault("thesis_refresh_events", {})
    for event in events:
        payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
        dedupe_key = payload.get("dedupeKey")
        if dedupe_key:
            emitted[dedupe_key] = {"emitted_at": isoformat_z(now), "event_id": event.get("id")}


def load_ticket_records(ticket_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not ticket_dir.exists():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(ticket_dir.glob("*.json")):
        try:
            ticket = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            records.append((path, {"_error": str(exc)}))
            continue
        if isinstance(ticket, dict):
            records.append((path, ticket))
    return records


def _ticket_prompt(ticket: dict[str, Any], checkpoint: str) -> str:
    structure = ticket.get("structure", {}) if isinstance(ticket.get("structure"), dict) else {}
    return (
        f"Options CLV checkpoint {checkpoint} is due for {ticket.get('underlying')} "
        f"{option_structure_label(structure)}. Use scripts/options-markout.py to mark the local ticket, "
        "update options-ledger.md if useful, then call wake_done."
    )


def _exit_prompt(ticket: dict[str, Any], reason: str) -> str:
    structure = ticket.get("structure", {}) if isinstance(ticket.get("structure"), dict) else {}
    return (
        f"Options exit/expiry review due ({reason}) for {ticket.get('underlying')} {option_structure_label(structure)}. "
        "Use scripts/options-markout.py with checkpoint exit/expiry, update options-ledger.md, then call wake_done."
    )


def _ticket_payload(ticket: dict[str, Any], path: Path, *, dedupe_key: str, checkpoint: str | None = None, reason: str | None = None) -> dict[str, Any]:
    return {
        "ticketId": ticket.get("ticket_id"),
        "signalId": ticket.get("signal_id"),
        "ticketPath": str(path),
        "checkpoint": checkpoint,
        "reason": reason,
        "ticket": ticket,
        "dedupeKey": dedupe_key,
    }


def _ticket_event_id(event_type: str, ticket_id: str, now, extra: str | None = None) -> str:
    parts = ["rime-options", event_type.replace("_", "-"), safe_part(ticket_id, max_len=45)]
    if extra:
        parts.append(safe_part(extra, max_len=16))
    parts.append(now.strftime("%Y%m%dT%H%M%SZ"))
    return safe_part("-".join(parts), max_len=120)


def _ticket_expiry_due(ticket: dict[str, Any], now) -> tuple[bool, str | None]:
    markouts = ticket.get("markouts", {}) if isinstance(ticket.get("markouts"), dict) else {}
    if any(key in markouts for key in ("exit", "expiry", "close")):
        return False, None
    structure = ticket.get("structure", {}) if isinstance(ticket.get("structure"), dict) else {}
    expiry_raw = structure.get("expiry")
    if not expiry_raw:
        return False, None
    try:
        expiry_date = parse_iso(str(expiry_raw) + "T00:00:00Z").date() if "T" not in str(expiry_raw) else parse_iso(str(expiry_raw)).date()
    except Exception:
        return False, None
    if expiry_date < now.date() or (expiry_date == now.date() and now.hour >= 21):
        return True, f"expiry {expiry_date.isoformat()} due"
    return False, None


def generate_ticket_lifecycle_events(
    *,
    ticket_dir: Path,
    state: dict[str, Any],
    now,
    session_id: str,
    max_events: int,
    schedule_statuses: tuple[str, ...] = ("paper_open",),
    checkpoints: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checkpoints = checkpoints or {"1h": 3600, "6h": 21600, "24h": 86400}
    events: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    clv_state = state.setdefault("clv_events", {})
    exit_state = state.setdefault("exit_events", {})
    for path, ticket in load_ticket_records(ticket_dir):
        if len(events) >= max_events:
            break
        if ticket.get("_error"):
            rejections.append({"ticketPath": str(path), "reason": ticket["_error"]})
            continue
        ticket_id = str(ticket.get("ticket_id") or path.stem)
        status = str(ticket.get("status") or "draft")
        if status == "paper_closed":
            continue
        try:
            created_at = parse_iso(str(ticket.get("created_at")))
        except Exception:
            rejections.append({"ticketId": ticket_id, "reason": "missing/invalid created_at"})
            continue
        markouts = ticket.get("markouts", {}) if isinstance(ticket.get("markouts"), dict) else {}
        if status in schedule_statuses:
            for checkpoint, seconds in checkpoints.items():
                if len(events) >= max_events:
                    break
                dedupe_key = f"options_clv:{ticket_id}:{checkpoint}"
                if checkpoint in markouts or dedupe_key in clv_state:
                    continue
                if now >= created_at + timedelta(seconds=seconds):
                    event = build_wake_event(
                        event_id=_ticket_event_id("clv_checkpoint_due", ticket_id, now, checkpoint),
                        session_id=session_id,
                        ts=isoformat_z(now),
                        event_type="options_clv_checkpoint_due",
                        priority=45,
                        prompt=_ticket_prompt(ticket, checkpoint),
                        payload=_ticket_payload(ticket, path, dedupe_key=dedupe_key, checkpoint=checkpoint),
                        source=SOURCE,
                    )
                    events.append(event)
        if len(events) >= max_events:
            break
        due, reason = _ticket_expiry_due(ticket, now)
        dedupe_key = f"options_exit:{ticket_id}"
        if due and dedupe_key not in exit_state:
            event = build_wake_event(
                event_id=_ticket_event_id("expiry_or_exit", ticket_id, now),
                session_id=session_id,
                ts=isoformat_z(now),
                event_type="options_expiry_or_exit",
                priority=75,
                prompt=_exit_prompt(ticket, reason or "exit due"),
                payload=_ticket_payload(ticket, path, dedupe_key=dedupe_key, reason=reason),
                source=SOURCE,
            )
            events.append(event)
    return events, rejections


def mark_ticket_lifecycle_events_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now) -> None:
    for event in events:
        payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
        dedupe_key = payload.get("dedupeKey")
        if not dedupe_key:
            continue
        target = state.setdefault("exit_events" if event.get("type") == "options_expiry_or_exit" else "clv_events", {})
        target[dedupe_key] = {"emitted_at": isoformat_z(now), "event_id": event.get("id")}


def poll_once(args, *, session_id: str | None) -> int:
    now = parse_iso(args.now) if args.now else utcnow()
    fixtures = load_fixtures(args.fixture, args.fixture_dir)
    provider = build_provider(args.provider)
    state = load_options_state(args.state_path)
    config = OptionQuoteFilterConfig(
        allow_underlyings=tuple(args.allow_underlying or ()),
        min_days_to_expiry=args.min_days_to_expiry,
        max_days_to_expiry=args.max_days_to_expiry,
        min_volume=args.min_volume,
        min_open_interest=args.min_open_interest,
        min_premium=args.min_premium,
        max_single_leg_abs_spread=args.max_single_leg_abs_spread,
        max_single_leg_spread_pct_of_mid=args.max_single_leg_spread_pct_of_mid,
        max_quote_age_seconds=args.max_quote_age_seconds,
    )
    effective_session_id = session_id or "dry-run-session"
    open_paper_thesis_ids = paper_open_thesis_ids(args.ticket_dir)
    events: list[dict[str, Any]] = []
    signal_events: list[dict[str, Any]] = []
    thesis_refresh_events: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for fixture in fixtures:
        if len(events) >= args.max_events:
            break
        if not is_active(fixture):
            rejections.append({"fixture": fixture.get("_fixturePath"), "reason": "inactive fixture"})
            continue
        try:
            materialized_fixture = materialize_provider_fixture(fixture, provider)
        except Exception as exc:
            rejections.append({"fixture": fixture.get("_fixturePath"), "reason": str(exc)})
            continue
        fixture_events, fixture_rejections = generate_options_events(
            fixture=materialized_fixture,
            now=now,
            session_id=effective_session_id,
            state=state,
            config=config,
            min_edge_pct_of_risk=args.min_edge_pct_of_risk,
            min_probability_margin=args.min_probability_margin,
            max_loss_cap=args.max_loss_cap,
            max_events=args.max_events - len(events),
            max_signals_per_thesis=args.max_signals_per_thesis,
            thesis_ids_with_open_paper=open_paper_thesis_ids,
        )
        events.extend(fixture_events)
        signal_events.extend(fixture_events)
        rejections.extend(fixture_rejections)
        if not args.no_thesis_refresh and len(events) < args.max_events:
            refresh_events, refresh_rejections = generate_thesis_refresh_events(
                fixture=materialized_fixture,
                now=now,
                session_id=effective_session_id,
                state=state,
                config=config,
                max_events=args.max_events - len(events),
                refresh_days=args.thesis_refresh_days,
                no_signal_days=args.thesis_no_signal_days,
                expiry_review_days=args.thesis_expiry_review_days,
                spot_move_pct=args.thesis_spot_move_pct,
                liquidity_drop_pct=args.thesis_liquidity_drop_pct,
            )
            events.extend(refresh_events)
            thesis_refresh_events.extend(refresh_events)
            rejections.extend(refresh_rejections)

    ticket_paths: list[str] = []
    if args.write_tickets:
        for event in signal_events:
            ticket = option_ticket_from_event(event, now=now, status=args.ticket_status)
            path = write_option_ticket(ticket, args.ticket_dir)
            ticket_paths.append(str(path))

    lifecycle_events: list[dict[str, Any]] = []
    lifecycle_rejections: list[dict[str, Any]] = []
    if not args.no_ticket_events and len(events) < args.max_events:
        schedule_statuses = tuple(args.schedule_status or ("paper_open",))
        lifecycle_events, lifecycle_rejections = generate_ticket_lifecycle_events(
            ticket_dir=args.ticket_dir,
            state=state,
            now=now,
            session_id=effective_session_id,
            max_events=args.max_events - len(events),
            schedule_statuses=schedule_statuses,
        )
        events.extend(lifecycle_events)
        rejections.extend(lifecycle_rejections)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ts": isoformat_z(now),
                    "dryRun": True,
                    "events": events,
                    "eventCount": len(events),
                    "rejections": rejections,
                    "rejectionCount": len(rejections),
                    "ticketPaths": ticket_paths,
                    "ticketsWritten": len(ticket_paths),
                    "candidateEventCount": len(signal_events),
                    "thesisRefreshEventCount": len(thesis_refresh_events),
                    "lifecycleEventCount": len(lifecycle_events),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return len(events)

    written = 0
    for event in events:
        path = write_wake_event(args.wake_root, event)
        print(f"wrote {event['type']} {event['id']} -> {path}")
        written += 1
    mark_options_events_emitted(state, signal_events, now=now)
    mark_thesis_refresh_events_emitted(state, thesis_refresh_events, now=now)
    mark_ticket_lifecycle_events_emitted(state, lifecycle_events, now=now)
    save_state(args.state_path, state)
    print(
        json.dumps(
            {
                "ts": isoformat_z(now),
                "eventsWritten": written,
                "rejections": len(rejections),
                "ticketsWritten": len(ticket_paths),
                "candidateEvents": len(signal_events),
                "thesisRefreshEvents": len(thesis_refresh_events),
                "lifecycleEvents": len(lifecycle_events),
            },
            sort_keys=True,
        )
    )
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit shadow options candidate/lifecycle wake events from fixture-defined thesis structures")
    parser.add_argument("--fixture", type=Path, action="append", help="fixture JSON with chain and signals/theses; repeatable")
    parser.add_argument("--fixture-dir", type=Path, default=Path("options/theses"), help="directory of active fixture/thesis JSON files (default: options/theses)")
    parser.add_argument("--provider", choices=["tradier"], help="market-data provider for thesis files that omit an embedded chain")
    parser.add_argument("--session-id", help="explicit target pi session id; or set RIME_WAKE_SESSION_ID")
    parser.add_argument("--wake-root", type=Path, default=DEFAULT_WAKE_ROOT, help=f"wake root (default: {DEFAULT_WAKE_ROOT})")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help=f"state path (default: {DEFAULT_STATE_PATH})")
    parser.add_argument("--dry-run", action="store_true", help="print events without requiring session id or writing wake/state")
    parser.add_argument("--once", action="store_true", help="single poll (default)")
    parser.add_argument("--loop", action="store_true", help="repeat fixture poll; mostly for integration testing")
    parser.add_argument("--interval-sec", type=int, default=900, help="loop interval seconds (default: 900)")
    parser.add_argument("--now", help="override current ISO timestamp for deterministic tests")
    parser.add_argument("--max-events", type=int, default=5, help="max events emitted per poll (default: 5)")
    parser.add_argument("--write-tickets", action="store_true", help="write dry-run option ticket JSON artifacts for emitted candidates")
    parser.add_argument("--ticket-dir", type=Path, default=Path("execution/options-tickets"), help="option ticket artifact directory")
    parser.add_argument("--ticket-status", choices=["draft", "blocked", "paper_open", "paper_closed"], default="draft")
    parser.add_argument("--no-ticket-events", action="store_true", help="do not scan option tickets for CLV/expiry lifecycle wakes")
    parser.add_argument("--schedule-status", action="append", choices=["draft", "paper_open"], help="ticket status eligible for CLV checkpoint wakes; default: paper_open")

    thesis_refresh = parser.add_argument_group("thesis refresh lifecycle")
    thesis_refresh.add_argument("--no-thesis-refresh", action="store_true", help="do not scan active thesis-search fixtures for refresh/review wakes")
    thesis_refresh.add_argument("--thesis-refresh-days", type=int, default=7, help="emit refresh when reviewedAt/generatedAt is this many days stale (default: 7)")
    thesis_refresh.add_argument("--thesis-no-signal-days", type=int, help="emit refresh when no option signal has fired this many days after review; defaults to thesis-refresh-days")
    thesis_refresh.add_argument("--thesis-expiry-review-days", type=int, default=7, help="emit refresh when option expiry is within this many days (default: 7)")
    thesis_refresh.add_argument("--thesis-spot-move-pct", type=float, default=0.08, help="emit refresh when underlying spot moves this fraction from last thesis check (default: 0.08)")
    thesis_refresh.add_argument("--thesis-liquidity-drop-pct", type=float, default=0.50, help="emit refresh when liquid contract count drops by this fraction from last thesis check (default: 0.50)")

    filters = parser.add_argument_group("quote filters")
    filters.add_argument("--allow-underlying", action="append", help="allow only this underlying; repeatable")
    filters.add_argument("--min-days-to-expiry", type=int, default=1)
    filters.add_argument("--max-days-to-expiry", type=int, default=45)
    filters.add_argument("--min-volume", type=float, default=100.0)
    filters.add_argument("--min-open-interest", type=float, default=500.0)
    filters.add_argument("--min-premium", type=float, default=0.05)
    filters.add_argument("--max-single-leg-abs-spread", type=float, default=0.05)
    filters.add_argument("--max-single-leg-spread-pct-of-mid", type=float, default=0.15)
    filters.add_argument("--max-quote-age-seconds", type=int)

    edge = parser.add_argument_group("edge gates")
    edge.add_argument("--min-edge-pct-of-risk", type=float, default=0.20)
    edge.add_argument("--min-probability-margin", type=float, default=0.05)
    edge.add_argument("--max-loss-cap", type=float, default=100.0)
    edge.add_argument("--max-signals-per-thesis", type=int, default=1, help="cap on candidate signals emitted per thesis per poll; top-scored wins (default: 1, shadow-paper convention)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.loop and args.once:
        parser.error("choose at most one of --loop or --once")
    try:
        session_id = require_session_id(args.session_id, dry_run=args.dry_run)
    except ValueError as exc:
        parser.error(str(exc))

    if not args.loop:
        poll_once(args, session_id=session_id)
        return 0

    while True:
        try:
            poll_once(args, session_id=session_id)
        except Exception as exc:
            print(f"poll failed: {exc}", file=sys.stderr)
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
