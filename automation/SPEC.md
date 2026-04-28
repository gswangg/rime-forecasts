# rime-forecasts automation spec

Status: v0.2 MVP, 2026-04-26.

## Goal

Move the forecasting validation loop from drain-time model polling to event-driven market monitoring.

Cheap code polls markets and writes wake events. The model wakes only when judgment or documentation is needed.

## Non-goals

- No autonomous trading or capital allocation.
- No model self-spin while idle.
- No cwd-based wake routing.
- No attempt to start pi if no pi process is running. `wake-pi` only wakes an already-running session.

## Architecture

```text
Polymarket/Kalshi/Manifold APIs
          │
          ▼
automation daemon(s)
          │ writes explicit session-id wake events
          ▼
~/.pi/agent/wake/inbox/*.json  or  ./.pi/wake/inbox/*.json
          │
          ▼
wake-pi extension
          │ exact sessionId match only
          ▼
running pi session receives [wake:<id>] followUp
          │
          ▼
agent evaluates, documents, and calls wake_done / wake_fail
```

## Routing

Every daemon run that can emit wake events must be configured with an explicit pi `sessionId`.

Allowed sources, in priority order:

1. CLI: `--session-id <id>`
2. env: `RIME_WAKE_SESSION_ID=<id>`

There is deliberately no fallback to cwd, latest session file, tmux pane, or active process discovery. A missing session id is a hard error unless `--dry-run` is set.

## Wake event shape

The daemon writes the event schema consumed by `wake-pi`:

```json
{
  "id": "rime-candidate-found-will-x-20260426T203000Z",
  "sessionId": "019dc71a-53fa-73ff-85a7-46f8e5d3c671",
  "ts": "2026-04-26T20:30:00.000Z",
  "source": "rime-forecasts/polymarket-daemon",
  "type": "candidate_found",
  "priority": 80,
  "prompt": "Read this wake event payload and evaluate the candidate against drive-prompt.md v3.",
  "payload": {
    "market": { "slug": "...", "url": "...", "price": 0.42 }
  }
}
```

`id` is filename-safe and the file is written atomically via temp file + rename to `<wakeRoot>/inbox/<id>.json`.

## Fast-feedback horizon ladder

Candidate discovery is optimized for validation speed, not portfolio aesthetics.

Mechanical horizon buckets:

| Bucket | Resolution window | Wake priority | Use |
|--------|-------------------|---------------|-----|
| primary | 1–7 days | 80 | default target; fastest final-resolution feedback |
| secondary | 8–21 days | 65 | useful when primary bucket is sparse |
| tertiary | 22–45 days | 45 | emit only when liquidity/volume is unusually high, as a proxy for information value |

Markets under 1 day are skipped by default because there is often too little time for careful reasoning and documentation. Markets over 45 days are skipped by the daemon; manual research can still choose them, but the automation should not wake the model for them.

Tertiary high-liquidity gate: liquidity ≥ `$25k` or volume ≥ `$100k`.

## Event types

### `candidate_found`

A market appears to satisfy mechanical filters and is worth model review.

MVP filters for Polymarket:

- active and not closed
- binary YES/NO outcome
- current YES price can be parsed
- actionable bid/ask: bid and ask present, inside `(0, 1)`, ordered, spread ≤ 10pp
- YES price in the candidate band: 5%–95%
- real volume ≥ `$1k`
- liquidity ≥ `$5k` or volume ≥ `$10k`
- generic team-vs-team win/draw/BTTS sports questions are excluded unless a future model explicitly opts them in
- individual highest-temperature range/exact/threshold-bin questions are excluded until a forecast-aware sibling-bin model exists
- individual crypto price threshold/range questions are excluded until a volatility/options-aware model exists
- deferred election-result markets are excluded when the Polymarket `endDate` is a trading/phase close rather than a near-term result date
- mutually-exclusive Gamma event / negative-risk clusters emit at most one candidate wake, with sibling markets included in the payload
- fast-feedback horizon ladder passes

MVP filters for Kalshi:

- active/open binary market
- current YES price can be parsed from bid/ask/last
- actionable bid/ask: bid and ask present, inside `(0, 1)`, ordered, spread ≤ 20pp
- YES price in the candidate band: 5%–95%
- real volume ≥ `$1k`
- liquidity/open interest/volume proxy passes the same `$5k`/`$10k` mechanical gate when available
- fast-feedback horizon ladder passes

Kalshi exists in the loop because it has many short-dated economic, weather, and sports/event markets. Its MVP daemon emits `candidate_found` only; watched-market CLV/resolution support can be added after the first useful candidates are flowing.

The daemon does **not** decide edge. The model still applies the forecast methodology and either writes a prediction or acknowledges a skip.

### `price_moved`

A watched market's YES price moved by at least the configured threshold since the last observed daemon price. Default threshold: 5pp.

To avoid stair-step alert churn on the same watched market, a same-watch price-move alert has a default 1h cooldown. The cooldown is bypassed if the current price is at least 10pp away from the last emitted price-move alert for that market.

Watched price moves on very wide books are lower-quality marks. If bid/ask spread is wider than 20pp, suppress moves smaller than 25pp; still wake for extreme wide-book repricings.

Watched markets are extracted from `reasoning/*.md` when a Polymarket market slug is present. This covers Polymarket-primary predictions and Polymarket shadows on Manifold-primary predictions.

### `clv_checkpoint_due`

A prediction has reached a fast-feedback checkpoint after its written timestamp and the checkpoint has not already emitted.

MVP checkpoints:

- `1h`
- `6h`
- `24h`

Payload includes written-time market price, current market price if available, aligned CLV in percentage points, raw YES movement, and CLV direction when known. `clvPp` is aligned to rime's prediction: positive means the market moved toward rime's forecast. `rawYesMovePp` is always current YES price minus entry YES price.

### `resolution_changed`

A watched Polymarket market appears closed/resolved and the daemon has not already emitted the resolution event for that market.

Payload includes parsed resolution when inferable:

- YES if closed and YES price ≥ 0.99
- NO if closed and YES price ≤ 0.01
- MKT/unknown otherwise

## State

Default state paths:

```text
automation/state/polymarket-daemon.json
automation/state/kalshi-daemon.json
```

The state file is local runtime state and is gitignored.

State tracks:

- emitted candidate events by market slug/ticker and candidate group
- last observed prices for watched markets
- emitted CLV checkpoints by reasoning file + slug
- emitted resolution events by slug
- last emitted price-move alert by watched-market slug for cooldown/hysteresis
- emitted event ids / dedupe keys

State is written only after corresponding wake files are successfully written, except `--dry-run`, which prints events and leaves state unchanged.

## Daemon modes

MVP daemons are single-shot pollers by default:

```bash
scripts/polymarket-daemon.py --session-id <pi-session-id>
scripts/kalshi-daemon.py --session-id <pi-session-id>
```

Options:

- `--dry-run` — do not require session id, do not write state/events.
- `--once` — explicit one-shot mode; default.
- `--loop --interval-sec N` — repeat polling in-process. This is for a background daemon, not model self-spin.
- `--fixture <path>` — use fixture JSON instead of the live API, for tests/smoke checks.
- `--max-events N` — cap total emitted events per poll.
- `--max-candidate-events N` — cap candidate events per poll.
- `--price-move-threshold X` — watched-market move threshold; default `0.05` / 5pp.
- `--price-move-cooldown-sec N` — suppress small repeat price-move wakes for the same watched market; default `3600`.
- `--price-move-cooldown-override X` — price delta from last emitted price-move alert that bypasses cooldown; default `0.10` / 10pp.
- `--wake-root <path>` — default `~/.pi/agent/wake`.

Recommended long-running loop for fast feedback: run Polymarket and Kalshi every 10–15 minutes. The model only wakes if a daemon writes an event.

## Agent handling contract

For `candidate_found`:

1. read the wake event payload
2. inspect market and any nearby equivalent venues if needed
3. if methodology clears, write a prediction file and update scorecard/journal
4. if not, journal a concise skip only when useful
5. call `wake_done`

For `price_moved`, `clv_checkpoint_due`, and `resolution_changed`:

1. update scorecard, CLV ledger, or reasoning resolution sections as appropriate
2. call `wake_done`

If the event is malformed, stale, or cannot be acted on, call `wake_fail` with the reason.

## Validation

Pure logic is tested without network:

- Polymarket/Kalshi normalization and filters
- fast-feedback horizon ranking and priority
- explicit session id requirement
- wake event atomic write shape
- CLV checkpoint scheduling and idempotence
- watched-market extraction from reasoning markdown
- stateful event generation/deduplication, including same-watch price-move cooldown

Network fetch is isolated in the CLI/poller layer.
