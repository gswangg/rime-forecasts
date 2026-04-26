# rime-forecasts

A validation experiment: can rime (an AI agent) produce forecasting calibration that's **economically tradeable**?

## What this is

rime is an AI agent that makes predictions on real-money and play-money prediction markets (Manifold, Kalshi, Polymarket), with full reasoning written before resolution. This repo is the public ledger.

The goal is not to bet yet. The experiment is pundit-style — predictions without capital — to validate whether rime's reasoning produces real edge. If it does, a follow-up project graduates to capitalized positions on Kalshi + Polymarket and subscription publishing. If it doesn't, the idea returns to the archive with documented lessons.

## Current status

*As of 2026-04-26 (session 2).*

- **10 predictions placed**: 8 v1 baseline (mixed categories, <10pp edges), 1 v2 Manifold prediction (WTI crude $150, 15.5pp edge), 1 v2.5.2 Polymarket-primary prediction (Tottenham relegation, 17.95pp edge). Earliest resolution 2026-05-27, latest 2026-07-18.
- **Methodology**: [`drive-prompt.md`](./drive-prompt.md) v2.5.2. 14–45 day resolution window, 10pp edge threshold with 3/5+ confidence, moved-market edge discount, venue-equality principle (Manifold, Kalshi, Polymarket all first-class).
- **Back-test (N=9)**: v2.5.1 methodology retrospectively tested on resolved Manifold markets. 6-for-6 prediction wins (+1.63 cumulative Brier advantage), 3-for-3 correct skips. See [`backtest/SUMMARY.md`](./backtest/SUMMARY.md).
- **Infrastructure**: [`scripts/check-resolutions.py`](./scripts/check-resolutions.py) batch-checks Manifold-primary and Polymarket-primary predictions plus Polymarket shadows, [`scripts/manifold-price-at.py`](./scripts/manifold-price-at.py) reconstructs historical Manifold prices.

## Structure

### Core files

- [`drive-prompt.md`](./drive-prompt.md) — the autonomous cycle rime runs each drain. Methodology, rules, find-work priority, stop criteria. Currently v2.5.2.
- [`scorecard.md`](./scorecard.md) — running calibration score. Summary + per-prediction detail. Updated on every resolution.
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

### Scripts

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

- The drive runs via [gswangg/auto-continue-pi](https://github.com/gswangg/auto-continue-pi). `ac on` enables, `ac off` pauses, `ac drive` reconfigures the drain prompt.
- Drive-prompt has a **cadence gate**: skips silently if the most recent journal entry is <18h old, no new resolution has appeared, and drive-prompt hasn't been edited since. Prevents rapid-drain thrash.
- Drive-prompt has a **skip-fatigue** stop: 25 consecutive gate-skip entries triggers `ac off` automatically.
- Skip actions journal locally but don't commit; predict/resolve actions commit as batches including accumulated skips.

## About rime

rime is the agent's chosen handle. Operated by [@gswangg](https://github.com/gswangg). Part of a larger project at [mycelium](https://github.com/gswangg/mycelium) (private) exploring whether an autonomous agent can do real, economically-productive work in the world.
