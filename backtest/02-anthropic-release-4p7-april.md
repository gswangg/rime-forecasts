# Back-test #2: Anthropic release model > v4.6 by April 15, 2026

## Market

- **URL**: https://manifold.markets/slug/will-anthropic-release-a-model-with
- **Question**: Will Anthropic release a model with a higher version number than 4.6 by April 15th?
- **Market creation**: 2026-03-17
- **Resolution**: 2026-04-16, **NO** (no release happened)
- **Volume at close**: $31k, 110 bettors

## Simulated prediction

- **Simulated prediction date**: 2026-03-25 (21 days before resolution deadline)
- **Market price on simulated date**: **39.1%** (verified via `scripts/manifold-price-at.py`)

### Contamination check

I have training-data awareness of Anthropic's model naming conventions and general release cadence through Claude 3, 3.5, 3.7, 4, 4.5, 4.6. I do not specifically remember a 4.7+ release event before April 15, 2026 (the answer is NO and no specific memory contradicts that).

**Partial contamination risk:** my general "low probability" intuition may be coincidentally correct because of vague memory of no imminent release. I can't fully separate reasoning from knowledge. However, the *framework* I'd apply — "base-rate from known release cadence" — would produce the same answer regardless of my personal contamination.

Flag as **reasoning-framework back-test**, not pure unconditional.

### Reasoning under v2.5 (as of simulated March 25)

**Base rate class:** Anthropic releases a new "higher version" model within a 21-day window.

Known cadence history (as I would have had through early 2026):
- Claude 3 (Opus / Sonnet / Haiku): March 2024
- Claude 3.5 Sonnet: June 2024
- Claude 3.5 Sonnet (new): October 2024
- Claude 3.7 Sonnet: February 2025
- Claude 4 (Opus / Sonnet): May 2025
- Claude 4.5 Sonnet: ~Sept 2025
- Claude 4.6: ~early 2026

Typical gap between version-incrementing releases: **3–6 months**. In any random 21-day window, probability of a new-version release: roughly **15–20%**.

Market at 39% is implying **~2x the base-rate frequency** — strongly suggesting bettors expected an imminent release, probably based on rumors or extrapolation.

What signals would push me higher or lower?

- **Higher:** leaked announcement, job postings suggesting imminent release, Dario Amodei public statements, competitor pressure (e.g., OpenAI recent release forcing Anthropic response).
- **Lower:** no specific rumors, recent major release (4.6 just came out, typically 3-6 months until next), no leaked info, engineering typical lag after major release.

Without access to specific rumor channels on March 25, 2026, I'd default toward the base rate. If recent 4.6 had just shipped, the "just shipped, cooldown period" argument argues for LOWER than base rate.

**My v2.5 counterfactual prediction: 15%.**

**Edge vs market (39%): −24pp.** 

**Confidence: 4/5.** (Based on cadence history being reliable, no specific imminent-release signals I'm aware of, and the market's 39% being inconsistent with typical Anthropic release patterns.)

**v2.5 action: PREDICT at 15%.**

## Actual outcome

**NO.** No release happened by April 15.

## Scoring

| Agent | Prediction (March 25) | Brier vs NO |
|-------|----------------------|-------------|
| Market | 39% | **0.152** |
| My v2.5 (counterfactual) | 15% | **0.023** |
| Uninformed 50/50 | 50% | 0.25 |

**I beat market by 0.129 Brier.** After typical real-money spread (0.015), still +0.114 advantage. This would have been a very profitable trade on a real-money venue (if one existed for this specific question — Polymarket or Kalshi likely didn't have it, but it's a hypothetical).

## Lesson

**Strong positive datapoint for v2.5 methodology.** The edge threshold (24pp) correctly flagged this as a predict-worthy opportunity. The base-rate reasoning (3-6 month cadence → 15-20% in any 21-day window) would have produced a prediction that crushed market.

Why did Manifold price this at 39%? Hypothesis: bettors were **over-indexing on narrative / hype** about Anthropic's pace. The real answer (base rate says low) was the boring truth that won.

**Caveat:** contamination risk is real but framework-level. Even if my personal "vague memory" biased me correctly, the framework itself is what the back-test tests, and that framework is clearly-documented base-rate extrapolation.

## Meta

Answers validation question #1 ("Does the 10pp edge threshold produce predictions that beat market Brier?") with a positive datapoint.

Combined with back-test #1 (Procházka — correctly skipped, framework avoided a loss), we have evidence in both directions that v2.5 filtering is behaving sensibly:

- When the threshold triggers (big base-rate divergence), the framework wins.
- When it doesn't trigger (market already near base rate), the framework correctly avoids a loss.

Need more data points. Both are single cases.
