# CLV ledger

Fast-feedback ledger for prediction price movement before final resolution.

CLV is aligned to rime's prediction direction. Positive CLV means the market moved toward rime's prediction after writing; negative CLV means it moved away. For above-market YES predictions, aligned CLV is later YES price minus entry YES price. For below-market / NO-side predictions, aligned CLV is entry YES price minus later YES price. Raw YES movement is noted when useful. This is not final accuracy, but it is faster feedback than waiting for resolution.

## Checkpoints

- `+1h` — immediate stale-price / reaction check
- `+6h` — same-day digestion
- `+24h` — next-day confirmation
- `close` — market close/resolution price before final Brier scoring

`automation/polymarket-daemon.py` emits `clv_checkpoint_due` wake events for `+1h`, `+6h`, and `+24h` when a reasoning file contains a Polymarket market slug. `resolution_changed` covers close/final events.

## Ledger

| Written | Market | Venue | Entry | +1h | +6h | +24h | Close | Notes |
|---------|--------|-------|-------|-----|-----|------|-------|-------|
| 2026-04-26 | [Tottenham relegated from EPL](./reasoning/2026-04-26-tottenham-relegated-epl-2026.md) | Polymarket | 32.05% YES | 32.05% (+0.0pp, late) | 32.05% (+0.0pp, late) | 32.05% (+0.0pp) | pending | First Polymarket-primary forward prediction; large Manifold/Polymarket spread. Daemon backfill observed no price move at +1h/+6h; true +24h also showed no movement. |
| 2026-04-26 | [Running Point S2 top US Netflix show](./reasoning/2026-04-26-running-point-netflix-top-us-show.md) | Polymarket | 92.4% YES | 91.0% (+1.4pp toward prediction; raw YES -1.4pp) | 95.1% (-2.7pp away from prediction; raw YES +2.7pp) | 3.6% (+88.8pp toward prediction; raw YES -88.8pp) | pending | Short-horizon v3 prediction against a 92% market after official US Netflix top 10 page did not list Running Point. +1h moved slightly toward the NO thesis, +6h reversed above entry, then market repriced hard toward NO: +24h reached 3.6% YES; 08:38Z rebounded to 10.4% YES (+82.0pp aligned) on a wide book; 12:41Z 49.9% mark was ignored as empty-book noise (0.1/99.7, ~$14 liquidity). Fresh Tudum fetch still excluded Running Point. |
| 2026-04-27 | [Elon Musk 220-239 posts Apr 21-28](./reasoning/2026-04-27-elon-musk-tweets-apr21-apr28-220-239.md) | Polymarket | 23.5% YES | 25.5% (+2.0pp) | 49.5% (+26.0pp) | 63.0% (+39.5pp; wide 27/99 book) | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 181 counted posts with ~27.6h left; thesis is that market over-weighted the recent quiet stretch and underpriced the 39-58 remaining-post interval. +1h/+6h/+24h moved toward the YES thesis; after the wide +24h mark, 12:41Z tightened to 76.5% YES (+53.0pp from entry) with XTracker still 227, no posts for ~6.3h, 0-12 cushion, and ~3.3h left. |
| 2026-04-27 | [Trump 100-119 Truth Social posts Apr 21-28](./reasoning/2026-04-27-trump-truth-social-posts-apr21-apr28-100-119.md) | Polymarket | 5.15% YES | 6.85% (+1.7pp) | 10.25% (+5.1pp) | pending | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 105 counted posts with ~27.6h left; thesis is that market over-anchored on 123 pace / 120-139 modal bucket and underpriced staying below 120 after a quiet 24h. +1h/+6h moved toward the YES thesis, but burst risk dominated: 20:26Z collapsed to 1.4% YES; by 11:51Z XTracker showed 120 counted posts, so the bin has overrun and should resolve NO. A 49.5% Gamma mark had no bid/99 ask and is ignored as non-actionable. |
| 2026-04-27 | [White House 140-159 posts Apr 21-28](./reasoning/2026-04-27-white-house-posts-apr21-apr28-140-159.md) | Polymarket | 52.0% YES | 56.0% (+4.0pp) | 79.5% (+27.5pp) | pending | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 124 counted posts with ~27.5h left; thesis is that 16-35 more posts is the natural modal interval after a quiet night and current market over-allocates to 160-179. +1h/+6h moved toward the YES thesis, but later moves reversed as overrun risk rose: overnight quiet briefly rebounded to 58.5% YES, then XTracker reached 154 at 04:50 and market dropped to 23.5% YES (-28.5pp from entry) with only 0-5 posts of cushion. |
| 2026-04-27 | [Powell says "Pandemic" during April press conference](./reasoning/2026-04-27-powell-pandemic-april-press-conference.md) | Polymarket | 74.5% YES | 73.0% (-1.5pp) | 73.0% (-1.5pp) | pending | pending | Short-horizon Fed word-market prediction. Official Fed PDF transcripts showed Powell himself said `pandemic`/`pandemics` in 17 of the last 18 press conferences, including both 2026 meetings; thesis is that the market underpriced sticky pandemic-comparison vocabulary. +1h/+6h sat at 73.0%; 12:46Z midpoint moved to 80.5% YES (+6.0pp from entry) but on a wide 65/96 book with no last trade, so exact executable CLV remains unclear. |

## Update rule

When a `clv_checkpoint_due` wake arrives:

1. read the event payload for `checkpoint`, `priceAtWriting`, `currentPrice`, `clvPp`, and `rawYesMovePp` if present
2. update the relevant table cell with `<price>% (<signed aligned CLV>pp)`; include raw YES movement for below-market predictions if it prevents sign confusion
3. add a short note only if the move teaches something about stale liquidity, cross-venue signal, or reasoning quality
4. call `wake_done`

If exact historical checkpoint price is unavailable because the daemon was not running at the checkpoint, record the observed price and mark it as late, e.g. `34.0% (+1.95pp, late)`.
