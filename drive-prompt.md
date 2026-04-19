# Drive prompt: rime-forecasts (validation experiment, v2.5.1)

*Spawned from `~/pi-work/mycelium/primordia/ideas/2026-04-19-rime-forecasts.md`. Purpose: test whether rime's forecasting reasoning produces **economically tradeable** calibration before any capital is committed.*

*Revision history:*
- *v2 (2026-04-19 early evening): 14–45d window, 10pp edge threshold, dual-venue shadow. Rationale in journal cycle 11.*
- *v2.1 (late evening): skip actions no longer commit (kills drain-induced git churn).*
- *v2.2: cadence gate is one-shot after drive-prompt edit (prevents indefinite gate bypass).*
- *v2.3: skip-fatigue stop criterion (25 consecutive gate-skips → `ac off`).*
- *v2.5 (2026-04-20): **venue-equality principle.** Removed "Manifold-primary, Kalshi/Poly as shadow" framing — all three are equal deal-flow sources. Cross-venue arbitrage is a documentation enhancement, never a selection filter. Correcting the drift that treated "Manifold-only" as a downgrade.*
- *v2.5.1 (2026-04-20): **edge + confidence gate tightened.** Closed a hole in the v2 edge rule: a 10pp+ edge with confidence 2/5 could technically predict under the old OR-language. Back-test #4 (Intel \$63) showed this is bad discipline — low-confidence threshold-edge calls lose on average. New rule: predict if `(edge ≥ 10pp AND confidence ≥ 3/5)` OR `(confidence ≥ 4/5 with novel information)`.*

## Goal

Accumulate 15–25 resolved predictions with published reasoning where the pre-friction edge is large enough that **a real-money trader on Kalshi or Polymarket could have profitably taken the same position after typical spread and slippage costs** (for predictions placed on those venues). At resolution, score objectively:

1. **Calibration** (Brier, log loss, calibration curve) — are the numbers well-tuned?
2. **Economic realizability** (post-friction Brier differential, net edge after 2–3pp spread on the venue the prediction was placed against) — would this have made money on a real-money venue?
3. **Cross-venue arbitrage** — when the *same* question is listed on multiple venues at materially different prices, that price spread is itself a tradeable signal worth documenting. This is a distinct value-add, not a gating criterion.
4. **Reasoning quality** — subjective review at checkpoints by Greg.

This experiment remains pundit-style — no actual betting during the validation phase. The shift from v1 is that we're now validating for a **specific downstream use case** (real-money positions on Kalshi and/or Polymarket + hybrid publishing), not generic forecasting virtue.

### Venue equality principle

All three venues are **equally valid deal-flow sources**. A prediction placed against a Manifold market, a Kalshi market, or a Polymarket market is equally good for this experiment provided it meets the niche + window + edge criteria. Do not prefer or penalize based on which venue the market lives on. Specifically:

- **Do not** skip a candidate because it exists only on one venue.
- **Do not** prefer a candidate because it exists on multiple venues.
- **Do** record cross-venue prices when the same question lists on multiple venues at a material spread — that spread is arbitrage-relevant data. But this is a documentation enhancement, not a selection filter.

### Venue roles (informational, not gating)

- **Manifold** — widest market universe, free public API. Good for AI/tech niches, lab strategy, specific product milestones, research questions.
- **Kalshi** — US-regulated, USD-denominated. Good on US economic releases (CPI, jobs), weather, specific policy outcomes, some sports. Limited on named-individual/company questions.
- **Polymarket** — USDC on-chain, deep liquidity on US politics, international events, crypto, sports. Broader than Kalshi on personality-specific and culture questions.

A given prediction will naturally land on one or more of these based on what's listed.

## What "success" looks like

By N=15+ resolved predictions, **all three** must be positive:

- **Calibration curve roughly diagonal** (predictions at ~70% resolve TRUE ~70% of the time, etc.).
- **Brier score better than naive "take market price as prediction"** by a margin that exceeds typical Kalshi spread (≥0.015 better on average, translating to a real-money edge after frictions).
- **Reasoning reads as insightful on reread** — specific, falsifiable, held up or lost instructively. Greg's subjective judgment.

Any one of the below kills the idea (archive with a hard-filter lesson):

- Calibration off in a systematic direction (e.g., consistent over/under-confidence; persistent NO-bias or YES-bias).
- Raw Brier beats market but the margin doesn't exceed expected Kalshi spread — i.e., calibrated but not tradeable.
- Reasoning is confident-sounding noise — hedged enough to be unfalsifiable, or post-hoc rationalized.

## Rules

- **Predict before resolution, always.** Every prediction file must include a timestamp earlier than the market's resolution. No post-hoc writing.
- **Publish to the public GitHub repo** at `gswangg/rime-forecasts` on every commit. No private-then-publish games.
- **Cover the reasoning, not just the number.** Required sections: market question (with resolution criteria), base rate, where you differ and why, falsifiability commitment, confidence.
- **Edge threshold (v2.5.1).** Only predict if **one** of:
  - (|my prediction − market price| ≥ **10pp**) AND (confidence ≥ **3/5**), OR
  - confidence ≥ **4/5** with a specific novel information claim,
  - OR the prediction captures a mechanism (not just a probability tweak) that is itself a testable thesis with confidence ≥ **3/5**.

  Low-confidence threshold-edge calls (e.g., 10pp edge at confidence 2/5) should be **skipped**. The v2.5.1 tightening was triggered by back-test #4 (Intel \$63) which showed that a marginal-edge low-confidence prediction loses on average. Sub-10pp "base-rate vibes" predictions are still always skipped, not logged — they dilute the scorecard.
- **Cross-venue arbitrage observation (when applicable).** When picking a candidate on one venue, do a quick check for the same question on the other two. If the same question lists elsewhere at a materially different price (≥5pp spread), record all prices in the prediction file — that spread is itself a useful observation and possibly an arbitrage opportunity. If no equivalent lists on other venues, just note "single-venue question" and move on. Single-venue predictions are equally valid.
- **One prediction per drive cycle.** Quality over volume. Skipping is a first-class action.
- **Diversify market types** across cycles — adoption curves, labor signals, technical-bet outcomes, model benchmarks, product metrics, policy/legal — not five model-release timing markets.
- **Honest base rate always.** Before stating a final prediction, write down what a naive base-rate estimate would be. If my prediction is within 3pp of the base rate, state that explicitly; don't manufacture differentiation.
- **Score honestly at resolution.** Update `scorecard.md` with Brier contribution, realized post-friction edge (see scorecard structure), and a brief reasoning-held-up note. Losses get documented the same as wins.
- **No capital allocation.** No Kalshi accounts, no Polymarket wallets, no Manifold play-money. Pure pundit mode until validation passes.

## Find-work (executed each drain)

Priority order:

1. **Check for newly-resolved markets.** Scan `reasoning/*.md` for any whose underlying market has resolved since last cycle (use `scripts/check-resolutions.py`). For each: append a Resolution section to the reasoning file (never edit the frozen pre-resolution content), update scorecard with Brier + realized-edge-after-friction, extract generalizable lessons to scorecard's Lessons section, commit and push.
2. **Cadence gate.** If the most recent entry in `journal.jsonl` was within the last **18 hours** AND no new resolution appeared this cycle AND this drive-prompt.md hasn't been edited since that journal entry, **skip automatically** (silent skip per v2.1). The market universe does not refresh on sub-daily cadence and the drive-prompt caller is likely being auto-continued without human review. This prevents the cycle-9-to-11 rapid-skip pattern from v1.

   The drive-prompt-edit exception is **one-shot**: a methodology change resets the gate for exactly one cycle. That cycle performs a full scan; when it journals its result (predict or skip), the gate re-engages and subsequent cycles skip silently until either 18 hours pass or drive-prompt is edited again. This prevents the gate from being defeated indefinitely by a single drive-prompt edit.
3. **Review upcoming deadlines across all three venues.** Scan each of Manifold, Kalshi, and Polymarket for markets closing in the **14–45 day window**. Treat all three as equal deal-flow sources per the venue-equality principle. Filter: objectively resolvable, crisp criterion, decent liquidity (Manifold: ≥15 bettors or ≥$2k volume; Kalshi/Polymarket: ≥$5k liquidity or ≥$10k volume). No preference or penalty based on which venue a market lives on.
4. **Pick ONE candidate and apply the edge threshold.** If |my prediction − market price| < 10pp AND confidence < 4/5, skip with a journal note listing what was evaluated. If it passes, write the prediction file and commit.
5. **Arbitrage check (documentation only, not a selection filter).** Before committing, quickly check if the same question lists on the other two venues. If yes and spread is ≥5pp, record all prices in the prediction file — the spread is itself an observation worth documenting (and potentially an arbitrage opportunity to flag for the trading graduation). If no equivalents exist elsewhere, note "single-venue question" and move on. This does NOT affect whether to take the prediction.

## Prediction file structure

```markdown
# <Market title> — resolves <YYYY-MM-DD>

**Primary venue**: Manifold | Kalshi | Polymarket
**Primary URL**: <url of the market being predicted>
**Other venues (same question, if any)**:
- Kalshi: <url or n/a>
- Polymarket: <url or n/a>
- Manifold: <url or n/a>
**Written**: <ISO timestamp>
**Prediction**: <probability, 0-100%>
**Primary venue price at writing**: <%>
**Other venue prices at writing (aligned to YES direction)**: <list or "single-venue">
**Edge vs primary venue**: <pp>
**Cross-venue spread (if any)**: <pp between highest and lowest>
**Confidence**: <1-5>

## Market question

<Exact question, including resolution criteria. Note if resolution is ambiguous or judge-panel-based — those should generally be skipped.>

## Base rate

<Reference-class estimate, stated as a number before stating the final prediction.>

## Where I differ from base rate (and why)

<Substantive reasoning. Identify at least one specific observation, dataset, or mechanism that the market might be underweighting or overweighting. If differing by <3pp from base rate, say so explicitly.>

## What would change my mind

<Concrete falsifiable signals that would flip direction. This is the falsifiability commitment.>

## Economics at this edge

<Given the stated edge and confidence, what's the approximate Kalshi EV per $1 notional AFTER a typical 2.5pp spread? Is this a trade that would actually be taken if capital were live? One-liner is fine.>

---

## Resolution (added after market resolves, never editing above)

**Resolved**: <YES/NO/n%>
**My prediction**: <%>
**Brier contribution**: <number>
**Realized edge vs primary venue**: <pp, positive if I beat the primary venue price>
**Post-friction edge**: <pp, after 2.5pp spread — only relevant if primary venue was real-money>
**Cross-venue outcome (if applicable)**: <which venue was closest to the outcome? arbitrage opportunity that existed?>
**Post-mortem**: <did reasoning hold up? what did I miss? what generalizes?>
```

## Scorecard structure

`scorecard.md` is regenerated each resolution cycle. Structure:

```markdown
# rime-forecasts scorecard

*Last updated: <ts>*

## Summary

- Predictions made: <N>
- Resolved: <M>
- Brier score (mine): <avg>
- Brier score (naive primary-venue): <avg> (trust-the-market baseline, by each prediction's primary venue)
- Brier advantage vs primary venue: <Δ> (positive = I beat the market I predicted against)
- Post-friction Brier advantage: <Δ − 0.015> (0.015 ≈ typical 2.5pp spread translated to Brier)
- Log loss: <avg>
- Calibration buckets: <e.g., 3 predictions in 70-80% bucket resolved 2/3 YES>
- Direction bias: <below-market / above-market / balanced counts>
- Cross-venue arbitrage observations: <summary of predictions where same question listed on multiple venues with ≥5pp spread, and which venue was closer to resolution>

## Resolved predictions

| Date | Market | Venue | Me | Mkt | Outcome | Brier | ΔvsMkt | Cross-venue? | Notes |
|------|--------|-------|----|----|---------|-------|--------|--------------|-------|

## Lessons

- <generalizable insight from resolution>

## Pending predictions

| Written | Market | Venue | Me | Mkt | Cross-venue? | Resolves |
|---------|--------|-------|----|----|--------------|----------|
```

## Journaling

After each cycle, append to `journal.jsonl`:

```json
{"ts":"<iso>","action":"predict|resolve|skip","files":["<filename>"],"edge_pp":<number or null>,"notes":"<brief>"}
```

**Commit behavior:**
- **predict** and **resolve** actions: commit and push the journal entry along with reasoning/scorecard changes in a single commit.
- **skip** actions: append to `journal.jsonl` locally but do **NOT** commit or push. Skip entries accumulate and are picked up by the next predict/resolve commit as a batch. This keeps the git log focused on substantive prediction activity and avoids drain-induced commit churn.

## Stop criterion

Call `ac off` when any of:

- 15+ predictions resolved AND scorecard shows clear signal (good or bad) — decision point: graduate-to-fruit, iterate with adjustments, or archive with lessons.
- 3 consecutive drain cycles with no action (markets not meeting bar) — **and the most recent prediction is >24 hours old**. If a recent prediction exists, the cadence gate (step 2 above) should catch the rapid-skip situation without escalation.
- **Skip fatigue: 25+ consecutive gate-skip entries in journal.jsonl.** At typical rapid drain cadence (~2-5 min apart) this corresponds to roughly an hour of silent skipping. Beyond that the cost of model invocations per drain outweighs the value of staying in the loop, and whatever market refresh we were waiting for hasn't happened. Call `ac off` and note the skip-fatigue trigger in the final commit so Greg can resume on purpose.
- Explicit halt from Greg.

## Context to read each cycle

- **This file.**
- **`reasoning/*.md`** — what's been predicted.
- **`scorecard.md`** — current calibration state.
- **`journal.jsonl` tail** — recent cycle actions.

## v1 → v2 migration note

The 8 predictions placed on 2026-04-19 under v1 rules stand as a **baseline batch**. Their average delta is ~7pp (which would generally fail v2's 10pp threshold), they're all in the 60-90 day resolution window, and none had Kalshi or Polymarket shadows. At first resolution wave (late June–mid July 2026), score them honestly under both v1 and v2 criteria. The v1 baseline tells us how the old methodology performs; new predictions from cycle 12+ tell us whether v2 improves the signal.

**Optional v1-baseline enrichment:** if time permits before v1 markets resolve, retroactively record the Kalshi and Polymarket prices as they currently stand for the 8 v1 markets. This lets us score cross-venue edge for v1 predictions too, even though the decisions were made without that data.

Do not retroactively invalidate or modify v1 predictions. Frozen reasoning is frozen reasoning.

## Post-validation path (if signal exists)

Not for this drive to execute, but documented so the experiment knows its exit:

- Graduate to `fruits/` as a mature venture.
- Register a domain.
- Complete Kalshi KYC with Greg.
- Stand up subscription infrastructure (Substack / X Articles).
- Begin positioned publishing (bet + write).
- This drive ends; a successor drive handles operational publishing.
