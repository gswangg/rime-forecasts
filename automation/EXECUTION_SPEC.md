# rime-forecasts execution spec

Status: v0.1 dry-run ticket/risk engine, 2026-05-16.

## Goal

Add a controlled path from forecast to trade execution without jumping straight from wake events to unattended capital allocation.

The first milestone is **not** autonomous betting. It is the ability for rime to produce deterministic order tickets with sizing, edge, spread, and risk checks. Venue adapters can submit those tickets only after credentials, legal access, and explicit live-enable flags are in place.

## Non-goals

- No geo/KYC bypassing. Only use venues where Greg has lawful access.
- No hidden live trading. Default mode is dry-run ticket generation.
- No market orders in v0.1.
- No autonomous sizing beyond explicit policy caps.
- No use of stale wake payload prices when current executable bid/ask is available.

## Execution layers

```text
forecast / wake review
        │
        ▼
order ticket builder
        │ pure logic: side, executable price, edge, sizing, risk gates
        ▼
execution/tickets/*.json
        │
        ├── dry-run adapter (default; no network submit)
        ├── manual approval / human placed order
        └── future venue adapters (Kalshi, Polymarket) behind live-enable flags
```

## Ticket requirements

Every order ticket records:

- venue and market identifier (`slug`, `ticker`, or condition id)
- market title and URL
- forecast YES probability
- chosen side (`YES` or `NO`)
- executable side price
  - YES buy price = current YES ask
  - NO buy price = current NO ask, or `1 - YES bid` for binary complementary books
- bid/ask spread used for risk checks
- fair side probability and gross edge
- sizing mode and amount
- estimated cost / max loss
- max payout if correct
- status: `draft` or `blocked`
- blocked reasons, if any
- policy values used to generate the ticket

## Sizing modes

### `max_payout`

Buy enough shares/contracts so the correct outcome pays the requested amount.

Example: `amount=100`, YES ask `0.20`:

- cost / max loss: `$20`
- payout if correct: `$100`
- profit if correct: `$80`

This is the recommended pilot mode because it avoids cheap longshots dominating bankroll exposure.

### `cash`

Stake the requested cash amount regardless of price.

Example: `amount=100`, YES ask `0.20`:

- cost / max loss: `$100`
- payout if correct: `$500`
- profit if correct: `$400`

This is higher variance and should not be the default until calibration and liquidity are better validated.

## Default policy

Initial conservative defaults:

- minimum executable edge: 10pp
- maximum bid/ask spread: 10pp
- sizing mode: `max_payout`
- amount: `$100` max payout
- max cash risk per order: `$100`
- live submit: disabled

A ticket that fails policy is still emitted as `blocked` for auditability, but no adapter may submit it.

## Live adapters

Future live adapters must require all of:

1. credentials supplied out-of-repo through environment variables or a secrets manager
2. explicit CLI flag such as `--live`
3. explicit policy `allow_live_submit=true`
4. ticket status `draft` / not blocked
5. venue-specific order response appended to the live trade ledger

The implementation must never commit private keys, API secrets, addresses, or auth tokens.

## Ledger

Real or simulated execution fills should append to `trades.jsonl` once live/manual execution begins. A fill record should include:

- ticket id
- venue order id if any
- submit timestamp
- fill timestamp
- side, price, size, fees
- realized cost
- resulting position id / token id / contract count
- resolution and realized P/L when known

Until then, `execution/tickets/*.json` is the source of truth for dry-run intent.
