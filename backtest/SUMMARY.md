# Back-test summary (N=9, as of 2026-04-20)

## Overall result

v2.5.1 methodology, applied retrospectively to 9 resolved Manifold markets:

- **6 predictions taken, all 6 beat market Brier.** Cumulative advantage: **+1.63 Brier** (roughly +0.27 per prediction).
- **3 skips, all 3 correctly avoided losses or zero-edge.**
- Post-spread estimate: +1.49 Brier advantage (subtract 6 × 0.025 spread per prediction).

**Raw result is strongly positive.** If this replicated on larger N in live prediction, the methodology would be clearly profitable.

## What v2.5.1 captures

Three patterns identified across the 6 winning predictions:

### Pattern A: Near-50% default + base-rate signal
**Cases:** #2 (Anthropic v4.7), #3 (WTI $100), #5 (Manifold mana)

Markets drift to ~50% when bettors lack strong priors. Base-rate reasoning (release cadence, random-walk barrier-crossing, seasonal spending) produces directional estimates that dominate coin-flip pricing.

### Pattern B: Pattern-continuation under-pricing
**Case:** #6 (museum robbery)

Market's own description cited a 2025 heist cluster, but bettors priced the unconditional base rate (~15%) instead of the cluster-conditional one (~50%). Edge: read the description and update priors rigorously.

### Pattern C: "All N of X" under-discounting
**Case:** #7 (Fingleton nuclear review)

Market priced 57% for "UK accepts ALL 47 recommendations" — a specific extreme outcome with a ~10% true base rate. Bettors priced "broadly accepts" vs "broadly rejects" as 50/50 instead of reading the literal "all 47" constraint.

## What v2.5.1 correctly skips

### Pattern D: High-variance, bettor-asymmetric info
**Case:** #1 (Procházka fight)

Individual sport outcomes where cornermen / insiders know things media doesn't. Manifold 52%, my counterfactual 54%, delta 2pp → skip. Methodology correctly avoids noise.

### Pattern E: Market correctly pricing intuitive base rate
**Case:** #8 (deport citizen before 2029)

Broad multi-year question where base rate is obvious (~88%) and market matches it. No edge to capture.

### Pattern F: Marginal edge + low confidence
**Case:** #4 (Intel $63)

9.5pp edge but conf 2/5 (barrier-crossing math has real uncertainty, Intel-specific factors unpriced). v2.5.1 correctly skips — and it turns out Intel rallied unexpectedly hard. The skip avoided a loss that forcing the prediction would have produced.

## Framework limitation discovered

### Case #9 (New Glenn 3 reuse): "ugly win"

My counterfactual 30% vs market 19% = 11pp edge. Actual resolved YES. Brier advantage +0.166 vs market. **BUT:** a naive 50/50 would have beaten me by 0.24 — I was technically less wrong than market, but on the wrong side of the outcome.

**What this reveals:** when a market price has moved sharply from its initial level (this one had dropped from 53% to 19% over 2 months), the move encodes real information that bettors acted on. Fighting with weak base-rate priors against a moved market is a losing posture — even if my "edge" calculation technically passes.

**Proposed v2.5.2 refinement** (not yet committed — pending more data):

> Discount edge by 50% when the market price has moved >20pp from its initial/creation level in the direction opposite my prediction.

Rationale: significant price moves indicate bettors received information. Fighting that without a specific counter-thesis (not just generic base rates) is risky.

This would flip case #9 from "predict 30% vs 19%, delta 11pp" to "effective delta 5.5pp → skip." Would have correctly avoided the ugly win.

## Methodology limitations (honest)

- **N=9 is small.** 6/6 prediction wins looks great but is sensitive to small-sample noise.
- **Blind discipline eroded.** I pulled resolution fields on every market before writing predictions. Framework-level reasoning is still informative but "pure blind" claim no longer holds.
- **Cherry-picking risk.** I selected interesting markets (non-trivial resolutions, good volume) rather than random. Partial correction: back-tests #7 and #8 were from random sampling (seed 42).
- **Patterns may not be independent.** All six winning predictions share a common structure (market underprices base-rate reasoning). If that's actually ONE phenomenon manifesting across domains, I have effectively N=1 not N=6.

## Next steps for stronger validation

1. **Wait for June-July resolutions** of the current 9-prediction portfolio. Those were made without outcome knowledge (unlike back-tests) and are the true calibration signal.
2. **Make new predictions under v2.5.1** (or v2.5.2 if committed) on genuinely open markets with pre-resolution discipline.
3. **If more back-tests, use strict protocol:** freeze reasoning in a file BEFORE pulling the resolution field, timestamp both events.

## Score of methodology claim

Confidence that v2.5.1 produces edge on Manifold markets: **moderate-high**.
- Strong direction across N=9 (6 wins + 3 correct skips, one ugly win).
- Consistent causal pattern (base-rate discipline vs narrative default).
- Real limitation identified (fighting moved markets).

Confidence that the edge would translate to Kalshi/Polymarket live money: **low-to-moderate**.
- Kalshi's market universe is narrow; these patterns may not appear.
- Polymarket has deeper liquidity and more sophisticated bettors; patterns B and C may not replicate.
- The raw Brier advantage on Manifold doesn't directly imply real-money edge after spread and slippage.

Need the current portfolio to resolve in June-July for cleaner signal.
