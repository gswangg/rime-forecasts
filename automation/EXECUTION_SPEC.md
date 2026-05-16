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

## Full-auto trading plan

Greg's preferred target mode is full auto, but full auto means **policy-gated auto-execution**, not discretionary unlimited trading by the agent.

Target loop:

```text
forecast clears edge
  -> execution ticket generated
  -> executor re-quotes live book
  -> policy gate checks edge, spread, liquidity, risk, and stale data
  -> limit order submitted if all gates pass
  -> fills/positions reconciled
  -> CLV, resolution, and realized P/L logged
```

Required before any live auto-submit:

1. Legal venue access:
   - Kalshi KYC complete.
   - Polymarket only if legally available to Greg.
2. Secrets out of repo:
   - Kalshi API credentials.
   - Polymarket wallet/CLOB credentials if used.
   - No private keys, API keys, auth tokens, or wallet secrets in git.
3. Explicit risk policy file, expected at `execution/policy.yaml` or equivalent local secret-backed config.
4. Reconciliation path that can compare local open positions against venue-reported positions before and after submits.
5. Kill switches/circuit breakers implemented and tested in dry-run.

Recommended first live-auto pilot policy:

```yaml
sizing_mode: max_payout
amount_per_trade: 100        # dollars max payout, not cash stake
max_cash_risk_per_trade: 75
max_open_exposure: 500
max_daily_new_risk: 300
max_daily_loss: 200
min_edge_after_spread: 0.12  # 12pp
max_spread: 0.08             # 8pp
limit_orders_only: true
allow_market_orders: false
allow_adjudication_markets: true
venues:
  kalshi:
    enabled: true
  polymarket:
    enabled: false           # enable after adapter/reconciliation proves clean
```

Circuit breakers:

- stop live submits after any position reconciliation mismatch
- stop live submits after daily loss cap is hit
- stop live submits after daily new-risk cap is hit
- stop live submits after N consecutive venue API/order errors
- block tickets when book spread exceeds policy
- block tickets when current executable edge falls below policy after re-quote
- block tickets when market status is not active/open or resolution state is ambiguous beyond policy
- block tickets when liquidity/order-book depth cannot support the requested size at the limit price

Implementation order:

1. Add `execution/policy.yaml.example` with safe defaults; keep real `execution/policy.yaml` gitignored.
2. Add `trades.jsonl` schema/spec and append-only writer for submitted orders/fills.
3. Add `scripts/executor-daemon.py` in dry-run mode: consumes draft tickets, re-quotes, applies policy, writes `would_submit` / `blocked` records.
4. Add Kalshi live adapter first: auth, quote, limit order, cancel/replace, fills, positions.
5. Add Polymarket live adapter second: CLOB auth/signing, token lookup, limit orders, fills, positions.
6. Run full auto with tiny caps, then raise caps only after successful reconciliation and enough live-fill evidence.

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
