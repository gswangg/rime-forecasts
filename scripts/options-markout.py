#!/usr/bin/env python3
"""Update a local shadow options ticket with a CLV/markout observation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.options import (
    add_option_markout,
    load_option_chain_snapshot,
    mark_structure_value_from_chain,
    option_markout,
    options_ledger_row,
)
from automation.timeutil import parse_iso, utcnow


def load_ticket(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("option ticket must be a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update a local option ticket with a paper markout and print a ledger row")
    parser.add_argument("--ticket", type=Path, required=True, help="execution/options-tickets/*.json ticket artifact")
    parser.add_argument("--checkpoint", required=True, help="mark checkpoint, e.g. 1h, 6h, 24h, exit, expiry")
    parser.add_argument("--now", help="mark timestamp; defaults to now")
    parser.add_argument("--mark-value", type=float, help="current structure value in dollars; for credit structures this is current cost to close")
    parser.add_argument("--underlying-price", type=float, help="underlying price at mark")
    parser.add_argument("--fixture", type=Path, help="current option-chain fixture to compute mark from leg mids")
    parser.add_argument("--iv", type=float)
    parser.add_argument("--delta", type=float)
    parser.add_argument("--gamma", type=float)
    parser.add_argument("--theta", type=float)
    parser.add_argument("--vega", type=float)
    parser.add_argument("--notes", default="")
    parser.add_argument("--no-write", action="store_true", help="print updated ticket/ledger row without writing back")
    parser.add_argument("--append-ledger", action="store_true", help="append the generated row to options-ledger.md")
    parser.add_argument("--ledger", type=Path, default=Path("options-ledger.md"), help="ledger path for --append-ledger")
    parser.add_argument("--print-json", action="store_true", help="print updated ticket JSON after the ledger row")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ticket = load_ticket(args.ticket)
    now = parse_iso(args.now) if args.now else utcnow()

    mark_value = args.mark_value
    underlying_price = args.underlying_price
    if args.fixture:
        snapshot = load_option_chain_snapshot(args.fixture)
        mark_value = mark_structure_value_from_chain(ticket.get("structure", {}), snapshot)
        underlying_price = underlying_price if underlying_price is not None else snapshot.underlying_mid
    if mark_value is None:
        raise SystemExit("--mark-value or --fixture is required")

    mark = option_markout(
        ticket,
        checkpoint=args.checkpoint,
        mark_value=mark_value,
        underlying_price=underlying_price,
        now=now,
        iv=args.iv,
        delta=args.delta,
        gamma=args.gamma,
        theta=args.theta,
        vega=args.vega,
        notes=args.notes,
    )
    updated = add_option_markout(ticket, mark)
    if not args.no_write:
        args.ticket.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row = options_ledger_row(updated)
    if args.append_ledger:
        with args.ledger.open("a", encoding="utf-8") as f:
            f.write(row + "\n")
    print(row)
    if args.print_json:
        print(json.dumps(updated, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
