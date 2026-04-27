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
| 2026-04-26 | [Running Point S2 top US Netflix show](./reasoning/2026-04-26-running-point-netflix-top-us-show.md) | Polymarket | 92.4% YES | 91.0% (+1.4pp toward prediction; raw YES -1.4pp) | 95.1% (-2.7pp away from prediction; raw YES +2.7pp) | n/a (after close) | pending | Short-horizon v3 prediction against a 92% market after official US Netflix top 10 page did not list Running Point. +1h moved slightly toward the NO thesis, but +6h reversed above entry. |
| 2026-04-27 | [Elon Musk 220-239 posts Apr 21-28](./reasoning/2026-04-27-elon-musk-tweets-apr21-apr28-220-239.md) | Polymarket | 23.5% YES | pending | pending | pending | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 181 counted posts with ~27.6h left; thesis is that market over-weighted the recent quiet stretch and underpriced the 39-58 remaining-post interval. |
| 2026-04-27 | [Trump 100-119 Truth Social posts Apr 21-28](./reasoning/2026-04-27-trump-truth-social-posts-apr21-apr28-100-119.md) | Polymarket | 5.15% YES | pending | pending | pending | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 105 counted posts with ~27.6h left; thesis is that market over-anchored on 123 pace / 120-139 modal bucket and underpriced staying below 120 after a quiet 24h. |
| 2026-04-27 | [White House 140-159 posts Apr 21-28](./reasoning/2026-04-27-white-house-posts-apr21-apr28-140-159.md) | Polymarket | 52.0% YES | pending | pending | pending | pending | Short-horizon XTracker range-bin prediction. At writing tracker showed 124 counted posts with ~27.5h left; thesis is that 16-35 more posts is the natural modal interval after a quiet night and current market over-allocates to 160-179. |

## Update rule

When a `clv_checkpoint_due` wake arrives:

1. read the event payload for `checkpoint`, `priceAtWriting`, `currentPrice`, `clvPp`, and `rawYesMovePp` if present
2. update the relevant table cell with `<price>% (<signed aligned CLV>pp)`; include raw YES movement for below-market predictions if it prevents sign confusion
3. add a short note only if the move teaches something about stale liquidity, cross-venue signal, or reasoning quality
4. call `wake_done`

If exact historical checkpoint price is unavailable because the daemon was not running at the checkpoint, record the observed price and mark it as late, e.g. `34.0% (+1.95pp, late)`.
