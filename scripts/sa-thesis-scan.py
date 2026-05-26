#!/usr/bin/env python3
"""Generate reviewable Situational Awareness options thesis candidates."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_WAKE_ROOT, require_session_id
from automation.options import FixtureOptionProvider, OptionChainProvider, chain_quote_is_stale
from automation.options_providers import TradierOptionProvider
from automation.sa_thesis import (
    SAThesisCandidate,
    build_candidate,
    chain_summary,
    entry_directions,
    entry_enabled,
    load_watchlist,
    merged_entry,
    emission_requires_prequalification,
    prequalify_candidate,
    quote_config_from_entry,
    select_expiry,
    spot_mid,
    trigger_reasons_for_entry,
    update_underlying_state,
)
from automation.state import save_state
from automation.timeutil import isoformat_z, parse_iso, utcnow
from automation.wake import build_wake_event, safe_part, write_wake_event

SOURCE = "rime-forecasts/sa-thesis-scan"
DEFAULT_WATCHLIST_PATH = Path("options/sa-watchlist.json")
DEFAULT_STATE_PATH = Path("automation/state/sa-thesis-scan.json")
DEFAULT_CANDIDATE_DIR = Path("automation/state/sa-thesis-candidates")


class SAThesisScanError(ValueError):
    pass


def load_scan_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "underlyings": {}, "emitted_candidates": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    state = data if isinstance(data, dict) else {}
    state.setdefault("version", 1)
    state.setdefault("underlyings", {})
    state.setdefault("emitted_candidates", {})
    return state


def build_provider(args) -> OptionChainProvider:
    if args.provider == "tradier":
        return TradierOptionProvider.from_env()
    if args.provider == "fixture":
        if not args.fixture:
            raise SAThesisScanError("--fixture is required for --provider fixture")
        return FixtureOptionProvider.from_file(args.fixture)
    raise SAThesisScanError(f"unsupported provider: {args.provider!r}")


def _event_id(candidate: SAThesisCandidate, now) -> str:
    return safe_part(f"rime-sa-thesis-{candidate.candidate_id}-{now.strftime('%Y%m%dT%H%M%SZ')}", max_len=120)


def _prompt(candidate: SAThesisCandidate) -> str:
    return (
        f"Review Situational Awareness options thesis candidate for {candidate.underlying} "
        f"({candidate.theme}, {candidate.direction}, triggers: {', '.join(candidate.trigger_reasons)}). "
        "Use automation/SA_THESIS_SPEC.md and options/STRATEGY_SITUATIONAL_AWARENESS.md. "
        "If accepted, promote the inactive thesis fixture into options/theses/*.json and run the options daemon dry-run; "
        "do not place live orders."
    )


def candidate_payload(candidate: SAThesisCandidate, path: Path | None = None) -> dict[str, Any]:
    payload = candidate.to_dict()
    if path is not None:
        payload["candidatePath"] = str(path)
    return payload


def candidate_event(candidate: SAThesisCandidate, *, now, session_id: str, path: Path | None = None) -> dict[str, Any]:
    return build_wake_event(
        event_id=_event_id(candidate, now),
        session_id=session_id,
        ts=isoformat_z(now),
        event_type="options_thesis_review_due",
        priority=candidate.priority,
        prompt=_prompt(candidate),
        payload=candidate_payload(candidate, path),
        source=SOURCE,
    )


def write_candidate(candidate: SAThesisCandidate, candidate_dir: Path) -> Path:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    path = candidate_dir / f"{candidate.candidate_id}.json"
    path.write_text(json.dumps(candidate.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def scan_once(
    *,
    watchlist: dict[str, Any],
    provider: OptionChainProvider,
    state: dict[str, Any],
    now,
    max_events: int,
    force: bool = False,
) -> tuple[list[SAThesisCandidate], list[dict[str, Any]]]:
    defaults = watchlist.get("defaults", {}) if isinstance(watchlist.get("defaults"), dict) else {}
    strategy = str(watchlist.get("strategy") or "situational-awareness-ai-stack")
    candidates: list[SAThesisCandidate] = []
    rejections: list[dict[str, Any]] = []
    first_seen_candidates = 0
    default_first_seen_limit = int(defaults.get("maxFirstSeenCandidatesPerScan", 3))

    for raw_entry in watchlist.get("entries", []):
        if len(candidates) >= max_events:
            break
        if not isinstance(raw_entry, dict):
            rejections.append({"entry": raw_entry, "reason": "entry must be an object"})
            continue
        entry = merged_entry(defaults, raw_entry)
        underlying = str(entry.get("underlying") or "").upper()
        if not underlying:
            rejections.append({"entry": raw_entry, "reason": "missing underlying"})
            continue
        if not entry_enabled(entry):
            rejections.append({"underlying": underlying, "reason": "disabled entry"})
            continue

        try:
            expiries = provider.list_expiries(underlying)
            expiry = select_expiry(
                expiries,
                now=now,
                target_days=int(entry.get("targetDays", 30)),
                min_days_to_expiry=int(entry.get("minDaysToExpiry", 7)),
                max_days_to_expiry=int(entry.get("maxDaysToExpiry", 60)),
            )
            if expiry is None:
                rejections.append({"underlying": underlying, "reason": "no expiry inside target window"})
                continue
            snapshot = provider.fetch_chain(underlying, expiry)
            if not entry.get("allowStaleChain", False):
                is_stale, stale_reason = chain_quote_is_stale(snapshot, now=now)
                if is_stale and not force:
                    rejections.append({
                        "underlying": underlying,
                        "reason": f"stale chain quote ({stale_reason}); SA scanner emission suppressed",
                    })
                    continue
            spot = spot_mid(snapshot)
            if spot is None or spot <= 0:
                rejections.append({"underlying": underlying, "reason": "missing underlying spot"})
                continue
            config = quote_config_from_entry(entry)
            summary = chain_summary(snapshot, now=now, config=config)
            liquid_count = int(summary["liquidContractCount"])
            state_row = state.get("underlyings", {}).get(underlying)
            reasons = trigger_reasons_for_entry(
                entry=entry,
                state_row=state_row,
                current_spot=spot,
                current_liquid_contracts=liquid_count,
                force=force,
                now=now,
            )
            min_liquid = int(entry.get("minLiquidContracts", 2))
            if liquid_count < min_liquid:
                rejections.append({"underlying": underlying, "reason": f"liquid contracts {liquid_count} below min {min_liquid}", "chainSummary": summary})
                update_underlying_state(
                    state,
                    underlying=underlying,
                    now=now,
                    spot=spot,
                    liquid_contracts=liquid_count,
                    option_expiry=expiry,
                    provider=snapshot.provider,
                )
                continue
            if not reasons:
                rejections.append({"underlying": underlying, "reason": "no trigger", "chainSummary": summary})
                update_underlying_state(
                    state,
                    underlying=underlying,
                    now=now,
                    spot=spot,
                    liquid_contracts=liquid_count,
                    option_expiry=expiry,
                    provider=snapshot.provider,
                )
                continue
            first_seen_checked = "first_seen" in reasons and "force" not in reasons
            first_seen_reviewed = False
            for direction in entry_directions(entry):
                if len(candidates) >= max_events:
                    break
                candidate = build_candidate(
                    strategy=strategy,
                    entry=entry,
                    direction=direction,
                    now=now,
                    spot=spot,
                    option_expiry=expiry,
                    chain_summary=summary,
                    trigger_reasons=reasons,
                )
                prequalification = prequalify_candidate(snapshot, candidate, entry=entry, now=now, config=config)
                candidate = replace(candidate, prequalification=prequalification)
                if emission_requires_prequalification(entry, reasons) and not prequalification.get("prequalified"):
                    rejection_reason = (
                        "first_seen prequalification failed"
                        if reasons == ("first_seen",)
                        else f"prequalification failed (triggers: {','.join(reasons)})"
                    )
                    rejections.append(
                        {
                            "candidateId": candidate.candidate_id,
                            "dedupeKey": candidate.dedupe_key,
                            "underlying": underlying,
                            "direction": direction,
                            "reason": rejection_reason,
                            "prequalification": prequalification,
                        }
                    )
                    continue
                if "first_seen" in reasons and "force" not in reasons:
                    first_seen_limit = int(entry.get("maxFirstSeenCandidatesPerScan", default_first_seen_limit))
                    if first_seen_candidates >= first_seen_limit:
                        rejections.append(
                            {
                                "candidateId": candidate.candidate_id,
                                "dedupeKey": candidate.dedupe_key,
                                "underlying": underlying,
                                "direction": direction,
                                "reason": f"first_seen throttle {first_seen_candidates} >= {first_seen_limit}",
                            }
                        )
                        continue
                if candidate.dedupe_key in state.get("emitted_candidates", {}):
                    rejections.append({"candidateId": candidate.candidate_id, "dedupeKey": candidate.dedupe_key, "reason": "already emitted"})
                    first_seen_reviewed = first_seen_reviewed or first_seen_checked
                    continue
                candidates.append(candidate)
                if "first_seen" in reasons and "force" not in reasons:
                    first_seen_candidates += 1
                    first_seen_reviewed = True
            update_underlying_state(
                state,
                underlying=underlying,
                now=now,
                spot=spot,
                liquid_contracts=liquid_count,
                option_expiry=expiry,
                provider=snapshot.provider,
                first_seen_reviewed=first_seen_reviewed if first_seen_checked else None,
                first_seen_checked=first_seen_checked,
            )
        except Exception as exc:
            rejections.append({"underlying": underlying, "reason": str(exc)})
            continue
    return candidates, rejections


def mark_candidates_emitted(state: dict[str, Any], candidates: list[SAThesisCandidate], *, now, paths: dict[str, Path], events: list[dict[str, Any]]) -> None:
    emitted = state.setdefault("emitted_candidates", {})
    event_by_key = {event.get("payload", {}).get("dedupeKey"): event for event in events}
    for candidate in candidates:
        event = event_by_key.get(candidate.dedupe_key, {})
        emitted[candidate.dedupe_key] = {
            "emitted_at": isoformat_z(now),
            "candidate_id": candidate.candidate_id,
            "event_id": event.get("id"),
            "candidate_path": str(paths[candidate.dedupe_key]) if candidate.dedupe_key in paths else None,
        }


def poll_once(args, *, session_id: str | None) -> int:
    now = parse_iso(args.now) if args.now else utcnow()
    watchlist = load_watchlist(args.watchlist)
    provider = build_provider(args)
    state = load_scan_state(args.state_path)
    candidates, rejections = scan_once(
        watchlist=watchlist,
        provider=provider,
        state=state,
        now=now,
        max_events=args.max_events,
        force=args.force,
    )
    effective_session_id = session_id or "dry-run-session"

    paths: dict[str, Path] = {}
    events: list[dict[str, Any]] = []
    if args.dry_run:
        for candidate in candidates:
            events.append(candidate_event(candidate, now=now, session_id=effective_session_id))
        print(
            json.dumps(
                {
                    "ts": isoformat_z(now),
                    "dryRun": True,
                    "candidateCount": len(candidates),
                    "eventCount": len(events),
                    "candidates": [candidate.to_dict() for candidate in candidates],
                    "events": events,
                    "rejections": rejections,
                    "rejectionCount": len(rejections),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return len(events)

    written = 0
    for candidate in candidates:
        path = write_candidate(candidate, args.candidate_dir)
        paths[candidate.dedupe_key] = path
        event = candidate_event(candidate, now=now, session_id=effective_session_id, path=path)
        wake_path = write_wake_event(args.wake_root, event)
        events.append(event)
        print(f"wrote {event['type']} {event['id']} -> {wake_path}")
        written += 1
    mark_candidates_emitted(state, candidates, now=now, paths=paths, events=events)
    save_state(args.state_path, state)
    print(json.dumps({"ts": isoformat_z(now), "eventsWritten": written, "rejections": len(rejections)}, sort_keys=True))
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Situational Awareness options thesis-review wakes")
    parser.add_argument("--watchlist", type=Path, default=DEFAULT_WATCHLIST_PATH)
    parser.add_argument("--provider", choices=["tradier", "fixture"], required=True)
    parser.add_argument("--fixture", type=Path, help="fixture option-chain source for --provider fixture")
    parser.add_argument("--session-id", help="explicit target pi session id; or set RIME_WAKE_SESSION_ID")
    parser.add_argument("--wake-root", type=Path, default=DEFAULT_WAKE_ROOT)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="emit candidates regardless of first-seen/move/liquidity triggers; still respects dedupe in non-dry-run")
    parser.add_argument("--max-events", type=int, default=5)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-sec", type=int, default=3600)
    parser.add_argument("--now", help="override current ISO timestamp for tests")
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
