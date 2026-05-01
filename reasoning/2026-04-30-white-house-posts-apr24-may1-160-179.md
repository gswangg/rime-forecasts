# White House 160-179 posts Apr 24-May 1 — resolves 2026-05-01

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/white-house-of-tweets-april-24-may-1-2026-160-179
**Polymarket market slug**: white-house-of-tweets-april-24-may-1-2026-160-179
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-30T15:36:35+00:00
**Prediction**: 40% YES
**Primary venue price at writing**: 10.5% YES (best bid 9.0%, best ask 12.0%; last trade 12.0%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +29.5pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether the White House X account (`@WhiteHouse`) posts **160-179** times from April 24, 2026 12:00 PM ET to May 1, 2026 12:00 PM ET.

Resolution source is the Polymarket XTracker `Post Counter` at https://xtracker.polymarket.com. The rules count main-feed posts, quote posts, and reposts captured by the tracker over the exact window.

At writing, XTracker / Gamma showed **153 counted posts** for the window. XTracker last sync was 2026-04-30T15:35:52Z. The latest counted post was 2026-04-30T00:31:10Z, so there had been a **15.1 hour posting gap**. There were about **24.4 hours** remaining.

This bin resolves YES if the tracker records **7-26 additional posts** before noon ET on May 1. It loses low if there are 0-6 more posts and loses high if there are 27+ more posts.

Sibling Polymarket prices checked at writing:

- 140-159: 0.3% YES
- 160-179: 10.5% YES
- 180-199: 75.5% YES
- 200+: 9.4% YES

The lower bins through 120-139 are already dead because the tracker is at 153.

## Base rate

Current recent-rate facts:

- total so far: 153
- posts in prior 48h: 65
- posts in prior 24h: 34
- posts in prior 12h: 0
- posts in prior 6h: 0
- current gap: 15.1h
- posts needed for this bin: 7-26

The hard part is balancing two real facts. The White House account can post in dense media-event bursts; the April 29 evening run included a large block of near-simultaneous photo/video posts. But as of writing it has not posted since 8:31 PM ET on April 29, and the remaining window is only Thursday afternoon/evening plus Friday morning.

Using XTracker history since January 2026, I compared pseudo-current windows with the same elapsed and remaining time. The empirical probability of **7-26 posts in the next ~24.4h** was:

- all hourly pseudo-current windows with partial count 140-170: **46.8%**
- partial count 148-158: **59.9%**
- partial count 140-170 and prior 24h 25-45 posts: **46.1%**
- partial count 148-158 and prior 24h 25-45 posts: **56.0%**
- partial count 148-158 and a 12h+ gap: **58.3%** (small N=12)
- same-clock daily anchors with partial count 140-170: **36.4%** (small N=22)
- same-clock daily anchors with partial count 148-158: **33.3%** (very small N=6)

The precise cuts are noisy, and the hourly samples overlap heavily. The central takeaway is still clear enough: from a current count around 153, the 160-179 interval is not a 10% tail. The main competition is overrun to 180-199, not failure to reach 160.

## Where I differ from base rate (and why)

I am at **40% YES**, above Polymarket's 10.5%.

The market is concentrating probability in the next higher bin: 180-199 was priced around 75.5%, with another 9.4% on 200+. That implies roughly an 85% chance of 27+ more White House posts over the next day. I think that is too aggressive given the 15-hour current silence and the lack of Thursday-morning posts.

This is not a claim that the account will stay quiet. It only needs seven posts to enter 160-179, and a normal White House afternoon can easily clear that. But 180+ requires a substantial new burst. The previous April 21-28 White House forecast taught the exact risk: once the account gets close to the upper edge, one posting block can overrun a bin quickly. Here, though, that lesson is already the market consensus. The price appears to over-apply it by treating 180-199 as nearly inevitable.

I discount the raw analog rates down to 40% because:

- the April 29 posting burst shows current-event demand for lots of White House media posts,
- the prior Apr21-Apr28 White House forecast was hurt by underestimating burst/overrun risk,
- same-clock daily samples are smaller and less supportive than the broad hourly analogs,
- the market is highly liquid for this cluster and may include active counter-watchers.

Even after those discounts, 10.5% is too low for the live 7-26 post interval.

## What would change my mind

Signals that would move me down:

- XTracker reaches 165+ before late afternoon ET on April 30.
- Another photo/video/repost thread starts, especially if it adds 10+ posts in under an hour.
- 180-199 stays tightly bid above 80% after no tracker growth, suggesting informed flow beyond the visible count.

Signals that would move me up:

- no new White House posts by Thursday evening ET
- a small restart that takes the count only into the low 160s, followed by another quiet stretch
- 180-199 loses bid while 160-179 stays near 10-15%

## Economics at this edge

At 40% true probability versus a 10.5% Polymarket midpoint, the pre-friction edge is **+29.5pp**. The executable ask was about 12.0%, still leaving roughly **+28pp** of gross edge if this estimate is right.

The book is reasonably actionable for a short-horizon range bin (9.0% bid / 12.0% ask, ~$3.9k single-market liquidity, large event volume). The risk is not spread; it is burstiness and the possibility that market participants are correctly anticipating another high-output White House posting block.

---

## Resolution (added after market resolves, never editing above)

Resolved **NO**.

At 2026-05-01T15:44Z, Gamma showed the 160-179 market closed/resolved with outcome prices `0/1`. The XTracker export showed **193** White House posts in the April 24 12:00 PM ET to May 1 12:00 PM ET window, with the latest in-window post at 2026-05-01T15:38:25Z. That exceeds the 179 upper bound, so this bin overran.

Forecast: **40% YES**. Outcome: **NO**. Brier: **0.160**. The primary market entry at 10.5% YES had Brier **0.011**, so this was materially worse than the market.

The key miss was source-state quality. At writing, the visible Gamma/XTracker state showed 153 counted posts and a long silence. The later export had **162** posts timestamped at or before the writing time, implying the visible count lagged/backfilled by roughly 9 posts. That made the true remaining cushion smaller than the thesis assumed. Posting then resumed and pushed the final count to 193. For White House range bins, tracker-count latency/backfill plus burst continuation deserve heavier weight than a visible silence gap.
