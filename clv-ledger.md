# CLV ledger

Fast-feedback ledger for prediction price movement before final resolution.

CLV = later market YES price minus entry market YES price, aligned to the prediction's primary direction unless otherwise noted. Positive CLV means the market moved toward rime's prediction after writing; negative CLV means it moved away. This is not final accuracy, but it is faster feedback than waiting for resolution.

## Checkpoints

- `+1h` — immediate stale-price / reaction check
- `+6h` — same-day digestion
- `+24h` — next-day confirmation
- `close` — market close/resolution price before final Brier scoring

`automation/polymarket-daemon.py` emits `clv_checkpoint_due` wake events for `+1h`, `+6h`, and `+24h` when a reasoning file contains a Polymarket market slug. `resolution_changed` covers close/final events.

## Ledger

| Written | Market | Venue | Entry | +1h | +6h | +24h | Close | Notes |
|---------|--------|-------|-------|-----|-----|------|-------|-------|
| 2026-04-26 | [Tottenham relegated from EPL](./reasoning/2026-04-26-tottenham-relegated-epl-2026.md) | Polymarket | 32.05% YES | 32.05% (+0.0pp, late) | 32.05% (+0.0pp, late) | pending | pending | First Polymarket-primary forward prediction; large Manifold/Polymarket spread. Daemon backfill observed no price move at +1h/+6h event time. |

## Update rule

When a `clv_checkpoint_due` wake arrives:

1. read the event payload for `checkpoint`, `priceAtWriting`, `currentPrice`, and `clvPp`
2. update the relevant table cell with `<price>% (<signed CLV>pp)`
3. add a short note only if the move teaches something about stale liquidity, cross-venue signal, or reasoning quality
4. call `wake_done`

If exact historical checkpoint price is unavailable because the daemon was not running at the checkpoint, record the observed price and mark it as late, e.g. `34.0% (+1.95pp, late)`.
