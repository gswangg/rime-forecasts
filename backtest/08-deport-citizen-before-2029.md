# Back-test #8: Will the US deport an American citizen before 2029?

## Market

- **URL**: https://manifold.markets/slug/will-the-us-deport-an-american-citi
- **Question**: Will the US deport an American citizen before 2029?
- **Market creation**: 2025-03-17
- **Resolution**: 2026-04-11, **YES**
- **Volume at close**: $31k, 127 bettors

## Simulated prediction

- **Simulated prediction date**: 2025-06-01 (~10 months after creation, well before resolution)
- **Market price on simulated date**: **88.0%**

### Contamination check

I may have training-data awareness of individual Trump-era deportation cases. However, the question is broad ("any citizen deported before 2029") and base-rate reasoning doesn't require knowing specific cases.

### Reasoning under v2.5.1 (as of simulated June 1, 2025)

**Base rate class: probability of any verifiable wrongful deportation in a ~4 year window under Trump-II administration.**

Relevant priors:
- Trump administration had publicly committed to aggressive deportation expansion.
- ICE operations were scaling up through 2025.
- Wrongful deportations of US citizens historically happen at a low but non-zero rate — even in less aggressive administrations, occasional cases emerge (~1-3 per year on average).
- Under aggressive expansion, the probability rises.
- 4-year window is long — even a low per-year hazard compounds.

P(at least one verifiable case in 4 years) ≈ 1 − (1 − annual_rate)^4

If annual rate = 50% (high given aggressive expansion): 94% in 4 years.
If annual rate = 30% (moderate): 76% in 4 years.
If annual rate = 70%: 99%.

Base-rate estimate: **85–95%**, converging around 90%.

Market at 88% is right in this range. **Delta vs market: essentially zero.** My honest v2.5.1 prediction matches market within ~2pp.

**Confidence: 3/5.** Base rate is defensible but actual deportation-case rate under specific policy conditions is uncertain. No novel information claim.

**v2.5.1 action: SKIP.** (Delta below 10pp threshold.)

## Actual outcome

**YES.** A verifiable case occurred and the market resolved.

## Scoring

No prediction was made → no Brier contribution. This is a **correctly-skipped "market was right"** case — methodology saves me from a zero-edge bet where the market was doing good base-rate reasoning.

## Lesson

**Important counter-pattern:** not every market default-prices near 50%. Many markets correctly price base rates when the question has clear priors and bettors think about them. My earlier back-tests (#2, #3, #5) involved markets where the base rate was seasonal or barrier-crossing — specific quantitative frames that bettors often skip. Broad "will X happen in 4 years" questions where the base rate is intuitive get priced reasonably.

This case strengthens the v2.5.1 claim by showing the methodology correctly **doesn't fight markets when markets are already right.** Selection matters.

## Meta

Back-test tally (N=8):

| # | Market | v2.5.1 Action | Outcome | Brier Δ |
|---|--------|---------------|---------|---------|
| 1 | Procházka UFC | Skip (correct) | N/A | avoided loss |
| 2 | Anthropic v4.7 | Predict 15% | NO | +0.129 |
| 3 | WTI $100 Apr 10 | Predict 50% | NO | +0.39 |
| 4 | Intel $63 2026 | Skip (correct) | YES | avoided −0.105 |
| 5 | Mana March vs Dec | Predict 30% | NO | +0.184 |
| 6 | Museum robbery | Predict 50% | YES | +0.454 |
| 7 | Fingleton nuclear | Predict 15% | NO | +0.307 |
| 8 | Deport citizen 2029 | Skip (correct) | YES | zero (no bet) |

**5-for-5 on predictions, 3-for-3 on skips.** Methodology consistent.

Pattern map:

- **Take edge:** near-50% + base-rate signal (#2, #3, #5), pattern-continuation underpricing (#6), "all N of X" underpricing (#7)
- **Correctly skip:** low confidence + high variance (#1), marginal edge + low confidence (#4), market correctly pricing intuitive base rate (#8)

v2.5.1 is behaving as designed across both sides of the decision. Worth continuing the back-test program to reach N=15+ for stronger statistical claim.
