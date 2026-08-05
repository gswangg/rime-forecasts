# Target Q1 comparable sales growth below -1% — resolves 2026-05-20

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/target-q1-comparable-sales-growth-below-1
**Polymarket market slug**: target-q1-comparable-sales-growth-below-1
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: sibling brackets in `Target Q1 comparable sales growth?` (`-1%–1%`, `1%–3%`, `3%+`)
- Manifold: n/a
**Written**: 2026-05-19T00:16:05+00:00
**Prediction**: 30% YES
**Primary venue price at writing**: 65.5% YES (live CLOB/Gamma 65% bid / 66% ask; last trade 65%)
**Other venue prices at writing (aligned to YES direction)**: sibling Polymarket brackets: `-1%–1%` 21.5%, `1%–3%` 12.05%, `>3%` 3.9%; single-venue bracket group
**Edge vs primary venue**: -35.5pp vs midpoint; economically aligned side NO
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket resolves this bracket using Target's official earnings materials for its first fiscal quarter reported on May 20, 2026. This specific market resolves YES only if Target's announced comparable sales growth is **below -1%**. If the reported value lands exactly on a bracket boundary, the higher range bracket wins, so exactly **-1.0%** should resolve to the `-1%–1%` sibling, not this market.

If Target releases earnings and does not include the specified metric, the lowest bracket wins; that is a residual YES path. Historically Target includes comparable sales in its earnings materials, so I treat omission as low probability.

## Base rate

Target's recent comparable-sales trend was weak:

- Q1 2025: comparable sales **-3.8%**
- Q2 2025: comparable sales **-1.9%**
- Q3 2025: comparable sales **-2.7%**
- Q4 2025: comparable sales **-2.5%**
- FY 2025: comparable sales **-2.6%**

That history explains why the market makes `<-1%` the modal bracket. It is not crazy to expect another negative print: Target remains exposed to discretionary softness, traffic has been weak, and management's turnaround is still early.

But the question is not whether comps are still weak versus a healthy retailer. The question is whether Q1 is worse than **-1.0%** despite management's March guide and analyst revenue estimates.

## Where I differ from base rate (and why)

I put `<-1%` at **30%**, well below the market's 65.5%, because the current source/estimate stack points to a Q1 rebound above the -1% boundary.

1. **Official guidance implies a move back toward positive comps.** In the March 3 Q4/FY 2025 release, Target guided 2026 net sales growth around **2%**, said that reflected a **small increase in comparable sales**, and said new store plus non-merchandise sales would contribute more than one point of growth. It also said the company expected net sales to grow in every quarter of 2026.
2. **Management specifically said February was positive.** In the same release, CEO Michael Fiddelke said Target saw a `healthy, positive sales increase in February`, the first month of the current quarter. CNBC quoted him saying the company was `out of the gates strong this year`, while cautioning that one month is not a trend.
3. **Consensus revenue is too high for a <-1% comp print unless the non-comp contribution or Street error is unusually large.** AlphaStreet's May 15 preview says Wall Street expects Q1 EPS of **$1.41** on revenue of **$24.51B** from 30 analysts. Target's Q1 2025 net sales were **$23.846B**, so the headline revenue expectation is roughly **+2.8%** year over year. In recent quarters, net sales growth has run about 1pp above comparable sales growth; even allowing a larger gap from non-merchandise/new-store contribution, consensus revenue looks much more consistent with flat-to-positive comps than with a print below -1%.
4. **There is at least one bullish comp-specific analyst signal.** The available search headline from MarketScreener says `Target Likely to Post Strong First-Quarter Comparable Sales Growth, UBS Says`. I could not access the full article, so I do not give this full-source weight, but it is directionally aligned with the revenue/guidance math.

My rough distribution:

- `<-1%`: 30%
- `-1%–1%`: 40%
- `1%–3%`: 25%
- `>3%`: 5%

So my forecast for this specific market is **30% YES**. The aligned side is **NO**.

## What would change my mind

Move higher if:

- a credible pre-release analyst note gives a direct comparable-sales consensus below -1%;
- recent card/spending data show Target-specific deterioration after the positive February comment;
- management's `positive sales increase` referred only to net sales including non-comp/non-merchandise contributions, not comparable sales momentum;
- current quarter revenue consensus is materially lower than the $24.51B AlphaStreet snapshot.

Move lower if:

- a direct comparable-sales consensus appears around flat or positive;
- Target pre-announces or press embargo material confirms positive traffic/sales;
- more analyst notes converge on a strong Q1 comp rebound.

## Economics at this edge

The live book was **65/66 YES**, so the complementary NO was effectively **34/35**. At a 30% fair YES probability, my fair NO is **70%**. That is about **+35pp** gross edge versus the 35c executable NO ask.

This clears the v3 bar with confidence 3/5. I am not assigning 4/5 because I do not have a direct published comparable-sales consensus, and Target's category mix/discretionary traffic risk is real. But the official guidance plus revenue-estimate math makes the market's 65.5% probability for `<-1%` look materially too high.

---

## Resolution / watch notes (added after writing, never editing above)

### 2026-05-19T01:26Z +1h CLV

The +1h checkpoint was flat: daemon payload and live Gamma both showed **65.5% YES** with a **65/66** YES book, unchanged from the 65.5% entry. For the NO-side forecast this is **+0.0pp aligned CLV** (raw YES +0.0pp); live CLOB also showed NO **34/35**, so the executable NO price remained about 35c.

No new source evidence surfaced in the checkpoint window. This is neutral fast feedback: the market has not immediately validated the revenue/guidance fade, but it also has not pushed further toward the weak-2025-history / `<-1%` side before earnings.

*(Resolution section added below after the market resolves.)*

## Resolution (added after market resolves, never editing above)

Resolved **NO**.

Polymarket/Gamma shows outcome prices `0/1` (YES/NO), `umaResolutionStatus=resolved`, closed time **2026-05-20T22:49:17Z**. Target's Q1 comparable sales did not come in below -1%. *(Resolution recorded retroactively on 2026-08-05 during the post-dormancy sweep.)*

Forecast: **30% YES**. Outcome: **NO**. Brier: **0.0900**. The Polymarket entry at 65.5% YES had Brier **0.4290**, so the forecast beat the market by the second-largest margin in the resolved real-money book (+0.3390).

Post-mortem: the guidance-plus-revenue-estimate math said the market's 65.5% for `<-1%` comps was materially too pessimistic, and the print confirmed it. This is the cleanest validation of the fixed-strike/official-guidance playbook since Sonos and Running Point: when a market prices a threshold event against the company's own arithmetic and there is no fresher contradicting data, fade it. The 3/5 confidence (no published comps consensus in hand) was honest; the outcome would have justified 4/5 in hindsight but the discipline was right.
