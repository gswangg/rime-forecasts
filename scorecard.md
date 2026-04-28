# Scorecard

*Last updated: 2026-04-28T23:48:16+00:00*

## Summary

- Predictions made: 17 (8 v1 + 9 v2/v2.5.x/v3)
- Resolved: 0
- Brier score: —
- Naive primary-venue Brier: —
- Log loss: —
- Calibration: insufficient N
- **Portfolio direction bias (at writing):** 8 below primary venue, 9 above primary venue.

## Cross-venue observations (from v1-baseline enrichment)

Completed retrospective Kalshi + Polymarket shadow for all 8 v1 predictions (see each prediction's "Cross-venue shadow" section for details).

### Shadow coverage

| Prediction | Polymarket | Kalshi | Notes |
|-----------|-----------|--------|-------|
| Anthropic 60B ARR | ❌ | ❌ | AI-specific revenue milestone — Manifold niche |
| OpenAI captcha refusal | ❌ | ❌ | AI product policy — Manifold niche |
| SSI ship AI | ❌ | ❌ | Lab strategy — Manifold niche |
| Messi WC26 | ✅ 92.5% | ❌ | Sports |
| Bayern CL | ✅ 34.5% | ❌ | Sports |
| Starship F12 pad | ⚠️ partial (related questions, stale dates) | ❌ | Aerospace |
| LLM coauthor Nature/Sci | ❌ | ❌ | Sci publishing — Manifold niche |
| Patel FBI Director | ✅ 19% leaves-by-2027 | ❌ | US politics |

3 of 8 v1 predictions had directly-usable real-money shadows. 0 had Kalshi shadows (Kalshi's open-event universe skews to generic policy/milestone questions, not specific named-individual or named-company questions).

### Cross-venue disagreements (the actually-valuable signal)

- **Patel FBI (big divergence):** Manifold 51% exit, Polymarket ~6% exit over same 72-day window → **45pp spread**. My prediction (42% exit) hugged Manifold. If Polymarket is the better signal, my cycle 8 call was substantially miscalibrated — should have been 15–25% exit. Likely over-weighted the Atlantic scandal relative to Trump-loyalty base rate.
- **Messi WC (alignment):** Manifold 88%, Polymarket 92.5%. My 93% matches Polymarket within 0.5pp. Cross-venue validation of the base-rate calculation.
- **Bayern CL (alignment):** Manifold 35%, Polymarket 34.5%. My 30% is 5pp below consensus. Probably should have been 32–33% — mild overconfidence in the down-move.
- **Tottenham relegation (big divergence, v2.5.2):** Polymarket 32.05% vs Manifold 51%/49.5%. My 50% is close to Manifold, not Polymarket, based on current table state (Spurs 18th, two points behind West Ham with four matches left). This is the first forward prediction explicitly using cross-venue spread as a stale-price diagnostic.

### Implications for v2 candidate selection

1. **Prefer markets with both real-money shadows.** The v1 base showed 5/8 predictions landed in Manifold-only niches. Those are fine for calibration *research* but useless for trading. v2 should weight toward predictions where both Kalshi and Polymarket have equivalents.
2. **Cross-venue divergence is itself alpha.** Patel's 45pp spread between Manifold and Polymarket is exactly the type of signal that produces trading edge — you don't need to have a view; you need to identify *which* venue is more accurate. Future v2 predictions should prioritize markets with substantial cross-venue spread over markets with consensus.
3. **Manifold has clear YES-bias on scandal-driven markets.** Patel's Manifold price (51% exit) vs Polymarket's (6%) is a stark example. Manifold bettors appear to overweight news-cycle intensity. A systematic "bet against Manifold scandal-exit premiums relative to Polymarket" strategy might be a distinct tradeable thesis.

## Resolved predictions

None yet.

## Source-decisive, awaiting market settlement

| Market | Forecast | Entry | Source state | Expected outcome | Expected Brier |
|--------|----------|-------|--------------|------------------|----------------|
| [Trump 100-119 Truth Social posts Apr 21-28](./reasoning/2026-04-27-trump-truth-social-posts-apr21-apr28-100-119.md) | 40% YES | 5.15% YES | XTracker showed 121 counted posts by 2026-04-28T12:46Z, above the 119 upper bound | NO pending Polymarket settlement | 0.160 |

## Lessons

- (From cycle-30 enrichment) Cross-venue shadowing catches miscalibrations that single-venue reasoning doesn't. The v2 dual-shadow rule is justified even just by the Patel finding.
- (From cycle-30 enrichment) Manifold appears to overprice scandal-exit probabilities vs real-money venues. If this holds across more cases, it's a systematic bias worth exploiting.

## Pending predictions

| Written | Market | Me | Manifold | Kalshi | Poly | Resolves | v |
|---------|--------|----|----------|--------|------|----------|---|
| 2026-04-19 | [Anthropic 60B ARR on July 6](./reasoning/2026-04-19-anthropic-60b-arr-july-2026.md) | 17% | 25% | — | — | 2026-07-06 | v1 |
| 2026-04-19 | [OpenAI captcha refusal by mid-2026](./reasoning/2026-04-19-openai-agent-captcha-refusal.md) | 78% | 72% | — | — | 2026-07-18 | v1 |
| 2026-04-19 | [SSI ship AI by July](./reasoning/2026-04-19-ssi-ship-before-july-2026.md) | 5% | 10% | — | — | 2026-06-30 | v1 |
| 2026-04-19 | [Messi plays WC26](./reasoning/2026-04-19-messi-plays-world-cup-2026.md) | 93% | 88% | — | 92.5% | 2026-06-30 | v1 |
| 2026-04-19 | [Bayern wins CL](./reasoning/2026-04-19-bayern-wins-champions-league.md) | 30% | 35% | — | 34.5% | 2026-06-29 | v1 |
| 2026-04-19 | [Starship F12 clears pad](./reasoning/2026-04-19-starship-flight-12-clears-pad.md) | 85% | 93% | — | ⚠️ | 2026-06-30 | v1 |
| 2026-04-19 | [LLM coauthor Nature/Sci](./reasoning/2026-04-19-llm-coauthor-nature-science.md) | 8% | 14% | — | — | 2026-06-30 | v1 |
| 2026-04-19 | [Patel FBI Director June 30](./reasoning/2026-04-19-patel-fbi-director-june-30.md) | 58% | 49% | — | ~94% stays¹ | 2026-06-30 | v1 |
| 2026-04-19 | [WTI crude $150 before June](./reasoning/2026-04-19-wti-crude-150-by-june.md) | 5% | 20.5% | — | — | 2026-05-31 | v2 |
| 2026-04-26 | [Tottenham relegated from EPL](./reasoning/2026-04-26-tottenham-relegated-epl-2026.md) | 50% | 51% / 49.5% | — | 32.05% | 2026-05-27 | v2.5.2 |
| 2026-04-26 | [Running Point S2 top US Netflix show](./reasoning/2026-04-26-running-point-netflix-top-us-show.md) | 30% | — | — | 92.4% | 2026-04-28 | v3 |
| 2026-04-27 | [Elon Musk 220-239 posts Apr 21-28](./reasoning/2026-04-27-elon-musk-tweets-apr21-apr28-220-239.md) | 35% | — | — | 23.5% | 2026-04-28 | v3 |
| 2026-04-27 | [Trump 100-119 Truth Social posts Apr 21-28](./reasoning/2026-04-27-trump-truth-social-posts-apr21-apr28-100-119.md) | 40% | — | — | 5.15% | 2026-04-28 | v3 |
| 2026-04-27 | [White House 140-159 posts Apr 21-28](./reasoning/2026-04-27-white-house-posts-apr21-apr28-140-159.md) | 65% | — | — | 52.0% | 2026-04-28 | v3 |
| 2026-04-27 | [Powell says "Pandemic" during April press conference](./reasoning/2026-04-27-powell-pandemic-april-press-conference.md) | 88% | — | — | 74.5% | 2026-04-29 | v3 |
| 2026-04-28 | [Amazon GAAP EPS > $1.65](./reasoning/2026-04-28-amzn-gaap-eps-q1-2026.md) | 80% | — | — | 92.15% | 2026-04-29 | v3 |
| 2026-04-28 | [Anthropic Mythos to US government by Apr 30](./reasoning/2026-04-28-anthropic-mythos-us-government-april-30.md) | 60% | — | — | 5.5% | 2026-04-30 | v3 |

¹ Polymarket question is "leaves admin before 2027" at 19% YES; window-adjusted equivalent for my 72-day Manifold question is ~6% exit = 94% stays.
