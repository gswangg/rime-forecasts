# Scorecard

*Last updated: 2026-08-05T02:00:36+00:00 (post-dormancy resolution sweep — 11 predictions resolved retroactively)*

## Summary

- Real-money primary predictions: 27 Kalshi/Polymarket-primary (**27 resolved, 0 pending — book complete**)
- Real-money primary Brier score: **0.155**
- Real-money primary-venue Brier: **0.300**
- Beat primary venue at resolution: **19/27 real-money**, 26/35 full historical
- Full historical ledger: 36 predictions made (27 real-money primary + 9 Manifold-primary legacy), 35 resolved
- Full historical Brier score: **0.130**
- Full historical primary-venue Brier: **0.247**
- Legacy paper-money Manifold-primary predictions: 9 total (8 resolved, 1 pending — Anthropic 60B ARR awaiting late creator resolution, market drifted to 79.5% vs my 17%; likely a large miss when it lands), retained for archive/backtest context but excluded from the active source policy going forward.
- Log loss: 0.405 (full historical, resolved)
- Calibration (35 resolved): 0-10% bucket: 0/4 YES; 10-20%: 0/3 YES; 20-30%: 0/1 YES; 30-40%: 2/9 YES; 40-50%: 1/3 YES; 50-60%: 1/3 YES; 60-70%: 1/2 YES; 70-80%: 1/2 YES; 80%+: **8/8 YES**. Low buckets (0-30%): 0/8 YES combined. Directionally well-calibrated; mid-bucket N still small.
- **Portfolio direction bias (full historical, at writing):** 19 below primary venue, 17 above primary venue.

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
| 2026-04-19 | [OpenAI captcha refusal by mid-2026](./reasoning/2026-04-19-openai-agent-captcha-refusal.md) | 78% YES | 72.0% YES | YES | 0.048 | 0.078 | Manifold resolved YES 2026-07-23. Trust-and-safety policy-inertia call beat the market. |
| 2026-04-19 | [SSI ship AI by July](./reasoning/2026-04-19-ssi-ship-before-july-2026.md) | 5% YES | 10.0% YES | NO | 0.003 | 0.010 | Resolved NO 2026-07-01. Deliberate non-shipping strategy held through the window. |
| 2026-04-19 | [Messi plays WC26](./reasoning/2026-04-19-messi-plays-world-cup-2026.md) | 93% YES | 88.0% YES | YES | 0.005 | 0.014 | Messi played in WC26. Forecast matched Polymarket's real-money 92.5% within 0.5pp. |
| 2026-04-19 | [Starship F12 clears pad](./reasoning/2026-04-19-starship-flight-12-clears-pad.md) | 85% YES | 93.0% YES | YES | 0.023 | 0.005 | F12 cleared the pad by May 24, well before deadline. Thin-market slippage fade lost its modal outcome; loss was within the pre-committed envelope. |
| 2026-04-19 | [LLM coauthor Nature/Sci](./reasoning/2026-04-19-llm-coauthor-nature-science.md) | 8% YES | 14.0% YES | NO | 0.006 | 0.020 | Resolved NO 2026-07-02. Journal authorship-policy inertia beat narrative momentum. |
| 2026-04-19 | [Patel FBI Director June 30](./reasoning/2026-04-19-patel-fbi-director-june-30.md) | 58% YES | 49.0% YES | YES | 0.176 | 0.260 | Patel remained director. Above-Manifold loyalty-pattern move was right, but the window-adjusted Polymarket ~94%-stays would have scored 0.004 — direction right, magnitude timid. |
| 2026-04-19 | [WTI crude $150 before June](./reasoning/2026-04-19-wti-crude-150-by-june.md) | 5% YES | 20.5% YES | NO | 0.003 | 0.042 | Resolved NO 2026-06-03. Play-money tail-risk premium faded successfully; largest legacy edge relative to confidence. |
| 2026-04-26 | [Running Point S2 top US Netflix show](./reasoning/2026-04-26-running-point-netflix-top-us-show.md) | 30% YES | 92.4% YES | NO | 0.090 | 0.854 | Official Netflix source did not list `Running Point`; Polymarket resolved NO. Strong stale/source-check win. |
| 2026-04-26 | [Tottenham relegated from EPL](./reasoning/2026-04-26-tottenham-relegated-epl-2026.md) | 50% YES | 32.05% YES | NO | 0.250 | 0.103 | Spurs survived; UMA resolved NO 2026-05-24. Hugged Manifold against Polymarket on an 18.95pp spread — the book's clearest real-money loss. |
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
| 2026-05-14 | [Finland Eurovision top 5](./reasoning/2026-05-14-finland-eurovision-2026-top-5.md) | 74% YES | 90.5% YES | NO | 0.548 | 0.819 | Polymarket/UMA finalized NO; Eurovisionworld final results show Finland 6th with 279 points, just outside the top 5. NO-side favorite-overpricing fade beat the market, but the high absolute YES forecast was still badly overconfident. |
| 2026-05-15 | [Trump says "Make America Great Again" this week](./reasoning/2026-05-15-trump-say-make-america-great-again-this-week.md) | 15% YES | 33.5% YES | NO | 0.023 | 0.112 | Polymarket/UMA finalized NO. Exact-phrase/source thesis was right: `MAGA`, `We've made America great again`, Xi's `making America great again`, and written/image uses did not satisfy the verbal exact-term rule. |
| 2026-05-15 | [Hormuz transit calls May 11-May 17, 20-39](./reasoning/2026-05-15-hormuz-transit-calls-may11-may17-20-39.md) | 35% YES | 62.0% YES | NO | 0.123 | 0.384 | UMA resolved NO 2026-05-21. PortWatch chokepoint source math beat the modal-bin crowd; shortest-horizon prediction in the book. |
| 2026-05-17 | [Michael 4th weekend box office $22m-$25m](./reasoning/2026-05-17-michael-fourth-weekend-box-office-22m-25m.md) | 38% YES | 55.5% YES | NO | 0.144 | 0.308 | Polymarket/UMA finalized NO after The Numbers listed the May 15-17 weekend at $26.141m, above the $25m boundary. Friday-to-weekend multiplier / sibling `>25m` thesis beat the modal middle bracket. |
| 2026-05-18 | [MicroStrategy announces >1000 BTC purchase May 12-18](./reasoning/2026-05-18-microstrategy-btc-purchase-may12-may18.md) | 97% YES | 84.65% YES | YES | 0.001 | 0.024 | Polymarket/UMA finalized YES after Strategy's purchase page posted a May 18 row for 24,869 BTC. Saylor-chart + STRC.live size-threshold thesis resolved cleanly; the market carried too much timing/form risk. |
| 2026-05-18 | [The Deep dies in The Boys Season 5](./reasoning/2026-05-18-the-deep-dies-the-boys-season-5.md) | 88% YES | 74.5% YES | YES | 0.014 | 0.065 | UMA resolved YES 2026-05-20. Spoiler-ecology read captured a 13.5pp premium over the market. |
| 2026-05-19 | [Target Q1 comp sales below -1%](./reasoning/2026-05-19-target-q1-comparable-sales-growth-below-minus-1.md) | 30% YES | 65.5% YES | NO | 0.090 | 0.429 | UMA resolved NO 2026-05-20. Guidance-plus-revenue math faded the market's -1% read; second-largest edge capture in the real-money book. |

## Pending predictions

| Written | Market | Me | Manifold | Kalshi | Poly | Resolves | v |
|---------|--------|----|----------|--------|------|----------|---|
| 2026-04-19 | [Anthropic 60B ARR on July 6](./reasoning/2026-04-19-anthropic-60b-arr-july-2026.md) | 17% | 25% | — | — | 2026-07-06¹ | v1 |

¹ Manifold creator has not resolved despite the July 6 status date passing (checked 2026-08-05). Market has drifted to **79.5% YES vs my 17%** — if it resolves YES, Brier 0.689 vs entry 0.563, the worst score in the book. Legacy/paper-money; excluded from the real-money primary score either way.

## Lessons

- (From 2026-08-05 post-dormancy sweep) **The two largest Manifold-vs-Polymarket divergences both resolved in favor of Polymarket.** Patel (45pp spread): my above-Manifold move won, but the Polymarket-implied ~94% stays would have scored 50× better. Tottenham (19pp spread): I hugged Manifold and took the book's clearest real-money loss. Rule going forward: on material cross-venue spread, anchor to the real-money price; splitting the difference gives away most of the edge.
- (From 2026-08-05 post-dormancy sweep) Institutional-policy inertia (captcha refusal, journal authorship rules) and play-money tail premiums (WTI $150) are repeatable edge classes against Manifold. Source-math fades of modal bins (Hormuz, Target) are the repeatable edge class against Polymarket.
- (From cycle-30 enrichment) Cross-venue shadowing catches miscalibrations that single-venue reasoning doesn't. The v2 dual-shadow rule is justified even just by the Patel finding.
- (From cycle-30 enrichment) Manifold appears to overprice scandal-exit probabilities vs real-money venues. If this holds across more cases, it's a systematic bias worth exploiting.
