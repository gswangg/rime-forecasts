# rime-forecasts

A validation experiment: can rime (an AI agent) produce forecasting calibration that's **economically tradeable**?

## What this is

rime is an AI agent that makes predictions on real-money and play-money prediction markets (Manifold, Kalshi, Polymarket), with full reasoning written before resolution. This repo is the public ledger.

The goal is not to bet yet. The experiment is pundit-style — predictions without capital — to validate whether rime's reasoning produces real edge. If it does, a follow-up project graduates to capitalized positions on Kalshi + Polymarket and subscription publishing. If it doesn't, the idea returns to the archive with documented lessons.

## Current status

*As of 2026-04-30.*

- **19 predictions placed**: 8 v1 baseline, 1 v2 Manifold prediction (WTI crude $150), 1 v2.5.2 Polymarket-primary prediction (Tottenham relegation), and 9 v3 short-horizon Polymarket predictions (Running Point top US Netflix show; Elon Musk 220-239 posts; Trump 100-119 Truth Social posts; White House 140-159 posts; Powell says `Pandemic`; AMZN GAAP EPS > `$1.65`; Anthropic Mythos to US government; White House 160-179 posts Apr 24-May 1; TSLA high $390 week of Apr 27). Formal scorecard resolutions still pending.
- **Methodology**: [`drive-prompt.md`](./drive-prompt.md) v4. Event-driven market monitoring via `wake-pi`; fast-feedback horizon ladder (1–7d primary, 8–21d secondary, 22–45d tertiary only if high-liquidity), 10pp edge threshold with 3/5+ confidence, moved-market edge discount, venue-equality principle, CLV checkpoints (+1h/+6h/+24h/close), and a new no-capital shadow participant-signal track for copy-after-delay validation.
- **Back-test (N=9)**: v2.5.1 methodology retrospectively tested on resolved Manifold markets. 6-for-6 prediction wins (+1.63 cumulative Brier advantage), 3-for-3 correct skips. See [`backtest/SUMMARY.md`](./backtest/SUMMARY.md).
- **Infrastructure**: [`scripts/check-resolutions.py`](./scripts/check-resolutions.py) batch-checks Manifold-primary and Polymarket-primary predictions plus Polymarket shadows, [`scripts/manifold-price-at.py`](./scripts/manifold-price-at.py) reconstructs historical Manifold prices, [`scripts/polymarket-daemon.py`](./scripts/polymarket-daemon.py) emits session-routed `wake-pi` events for Polymarket candidates/price moves/CLV/resolutions, [`scripts/kalshi-daemon.py`](./scripts/kalshi-daemon.py) emits Kalshi candidate events, [`scripts/polymarket-participant-daemon.py`](./scripts/polymarket-participant-daemon.py) is the MVP shadow participant-signal daemon, and [`scripts/polymarket-participant-score.py`](./scripts/polymarket-participant-score.py) builds conservative wallet score fixtures from bounded public-trade backfills.

## Structure

### Core files

- [`drive-prompt.md`](./drive-prompt.md) — event-driven operating prompt. Methodology, wake-event handling, daemon operation, stop criteria. Currently v4.
- [`scorecard.md`](./scorecard.md) — running calibration score. Summary + per-prediction detail. Updated on every resolution.
- [`clv-ledger.md`](./clv-ledger.md) — fast-feedback ledger for +1h/+6h/+24h/close price movement before final resolution.
- [`participant-ledger.md`](./participant-ledger.md) — shadow ledger for participant-signal / copy-after-delay validation.
- [`journal.jsonl`](./journal.jsonl) — append-only cycle log. One JSON object per cycle.

### Predictions

- [`reasoning/YYYY-MM-DD-<slug>.md`](./reasoning/) — one file per prediction. Structure: market URL(s), base rate, where I differ and why, falsifiability commitment, confidence, then post-resolution section added later.
- Post-resolution: Brier score, realized edge vs each venue, cross-venue notes, post-mortem. Frozen pre-resolution content is never edited.

### Back-tests

- [`backtest/`](./backtest/) — retrospective application of methodology to already-resolved markets. Used to validate v2.5.x before the current portfolio resolves.
- [`backtest/SUMMARY.md`](./backtest/SUMMARY.md) — consolidated findings.
- [`backtest/NN-<slug>.md`](./backtest/) — individual back-test cases.

### Sessions

- [`sessions/YYYY-MM-DD-session-N.md`](./sessions/) — narrative summaries of drive sessions. What happened, key findings, open questions. For human context restoration.

### Automation and scripts

- [`automation/SPEC.md`](./automation/SPEC.md) — event-driven market automation contract: exact `sessionId` wake routing, event types, state, and agent handling rules.
- [`automation/PARTICIPANT_SPEC.md`](./automation/PARTICIPANT_SPEC.md) — no-capital participant intelligence contract: public data sources, scoring, copy-after-delay economics, quality gates, and participant wake types.
- [`automation/LESSONS.md`](./automation/LESSONS.md) — lessons from wake-driven operation and the daemon filters/tests they produced.
- [`scripts/polymarket-daemon.py`](./scripts/polymarket-daemon.py) — one-shot or looped Polymarket poller. Writes candidate, price-move, CLV, and resolution `wake-pi` events; requires `--session-id` or `RIME_WAKE_SESSION_ID` unless `--dry-run`.
- [`scripts/kalshi-daemon.py`](./scripts/kalshi-daemon.py) — one-shot or looped Kalshi poller. Writes short-horizon candidate `wake-pi` events; same explicit session-id rule.
- [`scripts/polymarket-participant-daemon.py`](./scripts/polymarket-participant-daemon.py) — one-shot or looped Polymarket public-trade observer. Writes `participant_signal_candidate` wakes only when score/economics gates pass; unscored cold-start observations aggregate locally without waking.
- [`scripts/polymarket-participant-score.py`](./scripts/polymarket-participant-score.py) — bounded wallet backfill scorer. Fetches public wallet trades, marks them against current Gamma prices, subtracts a copy-delay penalty, applies shrinkage, and writes a `--score-fixture` JSON for the participant daemon. This is a triage proxy, not validated edge.
- [`scripts/check-resolutions.py`](./scripts/check-resolutions.py) — scan all reasoning files, fetch current Manifold + Polymarket status, report resolved + pending.
- [`scripts/manifold-price-at.py`](./scripts/manifold-price-at.py) — reconstruct a Manifold market's price at any past timestamp via bet-history pagination.

## Validation criteria

By **N=15+ resolved predictions**, all three must be positive for the idea to graduate:

1. **Calibration curve roughly diagonal** — predictions at ~70% resolve TRUE ~70% of the time.
2. **Brier score better than naive primary-venue baseline** by ≥0.015 (translating to real-money edge after spread).
3. **Reasoning reads as insightful on reread** — Greg's subjective judgment.

Any one of the following kills the idea:

- Calibration systematically biased (over/under-confident; NO-bias or YES-bias).
- Raw Brier beats market but margin doesn't exceed spread (calibrated but not tradeable).
- Reasoning is confident-sounding noise — hedged, unfalsifiable, or post-hoc rationalized.

## Methodology pattern discovered (preliminary)

From back-testing, v2.5.x appears to capture edge via **disciplined base-rate reasoning applied to markets that default-price near 50% or ignore stated context**. Three sub-patterns:

- **Pattern A:** Markets drift to ~50% when bettors lack priors; base-rate calc (release cadence, random-walk, seasonal) dominates.
- **Pattern B:** Markets anchor on unconditional base rate even when the description states cluster/pattern evidence.
- **Pattern C:** Markets price "all N of X" extreme-specificity outcomes as near coin-flip when true base rate is tail.

And three correct-skip patterns:

- High-variance bettor-asymmetric-info questions (individual sports).
- Markets correctly pricing intuitive base rates on broad multi-year questions.
- Marginal edge + low confidence in the base-rate math.

These patterns are preliminary — confirmed at N=9 retrospective. Needs forward validation from the current portfolio resolving in June-July 2026.

## Post-validation path (if signal exists)

1. Graduate to `fruits/` as a mature venture.
2. Register a domain.
3. Complete Kalshi KYC.
4. Stand up subscription infrastructure (Substack / X Articles).
5. Begin positioned publishing (bet + write).
6. The research drive ends; a successor drive handles operational publishing.

## Operational notes for contributors / successors

- Long-running work is now event-driven through [gswangg/wake-pi](https://github.com/gswangg/wake-pi): daemons write exact-session-id events, `wake-pi` injects `[wake:<id>]`, and the agent acknowledges with `wake_done` / `wake_fail`.
- [gswangg/auto-continue-pi](https://github.com/gswangg/auto-continue-pi) remains useful for bounded implementation/maintenance, but should not be used as a market polling loop.
- Start market monitoring with `scripts/polymarket-daemon.py --session-id <pi-session-id> --loop --interval-sec 900` and `scripts/kalshi-daemon.py --session-id <pi-session-id> --loop --interval-sec 900`.
- Participant-signal monitoring is shadow-only. Cold start it by running `scripts/polymarket-participant-daemon.py --session-id <pi-session-id> --once` with no score fixture; this stores wallet/domain/horizon observation aggregates but emits no unscored wakes. Then build a triage score file with `scripts/polymarket-participant-score.py --state-path automation/state/polymarket-participant-daemon.json --output automation/state/participant-scores.json`, and finally run the daemon with `--score-fixture automation/state/participant-scores.json`. Use `--dry-run --limit 100` for inspection.
- Skip actions journal locally but don't commit; predict/resolve/automation actions commit as useful checkpoints.

## About rime

rime is the agent's chosen handle. Operated by [@gswangg](https://github.com/gswangg). Part of a larger project at [mycelium](https://github.com/gswangg/mycelium) (private) exploring whether an autonomous agent can do real, economically-productive work in the world.
