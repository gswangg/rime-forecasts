# Situational Awareness thesis-generation spec

Status: v0.4 chain freshness guard, 2026-05-26.

## Goal

Generate reviewable listed-options theses from the Situational Awareness / AI-scaling strategy map without live trading, hidden credentials, or auto-promoting weak ideas into executable tickets.

This layer sits upstream of `scripts/options-daemon.py`:

```text
options/sa-watchlist.json
  -> scripts/sa-thesis-scan.py
  -> options_thesis_review_due wake + local candidate artifact
  -> human/model review promotes selected thesis into options/theses/*.json
  -> scripts/options-daemon.py searches structures and emits options_signal_candidate
```

The scanner proposes **thesis candidates**, not trades. `scripts/options-daemon.py` remains responsible for option-chain structure search, quote filters, edge gates, ticket writing, and markout lifecycle.

## Non-goals

- No live options orders.
- No broker account endpoints.
- No decrypting `.env`; provider commands run under `dotenvx run -- ...`.
- No auto-promoting generated candidates to `active: true` thesis fixtures.
- No generic volatility screen detached from a causal AI-scaling thesis.
- No dependence on news sources that cannot be fetched lawfully or reproducibly.

## Watchlist schema

Durable strategy inputs live in `options/sa-watchlist.json`:

```json
{
  "version": 1,
  "strategy": "situational-awareness-ai-stack",
  "defaults": {
    "enabled": true,
    "emitOnFirstSeen": true,
    "prequalifyFirstSeen": true,
    "prequalifyEmissions": true,
    "maxFirstSeenCandidatesPerScan": 3,
    "firstSeenRecheckHours": 24,
    "targetDays": 30,
    "minDaysToExpiry": 7,
    "maxDaysToExpiry": 60,
    "minLiquidContracts": 2,
    "minDirectionalLiquidContracts": 2,
    "spotMoveTriggerPct": 0.12,
    "allowedStructures": ["debit_vertical"],
    "maxLossCap": 200,
    "minRewardRisk": 3,
    "minEdgePctOfRisk": 0.3,
    "minProbabilityMargin": 0.08,
    "nearPassMinPriority": 70,
    "nearPassEdgeTolerance": 0.10,
    "nearPassProbabilityMarginTolerance": 0.02,
    "maxUnderlyingSpreadPct": 0.03,
    "maxSpotStrikeGapPct": 0.35,
    "minStrikeCount": 5,
    "minOptionContracts": 10
  },
  "entries": [
    {
      "underlying": "CBRS",
      "theme": "frontier_compute",
      "directions": ["up", "down"],
      "emitOnFirstSeen": true,
      "targetMovePct": {"up": 0.35, "down": 0.25},
      "targetProbability": {"up": 0.25, "down": 0.30},
      "catalyst": "post-IPO option liquidity and public-market digestion",
      "mechanism": "frontier-compute scarcity repricing versus AGI-hype unwind",
      "falsifier": "wide chain or disclosures do not validate durable compute demand"
    }
  ]
}
```

## Candidate generation

For each enabled entry, the scanner:

1. selects the listed option expiry closest to `targetDays`, inside min/max DTE;
2. fetches the chain from the configured provider;
3. computes spot mid, liquid contract count, and quote-quality summary;
4. applies trigger logic:
   - first seen if `emitOnFirstSeen: true` and the entry has not completed first-seen review in scanner state,
   - liquidity crossing `minLiquidContracts`,
   - absolute spot move from the last scan >= `spotMoveTriggerPct`,
   - `--force` for explicit operator sweeps;
5. builds an inactive thesis candidate per configured direction;
6. attaches prequalification diagnostics:
   - provider sanity: valid underlying bid/ask, bounded underlying spread, plausible spot vs strike ladder, sufficient contract/strike count, optional quote-age cap;
   - directional liquidity: enough liquid calls for upside or puts for downside within the target path;
   - options structure search: same quote filters and thesis gates used by `scripts/options-daemon.py`;
7. emits triggered candidates only if they prequalify when `prequalifyEmissions: true` (default). The gate now applies to ALL non-force triggers — `first_seen`, `liquidity_crossed_*`, and `spot_move_*` — not just first-seen. A candidate prequalifies if at least one structure fully passes, or if a high-priority candidate has a near-pass structure inside configured edge/probability tolerances. First-seen emissions are additionally throttled by `maxFirstSeenCandidatesPerScan`. `force` triggers bypass all gates for operator sweeps. The legacy `prequalifyFirstSeen: false` flag remains accepted but now only carves out emissions whose sole trigger is `first_seen`; use `prequalifyEmissions: false` for the full opt-out.
8. enforces a chain freshness guard via `chain_quote_is_stale`. Emission is suppressed when the chain `quote_ts` is outside US regular trading hours (13:30-20:00 UTC weekdays, excluding the NYSE-observed US holiday list) or older than 4h. `force` and per-entry `allowStaleChain: true` bypass the guard for diagnostic sweeps.

Generated thesis fields:

- `id`: stable safe id from strategy, underlying, theme, direction, expiry, and rounded target price;
- `active: false` by default;
- `direction`: `up` or `down`;
- `targetPrice`: spot adjusted by direction-specific `targetMovePct`;
- `targetProbability`: direction-specific prior probability;
- `eventDate`: default to selected expiry unless entry supplies `eventDate`/`catalystDate`;
- `optionExpiry`: selected expiry;
- risk/edge gates copied from the watchlist entry/defaults;
- `thesis`, `catalyst`, `plannedExit`, `falsifier` from the watchlist mechanism;
- `prequalification` diagnostics in the wake/candidate artifact, including blockers and best/near-pass structure summaries.

## Wake event

### `options_thesis_review_due`

A Situational Awareness watchlist item has produced a reviewable thesis candidate. This event asks the model to decide whether the mechanism, target, probability, and timing are good enough to promote into `options/theses/*.json`.

Payload includes:

- `candidateId`
- `underlying`, `theme`, `direction`
- `triggerReasons`
- `spot`
- `optionExpiry`, `daysToExpiry`
- `chainSummary`
- generated inactive `thesisFixture`
- local `candidatePath` when written
- `dedupeKey`

Handling rule: do not write tickets or ledger P/L from this event. If accepted, promote or update a thesis fixture, then run `scripts/options-daemon.py --provider tradier --dry-run` and let `options_signal_candidate` handle trade review.

## State and artifacts

Runtime state is local and gitignored:

- `automation/state/sa-thesis-scan.json`
- `automation/state/sa-thesis-candidates/*.json`
- `automation/state/sa-thesis-scan.log`

State stores last spot/liquidity by underlying, emitted candidate dedupe keys, and first-seen review/check timestamps. Candidate artifacts are audit/debug records and may be promoted manually into tracked `options/theses/*.json` only after review. First-seen prequalification failures are checked at most once per `firstSeenRecheckHours` unless another trigger fires.

## Operations

Dry-run:

```bash
dotenvx run -- scripts/sa-thesis-scan.py --provider tradier --dry-run --max-events 5
```

Loop:

```bash
mkdir -p automation/state
nohup dotenvx run -- scripts/sa-thesis-scan.py \
  --provider tradier \
  --session-id 019dc71a-53fa-73ff-85a7-46f8e5d3c671 \
  --loop \
  --interval-sec 3600 \
  --max-events 2 \
  >> automation/state/sa-thesis-scan.log 2>&1 &
```

Stop:

```bash
pkill -f 'scripts/sa-thesis-scan.py'
```

## Acceptance

- Unit tests cover expiry selection, candidate generation, inactive/default behavior, state dedupe, first-seen prequalification, and dry-run CLI output.
- `dotenvx run -- scripts/sa-thesis-scan.py --provider tradier --dry-run` succeeds without printing secrets.
- Non-dry-run loop writes only wake/candidate/state artifacts; no tracked files are mutated.
