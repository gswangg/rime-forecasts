# Scorecard

*Last updated: 2026-05-18T02:20:18+00:00*

## Summary

- Predictions made: 33 (8 v1 + 25 v2/v2.5.x/v3)
- Resolved: 20
- Brier score: 0.154
- Naive primary-venue Brier: 0.299
- Log loss: 0.467
- Calibration: insufficient N (0-10% bucket: 0/1 YES; 10-20% bucket: 0/2 YES; 20-30% bucket: 0/1 YES; 30-40% bucket: 2/6 YES; 40-50% bucket: 1/3 YES; 50-60% bucket: 0/1 YES; 60-70% bucket: 1/2 YES; 80%+ bucket: 4/4 YES)
- **Portfolio direction bias (at writing):** 18 below primary venue, 15 above primary venue.

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

| Written | Market | Forecast | Entry | Outcome | Brier | Market Brier | Notes |
|---------|--------|----------|-------|---------|-------|--------------|-------|
| 2026-04-19 | [Bayern wins Champions League](./reasoning/2026-04-19-bayern-wins-champions-league.md) | 30% YES | 35.0% YES | NO | 0.090 | 0.123 | PSG eliminated Bayern in the semifinal, advancing 6-5 on aggregate after a 1-1 second-leg draw. Small below-consensus base-rate win. |
| 2026-04-26 | [Running Point S2 top US Netflix show](./reasoning/2026-04-26-running-point-netflix-top-us-show.md) | 30% YES | 92.4% YES | NO | 0.090 | 0.854 | Official Netflix source did not list `Running Point`; Polymarket resolved NO. Strong stale/source-check win. |
| 2026-04-27 | [Elon Musk 220-239 posts Apr 21-28](./reasoning/2026-04-27-elon-musk-tweets-apr21-apr28-220-239.md) | 35% YES | 23.5% YES | YES | 0.423 | 0.585 | Market moved strongly toward the bin before close and resolved YES; forecast had positive edge but was underconfident. |
| 2026-04-27 | [Trump 100-119 Truth Social posts Apr 21-28](./reasoning/2026-04-27-trump-truth-social-posts-apr21-apr28-100-119.md) | 40% YES | 5.15% YES | NO | 0.160 | 0.003 | XTracker reached 121+ counted posts, overrunning the 119 upper bound. Burst risk dominated the quiet-stretch thesis. |
| 2026-04-27 | [White House 140-159 posts Apr 21-28](./reasoning/2026-04-27-white-house-posts-apr21-apr28-140-159.md) | 65% YES | 52.0% YES | NO | 0.423 | 0.270 | Resolved NO after overrun above 159. Another range-bin failure near an upper boundary. |
| 2026-04-27 | [Powell says "Pandemic" during April press conference](./reasoning/2026-04-27-powell-pandemic-april-press-conference.md) | 88% YES | 74.5% YES | YES | 0.014 | 0.065 | Source-based vocabulary persistence call resolved YES. |
| 2026-04-28 | [Amazon GAAP EPS > $1.65](./reasoning/2026-04-28-amzn-gaap-eps-q1-2026.md) | 80% YES | 92.15% YES | YES | 0.040 | 0.006 | AMZN beat; the market's higher confidence was better than the NO-side fade. |
| 2026-04-28 | [Anthropic Mythos to US government by Apr 30](./reasoning/2026-04-28-anthropic-mythos-us-government-april-30.md) | 60% YES | 5.5% YES | YES | 0.160 | 0.893 | Axios/credible-reporting adjudication thesis resolved YES after large positive CLV. |
| 2026-04-30 | [White House 160-179 posts Apr 24-May 1](./reasoning/2026-04-30-white-house-posts-apr24-may1-160-179.md) | 40% YES | 10.5% YES | NO | 0.160 | 0.011 | XTracker export showed 193 in-window posts, overrunning the 179 upper bound. Visible count at writing was stale/backfilled by ~9 posts, and a later burst made 180-199 the correct bin. |
| 2026-04-30 | [Tesla high $390 week of Apr 27](./reasoning/2026-04-30-tsla-high-390-week-apr27.md) | 40% YES | 23.5% YES | YES | 0.360 | 0.585 | Pyth/Gamma resolved YES; Yahoo proxy showed first RTH high >= $390 on May 1. Directionally right but underconfident. |
| 2026-05-03 | [Michael 2nd weekend box office > $55m](./reasoning/2026-05-03-michael-second-weekend-box-office-55m.md) | 28% YES | 42.25% YES | NO | 0.078 | 0.179 | The Numbers and Box Office Mojo finalized the May 1-3 weekend at $54.403m, below threshold. Forecast beat the market despite ugly interim CLV. |
| 2026-05-03 | [Elon Musk <40 tweets May 2-May 4](./reasoning/2026-05-03-elon-musk-tweets-may2-may4-0-39.md) | 3% YES | 13.5% YES | NO | 0.001 | 0.018 | XTracker counted 55 in-window posts, so the `<40` lower-tail bin resolved NO. Burst/backfill continuation thesis validated. |
| 2026-05-03 | [ON Semiconductor non-GAAP EPS > $0.61](./reasoning/2026-05-03-on-semiconductor-nongaap-eps-q1-2026.md) | 80% YES | 91.5% YES | YES | 0.040 | 0.007 | onsemi reported Q1 non-GAAP diluted EPS of $0.64, clearing the strict `>$0.61` strike. YES-side direction right, but market confidence beat the NO-side fade. |
| 2026-05-03 | [Sonos non-GAAP EPS > $0.01](./reasoning/2026-05-03-sonos-nongaap-eps-q2-2026.md) | 30% YES | 56.5% YES | NO | 0.090 | 0.319 | Sonos reported Q2 non-GAAP diluted EPS of `($0.02)`, below the strict `>$0.01` strike. Fixed-strike/rule thesis beat the market. |
| 2026-05-14 | [Cerebras IPO market cap < $50B](./reasoning/2026-05-14-cerebras-ipo-market-cap-less-than-50b.md) | 35% YES | 3.15% YES | NO | 0.123 | 0.001 | CBRS closed at $311.07; StockAnalysis/Yahoo showed ~215.23M shares out and ~$66.95B market cap, above $50B even on the outstanding-share interpretation. Source/rule thesis got the threshold right but underpriced the first-day IPO pop; market beat decisively. |
| 2026-05-14 | [Confirmed Hantavirus case in US by May 15](./reasoning/2026-05-14-hantavirus-confirmed-us-by-may-15.md) | 35% YES | 19.5% YES | YES | 0.423 | 0.648 | Polymarket/UMA finalized YES after a late proposed-YES repricing. Directionally beat the market, but post-mortem caveat: the decisive source was not surfaced before settlement; CDC/NBC/Yahoo/IDPH checks still looked adverse immediately before final YES. |
| 2026-05-14 | [Trump says "Taiwan" or "Tibet" with Xi](./reasoning/2026-05-14-trump-say-taiwan-tibet-xi-events.md) | 18% YES | 28.5% YES | NO | 0.032 | 0.081 | Polymarket/UMA resolved NO. Taiwan was central in readouts, but no qualifying live/broadcast Trump utterance of `Taiwan`/`Tibet` at an event featuring both Trump and Xi was counted. Rule-specific NO thesis beat the market. |
| 2026-05-14 | [Jerome Powell out as Fed Chair by May 15](./reasoning/2026-05-14-powell-out-as-fed-chair-by-may-15.md) | 95% YES | 17.5% YES | YES | 0.003 | 0.681 | Polymarket/UMA finalized YES after official Fed release said Powell's chair term concludes and the Board named him chair pro tempore until Warsh is sworn in. Source/adjudication thesis beat stale entry price decisively despite interim dispute. |
| 2026-05-14 | [Cyprus Eurovision top 10](./reasoning/2026-05-14-cyprus-eurovision-2026-top-10.md) | 18% YES | 6.5% YES | NO | 0.032 | 0.004 | Polymarket/UMA finalized NO; Eurovisionworld final results show Cyprus 19th with 75 points, outside the top 10. Cross-market bookmaker-anchor thesis lost to the lower Polymarket entry despite favorable interim CLV. |
| 2026-05-14 | [Finland Eurovision top 3](./reasoning/2026-05-14-finland-eurovision-2026-top-3.md) | 58% YES | 80.0% YES | NO | 0.336 | 0.640 | Polymarket/UMA finalized NO; Eurovisionworld final results show Finland 6th with 279 points, outside the top 3. Favorite-overpricing fade beat the market, though the absolute forecast still had YES as the modal outcome. |

## Pending predictions

| Written | Market | Me | Manifold | Kalshi | Poly | Resolves | v |
|---------|--------|----|----------|--------|------|----------|---|
| 2026-04-19 | [Anthropic 60B ARR on July 6](./reasoning/2026-04-19-anthropic-60b-arr-july-2026.md) | 17% | 25% | — | — | 2026-07-06 | v1 |
| 2026-04-19 | [OpenAI captcha refusal by mid-2026](./reasoning/2026-04-19-openai-agent-captcha-refusal.md) | 78% | 72% | — | — | 2026-07-18 | v1 |
| 2026-04-19 | [SSI ship AI by July](./reasoning/2026-04-19-ssi-ship-before-july-2026.md) | 5% | 10% | — | — | 2026-06-30 | v1 |
| 2026-04-19 | [Messi plays WC26](./reasoning/2026-04-19-messi-plays-world-cup-2026.md) | 93% | 88% | — | 92.5% | 2026-06-30 | v1 |
| 2026-04-19 | [Starship F12 clears pad](./reasoning/2026-04-19-starship-flight-12-clears-pad.md) | 85% | 93% | — | ⚠️ | 2026-06-30 | v1 |
| 2026-04-19 | [LLM coauthor Nature/Sci](./reasoning/2026-04-19-llm-coauthor-nature-science.md) | 8% | 14% | — | — | 2026-06-30 | v1 |
| 2026-04-19 | [Patel FBI Director June 30](./reasoning/2026-04-19-patel-fbi-director-june-30.md) | 58% | 49% | — | ~94% stays¹ | 2026-06-30 | v1 |
| 2026-04-19 | [WTI crude $150 before June](./reasoning/2026-04-19-wti-crude-150-by-june.md) | 5% | 20.5% | — | — | 2026-05-31 | v2 |
| 2026-04-26 | [Tottenham relegated from EPL](./reasoning/2026-04-26-tottenham-relegated-epl-2026.md) | 50% | 51% / 49.5% | — | 32.05% | 2026-05-27 | v2.5.2 |
| 2026-05-14 | [Finland Eurovision top 5](./reasoning/2026-05-14-finland-eurovision-2026-top-5.md) | 74% | — | — | 90.5% | 2026-05-16 | v3 |
| 2026-05-15 | [Hormuz transit calls May 11-May 17, 20-39](./reasoning/2026-05-15-hormuz-transit-calls-may11-may17-20-39.md) | 35% | — | — | 62.0% | 2026-05-17 | v3 |
| 2026-05-15 | [Trump says "Make America Great Again" this week](./reasoning/2026-05-15-trump-say-make-america-great-again-this-week.md) | 15% | — | — | 33.5% | 2026-05-17 | v3 |
| 2026-05-17 | [Michael 4th weekend box office $22m-$25m](./reasoning/2026-05-17-michael-fourth-weekend-box-office-22m-25m.md) | 38% | — | — | 55.5% | 2026-05-18 | v3 |

¹ Polymarket question is "leaves admin before 2027" at 19% YES; window-adjusted equivalent for my 72-day Manifold question is ~6% exit = 94% stays.

## Lessons

- (From cycle-30 enrichment) Cross-venue shadowing catches miscalibrations that single-venue reasoning doesn't. The v2 dual-shadow rule is justified even just by the Patel finding.
- (From cycle-30 enrichment) Manifold appears to overprice scandal-exit probabilities vs real-money venues. If this holds across more cases, it's a systematic bias worth exploiting.
