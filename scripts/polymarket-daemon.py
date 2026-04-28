#!/usr/bin/env python3
"""Polymarket event daemon for rime-forecasts.

Single-shot by default. Use --loop for a background process. Emits wake-pi JSON
files routed by explicit session id only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_REASONING_DIR, DEFAULT_STATE_PATH, DEFAULT_WAKE_ROOT, require_session_id
from automation.daemon_core import generate_events, mark_emitted, observe_watched_prices
from automation.polymarket import normalize_market
from automation.reasoning import extract_polymarket_watches
from automation.state import load_state, save_state
from automation.timeutil import isoformat_z, utcnow
from automation.wake import write_wake_event

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
USER_AGENT = "rime-forecasts/polymarket-daemon/0.1"


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def fetch_market_pages(*, limit: int, pages: int, now) -> list[dict]:
    raws: list[dict] = []
    end_date_min = (now + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    end_date_max = (now + timedelta(days=45)).isoformat().replace("+00:00", "Z")
    for page in range(pages):
        query = urllib.parse.urlencode(
            {
                "active": "true",
                "closed": "false",
                "limit": str(limit),
                "offset": str(page * limit),
                "order": "endDate",
                "ascending": "true",
                "end_date_min": end_date_min,
                "end_date_max": end_date_max,
            }
        )
        data = fetch_json(f"{GAMMA_MARKETS_URL}?{query}")
        if not isinstance(data, list) or not data:
            break
        raws.extend(item for item in data if isinstance(item, dict))
        if len(data) < limit:
            break
    return raws


def fetch_markets_by_slug(slugs: set[str]) -> list[dict]:
    raws: list[dict] = []
    for slug in sorted(slugs):
        query = urllib.parse.urlencode({"slug": slug})
        try:
            data = fetch_json(f"{GAMMA_MARKETS_URL}?{query}")
        except Exception as exc:  # fail this slug loudly in output, but continue other slugs
            print(f"warning: failed to fetch Polymarket slug {slug}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, list):
            raws.extend(item for item in data if isinstance(item, dict))
    return raws


def load_fixture(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and isinstance(data.get("markets"), list):
        return [item for item in data["markets"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise ValueError(f"fixture must be a list or object with markets list: {path}")


def dedupe_markets(raws: list[dict]):
    by_slug = {}
    for raw in raws:
        market = normalize_market(raw)
        if market.slug:
            by_slug[market.slug] = market
    return list(by_slug.values())


def poll_once(args, *, session_id: str | None) -> int:
    now = utcnow()
    state = load_state(args.state_path)
    watches = extract_polymarket_watches(args.reasoning_dir)

    if args.fixture:
        raws = load_fixture(args.fixture)
    else:
        raws = fetch_market_pages(limit=args.page_limit, pages=args.pages, now=now)
        watch_slugs = {watch.slug for watch in watches}
        raws.extend(fetch_markets_by_slug(watch_slugs))

    markets = dedupe_markets(raws)
    effective_session_id = session_id or "dry-run-session"
    events = generate_events(
        markets=markets,
        watches=watches,
        state=state,
        now=now,
        session_id=effective_session_id,
        price_move_threshold=args.price_move_threshold,
        price_move_cooldown_sec=args.price_move_cooldown_sec,
        price_move_cooldown_override=args.price_move_cooldown_override,
        price_move_reversal_band=args.price_move_reversal_band,
        price_move_max_spread=args.price_move_max_spread,
        price_move_wide_spread_override=args.price_move_wide_spread_override,
        price_move_untradeable_spread=args.price_move_untradeable_spread,
        max_candidate_events=args.max_candidate_events,
        max_events=args.max_events,
    )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ts": isoformat_z(now),
                    "dryRun": True,
                    "markets": len(markets),
                    "watches": len(watches),
                    "events": events,
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
        mark_emitted(state, [event], now=now)
        save_state(args.state_path, state)
        written += 1

    observe_watched_prices(state, markets, watches, now=now)
    save_state(args.state_path, state)
    print(
        json.dumps(
            {
                "ts": isoformat_z(now),
                "markets": len(markets),
                "watches": len(watches),
                "eventsWritten": written,
                "statePath": str(args.state_path),
            },
            sort_keys=True,
        )
    )
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit wake-pi events from Polymarket monitoring")
    parser.add_argument("--session-id", help="explicit target pi session id; or set RIME_WAKE_SESSION_ID")
    parser.add_argument("--wake-root", type=Path, default=DEFAULT_WAKE_ROOT, help=f"wake root (default: {DEFAULT_WAKE_ROOT})")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help=f"state path (default: {DEFAULT_STATE_PATH})")
    parser.add_argument("--reasoning-dir", type=Path, default=DEFAULT_REASONING_DIR, help=f"reasoning dir (default: {DEFAULT_REASONING_DIR})")
    parser.add_argument("--fixture", type=Path, help="fixture JSON list/object instead of live API")
    parser.add_argument("--dry-run", action="store_true", help="print events without requiring session id or writing wake/state")
    parser.add_argument("--once", action="store_true", help="single poll (default)")
    parser.add_argument("--loop", action="store_true", help="poll forever in this process")
    parser.add_argument("--interval-sec", type=int, default=300, help="loop interval seconds (default: 300)")
    parser.add_argument("--page-limit", type=int, default=100, help="Polymarket page size for candidate scan (default: 100)")
    parser.add_argument("--pages", type=int, default=5, help="Polymarket pages to scan for candidates (default: 5)")
    parser.add_argument("--max-events", type=int, default=10, help="max events emitted per poll (default: 10)")
    parser.add_argument("--max-candidate-events", type=int, default=3, help="max candidate events emitted per poll (default: 3)")
    parser.add_argument("--price-move-threshold", type=float, default=0.05, help="price move threshold as probability delta (default: 0.05 = 5pp)")
    parser.add_argument("--price-move-cooldown-sec", type=int, default=7200, help="suppress same-watch price move alerts inside this cooldown unless override delta is reached (default: 7200)")
    parser.add_argument("--price-move-cooldown-override", type=float, default=0.15, help="price delta from last alert that bypasses cooldown (default: 0.15 = 15pp)")
    parser.add_argument("--price-move-reversal-band", type=float, default=0.05, help="suppress recent reversal moves that return within this distance of the pre-alert price (default: 0.05 = 5pp)")
    parser.add_argument("--price-move-max-spread", type=float, default=0.20, help="suppress watched price moves on wider books unless wide-spread override is reached (default: 0.20 = 20pp)")
    parser.add_argument("--price-move-wide-spread-override", type=float, default=0.25, help="price delta that still wakes on wide watched-market books (default: 0.25 = 25pp)")
    parser.add_argument("--price-move-untradeable-spread", type=float, default=0.50, help="suppress watched price moves on books wider than this regardless of move size (default: 0.50 = 50pp)")
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
            # fail-loud but keep a daemon alive; external supervisor can still restart if desired.
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
