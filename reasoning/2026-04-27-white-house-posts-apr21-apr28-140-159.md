# White House 140-159 posts Apr 21-28 — resolves 2026-04-28

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/white-house-of-tweets-april-21-april-28-2026-140-159
**Polymarket market slug**: white-house-of-tweets-april-21-april-28-2026-140-159
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-27T12:32:24+00:00
**Prediction**: 65%
**Primary venue price at writing**: 52.0% YES (best bid 51.0%, best ask 53.0%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +13.0pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether the White House X account (`@WhiteHouse`) posts **140-159** times from April 21, 2026 12:00 PM ET to April 28, 2026 12:00 PM ET.

Resolution source is the Polymarket XTracker `Post Counter` at https://xtracker.polymarket.com. The rules count main-feed posts, quote posts, and reposts captured by the tracker over the exact window.

At writing, XTracker showed **124 counted posts** for the window. Last sync was 2026-04-27T12:30:46Z. The most recent counted post was 2026-04-27T01:38:02Z, so there had been a **10.9 hour posting gap**. There were about **27.5 hours** remaining.

This bin resolves YES if the tracker records **16-35 additional posts** before noon ET on Apr 28.

Sibling Polymarket prices checked at writing:

- 120-139: 1.05%
- 140-159: 52.0%
- 160-179: 39.5%
- 180-199: 3.25%
- 200+: 0.35%

The lower bins through 100-119 are already dead because the tracker is at 124.

## Base rate

Current recent-rate facts:

- total so far: 124
- posts in prior 24h: 11
- posts in prior 12h: 1
- posts in prior 6h: 0
- current gap: 10.9h
- posts needed for this bin: 16-35

The White House account is weekday/working-hours clustered. The current quiet stretch is not automatically bearish for the 140-159 bin, because the remaining window includes Monday daytime and Tuesday morning ET.

XTracker history since 2026-01-15 gives these empirical frequencies for **16-35 posts over the next ~27.5h**:

- same-clock daily anchors with partial count 100-150: 57.1%
- same-clock daily anchors with partial count 110-140: 55.6%
- same-clock daily anchors with partial count 120-130: 57.1% (small N=7)
- hourly anchors with partial count 110-140: 59.4%
- hourly anchors with partial count 120-130: 67.9%
- hourly anchors with 8h+ gap and partial count 120-130: 81.5% (small N=27)
- hourly anchors with prior 24h ≤ 20 and partial count 110-140: 64.8%

The exact conditioning is noisy, but the central message is stable: from a current count around 124, the next 27.5h usually lands in the 16-35 post interval more often than not.

## Where I differ from base rate (and why)

I am at **65% YES**, above Polymarket's 52%.

The market has already moved strongly toward this bin; the one-day price change was about +36.5pp. That move is not adverse to my view, and it reflects the tracker count making lower bins impossible. The question is whether the market is still over-allocating to 160-179 at 39.5%.

I think it is. To reach 160, the account needs **36+ posts** in the remaining window. That can happen, but it requires a fairly active Monday plus Tuesday morning. The current setup has only 11 posts in the prior 24h and no posts in the prior 10.9h. A normal White House workday restart probably adds enough to clear 140, but not necessarily enough to clear 160.

This is why 140-159 is the natural modal bin: the current count is already high enough that 120-139 is almost gone, but the recent slowdown makes 160+ less likely than the market's 40% allocation implies.

I am not higher than 65% because the account is institutional and can post in dense media-event bursts. A single press/travel/news cycle can add 20+ posts quickly, and the market's sharp move may contain information from people watching the same tracker.

## What would change my mind

Signals that would move me down:

- XTracker reaches 135-140 by afternoon ET on Apr 27.
- A press event or rapid-response thread produces a burst of retweets/reposts.
- The 160-179 sibling stays bid or rises without new tracker growth, suggesting better-informed flow.

Signals that would move me up:

- XTracker remains near 124 through late afternoon ET on Apr 27.
- No new posts appear by evening ET.
- The 160-179 sibling loses bid while 140-159 remains around coin-flip.

## Economics at this edge

At 65% true probability versus 52% market YES, the pre-friction edge is **+13.0pp**. The spread was about 2pp, so the edge is not huge after friction, but it clears the v3 threshold with confidence 3/5.

The main risk is burstiness. The market can move from a good 140-159 setup to a 160-179 setup in one active posting block.

---

*(Resolution section added below after the market resolves. The above is frozen.)*

## Post-writing watch notes

- 2026-04-27T15:52Z: Polymarket moved to **71.0% YES** (68% bid / 74% ask; last trade 74%), up 5.5pp from the daemon's previous observed price and **+19.0pp from entry**. This is strong short-run CLV toward the 65% thesis, but the market is now above my point estimate, so the remaining paper edge is gone without a fresh tracker-count update. No forecast/thesis change from price alone; continue watching for the overrun risk into 160+ posts.
- 2026-04-27T20:26Z: Polymarket moved down to **64.5% YES** (60% bid / 69% ask; last trade 53%), still **+12.5pp from entry** but back near my original 65% forecast. XTracker API showed **143 counted posts** at sync 20:25:47Z after 19 posts since writing; the bin now needs no more posts to enter, but only has **0-16 posts** of cushion before overrun to 160+. Historical analogs for partial counts around 140-150 and ~19.6h remaining put staying within 140-159 closer to the mid-30s/40s than 65%, so overrun risk has become the main live threat.
- 2026-04-27T20:56Z: Polymarket moved down again to **47.5% YES** (41% bid / 54% ask; last trade 53%), now **-4.5pp from entry** on midpoint. XTracker API showed **144 counted posts** at sync 20:55:47Z, with only **0-15 posts** of cushion and ~19.1h left. Historical analogs for partial 140-150 with active recent posting put overrun above 159 as the majority risk. This move is adverse evidence against the original 65% forecast, not just noise.
- 2026-04-27T21:58Z: Polymarket rebounded to **59.0% YES** (56% bid / 62% ask; last trade 51%), **+7.0pp from entry**. XTracker still showed **144 counted posts** at sync 21:56:12Z, with no posts in the prior ~1.3h and ~18.0h remaining. The idle hour reduces immediate overrun pressure, but the bin still has only 0-15 posts of cushion; partial-count analogs around 140-148 remain mostly below the original 65% estimate unless conditioning heavily on same-hour/gap inactivity.
- 2026-04-27T23:43Z: Polymarket rebounded further to **76.0% YES** (72% bid / 80% ask; last trade 65%), **+24.0pp from entry** and above the original 65% forecast. XTracker still showed **144 counted posts** at sync 23:40:48Z, with no posts in the prior ~3.0h and ~16.3h remaining. The prolonged idle stretch makes the 0-15 cushion more plausible than it looked during the 20:26-20:56 burst, but the book is wide and analogs are conditioning-sensitive: broad partial-count analogs still center near overrun, while low-recent-activity / same-hour analogs support a higher probability. No fresh YES edge at 76%; continue watching for any overnight burst.
- 2026-04-27T23:58Z: Polymarket whipsawed down to **40.5% YES** on a very wide **23% / 58%** book (last trade 13%), **-11.5pp from entry**. This was not pure book noise: XTracker sync 23:55:45 showed **150 counted posts** after six posts at 23:43-23:46, leaving only **0-9 posts** of cushion and ~16.0h left. Partial-count analogs around 145-155 make overrun above 159 the dominant risk (roughly only low-20s/30s staying in-bin under recent-activity conditioning). This is adverse evidence against the original 65% forecast.
