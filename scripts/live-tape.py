#!/usr/bin/env python3
"""Pull live Tradier tape color for one or more underlyings.

Standing rime practice: before evaluating a position, prediction, or thesis,
pull live tape across the relevant ticker plus its read-through basket. This
script is the single canonical helper for that habit.

Tradier market-data delays are typically sub-second for `markets/quotes` and
intraday history is available via `markets/timesales`. The script does not
place orders and does not call account endpoints.

Usage:

  dotenvx run -- scripts/live-tape.py NVDA QQQ SMH ANET AVGO MRVL VRT
  dotenvx run -- scripts/live-tape.py --intraday NVDA --interval 5min
  dotenvx run -- scripts/live-tape.py --thesis options/theses/nvda-frontier-compute-up-jun18.json --basket NVDA AMD SMH AVGO ANET MRVL VRT
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from automation.options_providers import TradierOptionProvider


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "    -"
    return f"{value:+6.2f}%"


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "        -"
    return f"${value:>8.2f}"


def _fmt_int(value: int | float | None) -> str:
    if value is None:
        return "          -"
    try:
        return f"{int(value):>11,}"
    except Exception:
        return "          -"


def _fmt_vol_pct(value: float | None) -> str:
    if value is None:
        return "    -"
    return f"{value:>5.0%}"


def _fmt_delay(seconds: float | None) -> str:
    if seconds is None:
        return "      -"
    if seconds < 60:
        return f"{seconds:>5.0f}s"
    if seconds < 3600:
        return f"{seconds/60:>4.1f}m"
    if seconds < 86400:
        return f"{seconds/3600:>4.1f}h"
    return f"{seconds/86400:>4.1f}d"


def pull_quotes(provider: TradierOptionProvider, symbols: list[str]) -> list[dict[str, Any]]:
    if not symbols:
        return []
    data = provider._get("markets/quotes", {"symbols": ",".join(symbols)})
    quotes = data.get("quotes", {}).get("quote", []) if isinstance(data, dict) else []
    if isinstance(quotes, dict):
        quotes = [quotes]
    return quotes


def quote_row(quote: dict[str, Any], now: dt.datetime) -> dict[str, Any]:
    trade_ts = quote.get("trade_date")
    delay = (now.timestamp() * 1000 - trade_ts) / 1000 if trade_ts else None
    pct = quote.get("change_percentage")
    last = quote.get("last")
    bid = quote.get("bid")
    ask = quote.get("ask")
    vol = quote.get("volume")
    avg = quote.get("average_volume")
    vol_pct = (vol / avg) if (vol is not None and avg) else None
    return {
        "symbol": quote.get("symbol"),
        "last": last,
        "bid": bid,
        "ask": ask,
        "change_pct": pct,
        "volume": vol,
        "average_volume": avg,
        "volume_vs_avg": vol_pct,
        "trade_ts_ms": trade_ts,
        "delay_seconds": delay,
    }


def format_table(rows: list[dict[str, Any]]) -> str:
    lines = []
    header = f"  {'symbol':<6} {'last':>9} {'bid':>9} {'ask':>9} {'chg':>7} {'vol':>11} {'avg':>11} {'vol%':>5} {'delay':>6}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for row in rows:
        lines.append(
            f"  {str(row.get('symbol') or ''):<6} {_fmt_price(row.get('last'))} {_fmt_price(row.get('bid'))} {_fmt_price(row.get('ask'))} "
            f"{_fmt_pct(row.get('change_pct'))} {_fmt_int(row.get('volume'))} {_fmt_int(row.get('average_volume'))} "
            f"{_fmt_vol_pct(row.get('volume_vs_avg'))} {_fmt_delay(row.get('delay_seconds'))}"
        )
    return "\n".join(lines)


def pull_intraday(provider: TradierOptionProvider, symbol: str, interval: str = "5min") -> list[dict[str, Any]]:
    data = provider._get(
        "markets/timesales",
        {"symbol": symbol, "interval": interval, "session_filter": "open"},
    )
    series = data.get("series", {}).get("data", []) if isinstance(data, dict) else []
    if isinstance(series, dict):
        series = [series]
    return series


def intraday_summary(symbol: str, series: list[dict[str, Any]]) -> dict[str, Any]:
    if not series:
        return {"symbol": symbol, "bars": 0}
    first = series[0]
    last_bar = series[-1]
    total_vol = sum((bar.get("volume") or 0) for bar in series)
    high = max((bar.get("high") or float("-inf")) for bar in series)
    low = min((bar.get("low") or float("inf")) for bar in series)
    vwap_num = sum(((bar.get("vwap") or bar.get("close") or 0) * (bar.get("volume") or 0)) for bar in series)
    vwap = vwap_num / total_vol if total_vol else None
    open_px = first.get("open")
    close_px = last_bar.get("close")
    pct_open_to_close = ((close_px / open_px) - 1) if (open_px and close_px) else None
    return {
        "symbol": symbol,
        "bars": len(series),
        "start": first.get("time"),
        "end": last_bar.get("time"),
        "open": open_px,
        "high": high if high != float("-inf") else None,
        "low": low if low != float("inf") else None,
        "close": close_px,
        "open_to_close_pct": pct_open_to_close,
        "vwap": vwap,
        "total_volume": total_vol,
    }


def format_intraday_table(summary: dict[str, Any], series: list[dict[str, Any]], tail: int = 10) -> str:
    lines = []
    sym = summary.get("symbol")
    lines.append(
        f"  {sym} intraday: bars={summary.get('bars')} range={summary.get('start')} -> {summary.get('end')}"
    )
    if summary.get("bars"):
        vwap_str = f"{summary.get('vwap'):.2f}" if summary.get('vwap') is not None else "-"
        lines.append(
            f"  session: open={summary.get('open')}, high={summary.get('high')}, low={summary.get('low')}, close={summary.get('close')}, "
            f"open_to_close={_fmt_pct((summary.get('open_to_close_pct') or 0) * 100)}, vwap={vwap_str}, total_vol={summary.get('total_volume'):,}"
        )
        lines.append(f"  last {tail} bars:")
        lines.append(f"    {'time':<22} {'o':>8} {'h':>8} {'l':>8} {'c':>8} {'vol':>10}")
        for bar in series[-tail:]:
            lines.append(
                f"    {bar.get('time',''):<22} {bar.get('open',0):>8.2f} {bar.get('high',0):>8.2f} {bar.get('low',0):>8.2f} {bar.get('close',0):>8.2f} {bar.get('volume',0):>10,}"
            )
    return "\n".join(lines)


def thesis_from_path(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def thesis_color(thesis_fixture: dict[str, Any], rows_by_sym: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    under = (thesis_fixture.get("underlying") or "").upper()
    row = rows_by_sym.get(under)
    for thesis in thesis_fixture.get("theses", []):
        target = thesis.get("targetPrice")
        direction = thesis.get("direction")
        spot = row.get("last") if row else None
        gap_pct = None
        if target and spot:
            if direction == "up":
                gap_pct = (target / spot - 1) * 100
            else:
                gap_pct = (spot / target - 1) * 100
        spot_chg = row.get("change_pct") if row else None
        lines.append(
            f"  {under} {thesis.get('id')} dir={direction} target=${target} spot={_fmt_price(spot)} "
            f"chg={_fmt_pct(spot_chg)} gap_to_target={_fmt_pct(gap_pct)}"
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pull live Tradier tape color for analysis")
    parser.add_argument("symbols", nargs="*", help="symbols to pull quotes for")
    parser.add_argument("--intraday", action="append", default=[], help="symbol(s) to pull intraday bars for; repeatable")
    parser.add_argument("--interval", default="5min", choices=["1min", "5min", "15min"], help="intraday bar interval")
    parser.add_argument("--tail", type=int, default=12, help="number of trailing intraday bars to show")
    parser.add_argument("--thesis", action="append", default=[], type=Path, help="thesis fixture JSON to color with current spot; repeatable")
    parser.add_argument("--basket", nargs="*", default=[], help="extra symbols to include in the quote table for sector color")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of formatted text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    provider = TradierOptionProvider.from_env()
    now = dt.datetime.now(dt.timezone.utc)

    symbols = list(dict.fromkeys([s.upper() for s in (list(args.symbols) + list(args.basket))]))
    thesis_fixtures = []
    for path in args.thesis or []:
        try:
            thesis_fixtures.append(thesis_from_path(path))
        except Exception as exc:
            print(f"# could not load thesis fixture {path}: {exc}", file=sys.stderr)
    for fixture in thesis_fixtures:
        under = (fixture.get("underlying") or "").upper()
        if under and under not in symbols:
            symbols.append(under)

    quotes = pull_quotes(provider, symbols) if symbols else []
    rows = [quote_row(q, now) for q in quotes]
    rows_by_sym = {(r.get("symbol") or "").upper(): r for r in rows}

    intraday_blocks: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for sym in args.intraday:
        sym_u = sym.upper()
        try:
            series = pull_intraday(provider, sym_u, interval=args.interval)
            summary = intraday_summary(sym_u, series)
            intraday_blocks.append((summary, series))
        except Exception as exc:
            print(f"# intraday fetch failed for {sym_u}: {exc}", file=sys.stderr)

    if args.json:
        payload = {
            "ts": now.isoformat(),
            "quotes": rows,
            "intraday": [
                {"summary": s, "tail_bars": series[-args.tail:]} for (s, series) in intraday_blocks
            ],
            "theses": [
                {
                    "fixturePath": str(path),
                    "underlying": (fixture.get("underlying") or "").upper(),
                    "rows": [
                        {
                            "thesisId": thesis.get("id"),
                            "direction": thesis.get("direction"),
                            "targetPrice": thesis.get("targetPrice"),
                            "spot": rows_by_sym.get((fixture.get("underlying") or "").upper(), {}).get("last"),
                        }
                        for thesis in fixture.get("theses", [])
                    ],
                }
                for path, fixture in zip(args.thesis or [], thesis_fixtures)
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"# live tape at {now.isoformat()}")
    if rows:
        print("# quote table")
        print(format_table(rows))
    for summary, series in intraday_blocks:
        print()
        print(format_intraday_table(summary, series, tail=args.tail))
    if thesis_fixtures:
        print()
        print("# thesis color")
        for fixture in thesis_fixtures:
            for line in thesis_color(fixture, rows_by_sym):
                print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
