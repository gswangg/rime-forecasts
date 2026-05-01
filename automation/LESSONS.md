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

**Observed:** first the Argentine soccer 1X2 cluster woke and skipped; after volume/spread filters, a high-volume Southampton vs Ipswich draw market woke and skipped for the same reason. Later, a PSG vs Bayern `Both Teams to Score` market woke as the same class. Atlético Madrid vs Arsenal exact-score bins then woke as another generic team-match derivative. A Rockets NBA playoff advancement market also woke, but active sportsbook series odds matched Polymarket almost exactly. BLAST Rivals esports MVP/winner/finalist wakes also required ad hoc team/player modeling and produced no clear edge.

**Lesson:** short resolution is not enough. Generic team-vs-team win/draw/BTTS/exact-score/series-advancement/tournament-winner/finalist markets should not wake the model unless a future sports/esports model or cross-venue signal explicitly opts them in.

**Implementation:** Polymarket candidate filtering excludes generic team match questions matching `Will <team> vs. <team> end in a draw?`, `Will <team> win on <date>?`, `<team> vs. <team>: Both Teams to Score`, `Exact Score: <team> <score> - <score> <team>?`, NBA playoff `Will <team> advance to the Conference Semifinals...` markets, and common esports tournament-winner/finalist questions like `Will <team> win BLAST ... 20XX?` and `Will <team> make it to the BLAST ... Grand Final?`.

### Individual weather range bins need a forecast-aware model

**Observed:** Dallas Apr 28 `82–83°F` woke and skipped after NWS forecast/grid showed a high around 88°F. Chengdu Apr 28 `24°C` then woke as the same class of candidate: individual temperature bin, low-ish price, no sibling-bin distribution in the payload. Taipei Apr 28 `34°C or higher` later showed the same class again with threshold wording the first regex missed. Seattle April precipitation `2.5–3 inches` later woke as the same weather-bin class: actual/forecast checks make the market plausible, but not a clean edge without a systematic sibling-bin weather model.

**Lesson:** weather can be a good fast-feedback domain, but waking individual range bins without fetching forecasts and sibling prices just asks the model to do ad hoc weather modeling. The daemon should either group/score the full city/date distribution or not wake these bins.

**Implementation:** Polymarket candidate filtering excludes highest-temperature range/exact/threshold questions matching `Will the highest temperature in <place> be between <range> on <date>?`, `Will the highest temperature in <place> be <temp>°C/°F on <date>?`, and `Will the highest temperature in <place> be <temp>°C/°F or higher/lower on <date>?`, plus monthly precipitation range/threshold bins such as `Will <place> have between <low> and <high> inches of precipitation in <month>?`, until a forecast-aware sibling-bin model exists.

### Mutually-exclusive event clusters should wake once with siblings

**Observed:** the Elon Musk tweet-count event emitted adjacent range-bin wakes (`180-199`, then `200-219`) from the same Polymarket event. Evaluating bins one-by-one duplicated source work and hid the fact that the real question was the full event distribution.

**Lesson:** high-volume mutually-exclusive clusters should be reviewed as a cluster, not as independent candidate wakes.

**Implementation:** Polymarket candidate generation now groups markets by Gamma event slug / negative-risk group, emits at most one candidate wake per group, records group-level dedupe state, and includes sibling market payloads in the wake event.

### Crypto price bins need a volatility/options model

**Observed:** Bitcoin Apr 28 above `$76k` and Ethereum Apr 28 above `$2,400` both woke as clean, liquid, short-horizon candidates. Then Bitcoin `$80k-$82k` woke as the same class with range wording. Spot/sibling-price checks put each market roughly in line with ordinary one-day crypto volatility; without an options-implied distribution or systematic vol model, the review was just ad hoc market-making.

**Lesson:** daily crypto threshold/range bins are liquid and fast, but not automatically rime edge. Waking individual thresholds or ranges without a volatility/options-aware model burns turns on efficient markets.

**Implementation:** Polymarket candidate filtering excludes individual crypto price threshold/range questions such as `Will the price of Bitcoin/Ethereum be above $X on <date>?`, `between $X and $Y`, `greater than $X`, and `less than $X` until a volatility/options model is added.

### Election winner markets can have close dates that are not resolution dates

**Observed:** West Bengal Legislative Assembly election winner woke as a `1.1d` primary candidate because Polymarket's `endDate` was Apr 29. The market description says results may remain unknown until Oct 31, and event context described Apr 29 as another polling phase, not final resolution. This is not fast feedback despite a near `endDate`.

**Lesson:** election-result markets often use `endDate` as trading close / election phase timing. The daemon should not treat that as a near-term resolution unless it has result-date awareness.

**Implementation:** Polymarket candidate filtering excludes election winner / most-seats markets whose description says results may not be known definitively by a later fallback date. Revisit with an election-calendar-aware horizon model if election markets become a priority.

### Question deadlines can be later than Gamma endDate

**Observed:** `SAVE Act becomes law by December 31, 2026?` woke as a `1.2d` primary candidate because Gamma's `endDate` was Apr 30 even though the title's resolution deadline is Dec 31. That is a trading/event close, not fast feedback.

**Lesson:** if the question explicitly says `by <Month> <day>, <year>` and that date is materially later than `endDate`, the title date should control fast-feedback eligibility.

**Implementation:** Polymarket candidate filtering excludes markets whose explicit question deadline is more than 7 days after Gamma `endDate`.

### Watched-market price moves need same-market hysteresis

**Observed:** White House `140-159` moved from 65.5% to 71.0% and then to 76.0% on adjacent daemon polls. The first wake was useful: it showed the market had moved through and above the 65% forecast. The second wake added little new information: same direction, same thesis state, no fresh resolution signal in the payload.

**Lesson:** watched-market price alerts are useful for large thesis-relevant moves, but 5pp stair-step alerts on the same market can burn turns during active trading.

**Implementation:** Polymarket price-move alerts now keep a same-market cooldown. After a price-move alert, further alerts for that watched market are suppressed for 2h unless the price is at least 15pp away from the last emitted alert price.

### Missing-book Gamma marks are not actionable price moves

**Observed:** Trump `100-119` emitted a 49.5pp price-move wake from a Gamma `outcomePrices` mark even though the market had no YES bid, a 99% ask, and only about `$1` liquidity. XTracker had already reached 120, so the source state was useful, but the price mark itself was not tradeable CLV.

**Lesson:** watched price moves should use actionable books like candidate discovery does. Missing/no-bid Gamma marks near resolution can be stale or structurally broken.

**Implementation:** Polymarket price-move alerts now require bid/ask present, inside `(0,1)`, and ordered before evaluating the move.

### Bounce-back price moves are often ping-pong, not new information

**Observed:** Elon `220-239` moved down from 68.5% to 55.0%, then back to 70.5% fifteen minutes later with no new XTracker posts. The second wake mostly returned to the pre-alert price and did not change the thesis state.

**Lesson:** a recent price move that merely reverses back near the pre-alert price is low-value churn even if the absolute move clears the cooldown override.

**Implementation:** Polymarket price-move alerts now store the pre-alert price. During the cooldown, a reversal that returns within 5pp of that pre-alert price is suppressed; a real break beyond that band still wakes.

### Wide-book watched-market stair steps are noisy

**Observed:** White House `140-159` kept emitting fast follow-up price moves as the book thinned near resolution. A tight 28/33 move after the post-count burst was useful, but the next 6/30 mark was a low-quality stair-step: same thesis state, nearly same XTracker count, much wider spread.

**Lesson:** watched-market price marks on very wide books should not wake for ordinary 5-15pp stair steps. They are still useful when the repricing is extreme enough to indicate a real market/state change.

**Implementation:** Polymarket price-move alerts suppress watched-market moves on books wider than 20pp unless the price moved at least 25pp since the previous daemon observation. Books wider than 50pp are always ignored as untradeable marks.

### Extreme-spread marks are not useful even when the midpoint moves a lot

**Observed:** Running Point rebounded from 10% to a 49.9% midpoint, but the book was 0.1% / 99.7% with only about `$14` liquidity. The source check still excluded Running Point from the Netflix US TV top 10; the midpoint was not an executable signal.

**Lesson:** the wide-book override should not apply to effectively empty books. A huge midpoint move on a near-100pp spread is worse than no mark.

**Implementation:** Polymarket price-move alerts suppress books wider than 50pp regardless of move size.

## Pending / watchlist

### Kalshi category quality

Kalshi's public feed includes many multi-leg MVE/parlay markets with poor/no pricing. If actionable-spread filtering is insufficient, explicitly downrank or filter `KXMVE*` tickers unless they have real bid/ask, volume, and a clean resolution rule.
