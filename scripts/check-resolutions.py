#!/usr/bin/env python3
"""
check-resolutions.py — scan all reasoning/*.md for their underlying Manifold
markets, query the Manifold API for current status, and print a summary.

Usage:
    ./scripts/check-resolutions.py              # full report
    ./scripts/check-resolutions.py --resolved   # only resolved markets
    ./scripts/check-resolutions.py --pending    # only pending markets

Exit code 0 always. Designed to be run during drive cycles as part of
"Check for newly-resolved markets" (find-work priority 1 in drive-prompt).
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REASONING_DIR = REPO_ROOT / "reasoning"
MANIFOLD_SLUG_API = "https://api.manifold.markets/v0/slug/{slug}"


def parse_reasoning_file(path: Path):
    """Extract Manifold slug, my prediction, and market price from a reasoning file."""
    text = path.read_text()
    # Manifold URL: **Manifold URL**: https://manifold.markets/<user>/<slug>
    url_match = re.search(r"\*\*Manifold URL\*\*:\s*(https://manifold\.markets/[^\s]+)", text)
    if not url_match:
        return None
    url = url_match.group(1)
    slug_match = re.search(r"manifold\.markets/[^/]+/([a-zA-Z0-9-]+)", url)
    if not slug_match:
        return None
    slug = slug_match.group(1)

    my_pred_match = re.search(r"\*\*Prediction\*\*:\s*(\d+(?:\.\d+)?)%", text)
    my_pred = float(my_pred_match.group(1)) / 100 if my_pred_match else None

    # Market price at writing — try both "Manifold price at writing" and "Market price at writing"
    mkt_match = re.search(r"\*\*(?:Manifold price|Market price) at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
    mkt_pred = float(mkt_match.group(1)) / 100 if mkt_match else None

    # Title from first # heading
    title_match = re.search(r"^#\s+(.+?)(?:\s*—|$)", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else slug

    return {
        "path": path,
        "slug": slug,
        "url": url,
        "title": title,
        "my_prediction": my_pred,
        "market_at_writing": mkt_pred,
    }


def fetch_manifold_status(slug: str):
    """Query Manifold API for current status of a market by slug."""
    try:
        url = MANIFOLD_SLUG_API.format(slug=slug)
        req = urllib.request.Request(url, headers={"User-Agent": "rime-forecasts/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return {
            "found": True,
            "probability": data.get("probability"),
            "isResolved": data.get("isResolved", False),
            "resolution": data.get("resolution"),
            "resolutionTime": data.get("resolutionTime"),
            "resolutionProbability": data.get("resolutionProbability"),
        }
    except urllib.error.HTTPError as e:
        return {"found": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"found": False, "error": str(e)[:80]}


def brier(pred: float, outcome: float) -> float:
    """Brier score for a single prediction. outcome is 1 for YES, 0 for NO, or a prob for partial."""
    return (pred - outcome) ** 2


def main():
    args = sys.argv[1:]
    only_resolved = "--resolved" in args
    only_pending = "--pending" in args

    files = sorted(REASONING_DIR.glob("*.md"))
    if not files:
        print("no reasoning files found")
        return

    predictions = []
    for f in files:
        p = parse_reasoning_file(f)
        if p:
            predictions.append(p)

    # Fetch status for each
    print(f"Checking {len(predictions)} prediction(s)...\n")
    results = []
    for p in predictions:
        status = fetch_manifold_status(p["slug"])
        p["status"] = status
        results.append(p)

    # Report
    resolved = [r for r in results if r["status"].get("isResolved")]
    pending = [r for r in results if r["status"].get("found") and not r["status"].get("isResolved")]
    errors = [r for r in results if not r["status"].get("found")]

    if not only_pending and (resolved or not only_resolved):
        print(f"=== RESOLVED ({len(resolved)}) ===")
        if resolved:
            for r in resolved:
                res = r["status"]["resolution"]  # YES / NO / MKT / CANCEL
                outcome = None
                if res == "YES":
                    outcome = 1.0
                elif res == "NO":
                    outcome = 0.0
                elif res == "MKT":
                    outcome = r["status"].get("resolutionProbability", 0.5)

                my_brier = brier(r["my_prediction"], outcome) if (outcome is not None and r["my_prediction"] is not None) else None
                mkt_brier = brier(r["market_at_writing"], outcome) if (outcome is not None and r["market_at_writing"] is not None) else None

                line = f"  {r['title'][:60]:60} | {res:6}"
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
            current = r["status"]["probability"]
            drift = None
            if r["market_at_writing"] is not None and current is not None:
                drift = current - r["market_at_writing"]
            drift_str = f" drift={drift*100:+.1f}pp" if drift is not None else ""
            my_str = f"me={r['my_prediction']*100:5.1f}%" if r["my_prediction"] is not None else "me=?"
            writing_str = f"@writing={r['market_at_writing']*100:5.1f}%" if r["market_at_writing"] is not None else "@writing=?"
            current_str = f"current={current*100:5.1f}%" if current is not None else "current=?"
            print(f"  {r['title'][:60]:60} | {my_str} {writing_str} {current_str}{drift_str}")
        print()

    if errors:
        print(f"=== ERRORS ({len(errors)}) ===")
        for r in errors:
            print(f"  {r['title'][:60]}: {r['status'].get('error', '?')}")


if __name__ == "__main__":
    main()
