# rime-forecasts options spec

Status: v0.1 proposal / shadow-only, 2026-05-19.

## Goal

Extend rime from event-contract forecasting into listed options while preserving the same discipline: no hidden live trading, executable prices only, and scoring against market-implied baselines.

Options enter the system in two roles:

1. **Signal layer:** use option chains / implied volatility to derive risk-neutral distributions for underlying price thresholds, ranges, and event-market sibling bins.
2. **Instrument layer:** track paper option trades or defined-risk spreads when rime has a model-vs-market edge after bid/ask, fees, and contract multiplier.

The first milestone is **shadow options coverage**: ingest chains, compute distributions, emit candidate/review events, and log paper marks. No live broker orders.

## Non-goals

- No live options trading until broker access, options approval level, local credentials, policy gates, and reconciliation exist.
- No uncovered short options in any automated or dry-run recommendation.
- No margin assumptions hidden inside the model.
- No market orders.
- No exercise/assignment automation in v0.1.
- No scraping or use of market data in violation of provider terms. Paid/provider credentials stay out of git.
- No using stale delayed quotes as if they were executable NBBO.

## Scope

Initial scope:

- US listed equity/ETF/index options for liquid underlyings.
- Expiries from 1 to 45 calendar days for fast feedback, with 1-21d preferred.
- Long premium trades and defined-risk verticals/calendars only.
- Options-derived distributions for Polymarket/Kalshi price-threshold or range markets.

Possible later scope:

- Deribit BTC/ETH options for crypto threshold markets.
- Earnings/event-volatility studies.
- Broker execution adapters once policy/reconciliation is proven.

## Instrument schema

An option contract record must carry enough data to reproduce the quote and risk state:

```json
{
  "underlying": "NVDA",
  "provider": "polygon|tradier|ibkr|theta|deribit|fixture",
  "symbol": "NVDA260522C00250000",
  "expiry": "2026-05-22",
  "right": "call",
  "strike": 250.0,
  "style": "american",
  "settlement": "physical",
  "multiplier": 100,
  "underlying_bid": 224.40,
  "underlying_ask": 224.45,
  "bid": 1.20,
  "ask": 1.28,
  "last": 1.25,
  "mid": 1.24,
  "iv": 0.62,
  "delta": 0.31,
  "gamma": 0.02,
  "theta": -0.11,
  "vega": 0.08,
  "volume": 1200,
  "open_interest": 5400,
  "quote_ts": "2026-05-19T03:20:00Z"
}
```

For spreads, store each leg plus derived net debit/credit, max loss, max gain, breakeven, and net Greeks.

## Data providers

v0.1 can use fixture files and delayed public data for research, but every record must label provider and delay. Candidate wakes that imply executable economics require a real-time or explicitly accepted delayed quote source.

Candidate provider order:

1. **Broker/API with tradable quote parity**: IBKR, Tradier, Schwab, Tastytrade, Alpaca options when available.
2. **Market-data API**: Polygon, ThetaData, Databento/OPRA, CBOE data products.
3. **Research-only fallback**: yfinance or delayed public chains; usable for model development, not executable edge claims.
4. **Crypto options**: Deribit public API for BTC/ETH; execution remains disabled unless lawful account access and policy exist.

Credentials and API keys must be supplied out-of-repo via environment variables or local config.

## Candidate filters

A contract or spread may emit an `options_signal_candidate` only when all mechanical gates pass:

- underlying is on an allowlist or explicitly requested
- expiry is 1-45d away, with 1-21d preferred
- bid and ask are present, ordered, and positive
- premium spread is acceptable:
  - single-leg: `ask - bid <= max($0.05, 15% of mid)`
  - spread: net executable spread <= 20% of max risk, tighter for high-frequency review
- volume >= 100 or open interest >= 500 for each single leg, unless explicitly testing a low-liquidity hypothesis
- quoted premium >= $0.05 and max loss can be computed
- no corporate-action ambiguity
- earnings/event calendar is recorded when inside the holding horizon
- no uncovered short leg
- defined-risk spread max loss <= policy cap
- model edge after spread and fees passes the active threshold

The daemon does not decide thesis quality. It emits only mechanically actionable candidates; the model still judges edge/confidence and documents skips/predictions.

## Edge definitions

Options are not binary event contracts, so Brier is not the primary score.

Use instrument-appropriate edge measures:

### Long premium / spread fair value

```text
edge_dollars = model_fair_value - executable_debit
edge_pct_of_risk = edge_dollars / max_loss
```

For credit spreads:

```text
edge_dollars = executable_credit - model_fair_credit
edge_pct_of_risk = edge_dollars / max_loss
```

### Probability/event mapping

For threshold markets, options can provide an implied probability:

- use vertical call/put spreads or fitted IV surface to estimate the risk-neutral CDF
- compare prediction-market YES price to the derived probability after carry/dividend/borrow adjustments
- record this as a signal for the prediction-market forecast, not as an options trade unless the option instrument itself clears economics

### Volatility edge

For straddles/strangles/calendars, express edge as:

- model expected move vs implied move
- model realized-vol forecast vs implied vol
- event-vol premium/discount after historical and forward-looking adjustments
- expected P/L distribution after theta and vol crush assumptions

## Scoring

Track both mark-to-market and expiry outcomes.

Required marks for option positions/signals:

- entry executable price
- +1h mark
- +6h mark
- +24h mark
- close/exit mark or expiry settlement
- underlying price at each mark
- implied vol / Greeks at each mark when available
- fees estimate

Primary options score:

- paper P/L after spread and fees
- return on max risk
- CLV in dollars and percent of max risk
- win/loss at exit/expiry
- calibration of predicted P/L quantiles when available

Secondary score:

- probability calibration for derived binary events (`underlying > K`, range bins, touch/no-touch approximations)
- comparison against market-implied no-trade baseline

Do not mix option P/L into prediction-market Brier. Keep `scorecard.md` for binary market predictions and `options-ledger.md` for options signals/trades.

## Wake events

Options events use the same `wake-pi` routing and exact session-id policy.

### `options_signal_candidate`

A contract/spread or options-derived distribution clears mechanical filters and needs model review.

Payload includes:

- underlying and contract/spread schema
- current executable bid/ask/net debit/credit
- provider and quote delay
- model-implied fair value or derived probability, if precomputed
- mechanical filter reason
- related Polymarket/Kalshi markets, if any

### `options_clv_checkpoint_due`

A tracked option signal/trade reached +1h/+6h/+24h.

Payload includes:

- entry price and current mark
- mark source/delay
- P/L after spread/fees
- underlying move
- IV/Greek changes when available

### `options_expiry_or_exit`

A tracked option signal/trade hit planned exit, expiry, or stop condition.

Payload includes:

- settlement/exit price
- realized P/L
- return on max risk
- whether thesis mechanism was right

## Ledger

`options-ledger.md` is the human-readable ledger. `journal.jsonl` gets one append-only JSON event for each substantive options prediction, CLV update, skip lesson, or expiry result.

Minimum ledger columns:

| Opened | Underlying | Structure | Thesis | Entry | +1h | +6h | +24h | Exit/expiry | P/L | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

## Execution policy

Options execution is disabled until explicitly implemented. Future policy must include:

- broker enabled flag
- account/options approval level
- max premium risk per trade
- max spread max-loss per trade
- max open Greeks by underlying and portfolio
- max expiry-day exposure
- earnings-event permission flag
- allow-list of structures (`long_call`, `long_put`, `debit_vertical`, etc.)
- assignment-risk handling for American options
- reconciliation against broker positions before and after every order

Live options orders require all existing execution safeguards plus broker-specific options approval and `allow_options_live_submit=true`.

## Implementation order

1. Create fixture schema and parser for option-chain snapshots.
2. Add quote-quality filters and unit tests.
3. Add Black-Scholes / IV utility functions for distribution estimates; use fixtures first.
4. Add `options-ledger.md` and journal event conventions.
5. Build `scripts/options-daemon.py --dry-run` that prints candidates from fixtures only.
6. Add provider adapter behind local credentials.
7. Emit `options_signal_candidate` wakes only after filters are conservative.
8. Add dry-run execution tickets for defined-risk options structures.
9. Only then consider broker live adapter design.
