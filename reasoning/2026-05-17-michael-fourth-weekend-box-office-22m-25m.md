# Michael 4th weekend box office between $22m and $25m — resolves 2026-05-18

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/will-michael-4th-weekend-box-office-be-between-22m-and-25m
**Polymarket market slug**: will-michael-4th-weekend-box-office-be-between-22m-and-25m
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: sibling bracket markets in the same event (`<19m`, `19m-22m`, `>25m`)
- Manifold: n/a
**Written**: 2026-05-17T00:37:48+00:00
**Prediction**: 38% YES
**Primary venue price at writing**: 55.5% YES (best bid 54.0%, best ask 57.0%; last trade 54.0%)
**Other venue prices at writing (aligned to YES direction)**: sibling Polymarket brackets: `<19m` ~0.4%, `19m-22m` ~0.45%, `>25m` ~44.5%; single-venue bracket group
**Edge vs primary venue**: -17.5pp vs midpoint; economically aligned side NO
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

This market resolves YES if *Michael*'s fourth domestic weekend box office is between **$22m and $25m** for the three-day weekend **May 15-May 17, 2026**, using the Daily Box Office Performance figures on The Numbers movie page once final rather than studio-estimate values are available.

The bracket rule says that if the reported value falls exactly between two brackets, it resolves to the higher range bracket. In practice, the important boundary here is **$25m**: above $25m resolves to the sibling `>25m` market, not this one.

## Base rate

The Numbers currently lists *Michael*'s Friday May 15 gross as an estimate of **$7.0m** from 3,560 theaters. The prior weekends on The Numbers were:

| Weekend | Fri | Sat | Sun | 3-day | Fri-to-weekend multiple |
|---|---:|---:|---:|---:|---:|
| Apr 24 opening | $39.29m | $32.46m | $25.45m | $97.21m | 2.47x |
| May 1 second weekend | $14.25m | $22.95m | $17.21m | $54.40m | 3.82x |
| May 8 third weekend | $8.80m | $14.44m | $14.67m | $37.90m | 4.31x |
| May 15 fourth weekend so far | $7.00m | ? | ? | ? | ? |

The third-weekend Sunday was inflated by Mother's Day, so a repeat 4.31x multiplier is probably too high. But even the second-weekend non-holiday pattern gives about **$26.7m** on a $7.0m Friday. A straight Friday week-over-week hold (-20%) applied to the prior $37.9m weekend also points above $25m, though that method likely overstates because last Sunday was holiday-aided.

BoxOfficeReport's May 14 weekend forecast was **$28.0m**, citing the return of some IMAX / premium screens, strong word of mouth, repeat business, and high buzz. That was published before Friday but is directionally consistent with the multiplier math.

## Where I differ from base rate (and why)

Polymarket's bracket group is effectively split between this `22m-25m` bin at about **55.5%** and the `>25m` sibling at about **44.5%**, with the lower bins near zero. I think the market is underweighting the chance that the Friday estimate converts to **above $25m**.

The threshold math is tight:

- To land in this market's bracket, $7.0m Friday needs a weekend multiple from **3.14x to 3.57x**.
- To resolve `>25m`, it needs a multiple above **3.57x**.

For a film with *Michael*'s recent weekend shape, that 3.57x cutoff is not especially high. The second weekend already did 3.82x without Mother's Day, and this weekend got a small theater count increase plus some premium-screen support. The Friday decline of about 20% versus last Friday also does not look weak enough to force a low-3x multiplier.

My distribution:

- `<22m`: 3%
- `$22m-$25m`: 38%
- `>25m`: 59%

So my forecast for this specific market is **38% YES**. The aligned side is **NO**, mostly because the sibling `>25m` outcome looks more likely than the current bracket.

## What would change my mind

Move higher if:

- Saturday estimates come in weak, especially below about $10.0m.
- Sunday-drop indicators point to an unusually sharp fall from Saturday.
- The Friday estimate is revised down materially or the eventual final The Numbers Friday is below $7.0m.

Move lower if:

- Saturday estimates are around $11m+.
- Weekend estimates from Deadline, Hollywood Reporter, BoxOfficeReport, The Numbers, or Box Office Mojo cluster at $26m+.
- Premium-screen / IMAX recapture is confirmed to be materially helping the fourth weekend.

## Economics at this edge

At a 55.5% YES midpoint and 57c executable YES ask, I do not want YES. My fair YES is 38%.

The executable NO ask is about **45c**, while my fair NO probability is about **62%**, giving roughly **+17pp** gross edge after crossing the spread. Liquidity is modest but acceptable for the paper experiment, and the bracket group is internally consistent enough that this is not just a stale single-market print.

Confidence is 3/5. The edge is a concrete source/projection thesis from The Numbers Friday data and recent weekend multipliers, but box-office brackets this narrow are sensitive to Saturday/Sunday estimates, studio-estimate revisions, and final-vs-estimate changes.

---

## Post-writing watch notes

### 2026-05-17T01:06Z favorable price move

A price-move wake fired less than an hour after writing: the daemon payload marked this bracket down from 56.0% to **48.0% YES**, while a live CLOB check was even lower at roughly **40/43 YES** (mid **41.5%**) and the sibling `>$25m` market was roughly **56/61 YES** (mid **58.5%**). Against the 55.5% entry mark, that is about **+7.5pp aligned CLV** using Gamma's payload mark, or about **+14.0pp** using the live executable/mid book.

No resolution-state change: Gamma still shows the market active/open. The Numbers is still Friday-only for the target weekend, with May 15 at **$7.0m**. While reviewing the move, I found Deadline's early Saturday update from May 16 projecting **$27m** for Michael's fourth weekend after a roughly **$7m** Friday, with IMAX/PLF screens helping. That is not a final source print, but it reinforces the original mechanism that `>$25m` is more likely than the `$22m-$25m` bracket.

CLV bookkeeping: this early price-move review is the closest available +1h backfill. The daemon then hit repeated DNS failures until 2026-05-18T02:14Z, so the exact +6h mark was not captured. Formal `1h`/`6h` checkpoint wakes later arrived after the market had already collapsed to ~1%, so I am not treating that next-day source-state mark as the actual one-hour or six-hour market reaction.

### 2026-05-18T03:28Z price collapse / source-state check

A second price-move wake marked this bracket down to **1.05% YES** from the prior 48% payload mark; live Gamma/CLOB during review was even lower at about **0.75% YES** (0.4/1.1 book). Against the 55.5% entry, that is roughly **+54.5pp to +54.8pp aligned CLV** for the NO-side forecast. The sibling `>$25m` market was roughly **99.1% YES**.

This move is now source-supported, not just flow. The Numbers movie page and weekend chart show *Michael*'s May 15-17 weekend at **$26,125,000**, above the $25m boundary. The daily table shows **$7,035,000** Friday, **$10,910,000** Saturday, and **$8,180,000** Sunday, summing to the same weekend total. If those values survive final revision, this `22m-25m` bracket resolves NO and the sibling `>$25m` resolves YES.

Gamma still shows this market active/open with no UMA resolution status, so this is not final scorecard resolution yet. Residual risk is a final The Numbers/studio revision cutting more than about **$1.125m** from the current weekend total, enough to move it below or exactly to the $25m boundary; otherwise the original `>$25m` mechanism has landed.

## Resolution (added after market resolves, never editing above)

Resolved **NO**.

Polymarket/Gamma finalized the market with outcome prices `0/1` (YES/NO), `umaResolutionStatus=resolved`, and closed time **2026-05-18T22:03:00Z**. The Numbers' Weekend Box Office Performance table now lists *Michael*'s May 15, 2026 weekend gross as **$26,140,937**, above the $25m upper boundary for this bracket. The Daily Box Office Performance rows sum to the same total: **$7,004,003** Friday, **$10,869,262** Saturday, and **$8,267,672** Sunday.

Forecast: **38% YES** / aligned side **NO**. Outcome: **NO**. Brier: **0.1444**. The primary market entry at 55.5% YES had Brier **0.3080**, so the NO-side forecast beat the market.

Post-mortem: this was a clean bracket-boundary/multiplier win. The Friday print was not weak enough for the modal `$22m-$25m` bin; even non-holiday second-weekend shape made the `>$25m` sibling more likely. The final $26.14m was only about $1.14m above the boundary, so confidence 3/5 was appropriate, but the market's 55.5% on the middle bracket gave too little weight to the recent weekend multiplier and premium-screen support.
