# Back-test #1: Jiří Procházka vs Carlos Ulberg (UFC 327)

## Market

- **URL**: https://manifold.markets/Liam42/will-jiri-prochazka-defeat-carlos-u
- **Question**: Will Jiří Procházka defeat Carlos Ulberg @ UFC 327?
- **Market creation**: 2026-04-05
- **Market creation price**: ~52% (Procházka favored)
- **Fight date**: 2026-04-11 (implied)
- **Actual resolution**: 2026-04-12, **NO** (Procházka lost)
- **Volume at close**: $97k, 17 bettors

## Simulated prediction

- **Simulated prediction date**: 2026-04-05 (same as market creation, pre-fight)
- **Information I would have had**: pre-fight fighter records, recent form, profile matchup
- **Information I would NOT have had**: fight outcome, training-camp news not covered by generic records

### Contamination check

UFC 327 and the specific Procházka-Ulberg result were not part of my training data (fight took place April 2026, after my training cutoff). I know general fighter profiles (Procházka as former LHW champ, Ulberg as rising NZ striker), not this specific fight's outcome. **Clean back-test.**

### Reasoning under v2.5

Reference class: former champion coming off losses vs younger ascending striker. Both heavy strikers.

- Procházka: former UFC LHW champion 2022, lost title 2023, lost rematch 2024, won in 2025. Known for wild pace and KO power. Elite chin historically but showed some decline.
- Ulberg: NZ striker, built solid record 2024-2025 with several KO wins. Younger, rising, good momentum.
- Profile matchup: striker vs striker, both with KO threat.
- Experience edge: Procházka.
- Youth / momentum edge: Ulberg.

Without specific odds or inside info, I'd estimate Procházka ~50-55% (slight favorite on experience and pedigree, but Ulberg's momentum is real).

**My v2.5 prediction: 54% Procházka wins.**

**Edge vs market (52%): +2pp.** Below v2.5's 10pp threshold.

**v2.5 action: SKIP.** No prediction would have been made under current methodology.

## Actual outcome

Procházka lost (market resolved NO).

## Scoring

| Agent | Pre-fight prediction | Brier vs NO outcome |
|-------|---------------------|---------------------|
| Market creation | 52% P wins (48% NO) | 0.27 |
| My v2.5 (counterfactual) | 54% P wins (46% NO) | 0.29 |
| Uninformed 50/50 | 50% | 0.25 |

If I had predicted, I would have been *worse* than both market and naive 50/50. The v2.5 edge threshold correctly stopped me from making this prediction — a small win for the methodology.

## Lesson

**V2.5's 10pp edge threshold did its job** in an obvious case. Single fights are high-variance, bettor-level information asymmetric (cornermen know things media doesn't), and without strong reason to differ from market I shouldn't be making tiny-edge predictions.

This data point alone says nothing about whether v2.5 *wins* — it only shows the methodology correctly filtered out a low-confidence prediction. To claim methodology validation I'd need cases where v2.5 DID take predictions and beat market. Those are harder to construct with contamination-free back-testing.

## Meta

This is a single data point toward answering **"Does the 10pp edge threshold produce predictions that actually beat market Brier on average?"** (validation question #1 in `backtest/README.md`). More data points needed.
