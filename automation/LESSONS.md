# Automation lessons

Lessons from wake-driven operation. When a lesson is validated, implement it in daemon filters/tests so future wakes get better.

## Validated and implemented

### Candidate must be economically actionable

**Observed:** `rime-kalshi-candidate-found-KXMVESPORTSMULTIGAMEEXTENDED...` woke on a multi-leg Kalshi sports parlay with `yesBid=0.0`, `yesAsk=1.0`, and stale `lastPrice=0.098`.

**Lesson:** last trade alone is not enough. Candidate markets need an actionable bid/ask.

**Implementation:** require bid and ask to be present, inside `(0, 1)`, ordered, and spread ≤ 20pp for Kalshi; ≤ 10pp for Polymarket.

### Displayed liquidity alone is not enough

**Observed:** the Argentine soccer 1X2 cluster woke three events with displayed Polymarket liquidity around `$70k`, but actual volume was `0`, `$135`, and `$2`.

**Lesson:** displayed liquidity can be passive LP inventory and does not imply market information or worth a model turn.

**Implementation:** require real volume ≥ `$1k` before candidate emission, in addition to the existing liquidity/volume mechanical gate.

### Near-certain tails are usually not useful candidate wakes

**Observed:** BOJ 50+ bps (`0.15%` YES), BOJ no-change (`98.7%` YES), and US-Iran meeting (`2.8%` YES) all resolved to quick skips. None had a plausible 10pp edge without specific outside information.

**Lesson:** markets below 5% or above 95% mostly wake us for “yes, market agrees with base rate.”

**Implementation:** candidate wakes require `5% ≤ YES price ≤ 95%`. Watched-market CLV/resolution events are unaffected.

## Pending / watchlist

### Cluster suppression

Multiple mutually exclusive markets from the same event can wake back-to-back. The soccer 1X2 cluster was mostly fixed by the volume floor, but high-volume clusters may still spam. If this repeats, group candidates by Polymarket event slug and emit at most one event per event per poll, with payload listing sibling markets.

### Niche filter for generic sports

Short-term sports markets offer fast resolution, but without a model or special information they are mostly efficient. If high-volume generic match/player-prop markets keep waking and skipping, add a soft filter or lower priority for generic sports unless cross-venue spread or unusual market structure is present.

### Kalshi category quality

Kalshi's public feed includes many multi-leg MVE/parlay markets with poor/no pricing. If actionable-spread filtering is insufficient, explicitly downrank or filter `KXMVE*` tickers unless they have real bid/ask, volume, and a clean resolution rule.
