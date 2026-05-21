# NVDA Q1 FY27 earnings reaction — direction call

- **Date written:** 2026-05-20 (post-print, pre-open 2026-05-21)
- **Underlying:** NVDA
- **Spot at write:** $223.67 (Tradier mid, 2026-05-20 19:52 UTC close)
- **Pre-print May 22 ATM straddle:** ~$13 → implied ±5.8% one-day move
- **Direction call:** up
- **Magnitude (base case, next session):** +7% to +12%
- **Confidence:** 4/5

This is a prediction-market-style direction call, not a trade. No paper ticket, no live order. It is logged for calibration only and does not enter `scorecard.md` because there is no Polymarket/Kalshi binary baseline.

## Actuals (Q1 FY27)

| metric | Q1 FY27 | Q4 FY26 | Q/Q | Y/Y |
|---|---:|---:|---:|---:|
| Revenue | $81.6B | $68.1B | +20% | +85% |
| Non-GAAP GM | 75.0% | 75.1% | -0.1pt | +14.2pt |
| GAAP EPS | $2.39 | $1.76 | +36% | +214% |
| Non-GAAP EPS | $1.87 | $1.59 | +18% | +140% |
| Data Center | $75.2B | — | +21% | +92% |
| DC compute | $60.4B | — | +18% | +77% |
| DC networking | $14.8B | — | +35% | +199% |
| Edge | $6.4B | — | +10% | +29% |

## Guide (Q2 FY27)

- Revenue: $91.0B ± 2% (implies ~+11.5% Q/Q sequential growth)
- Gross margin: 75.0% (stable)
- Explicitly **excludes** any Data Center compute revenue from China
- $80B incremental buyback authorization on top of $38.5B remaining
- Quarterly dividend raised from $0.01 to $0.25 (25x)

## Mechanism

1. Revenue beat of approximately $7B vs. likely consensus (~10% surprise).
2. Guide beat of approximately $10B vs. likely consensus (~12% surprise) and excludes China.
3. Gross margin held at 75% — no AI-capex digestion or pricing concession.
4. Networking accelerated to +199% Y/Y / +35% Q/Q, which is the pure scale-out cluster arms-race thesis turning into reported revenue rather than narrative.
5. $118.5B total buyback authorization plus a 25x dividend hike is unusual capital-return signaling for a name that has been criticized as a capex sponge.
6. Vera Rubin platform, BlueField-4, and Dynamo 1.0 give a visible forward product cycle.

## What would cut against this call

- Buy-the-rumor / sell-the-news mechanics if the stock was over-positioned into the print.
- Positioning crowd-out from systematic vol-target deleveraging on a large gap.
- Macro/rates/risk-off shock unrelated to the print.
- Specific China policy escalation (the guide already excludes China, but new tariffs or export controls could still hit sentiment).
- Networking growth being interpreted as one-off ramp rather than sustained.

## Implications for SA thesis fixtures

- **NVDA up Jun18 $250 (active):** well positioned. Spot path from $223.67 toward $235-$245 makes $250 by 2026-06-18 expiry materially more reachable. Pre-print best near-pass was the 245/250 call debit vertical (edge 0.286 vs 0.300, probability margin 0.060 vs 0.080). Post-print IV crush plus spot move should reprice the structure and may cross gates.
- **PLTR up Jun18 (active):** modest tailwind via sovereign AI demand correlation, not a direct read-through.
- **CORZ up Jun18 (active):** AI compute scarcity narrative reinforced; modest indirect tailwind.
- **SMH down (watch):** NVDA is a large SMH weight. The SMH downside thesis becomes harder if NVDA gaps up.
- **ANET, AVGO, MRVL:** networking +199% Y/Y is a strong read-through.
- **VRT, GEV, CEG, BE, ETN:** unbroken AI capex reinforces the power/cooling/grid leg.
- **MU, SNDK, WDC, STX:** indirect tailwind via HBM/storage demand.

## Operating note

No live orders. No paper tickets created from this analysis. Existing active thesis fixtures remain in place. The options daemon should:

- emit `options_thesis_refresh_due` for the NVDA fixture once spot moves >= 8% from the last recorded thesis-refresh baseline ($223.99 at restart);
- emit `options_signal_candidate` only if a generated structure clears edge / probability / reward-risk gates after the repriced chain is fetched.

Both outcomes will be reviewed on their own wakes.
