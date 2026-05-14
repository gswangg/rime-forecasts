# Cerebras IPO market cap < $50B at close — resolves 2026-05-14

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/will-cerebras-market-cap-be-less-than-50b-at-market-close-on-ipo-day
**Polymarket market slug**: will-cerebras-market-cap-be-less-than-50b-at-market-close-on-ipo-day
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: sibling bracket markets only
- Manifold: n/a
**Written**: 2026-05-14T13:22:35+00:00
**Prediction**: 35% YES
**Primary venue price at writing**: 3.15% YES (best bid 2.8%, best ask 3.5%; last trade 2.6%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +31.85pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether Cerebras Systems' market capitalization is **less than $50B** at the closing price on its first day of trading.

The market description says market capitalization is calculated as the **total number of outstanding shares multiplied by the official closing share price** of the publicly traded class on the first trading day. It also says that, where needed, all outstanding share classes should be included with conversion ratios to the publicly traded class. The primary sources are official company filings and the primary exchange's official listing page.

## Source state

Cerebras announced on May 13 that it priced its IPO at **$185.00/share**, selling **30,000,000 Class A shares**, with Nasdaq trading expected to begin May 14 under `CBRS`.

The May 11 S-1/A filing gives the share-count mechanics:

- Class A common stock outstanding immediately after the offering: **30,000,000** shares.
- Class B common stock outstanding immediately after the offering: **185,228,541** shares.
- Class N common stock: **none**.
- Total Class A + Class B + Class N outstanding after the offering: **215,228,541** shares, or **219,728,541** if the underwriters exercise the over-allotment option in full.
- The same section explicitly excludes stock options, RSUs, and other potentially issuable shares from this outstanding-share count.

At the $185 IPO price, that basic outstanding-share market cap is:

- **$39.82B** using 215.228541M shares.
- **$40.65B** if the full over-allotment count were included.

StockAnalysis is currently showing the same basic setup: **215.23M shares out** and **$39.82B market cap** at the $185 IPO price.

Therefore the `less than $50B` threshold is not a stock-price crash threshold under the contract wording. It requires the stock to close below roughly:

- **$232.31** with 215.228541M shares.
- **$227.55** with 219.728541M shares.

That is about a **+25.6%** first-day close above IPO price before the market resolves NO under the non-greenshoe count.

## Where I differ from the market

The market is pricing `<$50B` around **3%**. That looks like traders are using media-reported **fully diluted valuation**. Reuters/CNBC-style coverage says the $185 IPO price implies about **$56.4B fully diluted valuation**. If the market resolved on that number, `<$50B` would require a close below about $164, an 11%+ drop from the IPO price, and the 3% price would make sense.

But the Polymarket description does not say fully diluted valuation. It says **outstanding shares**, and then gives an explicit outstanding-share calculation standard using official filings. The official filing's outstanding count is around 215.2M shares and excludes options/RSUs/potential shares. That makes the $50B line a **$232-ish close threshold**, not a $164-ish threshold.

Cerebras is clearly a hot IPO: the range was raised, final pricing came above the marketed range, the order book was reported heavily oversubscribed, and AI infrastructure demand is the dominant IPO narrative. A first-day close above $232 is very possible. It only requires a 25-26% close pop, and comparable hot AI/chip listings can clear that. This keeps me far below 50%.

Still, 3% is too low if the rules use basic outstanding market cap. There are two distinct ways YES wins:

1. The stock opens/pops but closes below roughly $232.
2. The market adjudicates according to the explicit outstanding-share language rather than media fully diluted valuation.

My forecast: **35% YES**.

This is mostly a rule/source-arbitrage thesis, not a bearish view on the IPO.

## What would change my mind

Signals that would move me down:

- Nasdaq first trade / opening indication above **$235** with stable demand rather than a transient opening imbalance.
- Polymarket/UMA guidance that `market cap` here will use fully diluted valuation despite the outstanding-share wording.
- Official final prospectus language changing the post-offering outstanding share count materially above the S-1/A count.
- Confirmation that nominal/exercisable warrants are being counted as outstanding for the market-cap calculation.

Signals that would move me up:

- First trade below **$220**, or early trading below the $227-$232 threshold.
- Nasdaq / common finance pages displaying basic market cap below $50B using ~215M shares.
- Explicit resolution discussion citing the S-1/A outstanding-share table.

## Economics at this edge

At 35% true probability versus a 3.15% Polymarket midpoint, the edge is **+31.85pp** on YES.

The executable ask was about **3.5c**, so even after the spread the gross edge is enormous if the outstanding-share interpretation is correct. Liquidity is adequate for the experiment, though not large.

The main risk is not economics or spread. It is adjudication: if the market resolves on fully diluted valuation or includes a broad set of warrants/options/RSUs despite the wording, the apparent edge mostly disappears.

---

*(Resolution section added below after the market resolves, never editing above.)*
