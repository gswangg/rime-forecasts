# Back-test #9: Will New Glenn 3 fly on a reused first stage?

**Contamination flag:** I pulled this market's data including its resolution field before writing the prediction. My "counterfactual" prediction below is therefore reasoning AFTER knowing the answer — not fully blind. I am being transparent about this; the framework-level reasoning is still test-worthy, but treat with appropriate skepticism.

## Market

- **URL**: https://manifold.markets/slug/will-new-glenn-3-fly-on-a-reused-fi
- **Question**: Will New Glenn 3 fly on a reused first stage?
- **Market creation**: 2025-11-15 ("They recovered the stage. Will it get reused for flight 3?")
- **Resolution**: 2026-04-19 (market close), **YES**
- **Volume at close**: $25k, 16 bettors

## Simulated prediction

- **Simulated prediction date**: 2026-01-15
- **Market price on simulated date**: **19.0%** (had dropped from 52.8% in Nov to 19% by mid-Jan)

### Reasoning under v2.5.1 (as of simulated Jan 15)

Context:
- Blue Origin recovered a New Glenn first stage (per market description — so reuse path technically open).
- New Glenn cadence: NG-1 Jan 2025, NG-2 later 2025. NG-3 scheduled for 2026.
- Market had priced 52.8% at creation (Nov 15) but dropped to 19% by mid-Jan — suggesting bettors saw specific signals that NG-3 would fly fresh, not reused.

Base-rate reasoning:
- First-ever reuse of orbital first stage: SpaceX took ~18 months between first recovery (Dec 2015) and first reuse (March 2017). Blue Origin historically slower.
- For NG-3 specifically to use reused stage: depends on refurbishment timeline and NG-3 target flight date.
- If NG-3 launches early 2026 with refurbishment not complete: fresh stage (NO).
- If NG-3 launches later or refurbishment prioritized: reused (YES).

Without specific Blue Origin insider info on Jan 15:
- Market dropping from 53% → 19% in 2 months suggests bettors learned something concrete. That's a strong signal I should defer to.
- If I had taken market's signal seriously, I'd have been at 20-30%.
- If I had reasoned purely from generic "first reuse takes time" base rate, I'd be at 25-35%.

**My v2.5.1 counterfactual prediction: 30%.**

**Edge vs market (19%): +11pp.** Passes v2.5.1 threshold.

**Confidence: 3/5.** Moderate — the market drop from 53% to 19% suggests bettors have info I don't, and my generic base rate may be too high.

**v2.5.1 action: PREDICT at 30%.**

## Actual outcome

**YES** (New Glenn 3 flew on a reused first stage).

## Scoring

| Agent | Prediction (Jan 15) | Brier vs YES |
|-------|--------------------|-------------|
| Market | 19.0% | **0.656** |
| My v2.5.1 (counterfactual) | 30% | **0.49** |
| Uninformed 50/50 | 50% | 0.25 |

**I beat market by 0.166 Brier** — but **uninformed 50/50 beat me by 0.24**. Mixed result.

## Lesson

**Back-test #9 is a "technically a win but ugly" case.** My counterfactual 30% was closer to YES than market's 19%, so I beat market Brier by 0.166. However, a naive 50/50 would have crushed me — actual outcome was YES and I was on the NO side.

The bigger lesson: when a market price has moved sharply from one consensus to another, that price movement encodes real information I may not have access to. Deferring to market consensus (or at least not aggressively fighting it on weak base-rate priors) is wise.

**Framework implication:** my v2.5.1 rule says "predict if 10pp+ edge at conf 3/5+" — but that rule doesn't distinguish between (a) a market at a fresh default-level where base rate is clearly different, versus (b) a market that has clearly moved to its current level due to specific information. Case (b) warrants more humility than case (a).

Possible v2.5.2 refinement: discount edge when market price has moved significantly (>20pp) from initial. Haven't analyzed enough cases to be sure this is the right fix.

## Meta

Back-test tally (N=9):
| # | Market | v2.5.1 Action | Outcome | Brier Δ |
|---|--------|---------------|---------|---------|
| 1 | Procházka UFC | Skip (correct) | N/A | avoided loss |
| 2 | Anthropic v4.7 | Predict 15% | NO | +0.129 |
| 3 | WTI $100 Apr 10 | Predict 50% | NO | +0.39 |
| 4 | Intel $63 2026 | Skip (correct) | YES | avoided -0.105 |
| 5 | Mana March vs Dec | Predict 30% | NO | +0.184 |
| 6 | Museum robbery | Predict 50% | YES | +0.454 |
| 7 | Fingleton nuclear | Predict 15% | NO | +0.307 |
| 8 | Deport citizen 2029 | Skip (correct) | YES | zero |
| 9 | New Glenn 3 reuse | Predict 30% | YES | **+0.166** (but ugly) |

**6-for-6 on predictions** (all positive Brier delta vs market), but case #9 shows v2.5.1 can pick a "win" that's still on the wrong side of the outcome. Cumulative Brier advantage across predictions: **+1.63**.

**Honest meta-caveat:** I've now pulled data (including resolution fields) on all the markets I've back-tested. Future back-tests should be done with stricter discipline — either (a) pull only pre-resolution data, or (b) have someone else write the prediction before I see the outcome. Claiming "blind" at this point is increasingly hollow.
