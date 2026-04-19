#!/usr/bin/env python3
"""
manifold-price-at.py — paginate Manifold bet history to reconstruct a market's
price at an arbitrary past timestamp. Essential for back-testing since
Manifold's /v0/bets endpoint returns only the most recent 1000 bets.

Usage:
    ./scripts/manifold-price-at.py <slug> <date-YYYY-MM-DD>

Examples:
    ./scripts/manifold-price-at.py will-the-nhl-philadelphia-flyers-ma 2026-03-01
    ./scripts/manifold-price-at.py will-jiri-prochazka-defeat-carlos-u 2026-04-10

Returns: the probAfter of the most recent bet <= target timestamp, or the
initial market probability if target is before any bet.
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "rime-forecasts/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_contract_id_and_initial_prob(slug: str):
    data = fetch(f"https://api.manifold.markets/v0/slug/{slug}")
    return data.get("id"), data.get("initialProbability") or 0.5, data.get("createdTime", 0)


def paginate_bets(contract_id: str):
    """Yield bets oldest→newest by paginating with before cursor."""
    # Collect all bets, then sort ascending. Manifold returns newest→oldest.
    all_bets = []
    cursor = None
    while True:
        url = f"https://api.manifold.markets/v0/bets?contractId={contract_id}&limit=1000"
        if cursor:
            url += f"&before={cursor}"
        try:
            batch = fetch(url)
        except urllib.error.HTTPError as e:
            print(f"error at cursor {cursor}: HTTP {e.code}", file=sys.stderr)
            break
        if not batch:
            break
        all_bets.extend(batch)
        if len(batch) < 1000:
            break
        # Use oldest bet id as cursor
        cursor = batch[-1]["id"]
    all_bets.sort(key=lambda b: b.get("createdTime", 0))
    return all_bets


def price_at(slug: str, target_date: str):
    target_dt = datetime.fromisoformat(target_date).replace(tzinfo=timezone.utc)
    target_ts_ms = int(target_dt.timestamp() * 1000)

    contract_id, initial_prob, created_time = get_contract_id_and_initial_prob(slug)
    if not contract_id:
        return {"error": "contract not found"}

    if target_ts_ms < created_time:
        return {"error": f"target {target_date} is before market creation ({datetime.fromtimestamp(created_time/1000, tz=timezone.utc).date()})"}

    bets = paginate_bets(contract_id)
    if not bets:
        return {"price": initial_prob, "basis": "initial (no bets)", "bets_total": 0}

    # Find the most recent bet <= target_ts_ms
    most_recent = None
    for b in bets:
        if b.get("createdTime", 0) <= target_ts_ms:
            most_recent = b
        else:
            break

    if most_recent is None:
        return {"price": initial_prob, "basis": "initial (target predates first bet)", "bets_total": len(bets)}

    price = most_recent.get("probAfter")
    return {
        "price": price,
        "basis": f"probAfter of bet at {datetime.fromtimestamp(most_recent['createdTime']/1000, tz=timezone.utc).isoformat()}",
        "bets_total": len(bets),
        "bets_before_target": len([b for b in bets if b.get("createdTime", 0) <= target_ts_ms]),
    }


def main():
    if len(sys.argv) < 3:
        print("usage: manifold-price-at.py <slug> <YYYY-MM-DD>")
        sys.exit(1)
    slug = sys.argv[1]
    target = sys.argv[2]
    result = price_at(slug, target)
    if "error" in result:
        print(f"error: {result['error']}")
        sys.exit(1)
    print(f"slug:  {slug}")
    print(f"date:  {target}")
    print(f"price: {result['price']*100:.1f}%")
    print(f"basis: {result['basis']}")
    print(f"bets:  {result.get('bets_before_target', 0)} before target / {result['bets_total']} total")


if __name__ == "__main__":
    main()
