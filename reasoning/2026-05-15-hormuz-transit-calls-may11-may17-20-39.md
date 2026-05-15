# Hormuz transit calls May 11-May 17, 20-39 — resolves 2026-05-17

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/will-20-39-ships-transit-the-strait-of-hormuz-between-may-11-may-17
**Polymarket market slug**: will-20-39-ships-transit-the-strait-of-hormuz-between-may-11-may-17
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: sibling bins for `<20`, `40-59`, `60-79`, and `80+` in the same event
- Manifold: n/a
**Written**: 2026-05-15T23:35:22+00:00
**Prediction**: 35% YES
**Primary venue price at writing**: 62.0% YES (best bid 60.0%, best ask 64.0%; last trade 62.0%)
**Other venue prices at writing (aligned to YES direction)**: sibling Polymarket bins: `<20` ~10.0% YES, `40-59` ~19.5% YES, `60-79` ~2.05% YES, `80+` ~2.15% YES
**Edge vs primary venue**: -27.0pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

This market resolves YES if IMF PortWatch reports **20-39 total transit calls** for the Strait of Hormuz for all days from May 11, 2026 through May 17, 2026, inclusive.

Resolution source is IMF PortWatch's Strait of Hormuz transit-call data. The market description says transit calls include container, dry bulk, roll-on/roll-off, general cargo, and tanker ships; ships not reported by IMF PortWatch do not count. Revisions inside the market timeframe count until data for the final date is published.

At writing, the ArcGIS/PortWatch `Daily_Chokepoints_Data` API for `portid = 'chokepoint6'` had data only through **2026-05-10**. There was not yet any official PortWatch target-week data for May 11-May 17.

## Base rate

The long-run pre-crisis base rate is useless here. Before the current Hormuz disruption, PortWatch weekly totals were usually hundreds of transit calls. For example, January-February 2026 full Monday-Sunday weeks were commonly in the 480-730 range. That regime would make `80+` nearly automatic.

The relevant base rate is the post-disruption IMF PortWatch regime that began around the week of March 2, 2026. Recent full Monday-Sunday totals for `chokepoint6` were:

| Week starting | Total transit calls |
|---|---:|
| 2026-03-02 | 34 |
| 2026-03-09 | 41 |
| 2026-03-16 | 19 |
| 2026-03-23 | 24 |
| 2026-03-30 | 59 |
| 2026-04-06 | 46 |
| 2026-04-13 | 84 |
| 2026-04-20 | 37 |
| 2026-04-27 | 40 |
| 2026-05-04 | 11 |

Unweighted, those ten post-disruption weeks put the `20-39` bin at 3/10. That understates uncertainty because there are multiple regimes inside the disruption, but it is enough to make 62% look high.

The most recent official week, May 4-May 10, totaled **11** with daily counts `[3, 1, 0, 2, 0, 1, 4]`. That is a material lower-regime signal immediately before the target week.

## Where I differ from base rate (and why)

Polymarket's current modal bin is `20-39` at about **62%**, with `<20` around **10%** and `40-59` around **19.5%**. I think that over-concentrates probability in the middle bin.

My distribution is roughly:

- `<20`: 40%
- `20-39`: 35%
- `40-59`: 20%
- `60+`: 5%

The important disagreement is not that `20-39` is impossible. It is a plausible bin if the strait runs at roughly 3-5 reported transit calls per day. But the latest exact PortWatch print was only 11 for the previous full week, and the target week followed new escalation rather than a clear reopening. AP reported on May 14 that a ship anchored off the UAE was seized and another cargo ship near Oman sank after being attacked, with tensions escalating near the Strait of Hormuz. The PortWatch page itself warns that GPS jamming, AIS spoofing, and vessels going dark are present in the region; for this market, vessels not reported by PortWatch do not count.

That combination makes the lower tail materially larger than the market's 10% `<20` price. It also leaves a rebound/convoy path into `40-59`, so I do not want to simply buy `20-39` as the modal outcome at 62%. My forecast for this specific market is **35% YES**, aligned side **NO**.

## What would change my mind

Move higher if:

- IMF PortWatch publishes any May 11-May 17 target-week days showing a run-rate already near or above 4-5 transit calls per day.
- Credible live AIS/official reporting shows controlled convoys or a resumption of commercial traffic that should be captured by PortWatch rather than going dark.
- The May 4-May 10 data is revised materially upward before the target-week data is published, suggesting the 11 total was a reporting lag rather than a real collapse.

Move lower if:

- Target-week PortWatch days start printing 0-2 calls/day.
- New maritime-security reports indicate more seizures/attacks or wider AIS-dark behavior in and around Hormuz.
- The target-week data remains unpublished for the final date and the available partial week is below 20.

## Economics at this edge

At a 62% YES midpoint, the economically aligned side is NO. The executable NO ask is approximately 40c via the 60c YES bid, while my fair NO probability is about 65%.

The gross edge is about 25pp on the NO side after crossing the spread. Liquidity is modest (~$2.2k) and the YES book is wider than the best Eurovision/Powell books, but 60/64 is still tight enough for a paper-trade validation entry.

Confidence is 3/5: the edge is source-specific and quantified from exact PortWatch data, but the target week has no official prints yet and live AIS/dark-shipping dynamics can change quickly.

---

*(Resolution section added below after the market resolves, never editing above.)*
