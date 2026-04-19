# WTI crude oil cost more than $150/barrel before June 2026 — resolves 2026-05-31

**Manifold URL**: https://manifold.markets/SaviorofPlant/will-wti-crude-oil-cost-more-than-1
**Kalshi URL**: no equivalent (searched events API, no active WTI price-target series)
**Polymarket URL**: no equivalent (no active oil-price-threshold market)
**Written**: 2026-04-19T22:55:00+00:00
**Prediction**: 5%
**Manifold price at writing**: 20.5%
**Kalshi price at writing**: n/a
**Polymarket price at writing**: n/a
**Edge vs Manifold**: −15.5pp
**Edge vs Kalshi**: n/a
**Edge vs Polymarket**: n/a
**Confidence**: 4/5

**Cross-venue note:** Manifold-only signal. Neither Kalshi nor Polymarket lists an equivalent WTI price-target market. This downgrades the trading-relevance of the prediction per v2 rules — it's usable for calibration research, but the edge cannot be directly monetized on a real-money venue.

## Market question

> Will WTI crude oil cost more than $150/barrel before June? (According to investing.com)

Resolution source: investing.com WTI crude futures price (https://www.investing.com/commodities/crude-oil). Close 2026-05-31. I read "cost more than $150" liberally — any print (intraday or close) above $150 between market creation and May 31, 2026 resolves YES.

## Base rate

Reference class: WTI crude oil hitting new all-time highs in a 42-day window.

Historical context:
- WTI all-time high (closing): **~$133** in July 2008.
- WTI all-time high (intraday): **~$147.27** in July 2008.
- $150 has **never been breached** in WTI's 40+ year history on NYMEX.
- Current price (April 17, 2026 close): **$82.59**.
- 30-day high (April 7, 2026): **$112.95**.
- 52-week high: **$119.48**.

For the market to resolve YES, WTI must:
1. Move from ~$82 to >$150 — a **+82% move**.
2. Do so in **~42 calendar days** (~30 trading days).
3. Exceed the all-time intraday high by ~2%.

Reference class of "WTI +80% in 42 days from current level": I can think of zero historical analogs. The closest precedents:

- **2022 Russia invasion shock:** WTI went from $91 (Feb 23) to $130 (March 8) in ~2 weeks — a **43% move**. Supply shock plus geopolitical panic. Not enough to hit $150.
- **2008 summer peak:** WTI climbed from $90 (March 2008) to $147 (July 2008) in ~4 months — **63% over 120 days**, driven by demand growth + speculative bubble. Even that rate of climb, applied to 42 days, gives us +22% — WTI to ~$100, not $150.
- **1990 Gulf War I:** WTI spiked ~100% over ~6 weeks (from $16 to $32). Scale-normalized, that's the closest magnitude analog. Required the most disruptive Middle East event in a generation.

Base-rate estimate: **2–5%**, heavily weighted toward NO. A +82% move to a never-before-seen price in 42 days requires a geopolitical/supply event of the most severe magnitude in modern oil market history — something like an extended physical closure of the Strait of Hormuz, simultaneous Saudi output disruption, or US-Iran full military engagement with attacks on infrastructure.

## Where I differ from base rate (and why)

I am at **5%**, 15.5pp below the market's 20.5%.

The market is pricing ~1-in-5 odds of a historic-high oil spike. That's wildly above the base-rate class. Specific reasons I think the market is overpricing:

1. **$150 is a never-reached threshold.** Even the 2008 commodity bubble topped out near $147 intraday. Markets tend to over-respect round numbers ("$150") because they sound achievable — "we've seen $119, just a bit more to $150." But the gap between $119 (52w high) and $150 is 26%, and the gap from $82 (current) to $150 is 82%. These are structurally different events.

2. **Current macro context dampens upside.** Global oil demand is softening (China slowdown, EV adoption, efficiency gains). OPEC+ has 2–3 million barrels/day of spare capacity that can be deployed within weeks in response to supply shock. Saudi Arabia publicly stated in Q1 2026 its willingness to offset any Iranian disruption. These conditions materially suppress upside.

3. **Iran tension is already priced in.** The late March / early April spike to ~$113 was the Iran-premium bake. That's roughly 30% above the fundamental clearing price. For WTI to go from $113 (max recent premium) to $150, you'd need another 32% escalation beyond what the current Iran situation provides — Iran-US active shooting war, multi-week Hormuz closure that actually holds, multiple tanker attacks. These are tail events *on top of* already-elevated Iran risk.

4. **Market bettors may be anchoring on "touch $150 intraday vs close."** The question says "cost more than $150" which includes intraday prints. This opens a small path to YES via a momentary panic-buy spike. Still, hitting $150 intraday requires actual demand-side buying at that price, not just a quote — which means the clearing event has to be severe, not cosmetic. My 5% reflects this residual intraday-spike path.

5. **Manifold bettors on price-target markets have a weak track record.** Manifold has a known pattern of mispricing tail-event price targets (bettors like round-number milestones and overprice them). This is qualitative but a consistent observation across BTC, stock, and commodity markets.

Base rate 2–5%; I pick **5%** to leave room for genuine geopolitical tail (Iranian regime collapse with attempted Hormuz closure, or Saudi infrastructure attack that disables more capacity than expected, or broader Middle East war). Anything below 3% feels overconfident given I cannot rule out a supply shock.

## What would change my mind

Evidence that would move me toward YES (higher probability):

- WTI breaks $120 intraday. Signals momentum into historic-high territory.
- Iran actually closes Strait of Hormuz physically (not just rhetoric), sustained >72 hours. Would likely send oil to $130–150 quickly.
- Saudi infrastructure attack (refinery, pipeline, processing facility).
- Multi-country tanker attacks in Gulf with confirmed production losses.
- OPEC+ rejection of output increase during the crisis (unlikely but possible).
- US military action against Iran that disables Iranian production long-term.

Evidence that would strengthen NO:

- WTI stays in $80–100 range into May with no escalation.
- Iran-US de-escalation announcements.
- OPEC+ signals output increase.
- China demand data remains soft.
- Equity market signals risk-on environment (correlates with oil demand comfort).

## Economics at this edge

Given the 15.5pp Manifold edge and 4/5 confidence:

- Per $1 Manifold notional: expected value if true prob is 5% vs market 20.5% = $0.155.
- After typical Kalshi/Polymarket spread (2.5pp): net edge would be ~13pp → $0.13 per $1.
- **But there's no real-money venue** — this edge can't be monetized currently.
- If Kalshi or Polymarket list this market before resolution, flag for update.

This is the kind of prediction that would be taken aggressively if a real-money venue were available. The edge is large, confidence is high, and the asymmetric payoff (small stake, NO direction likely) is classic tail-bet territory. Pure calibration data for now.

---

*(Resolution section added below after market resolves on 2026-05-31. The above is frozen.)*
