# Donald Trump 100-119 Truth Social posts Apr 21-28 — resolves 2026-04-28

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/donald-trump-of-truth-social-posts-april-21-april-28-100-119
**Polymarket market slug**: donald-trump-of-truth-social-posts-april-21-april-28-100-119
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-27T12:28:11+00:00
**Prediction**: 40%
**Primary venue price at writing**: 5.15% YES (best bid 4.4%, best ask 5.9%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +34.85pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether Donald Trump posts **100-119** times on Truth Social from April 21, 2026 12:00 PM ET to April 28, 2026 12:00 PM ET.

Resolution source is the Polymarket XTracker `Post Counter` at https://xtracker.polymarket.com. The market rules count posts captured by the tracker over that exact window.

At writing, XTracker showed **105 counted posts** for the April 21-28 window. Last sync was 2026-04-27T12:26:15Z. The most recent counted post was 2026-04-27T03:00:20Z, so there had been a **9.4 hour posting gap**. There were about **27.6 hours** remaining.

This bin resolves YES if the tracker records **0-14 additional posts** before noon ET on Apr 28.

Sibling Polymarket prices checked at writing:

- 100-119: 5.15%
- 120-139: 67.4%
- 140-159: 22.0%
- 160-179: 4.9%
- 180-199: 0.6%
- 200+: 0.35%

The lower bins are already dead because the tracker is at 105.

## Base rate

The XTracker state is much less lopsided than the market price. Current recent-rate facts:

- total so far: 105
- posts in prior 24h: 6
- posts in prior 12h: 3
- posts in prior 6h: 0
- current gap: 9.4h
- posts needed to leave this bin: 15+

Historical Truth Social tracker data since 2026-01-21 gives mixed but clearly non-negligible mass on staying under 120.

For pseudo-current windows with the same remaining time (~27.6h), the probability of **≤14 future posts** was:

- all same-clock daily anchors: 34.8%
- same-clock daily anchors with partial count 90-120: 46.4%
- same-clock daily anchors with partial count 95-115: 42.1%
- hourly anchors with an 8h+ gap and previous 24h ≤ 20: 47.7%
- hourly anchors with 8h+ gap, previous 24h ≤ 10, and partial count 90-120: 67.1%
- hourly anchors with partial count 100-110: 35.3%

The exact partial-count cuts are small and noisy. But none justify a 5% YES price. The broad takeaway is that **staying below 120 is plausible**, not a tail.

## Where I differ from base rate (and why)

I am at **40% YES**, far above Polymarket's 5.15%.

The market appears to be anchoring on the tracker pace / modal bucket. The XTracker `includeStats` endpoint showed `pace: 123`, and Polymarket prices make `120-139` the 67% favorite. But a pace of 123 does not mean only a 5% chance of finishing 100-119. With 105 already counted, the difference between 119 and 123 is only four posts.

The recent posting rate points the other way:

- Only 6 posts in the prior 24 hours.
- Only 10 posts on Apr 25 ET and 6 posts on Apr 26 ET.
- No counted posts after 03:00Z / 11:00 PM ET before the Apr 27 morning sync.

A normal weekday burst can still move this into 120-139 quickly. But the YES price is treating the quiet stretch as almost irrelevant. I think that is wrong; the 100-119 bin should be priced as a live low/mid-probability outcome.

I am not going higher than 40% because the distribution is bursty and political posting can restart in clusters. A single morning grievance thread or repost chain can add 15 posts fast. The recent market move also suggests traders may be watching the same counter and actively concentrating probability into 120-139.

## What would change my mind

Signals that would move me down:

- XTracker reaches 112-115 by afternoon ET on Apr 27.
- A fresh Truth Social burst shows Trump is actively posting through the US workday.
- 120-139 stays heavily bid while 100-119 remains offered despite no count growth, suggesting informed flow.

Signals that would move me up:

- XTracker remains near 105 through late afternoon ET.
- No new posts appear by evening ET on Apr 27.
- The 120-139 market fails to keep its bid as the quiet stretch extends.

## Economics at this edge

At 40% true probability versus 5.15% market YES, the pre-friction edge is **+34.85pp**. The spread was wide in relative terms (4.4% bid / 5.9% ask), but even buying at the ask leaves a very large edge if this estimate is directionally right.

The risk is not market microstructure; it is burst risk. The market can lose in a few active posting hours.

---

*(Resolution section added below after the market resolves. The above is frozen.)*
