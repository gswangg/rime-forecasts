# Drive prompt: rime-forecasts (validation experiment, v2)

*Spawned from `~/pi-work/mycelium/primordia/ideas/2026-04-19-rime-forecasts.md`. Purpose: test whether rime's forecasting reasoning produces **economically tradeable** calibration before any capital is committed on Kalshi.*

*v2 (2026-04-19): revised after cycle 1–11 review. Key changes vs v1 — shorter resolution window, stricter edge threshold, dual-venue shadow requirement (Kalshi + Polymarket), and post-friction economics in scorecard. Rationale in journal.jsonl entry for cycle 11.*

## Goal

Accumulate 15–25 resolved predictions with published reasoning where the pre-friction edge is large enough that **a real-money trader on Kalshi or Polymarket could have profitably taken the same position after typical spread and slippage costs**. At resolution, score objectively:

1. **Calibration** (Brier, log loss, calibration curve) — are the numbers well-tuned?
2. **Economic realizability** (post-friction Brier differential, net edge after 2–3pp spread on each venue) — would this have made money on a real-money venue?
3. **Cross-venue triangulation** — when Manifold, Kalshi, and Polymarket disagree, which was closest to the eventual resolution? This is an independent signal about which venue's pricing is most trustworthy for a given market type.
4. **Reasoning quality** — subjective review at checkpoints by Greg.

This experiment remains pundit-style — no actual betting during the validation phase. The shift is that we're now validating for a **specific downstream use case** (real-money positions on Kalshi and/or Polymarket + hybrid publishing), not generic forecasting virtue.

### Venue roles

- **Manifold** — primary deal-flow source (widest market universe, free public API, where we find candidates).
- **Kalshi** — primary real-money shadow (US-regulated, clean legal path for eventual trading). USD-denominated. Good on US politics, economic data, some sports.
- **Polymarket** — secondary real-money shadow (USDC on-chain, deeper liquidity on politics/international/crypto, legally messier but informative). Complements Kalshi on markets Kalshi doesn't list.

When Kalshi and Polymarket both list an equivalent market, record both — cross-venue disagreement is itself signal.

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
- **Edge threshold.** Only predict if **either**:
  - |my prediction − market price| ≥ **10pp**, OR
  - confidence ≥ **4/5** with a specific novel information claim,
  - OR the prediction captures a mechanism (not just a probability tweak) that is itself a testable thesis.
  - Sub-10pp "base-rate vibes" predictions should be **skipped**, not logged. They dilute the scorecard.
- **Real-money shadow (required when possible).** For every prediction on Manifold, search **both** Kalshi and Polymarket for equivalent or closest markets. Record all three prices in the prediction file. If neither has an equivalent, note "no real-money equivalent — Manifold-only signal" and downgrade the prediction's expected usefulness. Predictions with no real-money analog are fine for calibration research but don't inform the trading thesis.
- **One prediction per drive cycle.** Quality over volume. Skipping is a first-class action.
- **Diversify market types** across cycles — adoption curves, labor signals, technical-bet outcomes, model benchmarks, product metrics, policy/legal — not five model-release timing markets.
- **Honest base rate always.** Before stating a final prediction, write down what a naive base-rate estimate would be. If my prediction is within 3pp of the base rate, state that explicitly; don't manufacture differentiation.
- **Score honestly at resolution.** Update `scorecard.md` with Brier contribution, realized post-friction edge (see scorecard structure), and a brief reasoning-held-up note. Losses get documented the same as wins.
- **No capital allocation.** No Kalshi accounts, no Polymarket wallets, no Manifold play-money. Pure pundit mode until validation passes.

## Find-work (executed each drain)

Priority order:

1. **Check for newly-resolved markets.** Scan `reasoning/*.md` for any whose underlying market has resolved since last cycle. For each: append a Resolution section to the reasoning file (never edit the frozen pre-resolution content), update scorecard with Brier + realized-edge-after-friction, extract generalizable lessons to scorecard's Lessons section, commit and push.
2. **Cadence gate.** If the most recent entry in `journal.jsonl` was within the last **18 hours** AND no new resolution appeared this cycle AND this drive-prompt.md hasn't been edited since that journal entry, **skip automatically** (silent skip per v2.1). The market universe does not refresh on sub-daily cadence and the drive-prompt caller is likely being auto-continued without human review. This prevents the cycle-9-to-11 rapid-skip pattern from v1.

   The drive-prompt-edit exception is **one-shot**: a methodology change resets the gate for exactly one cycle. That cycle performs a full scan; when it journals its result (predict or skip), the gate re-engages and subsequent cycles skip silently until either 18 hours pass or drive-prompt is edited again. This prevents the gate from being defeated indefinitely by a single drive-prompt edit.
3. **Review upcoming deadlines.** Look at Manifold's closing-soon markets in the resolution window of **14–45 days** (was 60–90 in v1 — too long for capital-efficient trading). Identify candidates: objectively resolvable, crisp criterion, ≥15 bettors OR ≥$2k volume (thin markets don't generalize to Kalshi).
4. **Pick ONE candidate and apply the edge threshold.** If the candidate's delta vs market is <10pp and confidence is <4/5, skip with a journal note listing what was evaluated. If it passes the threshold, write the prediction file and commit.
5. **Shadow pass.** Before committing, do one pass each on:
   - Kalshi: https://api.elections.kalshi.com/trade-api/v2/markets or web search for the question.
   - Polymarket: https://gamma-api.polymarket.com/markets or https://polymarket.com/ web search.
   Record Kalshi and Polymarket prices in the prediction file. Cross-venue spread (e.g., Manifold 72% / Kalshi 68% / Polymarket 75%) is itself an observation to note in reasoning.

## Prediction file structure

```markdown
# <Market title> — resolves <YYYY-MM-DD>

**Manifold URL**: <url>
**Kalshi URL**: <url or "no equivalent">
**Polymarket URL**: <url or "no equivalent">
**Written**: <ISO timestamp>
**Prediction**: <probability, 0-100%>
**Manifold price at writing**: <%>
**Kalshi price at writing**: <% or "n/a">
**Polymarket price at writing**: <% or "n/a">
**Edge vs Manifold**: <pp>
**Edge vs Kalshi**: <pp or "n/a">
**Edge vs Polymarket**: <pp or "n/a">
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
**Realized edge vs Manifold**: <pp — positive if I beat Manifold price>
**Realized edge vs Kalshi**: <pp or "n/a">
**Realized edge vs Polymarket**: <pp or "n/a">
**Post-friction edge (Kalshi)**: <pp, after 2.5pp spread>
**Post-friction edge (Polymarket)**: <pp, after 2.5pp spread>
**Cross-venue note**: <which venue was closest to the outcome? what does that suggest about venue trust for this market type?>
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
- Brier score: <avg of my predictions>
- Naive-Manifold Brier: <avg> (the score a "trust-Manifold" strategy would get)
- Naive-Kalshi Brier: <avg, when Kalshi shadow exists>
- Naive-Polymarket Brier: <avg, when Polymarket shadow exists>
- Brier advantage vs Manifold: <Δ> (positive = I beat Manifold)
- Brier advantage vs Kalshi: <Δ, on predictions with Kalshi shadows>
- Brier advantage vs Polymarket: <Δ, on predictions with Polymarket shadows>
- Post-friction Brier advantage: <Δ − 0.015> (0.015 ≈ typical 2.5pp spread translated to Brier)
- Log loss: <avg>
- Calibration buckets: <e.g., 3 predictions in 70-80% bucket resolved 2/3 YES>
- Direction bias: <below-market / above-market / balanced counts>
- Venue trust observations: <which venue's prices were most accurate on which market types?>

## Resolved predictions

| Date | Market | Me | Manifold | Kalshi | Poly | Outcome | Brier | ΔvsMf | ΔvsKa | ΔvsPm | Notes |
|------|--------|----|----------|--------|------|---------|-------|-------|-------|-------|-------|

## Lessons

- <generalizable insight from resolution>

## Pending predictions

| Written | Market | Me | Manifold | Kalshi | Poly | Resolves |
|---------|--------|----|----------|--------|------|----------|
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
