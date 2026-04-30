# Tesla high $390 week of Apr 27 — resolves 2026-05-01

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/will-tsla-reach-390-by-april-27-2026
**Polymarket market slug**: will-tsla-reach-390-by-april-27-2026
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-30T17:36:49+00:00
**Prediction**: 40% YES
**Primary venue price at writing**: 23.5% YES (best bid 20.0%, best ask 27.0%; last trade 21.0%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +16.5pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether Tesla, Inc. (TSLA) hits a 1-minute regular-trading-hours **High** of **$390 or higher** during the week of April 27, 2026.

Resolution source is Pyth 1-minute candle highs for `Equity.US.TSLA/USD`. Only regular trading hours count; pre-market and after-hours prices do not qualify.

At writing, Yahoo 1-minute data as a proxy showed TSLA around **$379.23** at 2026-04-30 13:38 ET. The RTH high so far this week was about **$382.76** on Apr 24, with Apr 30's RTH high about **$380.12**. The market therefore needs roughly a **+2.8%** move from spot to print $390 before Friday close.

Sibling Polymarket prices checked at writing:

- LOW $337.50: 2.7% YES
- HIGH $390: 23.5% YES
- HIGH $412.50: 3.1% YES
- HIGH $420: 2.3% YES

## Base rate

A +2.8% high-print in roughly the remaining 1.1 trading days is not the same as closing +2.8%. TSLA only has to spike intraday. The current setup already had a sharp Apr 30 rebound off a 10:09 ET low near $368.17 to $379+, so the path to $390 is a continuation of same-day volatility, not a full fresh regime break.

I used recent TSLA 5-minute Yahoo RTH data as a proxy for state-conditioned future highs. For pseudo-current windows around midday with roughly the same remaining trading time, the empirical probability that the future high exceeded the current price by at least the required **~2.84%** was:

- all midday windows: **36.8%**
- windows where the stock was up 1%+ vs prior close: **46.5%**
- windows rebounded 2%+ from the intraday low: **47.3%**
- up 1%+ and rebounded 2%+ from low: **52.8%**
- a tighter current-ish filter (up 1-3%, rebounded 2%+, still off high): **44.2%**

Those are overlapping samples and Yahoo is only a proxy for Pyth, so I discount them. But the broad message is stable: a $390 high is not a 20%-ish tail from this live state.

## Where I differ from base rate (and why)

I am at **40% YES**, above Polymarket's 23.5%.

The market seems to be treating $390 as if it requires a large directional close move. It does not. TSLA is already near $379, has traded in a ~12-point RTH range today, and only needs about another $10.8 intraday. In TSLA terms, that is live in a remaining Thursday afternoon plus Friday session.

The reason I am not higher than 40-45% is that the market's caution is partly justified:

- $390 has not printed in RTH this week; the best RTH proxy high is still only ~$382.8.
- Today's rebound may already reflect the easy mean reversion off the morning low.
- The broader high-strike sibling prices imply traders do not expect a full upside breakout.
- Pyth/Yahoo candle differences can matter near the threshold.

Still, the live state and recent high-volatility analogs make a 23.5% midpoint too low.

## What would change my mind

Signals that would move me down:

- TSLA stalls below $380 into the Apr 30 close.
- Friday opens weak or below ~$375.
- The $390 book stays offered below 25% despite TSLA grinding upward, suggesting informed resistance near the threshold.

Signals that would move me up:

- TSLA retakes $382-384 before the Apr 30 close.
- Any intraday momentum / short-covering burst pushes the stock into the high $380s.
- Adjacent $412.50/$420 bins remain cheap while $390 stays under 30%, implying the market still underprices a modest high print rather than a breakout.

## Economics at this edge

At 40% true probability versus a 23.5% Polymarket midpoint, the pre-friction edge is **+16.5pp**. The executable ask was about **27%**, so buying YES still leaves roughly **+13pp** of gross edge if the estimate is right.

The book is wide but not unusable (20% bid / 27% ask, ~$7.5k single-market liquidity, substantial event liquidity). The risk is threshold volatility and source precision, not microstructure alone.

---

*(Resolution section added below after the market resolves. The above is frozen.)*
