#!/usr/bin/env python3
"""Polymarket participant-signal daemon for rime-forecasts.

MVP scaffold. It observes public Polymarket data-api trades, normalizes them,
filters for shadow-copy quality, and emits wake-pi participant_signal_candidate
events only when configured score/economics gates pass.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.config import DEFAULT_WAKE_ROOT, require_session_id
from automation.participants import (
    MarketBook,
    ParticipantScore,
    generate_participant_events,
    mark_participant_events_emitted,
    normalize_polymarket_trade,
    participant_state_default,
)
from automation.polymarket import normalize_market
from automation.state import save_state
from automation.timeutil import isoformat_z, parse_iso, utcnow
from automation.wake import write_wake_event

DATA_API_TRADES_URL = "https://data-api.polymarket.com/trades"
GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
USER_AGENT = "rime-forecasts/polymarket-participant-daemon/0.1"
DEFAULT_STATE_PATH = Path("automation/state/polymarket-participant-daemon.json")


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def fetch_recent_trades(*, limit: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"limit": str(limit)})
    data = fetch_json(f"{DATA_API_TRADES_URL}?{query}")
    if not isinstance(data, list):
        raise ValueError("Polymarket data-api trades response was not a list")
    return [row for row in data if isinstance(row, dict)]


def fetch_markets_by_slug(slugs: set[str]) -> list[dict[str, Any]]:
    raws: list[dict[str, Any]] = []
    for slug in sorted(slugs):
        query = urllib.parse.urlencode({"slug": slug})
        try:
            data = fetch_json(f"{GAMMA_MARKETS_URL}?{query}")
        except Exception as exc:
            print(f"warning: failed to fetch Gamma market {slug}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, list):
            raws.extend(item for item in data if isinstance(item, dict))
    return raws


def load_fixture(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and isinstance(data.get("trades"), list):
        return [row for row in data["trades"] if isinstance(row, dict)]
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    raise ValueError(f"fixture must be a list or object with trades list: {path}")


def load_participant_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return participant_state_default()
    data = json.loads(path.read_text())
    state = participant_state_default()
    if isinstance(data, dict):
        state.update(data)
    for key, default in participant_state_default().items():
        state.setdefault(key, default)
    return state


def market_books_and_end_times(raw_markets: list[dict[str, Any]]) -> tuple[dict[str, MarketBook], dict[str, datetime]]:
    books: dict[str, MarketBook] = {}
    end_times: dict[str, datetime] = {}
    for raw in raw_markets:
        market = normalize_market(raw)
        if not market.slug:
            continue
        books[market.slug] = MarketBook(
            yes_bid=market.best_bid,
            yes_ask=market.best_ask,
            yes_price=market.yes_price,
            liquidity=market.liquidity,
            volume=market.volume,
        )
        if market.end_date is not None:
            end_times[market.slug] = market.end_date
    return books, end_times


def load_scores(path: Path | None) -> dict[tuple[str, str, str], ParticipantScore]:
    if not path:
        return {}
    data = json.loads(path.read_text())
    rows = data.get("scores", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("score fixture must be a list or object with scores list")
    scores: dict[tuple[str, str, str], ParticipantScore] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        score = ParticipantScore(
            wallet=str(row["wallet"]),
            domain=str(row["domain"]),
            horizon_bucket=str(row["horizonBucket"]),
            sample_size=int(row.get("sampleSize", 0)),
            mean_clv_pp=float(row.get("meanClvPp", 0.0)),
            copy_after_delay_mean_clv_pp=float(row.get("copyAfterDelayMeanClvPp", 0.0)),
            realized_roi=float(row["realizedRoi"]) if row.get("realizedRoi") is not None else None,
            shrinkage_weight=float(row.get("shrinkageWeight", 0.0)),
            score=float(row.get("score", 0.0)),
        )
        scores[(score.wallet.lower(), score.domain, score.horizon_bucket)] = score
    return scores


def poll_once(args, *, session_id: str | None) -> int:
    now = utcnow()
    state = load_participant_state(args.state_path)

    raw_trades = load_fixture(args.fixture) if args.fixture else fetch_recent_trades(limit=args.limit)
    trades = [normalize_polymarket_trade(row) for row in raw_trades]

    raw_markets: list[dict[str, Any]] = []
    if not args.no_books:
        raw_markets = fetch_markets_by_slug({trade.market_slug for trade in trades if trade.market_slug})
    books_by_slug, end_times_by_slug = market_books_and_end_times(raw_markets)
    scores = load_scores(args.score_fixture)

    effective_session_id = session_id or "dry-run-session"
    events = generate_participant_events(
        trades=trades,
        state=state,
        now=now,
        session_id=effective_session_id,
        books_by_slug=books_by_slug,
        end_times_by_slug=end_times_by_slug,
        scores_by_wallet_domain=scores,
        min_notional_usd=args.min_notional_usd,
        min_score_pp=args.min_score_pp,
        max_spread_pp=args.max_spread_pp,
        max_events=args.max_events,
        emit_unscored=args.emit_unscored,
        allow_micro=args.allow_micro,
    )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ts": isoformat_z(now),
                    "dryRun": True,
                    "trades": len(trades),
                    "markets": len(raw_markets),
                    "events": events,
                    "processedTransactionsInMemory": len(state.get("processed_transactions", {})),
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
        mark_participant_events_emitted(state, [event], now=now)
        save_state(args.state_path, state)
        written += 1

    # Save skip/unscored processed markers too, so cold-start loops do not reprocess the same trade forever.
    save_state(args.state_path, state)
    print(
        json.dumps(
            {
                "ts": isoformat_z(now),
                "trades": len(trades),
                "markets": len(raw_markets),
                "eventsWritten": written,
                "statePath": str(args.state_path),
            },
            sort_keys=True,
        )
    )
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit wake-pi events from Polymarket participant signals")
    parser.add_argument("--session-id", help="explicit target pi session id; or set RIME_WAKE_SESSION_ID")
    parser.add_argument("--wake-root", type=Path, default=DEFAULT_WAKE_ROOT, help=f"wake root (default: {DEFAULT_WAKE_ROOT})")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help=f"state path (default: {DEFAULT_STATE_PATH})")
    parser.add_argument("--fixture", type=Path, help="fixture JSON list/object with trades instead of live data-api")
    parser.add_argument("--score-fixture", type=Path, help="optional JSON score fixture for wallet/domain/horizon scores")
    parser.add_argument("--dry-run", action="store_true", help="print events without requiring session id or writing wake/state")
    parser.add_argument("--once", action="store_true", help="single poll (default)")
    parser.add_argument("--loop", action="store_true", help="poll forever in this process")
    parser.add_argument("--interval-sec", type=int, default=300, help="loop interval seconds (default: 300)")
    parser.add_argument("--limit", type=int, default=100, help="recent trade rows to fetch (default: 100)")
    parser.add_argument("--max-events", type=int, default=5, help="max participant events emitted per poll (default: 5)")
    parser.add_argument("--min-notional-usd", type=float, default=10.0, help="minimum observed trade notional (default: 10)")
    parser.add_argument("--min-score-pp", type=float, default=1.0, help="minimum shrunk participant score in CLV pp (default: 1.0)")
    parser.add_argument("--max-spread-pp", type=float, default=10.0, help="max copy-entry spread in percentage points (default: 10)")
    parser.add_argument("--emit-unscored", action="store_true", help="emit quality-gated trades even without established participant scores; for cold-start experiments")
    parser.add_argument("--allow-micro", action="store_true", help="allow micro-duration up/down markets; off by default")
    parser.add_argument("--no-books", action="store_true", help="do not fetch Gamma market books; disables copy-entry spread checks")
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
