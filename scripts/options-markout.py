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
    option_structure_label,
    options_ledger_row,
)
from automation.timeutil import parse_iso, utcnow


def _ledger_row_identity(ticket: dict) -> tuple[str, str, str]:
    """Return (date, underlying, structure_label) identifying a ticket's ledger row.

    These three columns together uniquely identify a paper position in the
    canonical ledger format. Used by --append-ledger to update-in-place
    instead of duplicating rows.
    """
    created = str(ticket.get("created_at") or "")[:10]
    underlying = str(ticket.get("underlying") or "")
    structure_label = option_structure_label(
        ticket.get("structure", {}) if isinstance(ticket.get("structure"), dict) else {}
    )
    return (created, underlying, structure_label)


def _row_matches_identity(line: str, identity: tuple[str, str, str]) -> bool:
    """True if a ledger markdown row matches the (date, underlying, structure) identity."""
    if not line.startswith("|"):
        return False
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 3:
        return False
    return (cols[0], cols[1], cols[2]) == identity


def update_ledger_in_place(path: Path, ticket: dict, row: str) -> str:
    """Replace the ledger row matching this ticket; append if no match exists.

    Returns the action taken: 'replaced' or 'appended'.
    """
    identity = _ledger_row_identity(ticket)
    if not path.exists():
        path.write_text(row + "\n", encoding="utf-8")
        return "appended"
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if _row_matches_identity(line, identity):
            lines[idx] = row
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return "replaced"
    # No matching row: append at end
    with path.open("a", encoding="utf-8") as f:
        f.write(row + "\n")
    return "appended"


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
        action = update_ledger_in_place(args.ledger, updated, row)
        print(f"# ledger: {action}")
    print(row)
    if args.print_json:
        print(json.dumps(updated, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
