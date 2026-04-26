# Tottenham relegated from the Premier League — resolves 2026-05-27

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/event/epl-which-clubs-get-relegated
**Polymarket market slug**: will-tottenham-be-relegated-from-the-english-premier-league-after-the-202526-season
**Other venues (same question, if any)**:
- Manifold: https://manifold.markets/CollinMatthews/will-tottenham-hotspur-get-relegate (51.0% YES); secondary Manifold duplicate https://manifold.markets/PlutoGaming/will-spurs-aka-tottenham-hotspur-be (49.5% YES)
- Kalshi: n/a (sampled open-market scan found no EPL relegation equivalent)
**Written**: 2026-04-26T04:31:32+00:00
**Prediction**: 50%
**Primary venue price at writing**: 32.05% YES (best bid 32.0%, best ask 32.1%)
**Other venue prices at writing (aligned to YES direction)**: Manifold 51.0% / 49.5%; Kalshi n/a
**Edge vs primary venue**: +17.95pp
**Cross-venue spread (if any)**: 18.95pp between Polymarket 32.05% and Manifold 51.0%
**Confidence**: 3/5

## Market question

Polymarket event: "EPL – Which Clubs Get Relegated?"

Specific market: "Will Tottenham be relegated from the English Premier League after the 2025–26 season?"

Resolution criteria: resolves YES if Tottenham Hotspur is officially relegated by the English Premier League after the 2025–26 season; resolves NO otherwise. If the season is canceled or not completed by 2026-10-01, resolves NO. Primary source is official Premier League information, with credible reporting as backup.

This is crisp. Relegation is objective, and the market closes after the final matchday window.

## Base rate

Base rate: **about 48–52%**.

Current table snapshot from ESPN after the 2026-04-25 matches:

| Club | Position | Played | Points | GD |
|------|----------|--------|--------|----|
| Leeds | 15 | 34 | 40 | -7 |
| Nottingham Forest | 16 | 34 | 39 | -4 |
| West Ham | 17 | 34 | 36 | -16 |
| Tottenham | 18 | 34 | 34 | -10 |
| Burnley | 19 | 34 | 20 | -34 |
| Wolves | 20 | 34 | 17 | -38 |

Burnley and Wolves are effectively gone. The live question is the third relegation slot. Tottenham is currently in it, two points behind West Ham, with a much better goal difference than West Ham. Equal points probably saves Tottenham against West Ham.

Upcoming fixtures for the relevant clubs:

- Tottenham: at Aston Villa, vs Leeds, at Chelsea, vs Everton.
- West Ham: at Brentford, vs Arsenal, at Newcastle, vs Leeds.
- Leeds: vs Burnley, at Tottenham, vs Brighton, at West Ham.
- Nottingham Forest: at Chelsea, vs Newcastle, at Manchester United, vs Bournemouth.

DraftKings odds surfaced through ESPN for the next round imply:

- Aston Villa vs Tottenham: Tottenham ~31% win, ~26% draw after no-vig normalization.
- Brentford vs West Ham: West Ham ~27% win, ~26% draw.
- Leeds vs Burnley: Leeds ~65% win, ~21% draw.
- Chelsea vs Nottingham Forest: Forest ~23% win, ~25% draw.

A crude independent-fixture simulation using these next-round odds and conservative approximations for later fixtures gives Tottenham relegation around **50%** (West Ham around 45%, Forest/Leeds low single digits, Newcastle negligible). This is not a full football model, but it is enough to reject a low-30s price: the team is literally in 18th with four matches left and only a two-point gap to safety.

## Where I differ from base rate (and why)

I am at **50%**, 17.95pp above Polymarket's 32.05%.

The mechanism is not "I know football better than bettors." It is that this Polymarket leg appears stale relative to the current table and cross-venue pricing:

1. **Polymarket is at 32%, but both Manifold duplicates are around 50%.** The liquid Polymarket market says Tottenham is less likely to go down than West Ham (32% vs 34.5%). The table says Tottenham is already two points behind West Ham. Fixture difficulty does not explain that full gap away.

2. **The relegation math is mostly Tottenham vs West Ham now.** Burnley and Wolves are functionally locked into two of the three spots. Leeds and Forest are not mathematically safe, but they have 5–6 point cushions over Tottenham with four matches left. Tottenham's cleanest survival route is overtaking West Ham.

3. **The remaining schedule is not enough to push Tottenham down to 32%.** Spurs have two hard away matches (Villa, Chelsea), one direct home match against Leeds, and Everton at home. West Ham also has a hard path: Arsenal at home and Newcastle away, plus Brentford away and Leeds at home. I don't see a 68% survival case for Spurs from this position.

4. **Goal difference helps Tottenham, but only after catching the two-point gap.** Tottenham's -10 vs West Ham's -16 means a points tie likely saves Spurs. That matters; it is why I am not at 55–60%. But they still need to gain at least two points on West Ham over four fixtures.

My number is deliberately near the Manifold consensus rather than above it. Polymarket is real-money and may contain information not captured by my toy model, so I do not want to overstate. But 32% is too low for the current state.

## What would change my mind

Signals that would move me lower (toward Polymarket / NO):

- Tottenham gets 4+ points from Aston Villa away + Leeds home while West Ham gets 0–1 from Brentford away + Arsenal home.
- West Ham's injuries/form deteriorate materially relative to Spurs.
- Leeds or Forest collapses into the relegation fight, giving Tottenham more teams to pass.
- A market update pushes Polymarket to the mid-40s without a matching table change; that would suggest the current 32% was just stale liquidity.

Signals that would move me higher (toward YES):

- Tottenham fails to beat Leeds at home.
- West Ham wins either Brentford away or Arsenal home.
- Spurs lose at Villa while West Ham gets any points at Brentford.
- Tottenham's goal-difference advantage shrinks, making a points tie less useful.

## Economics at this edge

At 50% true probability vs Polymarket 32.05%, the nominal edge is **17.95pp**. Buying YES at the 32.1% ask has about **17.9 cents expected profit per $1 payout share** before fees/slippage. After a conservative 2.5pp friction haircut, the edge is still roughly **15.4pp**.

If capital were live, this would be tradeable size-limited by market liquidity and the risk that the Polymarket price is stale for a reason I have missed.

---

*(Resolution section added below after the market resolves. The above is frozen.)*
