#!/usr/bin/env python3
"""
check-resolutions.py — scan reasoning/*.md, query the relevant market APIs,
and print resolved/pending status.

Supports:
- legacy Manifold-primary files with **Manifold URL**
- newer venue-equality files with **Primary venue** / **Primary URL**
- Polymarket-primary files when **Polymarket market slug** is present

Usage:
    ./scripts/check-resolutions.py              # full report
    ./scripts/check-resolutions.py --resolved   # only resolved markets
    ./scripts/check-resolutions.py --pending    # only pending markets

Exit code 0 always. Designed to run during drive cycles.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REASONING_DIR = REPO_ROOT / "reasoning"
MANIFOLD_SLUG_API = "https://api.manifold.markets/v0/slug/{slug}"
POLYMARKET_MARKETS_API = "https://gamma-api.polymarket.com/markets?{query}"


def pct_from_match(pattern: str, text: str):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1)) / 100
    except Exception:
        return None


def field(pattern: str, text: str):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def parse_polymarket_url(text: str):
    """Return (event_slug, market_slug) from explicit fields/URLs when present."""
    market_slug = field(r"\*\*Polymarket market slug\*\*:\s*([^\s]+)", text)
    if not market_slug:
        m = re.search(r"polymarket\.com/market/([a-zA-Z0-9-]+)", text)
        if m:
            market_slug = m.group(1)

    event_slug = None
    m = re.search(r"polymarket\.com/event/([a-zA-Z0-9-]+)", text)
    if m:
        event_slug = m.group(1)
    return event_slug, market_slug


def parse_reasoning_file(path: Path):
    """Extract venue, market slug(s), prediction, and writing-time price."""
    text = path.read_text()

    primary_venue = field(r"\*\*Primary venue\*\*:\s*([^\n]+)", text)
    primary_url = field(r"\*\*Primary URL\*\*:\s*(https?://[^\s]+)", text)

    manifold_url = field(r"\*\*Manifold URL\*\*:\s*(https://manifold\.markets/[^\s]+)", text)
    if not manifold_url:
        m = re.search(r"(?:Primary URL|Manifold):\s*(https://manifold\.markets/[^\s)]+)", text)
        if m:
            manifold_url = m.group(1)

    manifold_slug = None
    if manifold_url:
        m = re.search(r"manifold\.markets/[^/]+/([a-zA-Z0-9-]+)", manifold_url)
        if m:
            manifold_slug = m.group(1)

    poly_event_slug, poly_market_slug = parse_polymarket_url(text)

    if not primary_venue:
        if primary_url and "polymarket.com" in primary_url:
            primary_venue = "Polymarket"
        elif primary_url and "manifold.markets" in primary_url:
            primary_venue = "Manifold"
        elif manifold_url:
            primary_venue = "Manifold"
        else:
            primary_venue = "Unknown"

    my_pred = pct_from_match(r"\*\*Prediction\*\*:\s*(\d+(?:\.\d+)?)%", text)
    market_at_writing = (
        pct_from_match(r"\*\*Primary venue price at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
        or pct_from_match(r"\*\*(?:Manifold price|Market price) at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
    )

    title_match = re.search(r"^#\s+(.+?)(?:\s*[\u2014-]\s*resolves|$)", text, re.MULTILINE | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else path.stem

    # Skip files without a primary market we know how to query.
    if primary_venue.lower().startswith("manifold") and not manifold_slug:
        return None
    if primary_venue.lower().startswith("poly") and not (poly_market_slug or poly_event_slug):
        return None
    if primary_venue == "Unknown":
        return None

    return {
        "path": path,
        "title": title,
        "primary_venue": primary_venue,
        "primary_url": primary_url,
        "manifold_slug": manifold_slug,
        "manifold_url": manifold_url,
        "poly_event_slug": poly_event_slug,
        "poly_market_slug": poly_market_slug,
        "my_prediction": my_pred,
        "market_at_writing": market_at_writing,
    }


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "rime-forecasts/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fetch_manifold_status(slug: str):
    try:
        data = fetch(MANIFOLD_SLUG_API.format(slug=slug))
        return {
            "venue": "Manifold",
            "found": True,
            "probability": data.get("probability"),
            "isResolved": data.get("isResolved", False),
            "resolution": data.get("resolution"),
            "resolutionTime": data.get("resolutionTime"),
            "resolutionProbability": data.get("resolutionProbability"),
        }
    except urllib.error.HTTPError as e:
        return {"venue": "Manifold", "found": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"venue": "Manifold", "found": False, "error": str(e)[:80]}


def parse_poly_prices(market):
    prices_raw = market.get("outcomePrices") or market.get("outcome_prices") or "[]"
    try:
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
    except Exception:
        prices = []
    yes_price = None
    if prices:
        try:
            yes_price = float(prices[0])
        except Exception:
            pass

    last = market.get("lastTradePrice")
    try:
        last = float(last) if last is not None else None
    except Exception:
        last = None
    return yes_price, last


def fetch_polymarket_status(slug: str, *, is_market_slug: bool = True):
    """Fetch a Polymarket binary market by market slug, or first market in an event as legacy fallback."""
    try:
        query = urllib.parse.urlencode({"slug": slug})
        data = fetch(POLYMARKET_MARKETS_API.format(query=query))
        if not isinstance(data, list) or not data:
            # Gamma excludes many closed markets unless explicitly requested.
            query = urllib.parse.urlencode({"slug": slug, "closed": "true"})
            data = fetch(POLYMARKET_MARKETS_API.format(query=query))
        if not isinstance(data, list) or not data:
            return {"venue": "Polymarket", "found": False, "error": "not found"}

        market = None
        if is_market_slug:
            market = next((m for m in data if m.get("slug") == slug), None)
        if market is None:
            market = data[0]

        yes_price, last = parse_poly_prices(market)
        probability = yes_price if yes_price is not None else last
        closed = bool(market.get("closed", False))
        resolution = None
        if closed and probability is not None:
            if probability >= 0.99:
                resolution = "YES"
            elif probability <= 0.01:
                resolution = "NO"
            else:
                resolution = "MKT"

        return {
            "venue": "Polymarket",
            "found": True,
            "probability": probability,
            "yes_price": yes_price,
            "last_trade": last,
            "isResolved": closed,
            "resolution": resolution,
            "end_date": market.get("endDate"),
            "slug": market.get("slug"),
        }
    except urllib.error.HTTPError as e:
        return {"venue": "Polymarket", "found": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"venue": "Polymarket", "found": False, "error": str(e)[:80]}


def fetch_primary_status(pred):
    venue = pred["primary_venue"].lower()
    if venue.startswith("poly"):
        if pred.get("poly_market_slug"):
            return fetch_polymarket_status(pred["poly_market_slug"], is_market_slug=True)
        return fetch_polymarket_status(pred["poly_event_slug"], is_market_slug=False)
    if venue.startswith("manifold"):
        return fetch_manifold_status(pred["manifold_slug"])
    return {"venue": pred["primary_venue"], "found": False, "error": "unsupported venue"}


def fetch_shadow_status(pred):
    """Currently only Polymarket shadows for legacy Manifold files."""
    if pred["primary_venue"].lower().startswith("poly"):
        return None
    if pred.get("poly_market_slug"):
        return fetch_polymarket_status(pred["poly_market_slug"], is_market_slug=True)
    if pred.get("poly_event_slug"):
        return fetch_polymarket_status(pred["poly_event_slug"], is_market_slug=False)
    return None


def brier(pred: float, outcome: float) -> float:
    return (pred - outcome) ** 2


def outcome_from_status(status):
    res = status.get("resolution")
    if res == "YES":
        return 1.0
    if res == "NO":
        return 0.0
    if res == "MKT":
        return status.get("resolutionProbability", status.get("probability", 0.5))
    return None


def main():
    args = sys.argv[1:]
    only_resolved = "--resolved" in args
    only_pending = "--pending" in args

    files = sorted(REASONING_DIR.glob("*.md"))
    if not files:
        print("no reasoning files found")
        return

    predictions = [p for p in (parse_reasoning_file(f) for f in files) if p]
    print(f"Checking {len(predictions)} prediction(s)...\n")

    results = []
    for p in predictions:
        p["status"] = fetch_primary_status(p)
        p["shadow_status"] = fetch_shadow_status(p)
        results.append(p)

    resolved = [r for r in results if r["status"].get("found") and r["status"].get("isResolved")]
    pending = [r for r in results if r["status"].get("found") and not r["status"].get("isResolved")]
    errors = [r for r in results if not r["status"].get("found")]

    if not only_pending and (resolved or not only_resolved):
        print(f"=== RESOLVED ({len(resolved)}) ===")
        if resolved:
            for r in resolved:
                status = r["status"]
                res = status.get("resolution") or "?"
                outcome = outcome_from_status(status)
                my_brier = brier(r["my_prediction"], outcome) if (outcome is not None and r["my_prediction"] is not None) else None
                mkt_brier = brier(r["market_at_writing"], outcome) if (outcome is not None and r["market_at_writing"] is not None) else None

                line = f"  {r['title'][:55]:55} | {status.get('venue', r['primary_venue'])[:4]:4} | {res:6}"
                if r["my_prediction"] is not None:
                    line += f" | me={r['my_prediction']*100:5.1f}%"
                if r["market_at_writing"] is not None:
                    line += f" mkt={r['market_at_writing']*100:5.1f}%"
                if my_brier is not None:
                    line += f" | my_brier={my_brier:.4f}"
                if mkt_brier is not None:
                    line += f" mkt_brier={mkt_brier:.4f}"
                    if my_brier is not None:
                        delta = mkt_brier - my_brier
                        sign = "+" if delta > 0 else ""
                        line += f" Δ={sign}{delta:.4f}"
                print(line)
        else:
            print("  none yet")
        print()

    if not only_resolved and (pending or not only_pending):
        print(f"=== PENDING ({len(pending)}) ===")
        for r in pending:
            status = r["status"]
            current = status.get("probability")
            drift = None
            if r["market_at_writing"] is not None and current is not None:
                drift = current - r["market_at_writing"]
            drift_str = f" drift={drift*100:+.1f}pp" if drift is not None else ""
            my_str = f"me={r['my_prediction']*100:5.1f}%" if r["my_prediction"] is not None else "me=?"
            writing_str = f"@wr={r['market_at_writing']*100:5.1f}%" if r["market_at_writing"] is not None else "@wr=?"
            current_str = f"now={current*100:5.1f}%" if current is not None else "now=?"
            venue = status.get("venue", r["primary_venue"])
            shadow_str = ""
            ss = r.get("shadow_status")
            if ss and ss.get("found"):
                shadow_price = ss.get("probability")
                if shadow_price is not None:
                    shadow_str = f" shadow_poly={shadow_price*100:5.1f}%"
            print(f"  {r['title'][:55]:55} | {venue[:4]:4} | {my_str} {writing_str} {current_str}{drift_str}{shadow_str}")
        print()

    if errors:
        print(f"=== ERRORS ({len(errors)}) ===")
        for r in errors:
            print(f"  {r['title'][:55]} [{r['primary_venue']}]: {r['status'].get('error', '?')}")

    poly_shown = any(
        (r["status"].get("venue") == "Polymarket" and r["status"].get("found"))
        or (r.get("shadow_status") and r["shadow_status"].get("found"))
        for r in results
    )
    if poly_shown:
        print()
        print("Note: Polymarket prices are raw YES prices for the queried market.")
        print("      Legacy event-level shadows may need direction-flip or market selection checks;")
        print("      explicit Polymarket market slugs are exact.")


if __name__ == "__main__":
    main()
