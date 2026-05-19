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
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_WAKE_ROOT, require_session_id
from automation.options import (
    OptionContract,
    OptionOpportunity,
    OptionQuoteFilterConfig,
    OptionStructure,
    build_credit_vertical,
    build_debit_vertical,
    build_long_option,
    contract_quote_filter_reason,
    evaluate_structure_edge,
    find_opportunities_for_thesis,
    normalize_thesis,
    option_ticket_from_event,
    parse_option_chain_snapshot,
    write_option_ticket,
)
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
    if "chain" not in data and "contracts" not in data:
        raise OptionsDaemonError("options fixture requires a chain object or top-level contracts list")
    signals = data.get("signals", [])
    if not isinstance(signals, list):
        raise OptionsDaemonError("options fixture signals must be a list")
    theses = data.get("theses", [])
    if not isinstance(theses, list):
        raise OptionsDaemonError("options fixture theses must be a list")
    return data


def load_options_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"emitted_signals": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    state = data if isinstance(data, dict) else {}
    state.setdefault("emitted_signals", {})
    return state


def _contract_by_symbol(contracts: tuple[OptionContract, ...]) -> dict[str, OptionContract]:
    return {contract.symbol: contract for contract in contracts}


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


def _opportunity_payload(opportunity: OptionOpportunity, leg_filter_reasons: list[dict[str, Any]]) -> dict[str, Any]:
    signal_id = _opportunity_signal_id(opportunity)
    return {
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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chain_raw = fixture.get("chain", fixture)
    snapshot = parse_option_chain_snapshot(chain_raw)
    symbols = _contract_by_symbol(snapshot.contracts)
    events: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    for raw_thesis in fixture.get("theses", []):
        if len(events) >= max_events:
            break
        if not isinstance(raw_thesis, dict):
            rejections.append({"thesis": raw_thesis, "reason": "thesis must be an object"})
            continue
        try:
            thesis = normalize_thesis(raw_thesis)
            opportunities = find_opportunities_for_thesis(snapshot.contracts, thesis, now=now, config=config)
        except Exception as exc:
            rejections.append({"thesis": raw_thesis.get("id") if isinstance(raw_thesis, dict) else None, "reason": str(exc)})
            continue
        if not opportunities:
            rejections.append({"thesisId": thesis.id, "reason": "no generated structure passed gates"})
            continue
        for opportunity in opportunities[: max(0, max_events - len(events))]:
            signal_id = _opportunity_signal_id(opportunity)
            if signal_id in state.get("emitted_signals", {}):
                rejections.append({"signalId": signal_id, "reason": "already emitted"})
                continue
            leg_reasons = _leg_filter_reasons(opportunity.structure, now=now, config=config)
            payload = _opportunity_payload(opportunity, leg_reasons)
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
            if len(events) >= max_events:
                break

    for raw_signal in fixture.get("signals", []):
        if len(events) >= max_events:
            break
        if not isinstance(raw_signal, dict):
            rejections.append({"signal": raw_signal, "reason": "signal must be an object"})
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


def poll_once(args, *, session_id: str | None) -> int:
    now = parse_iso(args.now) if args.now else utcnow()
    fixture = load_fixture(args.fixture)
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
    events, rejections = generate_options_events(
        fixture=fixture,
        now=now,
        session_id=effective_session_id,
        state=state,
        config=config,
        min_edge_pct_of_risk=args.min_edge_pct_of_risk,
        min_probability_margin=args.min_probability_margin,
        max_loss_cap=args.max_loss_cap,
        max_events=args.max_events,
    )

    ticket_paths: list[str] = []
    if args.write_tickets:
        for event in events:
            ticket = option_ticket_from_event(event, now=now, status=args.ticket_status)
            path = write_option_ticket(ticket, args.ticket_dir)
            ticket_paths.append(str(path))

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
    mark_options_events_emitted(state, events, now=now)
    save_state(args.state_path, state)
    print(json.dumps({"ts": isoformat_z(now), "eventsWritten": written, "rejections": len(rejections), "ticketsWritten": len(ticket_paths)}, sort_keys=True))
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit shadow options candidate wake events from fixture-defined thesis structures")
    parser.add_argument("--fixture", type=Path, required=True, help="fixture JSON with chain and signals")
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
