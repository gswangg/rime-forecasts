# Automation lessons

Lessons from wake-driven operation. When a lesson is validated, implement it in daemon filters/tests so future wakes get better.

## Validated and implemented

### CLV sign must be prediction-aligned, not raw YES movement

**Observed:** the first Running Point CLV wake reported `-1.4pp CLV` because the raw YES price moved from `92.4%` to `91.0%`. But rime's forecast was below market (`30% YES`), so a lower YES price is favorable and should be `+1.4pp` aligned CLV.

**Lesson:** CLV should answer “did the market move toward rime?” not merely “did YES go up?” Raw YES movement is still useful as a secondary field.

**Implementation:** `clv_checkpoint_due` payloads now include prediction-aligned `clvPp`, `rawYesMovePp`, and `clvDirection`. Ledger entries use aligned CLV and note raw YES movement when sign confusion is likely.

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

### Generic team-match sports need a model edge, not just fast resolution

**Observed:** first the Argentine soccer 1X2 cluster woke and skipped; after volume/spread filters, a high-volume Southampton vs Ipswich draw market woke and skipped for the same reason. These markets are fast, liquid enough, and mechanically clean, but without a team model or specific information they are not a rime advantage area.

**Lesson:** short resolution is not enough. Generic team-vs-team win/draw markets should not wake the model unless a future sports model/cross-venue signal explicitly opts them in.

**Implementation:** Polymarket candidate filtering excludes generic team match questions matching `Will <team> vs. <team> end in a draw?` and `Will <team> win on <date>?`.

### Individual weather range bins need a forecast-aware model

**Observed:** Dallas Apr 28 `82–83°F` woke and skipped after NWS forecast/grid showed a high around 88°F. Chengdu Apr 28 `24°C` then woke as the same class of candidate: individual temperature bin, low-ish price, no sibling-bin distribution in the payload. Taipei Apr 28 `34°C or higher` later showed the same class again with threshold wording the first regex missed.

**Lesson:** weather can be a good fast-feedback domain, but waking individual range bins without fetching forecasts and sibling prices just asks the model to do ad hoc weather modeling. The daemon should either group/score the full city/date distribution or not wake these bins.

**Implementation:** Polymarket candidate filtering excludes highest-temperature range/exact/threshold questions matching `Will the highest temperature in <place> be between <range> on <date>?`, `Will the highest temperature in <place> be <temp>°C/°F on <date>?`, and `Will the highest temperature in <place> be <temp>°C/°F or higher/lower on <date>?` until a forecast-aware sibling-bin model exists.

### Mutually-exclusive event clusters should wake once with siblings

**Observed:** the Elon Musk tweet-count event emitted adjacent range-bin wakes (`180-199`, then `200-219`) from the same Polymarket event. Evaluating bins one-by-one duplicated source work and hid the fact that the real question was the full event distribution.

**Lesson:** high-volume mutually-exclusive clusters should be reviewed as a cluster, not as independent candidate wakes.

**Implementation:** Polymarket candidate generation now groups markets by Gamma event slug / negative-risk group, emits at most one candidate wake per group, records group-level dedupe state, and includes sibling market payloads in the wake event.

## Pending / watchlist

### Kalshi category quality

Kalshi's public feed includes many multi-leg MVE/parlay markets with poor/no pricing. If actionable-spread filtering is insufficient, explicitly downrank or filter `KXMVE*` tickers unless they have real bid/ask, volume, and a clean resolution rule.
