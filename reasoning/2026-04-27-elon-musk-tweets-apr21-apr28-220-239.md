# Elon Musk 220-239 posts Apr 21-28 — resolves 2026-04-28

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/elon-musk-of-tweets-april-21-april-28-220-239
**Polymarket market slug**: elon-musk-of-tweets-april-21-april-28-220-239
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-27T12:24:19+00:00
**Prediction**: 35%
**Primary venue price at writing**: 23.5% YES (best bid 23.0%, best ask 24.0%; candidate event price was 26.5% at 2026-04-27T12:11Z)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +11.5pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether Elon Musk posts **220-239** times on X from April 21, 2026 12:00 PM ET to April 28, 2026 12:00 PM ET.

Resolution source is the Polymarket XTracker `Post Counter` at https://xtracker.polymarket.com. The rules count main-feed posts, quote posts, and reposts. Replies generally do not count unless shown on the main feed and counted by the tracker. Deleted posts count if captured by the tracker.

At writing, XTracker showed **181 counted posts** for the window. Last sync was 2026-04-27T12:21:41Z; the most recent counted post was 2026-04-27T04:11:04Z. There were about **27.6 hours** remaining. This bin resolves YES if the tracker records **39-58 additional posts** before noon ET on Apr 28.

Current neighboring Polymarket prices checked at writing:

- 180-199: 12.45%
- 200-219: 45.5%
- 220-239: 23.5%
- 240-259: 8.5%
- 260-279: 3.0%
- 280-299: 1.05%

## Base rate

The naive base rate from the current event state is not the full seven-day historical mean. Musk is at only 181 posts after roughly 140.4 hours, with an 8+ hour current silence and only 13 counted posts in the prior 24 hours. That makes `200-219` the modal-looking bucket.

But the remaining-window distribution has historically been fatter than the market's current cluster implies. Using XTracker posts from 2025-11-18 through the current sync, I compared pseudo-current windows with a 27.6-hour remaining interval.

The empirical probability of **39-58 posts in the next ~27.6h** was:

- all hourly pseudo-current windows: 33.8%
- hourly windows with current-like 6h+ posting gap: 33.6%
- hourly windows with previous 24h ≤ 20 posts: 41.8%
- hourly windows with 6h+ gap and previous 24h ≤ 20 posts: 43.4%
- hourly windows with prior-window partial count 160-205: 32.8%
- daily same-elapsed windows with partial count 150-220: 32.4%
- daily same-elapsed windows with partial count 160-205: 21.1% (small N=19 and very noisy)

Those samples are correlated and not clean iid draws. Still, most of the relevant conditioning says the 39-58 remaining-post interval is closer to the low/mid 30s than to the low 20s.

## Where I differ from base rate (and why)

I am at **35% YES**, above Polymarket's 23.5%.

The market appears to be over-weighting the recent quiet stretch and under-weighting the tendency for Musk posting to re-accelerate after lulls. The 220-239 bucket does not require a high-output mania day. From 181, it only needs 39 posts over 27.6 hours, while avoiding 59+ posts. That is roughly 1.4 posts/hour on average. For this account, that is not an extreme rate.

The important distinction from the adjacent 200-219 bucket: `200-219` needs only 19-38 more posts, but its price already reflects that and has moved sharply upward. `220-239` is cheaper after a one-day down-move, while the historical conditional distribution still gives substantial mass to the 39-58 range.

I am not higher than 35% because the market is probably right that this is no longer a normal-output window:

- The last counted post was 8+ hours before the XTracker sync.
- The prior 24h count was only 13.
- The exact bin loses both to continued quiet (`180-199` / `200-219`) and to a high-output rebound (`240+`).
- XTracker data since Nov 2025 is regime-mixed and hourly overlapping-window samples overstate precision.

So this is an empirical stale/recency-pricing edge, not a strong information edge.

## What would change my mind

Signals that would move me down:

- No new counted posts by late afternoon ET on Apr 27.
- XTracker remaining below ~190 with under 20 hours left.
- Evidence that Musk is offline/traveling/asleep through the US day.
- Market prices shifting `200-219` higher without new count growth, implying informed traders see continued quiet.

Signals that would move me up:

- A burst to 190-195 counted posts before evening ET on Apr 27.
- Multiple quote/repost chains restarting after the current 8h quiet period.
- Adjacent 240+ bins staying cheap while 220-239 remains below 30%.

## Economics at this edge

At 35% true probability versus 23.5% market YES, the pre-friction edge is **+11.5pp**. The bid/ask spread was about 1pp, so a paper trader buying YES around 24 cents would still have roughly 10pp gross edge if this estimate is right.

The edge is thin enough that sizing would be modest in a live account. The main risk is overfitting historical XTracker windows and ignoring information in the recent market move/count slowdown.

---

*(Resolution section added below after the market resolves. The above is frozen.)*

## Post-writing watch notes

- 2026-04-27T15:07Z: Polymarket moved to **31.0% YES** (30% bid / 32% ask), up 6.5pp from the daemon's previous observed price and **+7.5pp from entry**. This is short-run CLV toward the 35% thesis, but it also compresses the remaining edge to about 4pp. No forecast/thesis change; keep watching the scheduled +6h/+24h checkpoints and final XTracker count.
- 2026-04-27T16:40Z: Polymarket moved to **39.5% YES** (39% bid / 40% ask), **+16.0pp from entry** and now above my 35% point estimate. XTracker API showed **191 counted posts** at sync 16:40:52Z, up 10 from writing; the bin now needs **29-48 more posts** in the remaining ~23.3h. A quick historical recheck on XTracker posts put the analogous 29-48 remaining-post interval around the low/mid-30s under partial-count conditioning, so the original underpricing edge is gone or at least much thinner. The market move is useful positive CLV, not a reason to chase the bin above the original estimate.
- 2026-04-27T18:26Z: Polymarket moved to **49.5% YES** (49% bid / 50% ask), **+26.0pp from entry**. XTracker API showed **198 counted posts** at sync 18:25:44Z after seven additional posts since 16:40Z; the bin now needs **22-41 more posts** in the remaining ~21.6h. Historical analogs for similar partial counts and remaining time cluster around the high-30s/low-40s for this interval, so the market has moved beyond the original edge. Positive CLV is strong, but current fair value is no longer obviously above market.
- 2026-04-27T20:26Z: Polymarket moved down to **43.5% YES** (43% bid / 44% ask), still **+20.0pp from entry**. XTracker API showed **213 counted posts** at sync 20:25:52Z; the bin now needs **7-26 more posts** in the remaining ~19.6h. Historical analogs for partial count ~205-220 put the 7-26 interval around ~38-44%, with overrun above 239 the main risk, so this move brings the market back near a plausible fair range rather than reopening the original YES edge.
- 2026-04-27T21:28Z: Polymarket moved down to **39.5% YES** (39% bid / 40% ask), still **+16.0pp from entry** and slightly above the original 35% forecast. XTracker API showed **215 counted posts** at sync 21:25:51Z; the bin now needs **5-24 more posts** in the remaining ~18.5h. Historical analogs around partial count 210-220 put the 5-24 interval mostly in the low/mid-30s with overrun above 239 as the dominant risk, so market drift is directionally sensible.
- 2026-04-28T00:13Z: Polymarket moved up to **46.5% YES** (46% bid / 47% ask), **+23.0pp from entry** and well above the original 35% forecast. XTracker API showed **219 counted posts** at sync 00:10:52Z; the bin needs only **1** more post to enter, but only **20** more posts to overrun above 239 with ~15.8h left. The move is source-supported rather than just flow: three posts in the prior hour and six since 21:12Z. Broad partial-count analogs still put overrun as the main risk; recent-activity conditioning can justify something near the market, but not a fresh YES edge.
