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

## Positioning, vol-crush, and rotation discipline

Mega-cap event-vol prints (earnings, capex updates, policy events) do not have a clean fundamental-to-direction map. Three forces sit on top of the fundamental delta and routinely flip the post-event direction even when the print is unambiguously strong:

1. **Vol-crush hurdle.** The pre-event ATM straddle defines the threshold the print must clear to drive a positive return. A beat-and-raise inside the implied move usually produces flat-to-down because vol crush deflates premium and dealer hedging flows kick in. Compare thesis-target move to the chain's implied move to expiry before judging. `options_signal_candidate` and `options_thesis_refresh_due` wakes now carry `tapeContext.chainImpliedMoveToExpiry` and `targetMoveVsImpliedRatio`; ratios <= 1.0 mean the chain already prices the directional outcome inside its distribution.
2. **Positioning crowding.** Names that have run materially into an event lack a marginal buyer at the print. Long-only and systematic funds are at max position, and the sell-side is taking profit on the known catalyst. Strong fundamentals alone do not translate to upside in this state. Live tape (`scripts/live-tape.py`) surfaces sector-relative behavior and is the standing practice for this check.
3. **Rotation within thesis.** When the primary expression of a thesis is over-owned, beats produce rotation into second-derivative names (networking, power, memory, datacenter conversion) rather than rally in the primary. The thesis is being validated by the read-throughs; the primary becomes the funding leg. Always survey the read-through basket before accepting a primary-name structure.

Apply: when reviewing an SA thesis or generated signal candidate, the wake payload now exposes the implied-move comparison and the live-tape helper exposes basket dispersion. Reject a signal where (a) target move is well inside implied move and the thesis is not vol/path specific, or (b) the read-through basket is being bid materially while the primary is being distributed. Prefer the cheap expression of a validated thesis when a structure passes gates on a less-crowded name.

NVDA Q1 FY27 (2026-05-20) is the calibration episode for this discipline. See `automation/LESSONS.md` for the full lesson record.

## Falsifiers for the whole strategy

- model progress stalls at the data wall;
- agent/unhobbling progress disappoints;
- AI revenue fails to justify capex;
- power buildout is politically or physically blocked;
- option IV prices the bottleneck better than our thesis;
- crowding converts every clean thesis into bad reward/risk;
- policy/security response captures value in private/government channels rather than public equities.
