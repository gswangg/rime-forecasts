#!/usr/bin/env python3
"""Fetch and normalize option-chain snapshots for shadow options fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.options import FixtureOptionProvider
from automation.options_providers import TradierOptionProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a normalized option-chain snapshot")
    parser.add_argument("--provider", choices=["tradier", "fixture"], required=True)
    parser.add_argument("--underlying", required=True)
    parser.add_argument("--expiry", help="YYYY-MM-DD expiry; defaults to provider's nearest expiry")
    parser.add_argument("--fixture", type=Path, help="fixture provider source for tests/local replay")
    parser.add_argument("--output", type=Path, help="write normalized chain JSON to this path; otherwise stdout")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser


def provider_from_args(args):
    if args.provider == "tradier":
        return TradierOptionProvider.from_env()
    if args.provider == "fixture":
        if not args.fixture:
            raise SystemExit("--fixture is required for --provider fixture")
        return FixtureOptionProvider.from_file(args.fixture)
    raise SystemExit(f"unsupported provider: {args.provider}")


def main() -> int:
    args = build_parser().parse_args()
    provider = provider_from_args(args)
    expiry = date.fromisoformat(args.expiry) if args.expiry else None
    snapshot = provider.fetch_chain(args.underlying, expiry)
    payload = snapshot.to_dict()
    text = json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
