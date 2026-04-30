#!/usr/bin/env python3
"""Bounded Polymarket wallet backfill scorer.

Fetches recent public trades for candidate wallets and writes a score fixture that
`scripts/polymarket-participant-daemon.py --score-fixture` can consume.

Scores are current-mark triage proxies, not proof of copyable edge. Prospective
participant_signal_candidate wakes still need copy-after-delay validation.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.participants import (
    MarketBook,
    normalize_polymarket_trade,
    score_backfilled_wallet_trades,
)
from automation.polymarket import normalize_market
from automation.timeutil import isoformat_z, utcnow

DATA_API_TRADES_URL = "https://data-api.polymarket.com/trades"
GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
USER_AGENT = "rime-forecasts/polymarket-participant-score/0.1"
DEFAULT_STATE_PATH = Path("automation/state/polymarket-participant-daemon.json")


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def fetch_wallet_trades(wallet: str, *, limit: int) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"user": wallet, "limit": str(limit)})
    data = fetch_json(f"{DATA_API_TRADES_URL}?{query}")
    if not isinstance(data, list):
        raise ValueError(f"Polymarket trades response for {wallet} was not a list")
    return [row for row in data if isinstance(row, dict)]


def fetch_markets_by_slug(slugs: set[str], *, max_markets: int) -> list[dict[str, Any]]:
    raws: list[dict[str, Any]] = []
    for slug in sorted(slugs)[:max_markets]:
        query = urllib.parse.urlencode({"slug": slug})
        try:
            data = fetch_json(f"{GAMMA_MARKETS_URL}?{query}")
        except Exception as exc:
            print(f"warning: failed to fetch Gamma market {slug}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, list):
            raws.extend(item for item in data if isinstance(item, dict))
    return raws


def load_state_wallets(path: Path, *, max_wallets: int, min_count: int, min_notional: float) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    observations = data.get("wallet_observations", {}) if isinstance(data, dict) else {}
    wallet_rows: dict[str, dict[str, Any]] = {}
    if isinstance(observations, dict):
        for record in observations.values():
            if not isinstance(record, dict):
                continue
            wallet = str(record.get("wallet") or record.get("displayWallet") or "").lower()
            if not wallet:
                continue
            row = wallet_rows.setdefault(wallet, {"wallet": wallet, "count": 0, "notional": 0.0, "lastObservedAt": ""})
            row["count"] += int(record.get("count", 0))
            row["notional"] += float(record.get("totalNotionalUsd", 0.0))
            row["lastObservedAt"] = max(str(row.get("lastObservedAt") or ""), str(record.get("lastObservedAt") or ""))
    candidates = [
        row
        for row in wallet_rows.values()
        if int(row["count"]) >= min_count and float(row["notional"]) >= min_notional
    ]
    candidates.sort(key=lambda row: (row["notional"], row["count"], row["lastObservedAt"]), reverse=True)
    return [str(row["wallet"]) for row in candidates[:max_wallets]]


def load_fixture(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)], []
    if not isinstance(data, dict):
        raise ValueError("fixture must be a list or object")

    trades: list[dict[str, Any]] = []
    if isinstance(data.get("trades"), list):
        trades.extend(row for row in data["trades"] if isinstance(row, dict))
    wallets = data.get("wallets")
    if isinstance(wallets, dict):
        for rows in wallets.values():
            if isinstance(rows, list):
                trades.extend(row for row in rows if isinstance(row, dict))
    markets = [row for row in data.get("markets", []) if isinstance(row, dict)] if isinstance(data.get("markets"), list) else []
    return trades, markets


def normalize_trade_rows(rows: list[dict[str, Any]]) -> list[Any]:
    trades = []
    for row in rows:
        try:
            trades.append(normalize_polymarket_trade(row))
        except Exception as exc:
            print(f"warning: skipped malformed trade row: {exc}", file=sys.stderr)
    return trades


def market_maps(raw_markets: list[dict[str, Any]]) -> tuple[dict[str, MarketBook], dict[str, Any]]:
    books: dict[str, MarketBook] = {}
    end_times: dict[str, Any] = {}
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


def unique_wallets_from_trades(rows: list[dict[str, Any]], *, max_wallets: int) -> list[str]:
    wallets: list[str] = []
    seen: set[str] = set()
    for row in rows:
        wallet = str(row.get("proxyWallet") or row.get("user") or "").lower()
        if wallet and wallet not in seen:
            wallets.append(wallet)
            seen.add(wallet)
            if len(wallets) >= max_wallets:
                break
    return wallets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill public Polymarket wallet trades into participant score fixture")
    parser.add_argument("--wallet", action="append", default=[], help="wallet/proxyWallet to backfill; may be repeated")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help=f"participant daemon state path for wallet candidates (default: {DEFAULT_STATE_PATH})")
    parser.add_argument("--fixture", type=Path, help="offline fixture: list or object with trades/markets")
    parser.add_argument("--output", type=Path, help="write score fixture JSON here; stdout if omitted")
    parser.add_argument("--limit-per-wallet", type=int, default=200, help="max public trades fetched per wallet (default: 200)")
    parser.add_argument("--max-wallets", type=int, default=25, help="max wallets selected from state/fixture (default: 25)")
    parser.add_argument("--max-markets", type=int, default=200, help="max unique markets fetched from Gamma (default: 200)")
    parser.add_argument("--min-observation-count", type=int, default=1, help="state wallet selection minimum observed trades (default: 1)")
    parser.add_argument("--min-observation-notional", type=float, default=0.0, help="state wallet selection minimum observed notional (default: 0)")
    parser.add_argument("--min-trade-notional", type=float, default=10.0, help="minimum historical trade notional included in scoring (default: 10)")
    parser.add_argument("--min-samples", type=int, default=5, help="minimum qualified trades for a score row (default: 5)")
    parser.add_argument("--prior-n", type=int, default=25, help="shrinkage prior sample size (default: 25)")
    parser.add_argument("--copy-delay-penalty-pp", type=float, default=1.0, help="fixed penalty from raw current CLV to copy-after-delay proxy (default: 1pp)")
    parser.add_argument("--include-micro", action="store_true", help="include micro-duration up/down markets")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = utcnow()

    fixture_trade_rows: list[dict[str, Any]] = []
    fixture_market_rows: list[dict[str, Any]] = []
    if args.fixture:
        fixture_trade_rows, fixture_market_rows = load_fixture(args.fixture)

    wallets = [wallet.lower() for wallet in args.wallet]
    if not wallets and fixture_trade_rows:
        wallets = unique_wallets_from_trades(fixture_trade_rows, max_wallets=args.max_wallets)
    if not wallets:
        wallets = load_state_wallets(
            args.state_path,
            max_wallets=args.max_wallets,
            min_count=args.min_observation_count,
            min_notional=args.min_observation_notional,
        )
    wallets = list(dict.fromkeys(wallets))[: args.max_wallets]
    if not wallets:
        raise SystemExit("no wallets supplied and no eligible wallet observations found")

    raw_trades: list[dict[str, Any]] = []
    if fixture_trade_rows:
        wallet_set = set(wallets)
        raw_trades = [
            row
            for row in fixture_trade_rows
            if str(row.get("proxyWallet") or row.get("user") or "").lower() in wallet_set
        ]
    else:
        for wallet in wallets:
            try:
                raw_trades.extend(fetch_wallet_trades(wallet, limit=args.limit_per_wallet))
            except Exception as exc:
                print(f"warning: failed to fetch trades for {wallet}: {exc}", file=sys.stderr)

    trades = normalize_trade_rows(raw_trades)
    raw_markets = fixture_market_rows
    if not raw_markets:
        raw_markets = fetch_markets_by_slug({trade.market_slug for trade in trades if trade.market_slug}, max_markets=args.max_markets)
    books_by_slug, end_times_by_slug = market_maps(raw_markets)

    scores = score_backfilled_wallet_trades(
        trades=trades,
        books_by_slug=books_by_slug,
        end_times_by_slug=end_times_by_slug,
        min_notional_usd=args.min_trade_notional,
        min_samples=args.min_samples,
        prior_n=args.prior_n,
        copy_delay_penalty_pp=args.copy_delay_penalty_pp,
        allow_micro=args.include_micro,
    )
    payload = {
        "generatedAt": isoformat_z(now),
        "source": "rime-forecasts/polymarket-participant-score/current-price-backfill",
        "method": "participant-direction current YES mark minus trade-implied entry, minus fixed copy-delay penalty, then shrinkage",
        "warning": "This is a triage fixture only; it is not prospective copy-after-delay edge.",
        "config": {
            "wallets": wallets,
            "limitPerWallet": args.limit_per_wallet,
            "maxWallets": args.max_wallets,
            "maxMarkets": args.max_markets,
            "minTradeNotionalUsd": args.min_trade_notional,
            "minSamples": args.min_samples,
            "priorN": args.prior_n,
            "copyDelayPenaltyPp": args.copy_delay_penalty_pp,
            "includeMicro": args.include_micro,
        },
        "tradesFetched": len(raw_trades),
        "tradesNormalized": len(trades),
        "marketsLoaded": len(raw_markets),
        "scores": scores,
    }

    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content)
        print(json.dumps({"output": str(args.output), "scores": len(scores), "wallets": len(wallets)}, sort_keys=True))
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
