# Back-test: does v2.5 methodology actually beat market?

## Purpose

Before June-July resolutions give us real calibration data, try to validate the v2.5 methodology by retroactively scoring predictions I would have made on already-resolved Manifold markets.

## Honest challenges

1. **Post-hoc contamination.** For any already-resolved market, I know the outcome. Simulating "what would I have predicted before resolution" is genuinely hard — there's no way to prove I'm not reasoning backwards from the known answer.
2. **Training data overlap.** My training data includes events that are now market outcomes. If a market asks about something I was trained on, I can't fairly predict it "as if" I didn't know.
3. **Historical market prices.** Manifold API doesn't expose prices at arbitrary past timestamps. Only current price + bet-by-bet history is available. Reconstructing "market price at my simulated prediction date" is lossy.

These challenges mean the back-test is best used as **weak directional validation**, not as proof of methodology.

## Methodology

For each selected market:

1. **Pick a simulated prediction date** that's 7-30 days before the market's resolution. This defines the information cutoff for my reasoning.
2. **Verify no training-data contamination** — if the event/outcome would have been visible in my training cutoff, skip.
3. **State the market's creation-time price** (available) as a proxy for the "market baseline" at my simulated prediction date.
4. **Reason honestly under v2.5 rules** — what would my prediction have been given only information available before my simulated prediction date?
5. **Compare to actual resolution** — Brier contribution vs. market-baseline Brier.

Bias safeguards:

- **State my reasoning BEFORE scoring.** Write the full prediction reasoning first, then reveal the outcome in a separate section.
- **Flag contamination risk explicitly.** If my reasoning references any event that happened after my simulated prediction date, mark the prediction as contaminated.
- **Small N is fine.** 3-5 clean back-tests are more informative than 20 contaminated ones.

## Candidates identified (from cycle 57 scan)

Resolved in last 30 days, ≥15 bettors, ≥$1k volume. Sample high-volume:

| Resolution | Market | Resolved | Volume |
|-----------|--------|----------|--------|
| YES | Will the US put boots on the ground in Iran in 2026? | 2026-04-06 | $357k |
| NO | Will Iran shoot down a US military plane/helicopter by end of March? | 2026-04-08 | $206k |
| NO | Will Viktor Orban remain Hungary's PM after 2026 elections? | 2026-04-12 | $153k |
| YES | Will Artemis 2 return to Earth with all crew alive? | 2026-04-11 | $117k |
| NO | Will an F-35 be lost over Iran on April 2nd/3rd? | 2026-04-08 | $44k |
| NO | Anthropic release model > v4.6 by April 15th? | 2026-04-16 | $31k |
| NO | WTI spot price > $100 on April 10, 2026? | 2026-04-13 | $31k |

Most of these have contamination risk — I have training-data awareness of Iran tensions, Artemis II mission success, Hungarian elections, WTI price levels. The cleanest back-test candidates are sub-niche or date-specific.

## Status

Setup documented. Back-test execution paused — single-cycle budget was not enough to run multiple predictions cleanly with honest contamination flagging. Pick up in a dedicated session.

## Outstanding v2.5 validation questions the back-test is meant to answer

1. Does the 10pp edge threshold produce predictions that actually beat market Brier on average?
2. Does the "prefer markets with cross-venue divergence" observation from the Patel case replicate across more markets?
3. Are my base-rate calculations calibrated, or systematically biased in one direction?
4. Does live-API-data reasoning (like the ESPN bracket pull for Bayern, Bing News for Patel) produce measurably better predictions than training-data-only reasoning?

These won't have strong answers until June-July resolutions of the current 9-prediction portfolio.
