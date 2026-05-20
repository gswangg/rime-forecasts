# Situational Awareness options strategy

Status: shadow-only seed strategy, 2026-05-20.

## Thesis

Leopold Aschenbrenner's *Situational Awareness* thesis is not generic AI enthusiasm. The tradable version is:

> AGI/superintelligence timelines force a compute, power, datacenter, memory, networking, security, and national-industrial mobilization faster than most public-market participants model.

The 13F read is consistent with this: long physical AI bottlenecks and selective memory/storage convexity, hedged with downside on crowded headline AI/semi beta.

This strategy uses that thesis as a **research prior**, not as copied positioning. Every options signal still needs a current catalyst, executable quotes, defined risk, and a documented model-vs-market edge.

## Public-market legs to monitor

| leg | Watchlist | What has to be true |
|---|---|---|
| Frontier compute / accelerators | `NVDA`, `AMD`, `AVGO`, `TSM`, `ASML`, `CBRS`, `SMH` | compute scaling remains the central arms race, but obvious beta can be crowded |
| Power / electrical / thermal | `BE`, `GEV`, `VRT`, `ETN`, `PWR`, `CEG`, `VST`, `TLN`, `NRG` | power/interconnect/cooling becomes the binding constraint |
| Memory / storage | `MU`, `SNDK`, `WDC`, `STX` | HBM/DRAM/NAND/storage scarcity reprices beyond current cycle expectations |
| Networking / interconnect | `ANET`, `AVGO`, `MRVL`, `CRDO`, `ALAB` | scale-out clusters bottleneck on fabric/optics/interconnect |
| Neocloud / datacenter conversion | `CRWV`, `CORZ`, `IREN`, `APLD`, `CLSK`, `RIOT` | compute capacity and power access matter more than legacy business labels |
| Security / sovereign compute / defense AI | `PLTR`, cyber basket, defense primes, secure cloud beneficiaries | AGI becomes national-security infrastructure |
| Hedge book | `SMH`, `QQQ`, `NVDA`, `AMD`, `AVGO`, `ORCL`, `CRWV` | crowded AI beta can break even when the long-run thesis remains right |

## Preferred option expressions

1. **Debit call verticals on bottleneck repricing**
   - Use after a catalyst confirms the bottleneck: earnings, capex guide, power contract, supply pricing, customer win, policy change.
   - Prefer 2-8 week expiries; avoid same-week lotto unless there is a precise event window.

2. **Put debit verticals on crowded obvious beta**
   - Hedge/fade euphoric semi or neocloud moves, especially into earnings, capex disappointment, export-control, rates, or financing stress.
   - This is a hedge/trade against crowding, not a rejection of the core thesis.

3. **Long naked OTM calls only when convexity is demonstrably cheap**
   - Needs exceptional liquidity and an explicit volatility view.
   - Default remains debit verticals because IV and spreads are expensive in this theme.

4. **No uncovered shorts**
   - Credit spreads remain supported by code but require explicit review and defined-risk accounting.

## Cerebras / `CBRS` note

Cerebras is now public (`CBRS`) and directly maps to the frontier-compute leg. Treat it as a special watch item, not an automatic long:

- post-IPO options can have unstable liquidity, very wide spreads, incomplete greeks, and narrative-driven IV;
- upside case: non-NVIDIA accelerator demand, inference/training cluster diversification, sovereign/non-hyperscaler compute demand;
- downside case: customer concentration, software ecosystem gap, gross-margin/scale questions, lockup/float dynamics, and AGI-hype premium unwind;
- acceptable expressions are defined-risk verticals only until the chain stabilizes.

## Signal gates

A Situational Awareness options signal may be opened for paper tracking only if all apply:

- concrete catalyst inside the option horizon;
- thesis explains *which bottleneck* is mispriced and why now;
- executable bid/ask passes `automation/OPTIONS_SPEC.md` filters;
- max loss fits local policy cap;
- model probability and target price are written before seeing generated structures;
- option IV/spread is not the whole thesis;
- exit plan and falsifier are explicit.

## Operating flow

1. Let the thesis scanner generate review candidates from `options/sa-watchlist.json`. First-seen is enabled for the curated list, but wakes are prequalified by provider sanity, directional liquidity, and options-structure search before review:
   ```bash
   dotenvx run -- scripts/sa-thesis-scan.py --provider tradier --dry-run --max-events 5
   ```
2. Promote an accepted watch candidate into an active `options/theses/*.json` file.
3. Fetch the chain through the provider, without committing credentials:
   ```bash
   dotenvx run -- scripts/options-chain-fetch.py --provider tradier --underlying CBRS --expiry <YYYY-MM-DD> --output /tmp/cbrs-chain.json --pretty
   ```
4. Dry-run the funnel:
   ```bash
   dotenvx run -- scripts/options-daemon.py --fixture-dir options/theses --provider tradier --dry-run
   ```
5. While an accepted thesis fixture is active, let `scripts/options-daemon.py` emit `options_thesis_refresh_due` when review is stale, no signal has fired, expiry approaches, spot/liquidity moves, or structure-search gates change. Refresh handling should update `reviewedAt`/notes or deactivate the fixture; it should not create a paper trade.
6. If a signal candidate is worth shadow tracking, write a local ticket with `--write-tickets --ticket-status paper_open` and mark +1h/+6h/+24h/exit.
7. Keep options P/L in `options-ledger.md`; do not mix it into prediction-market Brier.

## Falsifiers for the whole strategy

- model progress stalls at the data wall;
- agent/unhobbling progress disappoints;
- AI revenue fails to justify capex;
- power buildout is politically or physically blocked;
- option IV prices the bottleneck better than our thesis;
- crowding converts every clean thesis into bad reward/risk;
- policy/security response captures value in private/government channels rather than public equities.
