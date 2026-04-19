# Drive prompt: rime-forecasts (validation experiment)

*This is a validation experiment spawned from the primordium at `~/pi-work/mycelium/primordia/ideas/2026-04-19-rime-forecasts.md`. Purpose: test whether rime's forecasting reasoning produces useful calibration before any infrastructure or capital is committed.*

## Goal

Accumulate 15–25 resolved predictions on Manifold markets with published reasoning. At resolution, score the predictions objectively (Brier score, log loss, calibration curve). Pass/fail the idea based on whether calibration is demonstrably better than a naive base-rate strategy AND the reasoning is judged insightful rather than post-hoc rationalized.

This experiment is pundit-style — predictions without betting. No accounts, no capital, no X posts yet. Pure reasoning scored against public resolutions.

## What "success" looks like

By N=20 resolved predictions, any of these is a positive signal:

- **Calibration curve roughly diagonal** (predictions at ~70% resolve TRUE ~70% of the time, etc.).
- **Brier score better than naive base-rate** (not hard — most markets have obvious base rates — but not trivially easy either).
- **Reasoning reads as actually insightful** on reread: the writing produced specific, falsifiable claims that held up, or lost in instructive ways. This is Greg's subjective judgment at the review checkpoint.

Any of these is a negative signal (idea returns to archive with a hard-filter lesson):

- Calibration off in a systematic direction (consistently overconfident on "yes", for example).
- Worse than base-rate.
- Reasoning reads as confident-sounding noise — the kind of writing that sounds smart but doesn't commit to anything specific.

## Rules

- **Predict before resolution, always.** Every prediction file must include a timestamp earlier than the market's resolution. No post-hoc writing.
- **Publish to the public GitHub repo** at `gswangg/rime-forecasts` on every commit. The repo is the public ledger. No private-then-publish games.
- **Cover the reasoning, not just the number.** A prediction file without reasoning is not a valid prediction. The reasoning must include: what question, what base rate, what I think differs from base rate and why, what specific evidence would change my mind, what resolution criteria matter.
- **One prediction per drive cycle.** Not five. Quality over volume — this is directly the lesson from primordia's prior-attempt failure. If a market doesn't meet the bar for thoughtful reasoning, skip it this cycle.
- **Diversify market types.** Don't only cover model-release timing markets (too correlated — one source of insight per prediction). Mix: adoption curves, labor signals, technical-bet outcomes, model benchmarks, product metrics.
- **Honest base rate always.** Before stating a prediction, write down what a naive base-rate estimate would be. If your final prediction is only marginally different from base rate, that's fine and must be stated. Don't inflate confidence to seem differentiated.
- **Score honestly at resolution.** When a market resolves, update `scorecard.md` with the Brier contribution and a brief note on whether the reasoning held up. Losses get documented the same as wins.
- **No capital allocation.** Not even Manifold play-money. The experiment isolates "does the reasoning produce calibration" from "does betting behavior produce returns."

## Find-work (executed each drain)

Priority order:

1. **Check for newly-resolved markets.** Scan `reasoning/*.md` for files whose market has resolved since last check. For each: update scorecard with Brier/log-loss contribution, append resolution note to the reasoning file (not modifying the prior reasoning — add a new resolution section), commit and push. Lessons worth generalizing go into a "lessons" section of scorecard.md.
2. **Review upcoming deadlines.** Look at Manifold's trending / closing-soon markets in the tech-forecasting niche. Identify candidates: resolution date within 60–90 days, objectively resolvable (not "who will win"-style soft markets), interesting enough to write substantively about.
3. **Pick ONE candidate to predict this cycle.** Write a full prediction file at `reasoning/YYYY-MM-DD-<slug>.md` with the required structure (see below). Commit and push.
4. **If neither (1) nor (2)/(3) produces concrete work**, journal the cycle as "no action — nothing met bar" with a brief note on what was considered. Call `ac off` if this happens 3 cycles in a row (probably indicates the niche is too narrow or my search is not finding markets; ask Greg for input).

## Prediction file structure

```markdown
# <Market title> — resolves <YYYY-MM-DD>

**Manifold URL**: <url>
**Written**: <ISO timestamp>
**Prediction**: <probability, 0-100%>
**Market price at writing**: <%>

## Market question

<Exact question being predicted, including resolution criteria>

## Base rate

<Naive estimate using reference classes — similar historical outcomes, prior frequencies, market maker odds. This is the anchor.>

## Where I differ from base rate (and why)

<Substantive reasoning. Specific sources or observations. What do I know that the market doesn't, or what am I weighting differently?>

## What would change my mind

<Concrete evidence that, if observed before resolution, would flip my prediction. This is the falsifiability commitment.>

## Confidence

<How confident am I in the prediction itself? 1-5. Low confidence + strong base-rate adherence is fine.>

---

## Resolution (added after market resolves, never editing above)

**Resolved**: <YES/NO/n%>
**My prediction**: <%>
**Brier contribution**: <number>
**Post-mortem**: <did reasoning hold up? What did I miss? What generalizes?>
```

## Scorecard structure

`scorecard.md` is regenerated each resolution cycle. Structure:

```markdown
# rime-forecasts scorecard

*Last updated: <ts>*

## Summary

- Predictions made: <N>
- Resolved: <M>
- Brier score: <avg>
- Log loss: <avg>
- Calibration: <qualitative + bucket breakdown>

## Resolved predictions

| Date | Market | Prediction | Outcome | Brier | Notes |
|------|--------|-----------|---------|-------|-------|
| ... |

## Lessons

- <generalizable insight from resolution>
- <...>

## Pending predictions

| Written | Market | Prediction | Resolves |
|---------|--------|-----------|----------|
| ... |
```

## Journaling

After each cycle, append to `journal.jsonl`:

```json
{"ts":"<iso>","action":"predict|resolve|skip","files":["<filename>"],"notes":"<brief>"}
```

## Stop criterion

Call `ac off` when any of:

- 20+ predictions resolved AND scorecard shows clear signal (good or bad) — decision point: graduate-to-fruit, iterate with adjustments, or archive with lessons.
- 3 consecutive drain cycles with no action (markets not meeting bar).
- Explicit halt from Greg.

## Context to read each cycle

- **This file** — reasoning structure and rules.
- **`reasoning/*.md`** — what I've already predicted; don't repredict the same market.
- **`scorecard.md`** — current state of the calibration ledger.
- **`journal.jsonl` tail** — what I did recently.

## Post-validation path (if signal exists)

Not for this drive to execute, but documented so the experiment knows its exit:

- Graduate to `fruits/` as a mature venture.
- Register own domain.
- Set up Kalshi KYC with Greg for capitalized positions.
- Stand up subscription infrastructure.
- Begin X Articles cross-posting.
- This drive ends; a new drive takes over operational publishing.
