#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automation.execution import ExecutionPolicy, MarketQuote, build_order_ticket, ticket_summary, write_ticket

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "rime-forecasts-execution/0.1", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def decode_jsonish(value: Any, default: list[Any]) -> list[Any]:
    if value is None:
        return list(default)
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return list(default)
        return decoded if isinstance(decoded, list) else list(default)
    return list(default)


def float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0 < parsed < 1 else None


def gamma_market(identifier: str) -> dict[str, Any]:
    if identifier.isdigit():
        return fetch_json(f"{GAMMA}/markets/{identifier}")
    slug = urllib.parse.quote(identifier, safe="")
    markets = fetch_json(f"{GAMMA}/markets?slug={slug}")
    if not markets:
        raise RuntimeError(f"no Polymarket Gamma market found for slug {identifier!r}")
    return markets[0]


def clob_price(token_id: str, side: str) -> float | None:
    try:
        data = fetch_json(f"{CLOB}/price?token_id={urllib.parse.quote(token_id)}&side={side}")
    except Exception:
        return None
    return float_or_none(data.get("price"))


def polymarket_quote(identifier: str) -> MarketQuote:
    market = gamma_market(identifier)
    outcomes = [str(o).strip().lower() for o in decode_jsonish(market.get("outcomes"), [])]
    token_ids = [str(t) for t in decode_jsonish(market.get("clobTokenIds"), [])]

    yes_bid = float_or_none(market.get("bestBid"))
    yes_ask = float_or_none(market.get("bestAsk"))
    no_bid = None
    no_ask = None

    if token_ids and outcomes:
        try:
            yes_token = token_ids[outcomes.index("yes")]
            yes_bid = clob_price(yes_token, "BUY") or yes_bid
            yes_ask = clob_price(yes_token, "SELL") or yes_ask
        except (ValueError, IndexError):
            pass
        try:
            no_token = token_ids[outcomes.index("no")]
            no_bid = clob_price(no_token, "BUY")
            no_ask = clob_price(no_token, "SELL")
        except (ValueError, IndexError):
            pass

    market_id = str(market.get("id") or market.get("slug") or identifier)
    slug = str(market.get("slug") or identifier)
    return MarketQuote(
        venue="Polymarket",
        market_id=market_id,
        title=str(market.get("question") or market.get("title") or slug),
        url=f"https://polymarket.com/market/{slug}",
        yes_bid=yes_bid,
        yes_ask=yes_ask,
        no_bid=no_bid,
        no_ask=no_ask,
        liquidity=float(market.get("liquidityNum") or market.get("liquidity") or 0),
        volume=float(market.get("volumeNum") or market.get("volume") or 0),
    )


def manual_quote(args: argparse.Namespace) -> MarketQuote:
    return MarketQuote(
        venue=args.venue_name,
        market_id=args.market_id,
        title=args.title,
        url=args.url,
        yes_bid=args.yes_bid,
        yes_ask=args.yes_ask,
        no_bid=args.no_bid,
        no_ask=args.no_ask,
    )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build a dry-run rime execution ticket from a live or manual quote.")
    p.add_argument("--venue", choices=["polymarket", "manual"], required=True)
    p.add_argument("--forecast-yes", type=float, required=True, help="Rime fair YES probability, 0-1.")
    p.add_argument("--side", choices=["YES", "NO"], help="Override side; default chooses best positive edge.")
    p.add_argument("--sizing-mode", choices=["max_payout", "cash"], default="max_payout")
    p.add_argument("--amount", type=float, default=100.0)
    p.add_argument("--min-edge", type=float, default=0.10)
    p.add_argument("--max-spread", type=float, default=0.10)
    p.add_argument("--max-cash-risk", type=float, default=100.0)
    p.add_argument("--ticket-dir", default="execution/tickets")
    p.add_argument("--no-write", action="store_true", help="Print ticket only; do not write execution/tickets/*.json")
    p.add_argument("--notes", default="")

    poly = p.add_argument_group("Polymarket")
    poly.add_argument("--slug", help="Polymarket market slug")
    poly.add_argument("--gamma-id", help="Polymarket Gamma market id")

    manual = p.add_argument_group("Manual quote")
    manual.add_argument("--venue-name", default="Manual")
    manual.add_argument("--market-id", default="manual-market")
    manual.add_argument("--title", default="Manual market")
    manual.add_argument("--url", default="")
    manual.add_argument("--yes-bid", type=float)
    manual.add_argument("--yes-ask", type=float)
    manual.add_argument("--no-bid", type=float)
    manual.add_argument("--no-ask", type=float)
    return p


def main() -> int:
    args = parser().parse_args()
    if args.venue == "polymarket":
        identifier = args.gamma_id or args.slug
        if not identifier:
            raise SystemExit("--slug or --gamma-id is required for --venue polymarket")
        quote = polymarket_quote(identifier)
    else:
        if args.yes_bid is None or args.yes_ask is None:
            raise SystemExit("--yes-bid and --yes-ask are required for --venue manual")
        quote = manual_quote(args)

    policy = ExecutionPolicy(
        min_edge=args.min_edge,
        max_spread=args.max_spread,
        sizing_mode=args.sizing_mode,
        amount=args.amount,
        max_cash_risk=args.max_cash_risk,
        allow_live_submit=False,
    )
    ticket = build_order_ticket(
        quote=quote,
        forecast_yes=args.forecast_yes,
        policy=policy,
        side=args.side,
        now=datetime.now(timezone.utc),
        notes=args.notes,
    )
    print(ticket_summary(ticket))
    print(ticket.to_json())
    if not args.no_write:
        path = write_ticket(ticket, ROOT / args.ticket_dir)
        print(f"wrote {path}")
    return 0 if ticket.status == "draft" else 2


if __name__ == "__main__":
    raise SystemExit(main())
