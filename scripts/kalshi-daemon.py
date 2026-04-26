#!/usr/bin/env python3
"""Kalshi event daemon for rime-forecasts.

Single-shot by default. Use --loop for a background process. Emits wake-pi
candidate_found JSON files routed by explicit session id only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_WAKE_ROOT, require_session_id
from automation.kalshi import normalize_market
from automation.kalshi_core import generate_events, mark_emitted
from automation.state import load_state, save_state
from automation.timeutil import isoformat_z, utcnow
from automation.wake import write_wake_event

KALSHI_MARKETS_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
USER_AGENT = "rime-forecasts/kalshi-daemon/0.1"
DEFAULT_STATE_PATH = REPO_ROOT / "automation" / "state" / "kalshi-daemon.json"


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def fetch_market_pages(*, limit: int, pages: int) -> list[dict]:
    raws: list[dict] = []
    cursor = None
    for _page in range(pages):
        params = {"status": "open", "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        query = urllib.parse.urlencode(params)
        data = fetch_json(f"{KALSHI_MARKETS_URL}?{query}")
        markets = data.get("markets", []) if isinstance(data, dict) else []
        raws.extend(item for item in markets if isinstance(item, dict))
        cursor = data.get("cursor") if isinstance(data, dict) else None
        if not cursor or not markets:
            break
    return raws


def load_fixture(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and isinstance(data.get("markets"), list):
        return [item for item in data["markets"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise ValueError(f"fixture must be a list or object with markets list: {path}")


def dedupe_markets(raws: list[dict]):
    by_ticker = {}
    for raw in raws:
        market = normalize_market(raw)
        if market.ticker:
            by_ticker[market.ticker] = market
    return list(by_ticker.values())


def poll_once(args, *, session_id: str | None) -> int:
    now = utcnow()
    state = load_state(args.state_path)
    raws = load_fixture(args.fixture) if args.fixture else fetch_market_pages(limit=args.page_limit, pages=args.pages)
    markets = dedupe_markets(raws)
    effective_session_id = session_id or "dry-run-session"
    events = generate_events(
        markets=markets,
        state=state,
        now=now,
        session_id=effective_session_id,
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

    save_state(args.state_path, state)
    print(
        json.dumps(
            {
                "ts": isoformat_z(now),
                "markets": len(markets),
                "eventsWritten": written,
                "statePath": str(args.state_path),
            },
            sort_keys=True,
        )
    )
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit wake-pi candidate events from Kalshi monitoring")
    parser.add_argument("--session-id", help="explicit target pi session id; or set RIME_WAKE_SESSION_ID")
    parser.add_argument("--wake-root", type=Path, default=DEFAULT_WAKE_ROOT, help=f"wake root (default: {DEFAULT_WAKE_ROOT})")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help=f"state path (default: {DEFAULT_STATE_PATH})")
    parser.add_argument("--fixture", type=Path, help="fixture JSON list/object instead of live API")
    parser.add_argument("--dry-run", action="store_true", help="print events without requiring session id or writing wake/state")
    parser.add_argument("--once", action="store_true", help="single poll (default)")
    parser.add_argument("--loop", action="store_true", help="poll forever in this process")
    parser.add_argument("--interval-sec", type=int, default=900, help="loop interval seconds (default: 900)")
    parser.add_argument("--page-limit", type=int, default=200, help="Kalshi page size for candidate scan (default: 200)")
    parser.add_argument("--pages", type=int, default=3, help="Kalshi pages to scan for candidates (default: 3)")
    parser.add_argument("--max-events", type=int, default=10, help="max events emitted per poll (default: 10)")
    parser.add_argument("--max-candidate-events", type=int, default=3, help="max candidate events emitted per poll (default: 3)")
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
