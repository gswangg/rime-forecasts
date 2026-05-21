# rime-forecasts options spec

Status: v0.6 thesis-search lifecycle and per-thesis cap, 2026-05-21.

## Goal

Extend rime from event-contract forecasting into listed options while preserving the same discipline: no hidden live trading, executable prices only, and scoring against market-implied baselines.

Options enter the system in two roles:

1. **Signal layer:** use option chains / implied volatility to derive risk-neutral distributions for underlying price thresholds, ranges, and event-market sibling bins.
2. **Instrument layer:** track paper option trades or defined-risk spreads when rime has a model-vs-market edge after bid/ask, fees, and contract multiplier.

The first milestone is **shadow options coverage**: ingest chains, compute distributions, emit candidate/review events, and log paper marks. No live broker orders.

v0.2 shifted from hand-authored option structures toward a thesis-driven funnel: a catalyst thesis specifies direction, target zone, event date, model probability, and risk caps; code searches liquid contracts for capped-risk structures that express it.

v0.3 stitches that funnel into wake lifecycle operation: active thesis fixtures live in `options/theses/`, `scripts/options-daemon.py` can loop over them, accepted candidates can write local paper tickets, and open tickets can emit CLV/expiry wake events.

v0.4 adds a thesis strategy layer for the Situational Awareness / AI-scaling stack, supports staged inactive thesis fixtures, and distinguishes the catalyst `eventDate` from the contract `optionExpiry` used for structure search. Thesis discovery itself is specified separately in `automation/SA_THESIS_SPEC.md`; generated review candidates must be promoted into `options/theses/*.json` before this options funnel searches structures.

v0.5 adds active thesis-search lifecycle review. The daemon continuously snapshots active Situational Awareness thesis fixtures against current spot, liquidity, expiry, and structure-search diagnostics, and emits `options_thesis_refresh_due` when a search is stale, near expiry, materially moved, liquidity-regressed, or structure availability changed.

v0.6 caps how many candidate `options_signal_candidate` wakes a single thesis can emit per poll. The default is 1: the top-scored structure per thesis wins and alternative passing structures from the same thesis are suppressed (logged as `per-thesis cap reached`). This matches the shadow-paper convention of one representative position per thesis. Use `--max-signals-per-thesis N` to lift the cap for diagnostic sweeps. The ticket-id encoding was also widened so multiple structures from the same thesis no longer collide on disk when the cap is lifted.

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

Provider interfaces are code-shaped before credentials exist via `automation/options.py::OptionChainProvider` and `FixtureOptionProvider`; `automation/options_providers.py::TradierOptionProvider` implements a read-only Tradier market-data adapter:

- `list_expiries(underlying) -> tuple[date, ...]`
- `fetch_chain(underlying, expiry | None) -> OptionChainSnapshot`
- `fetch_quote(symbol) -> OptionContract`
- `provider`, `quote_ts`, `quote_delay_seconds`, and raw response metadata on every normalized record
- no credentials or account identifiers in repo fixtures, state, tickets, or logs

Tradier usage requires `TRADIER_TOKEN` or `TRADIER_API_KEY` in the local environment; optional `TRADIER_BASE_URL` can point at sandbox or an alternate endpoint. The adapter uses market-data endpoints only and never submits orders. Greg's durable setup keeps the key in encrypted dotenvx state; invoke provider commands with `dotenvx run -- ...` rather than decrypting `.env`.

Candidate provider order:

1. **Broker/API with tradable quote parity**: IBKR, Tradier, Schwab, Tastytrade, Alpaca options when available.
2. **Market-data API**: Polygon, ThetaData, Databento/OPRA, CBOE data products.
3. **Research-only fallback**: yfinance or delayed public chains; usable for model development, not executable edge claims.
4. **Crypto options**: Deribit public API for BTC/ETH; execution remains disabled unless lawful account access and policy exist.

Credentials and API keys must be supplied out-of-repo via environment variables or local config.

## Funnel stages

The options opportunity funnel is deliberately reject-heavy:

1. **Catalyst/thesis input** — direction, target zone, catalyst date, option expiry, model probability, mechanism, falsifier, and exit plan.
2. **Tradability filter** — underlying allowlist, expiry window, bid/ask integrity, spread, volume/open interest, quote freshness, no corporate-action ambiguity.
3. **Structure search** — generate capped-risk long options and debit verticals whose payoff zone matches the thesis; credit spreads remain supported only when explicitly requested.
4. **EV/asymmetry gate** — compare model fair value to executable debit/credit after multiplier and fees; require edge as percent of max risk and probability margin over breakeven.
5. **Paper ticket** — write an auditable dry-run options ticket for accepted candidates.
6. **CLV/markouts** — record +1h/+6h/+24h/current/exit marks, underlying move, IV/Greek changes, and realized/expiry P/L.

The funnel asks: "where do we have a causal forecast edge, and which capped-risk option structure pays enough for being right?" It should not scan for generic cheap options.

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

Options events use the same `wake-pi` routing and exact session-id policy. `scripts/options-daemon.py` emits candidate and lifecycle wakes in non-dry-run mode; `--dry-run` prints the same event payloads without writing wake files.

### `options_signal_candidate`

A contract/spread or options-derived distribution clears mechanical filters and needs model review.

Payload includes:

- underlying and contract/spread schema
- current executable bid/ask/net debit/credit
- provider and quote delay
- model-implied fair value or derived probability, if precomputed
- thesis fields: catalyst, mechanism, target zone, model probability, planned exit, falsifier
- mechanical filter reason
- related Polymarket/Kalshi markets, if any

### `options_thesis_refresh_due`

An active thesis-search fixture needs review even though no paper trade may exist. The daemon scans active Situational Awareness thesis fixtures from `options/theses/*.json` and emits refresh wakes when configured lifecycle checks fire:

- `review_stale_<N>d`: fixture `reviewedAt`/`generatedAt` is older than `--thesis-refresh-days`;
- `no_signal_<N>d`: no `options_signal_candidate` has emitted for the thesis after the no-signal interval;
- `expiry_within_<N>d`: searched option expiry is close;
- `spot_move_±X%`: underlying moved materially since the last thesis check;
- `liquidity_drop_-X%`: liquid contract count deteriorated materially;
- `structure_now_passes` / `structure_no_longer_passes`: search gates crossed between checks.

Payload includes:

- thesis id and fixture path;
- current spot, distance to target, days to expiry, and chain/liquidity summary;
- current structure-search diagnostics, including best passing/blocked structure;
- reasons and dedupe key.

Handling rule: reassess the thesis, catalyst, target probability, falsifier, and market conditions. If valid, update `reviewedAt`/notes if useful; if invalid or stale, deactivate the fixture. Do not write tickets or ledger P/L from a refresh wake.

### `options_clv_checkpoint_due`

A tracked option signal/trade reached +1h/+6h/+24h. The daemon scans local `execution/options-tickets/*.json` and emits checkpoints for eligible statuses, default `paper_open`.

Payload includes:

- ticket id/path and full ticket snapshot
- checkpoint name and dedupe key
- entry price/max loss/evaluation via ticket payload
- instructions to mark with `scripts/options-markout.py`

The mark itself is not guessed from stale data in the wake event; use current quote/fixture/manual mark at processing time.

### `options_expiry_or_exit`

A tracked option signal/trade hit planned exit, expiry, or stop condition. v0.3 detects option expiry from the ticket structure and emits one `options_expiry_or_exit` wake unless an exit/expiry/close markout already exists.

Payload includes:

- ticket id/path and full ticket snapshot
- due reason / dedupe key
- instructions to mark with `scripts/options-markout.py`
- realized P/L and thesis correctness are filled during wake processing, not by the daemon

## Ledger

`options-ledger.md` is the human-readable ledger. `journal.jsonl` gets one append-only JSON event for each substantive options prediction, CLV update, skip lesson, or expiry result.

Minimum ledger columns:

| Opened | Underlying | Structure | Thesis | Entry | +1h | +6h | +24h | Exit/expiry | P/L | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

Paper ticket artifacts live under `execution/options-tickets/` and are gitignored. `scripts/options-daemon.py --write-tickets` writes them from accepted shadow candidates. `scripts/options-markout.py` updates a ticket from manual mark values or a current chain fixture and prints a ready-to-paste `options-ledger.md` row; `--append-ledger` appends that row to `options-ledger.md` when review has accepted the mark.

Ticket artifacts include:

- ticket id and status (`draft`/`blocked`/`paper_open`/`paper_closed`)
- thesis fields and source fixture/provider
- full structure schema and legs
- entry executable quote, net debit/credit, max loss, max gain, breakeven
- model fair value, model probability, breakeven probability, edge dollars, edge percent of risk
- planned exit/falsifier
- markout slots for +1h/+6h/+24h/exit

`execution/options-tickets/` is local runtime state unless explicitly promoted; do not commit private provider/broker metadata.

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

1. Create fixture schema and parser for option-chain snapshots. **Implemented:** `automation/options.py::parse_option_chain_snapshot` / `load_option_chain_snapshot`.
2. Add quote-quality filters and unit tests. **Implemented:** `OptionQuoteFilterConfig`, `contract_quote_filter_reason`, `tests/test_options.py`.
3. Add Black-Scholes / IV utility functions for distribution estimates; use fixtures first. **Implemented:** Black-Scholes pricing, risk-neutral threshold/range helpers, capped-risk structure builders, and edge evaluation.
4. Add `options-ledger.md` and journal event conventions. **Implemented.**
5. Build `scripts/options-daemon.py --dry-run` that prints candidates from fixtures only. **Implemented:** fixture chain + `signals[]` flow; dry-run prints candidate events/rejections.
6. Add thesis-to-structure search over fixtures: generate long/debit-vertical candidates from direction, target zone, option expiry, model probability, and max-risk constraints. **Implemented.**
7. Extend `scripts/options-daemon.py` so `theses[]` can auto-generate and rank structures, not only consume hand-authored `signals[]`. **Implemented.**
8. Add dry-run options ticket artifacts under `execution/options-tickets/` plus ledger/markout helpers. **Implemented:** `option_ticket_from_event`, `write_option_ticket`, `option_markout`, `add_option_markout`, `options_ledger_row`, `scripts/options-daemon.py --write-tickets`, and `scripts/options-markout.py`.
9. Add provider interfaces behind local credentials. **Implemented for fixture + Tradier market data:** `OptionChainProvider`, `FixtureOptionProvider`, `TradierOptionProvider`, and `scripts/options-chain-fetch.py`. Additional providers remain future work.
10. Emit `options_signal_candidate` wakes only after filters are conservative. **Implemented for fixture `signals[]`, generated `theses[]`, and provider-backed thesis files.**
11. Add CLV/expiry lifecycle wake scanning for local paper tickets. **Implemented:** `options_clv_checkpoint_due` and `options_expiry_or_exit` from `execution/options-tickets/`.
12. Add active thesis-search lifecycle review. **Implemented:** `options_thesis_refresh_due` from active Situational Awareness thesis fixtures, with stale/no-signal/expiry/spot/liquidity/structure-change checks.
13. Cap per-thesis candidate emissions and fix ticket-id collision so the shadow-paper book stays canonical. **Implemented:** `--max-signals-per-thesis` (default 1) and widened ticket-id encoding.
14. Only then consider broker live adapter design.

## Fixture signal format

`scripts/options-daemon.py --fixture <path> --dry-run` expects:

```json
{
  "chain": {
    "underlying": "NVDA",
    "provider": "fixture",
    "underlying_bid": 224.40,
    "underlying_ask": 224.45,
    "quote_ts": "2026-05-19T03:20:00Z",
    "contracts": [
      {"symbol":"NVDA260522C00250000","expiry":"2026-05-22","right":"call","strike":250,"bid":1.20,"ask":1.28,"volume":1200,"open_interest":5400},
      {"symbol":"NVDA260522C00260000","expiry":"2026-05-22","right":"call","strike":260,"bid":0.42,"ask":0.48,"volume":1200,"open_interest":5400}
    ]
  },
  "signals": [
    {
      "id": "nvda-upside-spread",
      "structure": "debit_vertical",
      "long": "NVDA260522C00250000",
      "short": "NVDA260522C00260000",
      "modelFairValue": 125.0,
      "modelProbability": 0.25,
      "thesis": "catalyst creates upside distribution mismatch",
      "catalyst": "earnings guidance",
      "plannedExit": "post-event mark",
      "falsifier": "guide unchanged"
    }
  ]
}
```

Supported structures in the fixture daemon: `long_call`, `long_put`, `debit_vertical`, `credit_vertical`. Values are dollars per one standard 100x option contract after multiplier, so `modelFairValue: 125.0` means $125.

## Thesis fixture format

Generated-structure fixtures should add `theses[]` alongside or instead of hand-authored `signals[]`. Active files can live in `options/theses/*.json` and are loaded by default via `--fixture-dir options/theses`:

```json
{
  "active": true,
  "chain": {"underlying":"NVDA","provider":"fixture","contracts": []},
  "theses": [
    {
      "id": "nvda-guidance-upside",
      "direction": "up",
      "targetPrice": 250.0,
      "targetProbability": 0.35,
      "eventDate": "2026-05-22",
      "optionExpiry": "2026-05-29",
      "maxLossCap": 100.0,
      "minRewardRisk": 3.0,
      "minEdgePctOfRisk": 0.20,
      "allowedStructures": ["debit_vertical", "long_call"],
      "thesis": "guidance setup gives a higher probability of a move through $250 than options imply",
      "catalyst": "earnings guidance",
      "plannedExit": "first liquid mark after earnings call",
      "falsifier": "management keeps guidance unchanged"
    }
  ]
}
```

The search generates candidate structures, computes executable debit, max loss/gain, breakeven, reward/risk, model fair value from the thesis probability/payoff approximation, and ranks accepted candidates by edge percent of risk plus asymmetry/spread quality. Set fixture-level or thesis-level `active: false` to stage watch items without provider fetches or wake emissions. `eventDate` is the catalyst/review date; `optionExpiry` (or legacy `expiry`) is the listed-option expiry searched. If `optionExpiry` is omitted, the search falls back to `eventDate`.

## Daemon operation

Candidate dry-run:

```bash
scripts/options-daemon.py --fixture path/to/fixture.json --dry-run
scripts/options-daemon.py --fixture-dir options/theses --dry-run
# provider-backed thesis files that omit embedded chain data:
dotenvx run -- scripts/options-daemon.py --fixture-dir options/theses --provider tradier --dry-run
```

Fetch a normalized current chain:

```bash
dotenvx run -- scripts/options-chain-fetch.py --provider tradier --underlying NVDA --expiry 2026-05-22 --output /tmp/nvda-chain.json --pretty
```

Active thesis-search refresh is enabled by default for Situational Awareness fixtures. Useful controls:

```bash
--no-thesis-refresh
--thesis-refresh-days 7
--thesis-no-signal-days 7
--thesis-expiry-review-days 7
--thesis-spot-move-pct 0.08
--thesis-liquidity-drop-pct 0.50
--max-signals-per-thesis 1
```

The per-thesis cap defaults to 1. Suppressed alternative structures show up in the dry-run rejection list with a `per-thesis cap reached` reason and a small sample so reviewers can audit what was held back.

Wake-producing loop, pinned to the rime session:

```bash
dotenvx run -- scripts/options-daemon.py \
  --fixture-dir options/theses \
  --provider tradier \
  --session-id 019dc71a-53fa-73ff-85a7-46f8e5d3c671 \
  --loop \
  --interval-sec 900 \
  --write-tickets \
  --ticket-status paper_open
```

Lifecycle-only scan, useful after tickets exist:

```bash
scripts/options-daemon.py \
  --fixture-dir options/theses \
  --session-id 019dc71a-53fa-73ff-85a7-46f8e5d3c671 \
  --once
```

`--schedule-status paper_open` is the default for CLV wakes. Add `--schedule-status draft` only when draft tickets should be marked before model review.

Manual/current-fixture markout:

```bash
scripts/options-markout.py \
  --ticket execution/options-tickets/<ticket>.json \
  --checkpoint 1h \
  --fixture path/to/current-chain.json \
  --append-ledger
```

If no current chain fixture exists, pass `--mark-value` and `--underlying-price` manually.
