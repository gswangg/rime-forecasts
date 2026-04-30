# rime-forecasts participant intelligence spec

Status: v0.1 scaffold, 2026-04-30.

## Goal

Test whether observable market participants contain copyable residual edge after detection latency, bid/ask spread, slippage, liquidity limits, and domain/regime decay.

This is **shadow research only**. The system must never place trades, recommend capital allocation as an instruction, or treat leaderboard PnL as proof of edge.

## Non-goals

- No autonomous trading.
- No wallet hero worship.
- No raw-copy alerts from one-off wins.
- No inference from stale/empty books.
- No attempt to deanonymize traders beyond public wallet/profile fields exposed by the venue.
- No use of private credentials or authenticated APIs for participant discovery in the MVP.

## Core idea

A participant action is useful only if a real trader could observe it and still enter with edge at the **post-detection executable book**.

The unit of analysis is not:

```text
wallet made money historically
```

It is:

```text
wallet W bought/sold outcome O in market M at time T;
we observed it at T+d;
the current executable book at T+d allowed a shadow copy entry at price P;
that shadow entry later produced positive CLV/final value after friction in this market domain/horizon.
```

## Data sources

MVP Polymarket public endpoints:

- `https://data-api.polymarket.com/trades?limit=N` — recent public trades.
- `https://data-api.polymarket.com/trades?user=<proxyWallet>&limit=N` — public trades by wallet.
- `https://data-api.polymarket.com/activity?user=<proxyWallet>&limit=N` — public wallet activity, including `TRADE` and `REDEEM` events where available.
- Gamma market endpoints already used by the Polymarket daemon for market metadata and books.

Future sources:

- CLOB order book endpoints for exact executable copy price.
- Resolved market history for trader/wallet realized ROI by market type.
- Kalshi public participant data if available.

## Data model

### Participant trade

Normalized fields:

```json
{
  "venue": "Polymarket",
  "wallet": "0x...",
  "name": "display name if any",
  "pseudonym": "pseudonym if any",
  "side": "BUY|SELL",
  "outcome": "Yes|No|Up|Down|...",
  "outcomeIndex": 0,
  "price": 0.42,
  "size": 100.0,
  "notional": 42.0,
  "timestamp": "2026-04-30T00:00:00Z",
  "marketSlug": "will-x-happen",
  "eventSlug": "event-slug",
  "title": "Market title",
  "conditionId": "0x...",
  "asset": "token id",
  "transactionHash": "0x..."
}
```

### Participant score

Scores are domain/horizon-specific and shrink strongly toward zero.

Suggested fields:

```json
{
  "wallet": "0x...",
  "domain": "politics|crypto|earnings|sports|macro|culture|source|other",
  "horizonBucket": "micro|intraday|1-7d|8-21d|22-45d|long",
  "sampleSize": 25,
  "realizedRoi": 0.12,
  "meanClvPp": 3.4,
  "copyAfterDelayMeanClvPp": 1.1,
  "winRate": 0.58,
  "shrinkageWeight": 0.42,
  "score": 0.46
}
```

### Shadow copy signal

A signal records what would have happened if rime copied at the observed book after delay.

```json
{
  "signalId": "participant:wallet:market:tx",
  "wallet": "0x...",
  "marketSlug": "will-x-happen",
  "domain": "source",
  "horizonBucket": "1-7d",
  "observedTrade": { ... },
  "detectedAt": "2026-04-30T00:05:00Z",
  "copyEntry": {
    "side": "BUY_YES|BUY_NO|SKIP",
    "referencePrice": 0.42,
    "executablePrice": 0.45,
    "bid": 0.41,
    "ask": 0.45,
    "spreadPp": 4.0,
    "maxNotionalUsd": 50.0
  },
  "status": "watching|skipped|resolved",
  "checkpoints": {
    "1h": null,
    "6h": null,
    "24h": null,
    "close": null
  },
  "resolution": null
}
```

## Domain buckets

Initial title/slug heuristics are intentionally coarse:

- `crypto`: Bitcoin, Ethereum, Solana, Chainlink, token tickers, up/down crypto micro-markets.
- `earnings`: quarterly earnings, EPS, revenue, company ticker earnings questions.
- `sports`: team-vs-team games, exact scores, player stats, tournament outcomes.
- `macro`: Fed, CPI, GDP, jobs, commodities, rates, FX.
- `politics`: elections, bills, officeholders, geopolitical policy.
- `source`: markets resolved by a named tracker/source or adjudication rule where source interpretation dominates.
- `culture`: celebrities, streamers, entertainment, social-media count markets.
- `other`: fallback.

Domain buckets are for scoring and throttling, not truth. They can be overridden later.

## Horizon buckets

Relative to market end/resolution time when known:

| Bucket | Window |
|--------|--------|
| micro | under 1 hour |
| intraday | 1 hour to under 1 day |
| 1-7d | 1 to 7 days |
| 8-21d | 8 to 21 days |
| 22-45d | 22 to 45 days |
| long | over 45 days or unknown |

## Signal quality gates

The daemon should suppress ordinary participant wakes unless all are true:

- observed trade notional is meaningful (`price * size >= $10` initially; raise if noisy)
- market has parseable slug/title/outcome/side
- current market book is actionable if copy entry is evaluated
- spread is not too wide for the signal class
- participant score is not just one lucky trade; use shrinkage/min-sample gates for high-priority wakes
- market is not a micro-duration up/down market unless a future microstructure model explicitly opts in
- copy-after-delay executable price is not obviously worse than the observed trader price by more than the candidate edge budget

A skipped participant observation may still be stored in local state for aggregate scoring, but should not wake the model.

## Event types

### `participant_signal_candidate`

A participant action appears potentially informative and worth model review.

Payload includes:

- normalized trade
- trader score summary if available
- domain/horizon bucket
- current market/book snapshot if available
- proposed shadow copy entry or reason no copy entry is possible
- dedupe key `participant:<wallet>:<marketSlug>:<transactionHash>`

Model handling:

1. Decide whether to add a shadow signal to `participant-ledger.md`.
2. Do not create a normal prediction unless market methodology independently clears.
3. Call `wake_done`/`wake_fail`.

### `participant_clv_checkpoint_due`

A shadow copy signal reached a CLV checkpoint.

Payload includes entry price, current price, aligned CLV, raw movement, and book quality.

### `participant_resolution_changed`

A shadow copy signal's market resolved.

Payload includes inferred final outcome and copy-entry PnL if computable.

## State

Default local state:

```text
automation/state/polymarket-participant-daemon.json
```

State tracks:

- processed transaction hashes
- cold-start wallet/domain/horizon observation aggregates (`count`, side counts, total notional, first/last trade timestamps, last seen market)
- known wallets and aggregate score snapshots
- emitted participant signal ids
- shadow signal checkpoint emissions
- last fetch timestamp/page cursor when available

State is local runtime state and gitignored.

## Cold-start workflow

Participant intelligence starts with observations, not wakes:

1. **Observe without scores** — run the participant daemon with no score fixture. It records processed trades and `wallet_observations` aggregates by wallet/domain/horizon, but suppresses unscored wakes.
   ```bash
   scripts/polymarket-participant-daemon.py --session-id <pi-session-id> --once
   ```
2. **Backfill candidate wallets** — score wallets seen in local state, bounded by wallet/market limits.
   ```bash
   scripts/polymarket-participant-score.py \
     --state-path automation/state/polymarket-participant-daemon.json \
     --output automation/state/participant-scores.json
   ```
3. **Run with score gates** — pass the score fixture into the daemon. Only future trades matching wallet/domain/horizon scores and quality gates can emit `participant_signal_candidate` wakes.
   ```bash
   scripts/polymarket-participant-daemon.py \
     --session-id <pi-session-id> \
     --score-fixture automation/state/participant-scores.json \
     --loop --interval-sec 300
   ```

Do not retroactively wake old cold-start trades after they become scored. That would fake detection latency.

## Daemon modes

```bash
scripts/polymarket-participant-daemon.py --dry-run --limit 100
scripts/polymarket-participant-daemon.py --session-id <pi-session-id> --once
scripts/polymarket-participant-daemon.py --session-id <pi-session-id> --loop --interval-sec 300
scripts/polymarket-participant-score.py --state-path automation/state/polymarket-participant-daemon.json --output automation/state/participant-scores.json
```

Options should mirror market daemons where practical:

- `--dry-run`
- `--once`
- `--loop --interval-sec N`
- `--fixture <path>`
- `--score-fixture <path>`
- `--max-events N`
- `--wake-root <path>`
- `--session-id <id>` or `RIME_WAKE_SESSION_ID`
- `--min-notional-usd`
- `--min-score-pp`

## Scoring principles

### Shrinkage

Use a simple transparent shrinkage before any complex model:

```text
shrinkage_weight = sample_size / (sample_size + prior_n)
shrunk_edge = raw_edge * shrinkage_weight
```

Initial `prior_n` should be high (`25` or more) because public wallets are selected from a huge universe.

### Backfill score fixture

`scripts/polymarket-participant-score.py` creates a conservative triage fixture from bounded public wallet trade fetches:

- group by wallet/domain/horizon
- compute participant-direction movement from historical trade price to current Gamma YES mark
- subtract a fixed copy-delay penalty
- shrink toward zero with `sample_size / (sample_size + prior_n)`
- emit rows consumable by `scripts/polymarket-participant-daemon.py --score-fixture`

This is **not** validated copytrading edge. It is a way to choose which wallets deserve prospective shadow tracking. Real signal quality is measured only by future post-detection copy entries.

### Copy-after-delay discount

For each signal, distinguish:

- trader entry price
- first observed price by daemon
- executable copy price at detection
- subsequent CLV/final outcome

If the edge disappears between trader entry and detection, the trader may still be good but the signal is not copyable.

### Portfolio view

Future simulated portfolios should cap by:

- wallet/trader
- market
- event cluster
- domain
- horizon
- correlated narrative/theme

## Ledger rules

`participant-ledger.md` records only durable shadow signals and aggregate lessons, not every raw trade.

A ledger entry should include:

- timestamp detected
- wallet/pseudonym
- market/outcome/side
- observed trade price/size/notional
- copy entry price/book
- reason signal was accepted
- CLV checkpoints and final outcome when known

## Validation

Pure logic tests should cover:

- trade normalization from Polymarket data-api rows
- notional calculation
- domain/horizon bucketing
- shrinkage score calculation
- copy entry economics from bid/ask for BUY/SELL and YES/NO outcomes
- quality gates for tiny trades, micro markets, wide books, and low-score wallets
- cold-start observation aggregation without emitting unscored wakes
- event id/dedupe construction

Network fetch belongs in the script layer and should be fixture-testable.
