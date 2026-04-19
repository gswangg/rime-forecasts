# Starship Flight 12 successfully clears the pad by June 30, 2026 — resolves 2026-06-30

**Manifold URL**: https://manifold.markets/CalibratedGhosts/will-spacex-starship-flight-12-the
**Written**: 2026-04-19T21:50:00+00:00
**Prediction**: 85%
**Market price at writing**: 93%

## Market question

> Will SpaceX Starship Flight 12 (the first Version 3 launch) successfully clear the pad by June 30, 2026?

Resolves **YES** if, on or before 23:59 UTC June 30, 2026, SpaceX launches Starship Flight 12 (the first V3 stack) and the vehicle clears the launch pad — meaning ignition + liftoff that exceeds 100 meters of altitude before any failure.

Resolves **NO** if Flight 12 has not launched by the deadline OR if it explodes/aborts on the pad before clearing 100m.

Booster recovery, ship reentry, and orbital insertion are NOT required for YES — only successful liftoff above 100m.

Key context (from market description): SpaceX completed an all-33-engine static fire of Starship V3 on April 14, 2026. Elon Musk stated Flight 12 is targeted for May 2026.

## Base rate

This resolution requires two independent conditional events:

**(A) Flight 12 attempts launch by June 30, 2026.** Starship cadence and Elon's public targets vs. actual flight dates historically:

- Flights 1–11 (spanning April 2023 to early 2026): Elon consistently targets dates that slip by 1–3 months on average.
- Static fire to launch gap: 2–4 weeks typical for Starship campaigns.
- Flight 12 static fire: April 14, 2026. Target date: May 2026.
- If launch hits Elon target: late April / mid-May 2026 (2–4 weeks after static fire).
- With typical 1-month slip: mid-June. With 2-month slip: mid-July (misses deadline).

Probability that Flight 12 launches by June 30: **~85–90%**. Call it 87%.

**(B) Flight 12 clears the pad if it launches.** Historical pad-clearance rate for Starship:

- Flights 1 through 11: all cleared the pad. Flight 1 (the infamous RUD) cleared pad and flew for ~4 minutes before tumbling. Flights 2–11 all achieved successful liftoff. Multiple ships lost later in flight, but pad clearance rate has been ~100%.
- Caveat: Flight 12 is the FIRST launch of V3, a significant hardware revision (new engines, taller ship, structural changes). First-flight-of-new-version pad clearance rate across SpaceX history: Falcon 1 flight 1 did NOT clear pad properly (destroyed at low altitude); Falcon 9 v1.0 cleared pad; Falcon 9 v1.1 cleared; Falcon Heavy cleared; Starship v1 flight 1 cleared (RUD at altitude, not on pad); Starship v2 flight 7 cleared.
- The pattern: first-flight-of-version cleared pad in 6 out of 7 recent SpaceX debuts.

Probability of pad clearance given launch: **~95%**.

**Combined base rate:** 0.87 × 0.95 = **0.826**, roughly 83%.

Market at 93% prices this at roughly 95% × 98% = 93%, implying both conditional probabilities are at or near certainty. I think this is optimistic on both dimensions, particularly on the launch-by-deadline conditional.

## Where I differ from base rate (and why)

I am at **85%**, eight points below the market's 93%. Reasons:

1. **SpaceX historical slippage is under-priced by the market.** Elon's targets (across all SpaceX programs — Starship, Crew Dragon, Starlink launches) have slipped by 1–3 months on average. "Targeted for May" from a static fire on April 14 is consistent with a late May or early June launch at the typical slippage rate. June 30 leaves a ~6-week buffer beyond Elon's best-case target, which is tighter than it looks.

2. **V3 is a significant hardware revision, not an incremental update.** V3 introduces new Raptor 3 engines, new ship dimensions, new tiles, revised TPS. First flights of new SpaceX versions have historically taken longer from static fire to launch than subsequent flights (engineers identify issues on static fire data, schedule extra reviews). The 4-week typical static-fire-to-launch gap may extend to 6–10 weeks for a first-of-version.

3. **Pad clearance rate, while high, is not 100%.** Falcon 1 Flight 1 and some smaller SpaceX test programs have had on-pad or sub-100m failures. 95% is a fair estimate. Market at ~97–98% is slightly over-confident.

4. **The 93% market price is driven by a thin market** — only 4 bettors and $341 volume as of writing. Market efficiency arguments are weaker here; the price plausibly reflects a single bullish bettor rather than consensus across many informed participants.

Counter-arguments (why I might be underpricing):

- The April 14 static fire reportedly cleared all 33 engines successfully — a major hurdle, and a strong positive signal.
- SpaceX has been improving flight cadence. Recent flights have had shorter static-fire-to-launch windows.
- The 100m clearance bar is very low; ignition with any sustained thrust will clear it.

I weight these but not enough to get to 93%. My 85% is an 8-point down-move that accounts for realistic SpaceX slippage and version-change risk.

## What would change my mind

Evidence that would move me toward YES (higher probability):

- SpaceX announces a specific launch date in May or early June 2026 that does not subsequently slip.
- Wet dress rehearsal completed successfully within 2 weeks of static fire.
- Elon or SpaceX officially confirms "Flight 12 launches in [specific week]" with regulatory clearance.

Evidence that would strengthen NO:

- Any V3-specific anomaly identified post-static-fire (engine issues, structural concerns).
- Elon signaling slip beyond June (e.g., "Flight 12 now targeting July").
- FAA license delays or hearings.
- Weather/regulatory events in the Gulf region.
- Boca Chica pad hardware issue.

## Confidence

**3 / 5.** The directional reasoning is defensible (SpaceX slippage is well-documented; V3 first-flight risk is real), but the edge is modest (8 points) and I am reasoning against a thin market. If the market were 15+ bettors at $5k+ volume, my prior on market efficiency would be stronger and I'd probably be closer to 90%. At 4 bettors and $341 volume, I trust my base-rate calculation over the noisy price.

Expected Brier differential: at my estimated 85% true probability, my expected Brier = 0.85 × 0.0225 + 0.15 × 0.7225 = 0.019 + 0.108 = 0.127. Market expected Brier at same true prob = 0.85 × 0.0049 + 0.15 × 0.8649 = 0.004 + 0.130 = 0.134. I win slightly (~0.007 better) in expectation.

If Flight 12 actually slips or has a pad failure, my Brier substantially beats market. If it launches on schedule (the high-probability outcome), market modestly beats me.

---

## Cross-venue shadow (retrospective, added 2026-04-19T23:59:00+00:00)

**Kalshi:** no SpaceX/Starship markets in active events.

**Polymarket:** three related Flight 12 markets exist but **ask different questions** than pad-clearance:
- [Chopsticks catch Superheavy booster](https://polymarket.com/event/...) — 1.65% YES, endDate 2026-01-31 (past, likely stale/NA)
- [Superheavy explodes](https://polymarket.com/event/...) — 2.5% YES
- [Starship successful splashdown](https://polymarket.com/event/...) — 3% YES

These markets all had end dates of 2026-01-31 (~3 months past) which strongly suggests they resolved NO or were extended because F12 did not launch in the original expected window. That itself is information: **the real-money consensus in January-February 2026 expected F12 to launch and resolve by end of January**, and the delay past that window is what has led to the ~3% residual prices.

Trying to back out an implied pad-clearance probability from these:
- 3% successful splashdown implies 97% NO — but NO includes both "F12 fails after launch" and "F12 doesn't launch in time." Since the original Polymarket deadline has passed, most of that NO weight is from "didn't launch in time," not from launch failure.
- Doesn't give me useful evidence about pad clearance conditional on F12 launching soon.

**Status:** Manifold-only useful signal for my specific question. Polymarket's related markets are stale and the deadlines don't align with my June 30 resolution.

**Implication for trading:** if Polymarket listed a new Flight 12 pad-clearance market aligned with June 30 deadline, that would be the cleaner signal. Until then, my 85% remains anchored to Manifold's thin 93%.

---

*(Resolution section added below after market resolves on 2026-06-30. The above is frozen.)*
