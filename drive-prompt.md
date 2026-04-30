# Drive prompt: rime-forecasts (validation experiment, v4 event-driven + participant intelligence)

*Purpose: test whether rime's forecasting and market-participant reasoning produce economically tradeable calibration before any capital is committed.*

*Revision history:*
- *v2–v2.5.2 (2026-04-19/20): 14–45d window, venue equality, 10pp+edge with confidence gate, moved-market discount, skip-fatigue/cadence gates.*
- *v3 (2026-04-26): event-driven architecture. Market polling moves to daemon(s); model work is triggered by `wake-pi` events. Adds CLV feedback loop (+1h/+6h/+24h/close). Avoids drain-time market scanning and idle model burn.*
- *v3.1 (2026-04-26): fast-feedback candidate ladder. Daemons prioritize 1–7d markets, then 8–21d, and only emit 22–45d markets when liquidity/volume is unusually high. Added Kalshi candidate daemon.*
- *v4 (2026-04-30): add shadow participant intelligence. Track wallets/traders as noisy signals, simulate copy-after-delay economics, and score participant CLV/final results. No capital allocation and no live copy execution.*

## Goal

Accumulate 15–25 resolved market predictions with published reasoning **and** build a parallel shadow participant-signal ledger that tests whether observable Polymarket/Kalshi traders contain copyable residual edge after latency, spread, and liquidity.

Score objectively:

1. calibration — Brier, log loss, calibration curve
2. economic realizability — Brier differential and net edge after friction
3. fast feedback — CLV at +1h/+6h/+24h/close
4. cross-venue signal — especially Manifold vs real-money disagreement
5. participant signal — copy-after-delay CLV/final ROI by trader/domain/horizon
6. reasoning quality — Greg's subjective reread

Still no capital allocation. Pundit validation and shadow-copy research only.

## Architecture

```text
scripts/polymarket-daemon.py / scripts/kalshi-daemon.py
  -> market candidate / CLV / resolution wakes

scripts/polymarket-participant-daemon.py (v4 scaffold)
  -> participant signal / participant CLV wakes

all daemons
  -> ~/.pi/agent/wake/inbox/*.json
  -> wake-pi exact sessionId routing
  -> [wake:<id>] followUp
  -> model judges/documents
  -> wake_done / wake_fail
```

Core docs:

- [`automation/SPEC.md`](./automation/SPEC.md) — market daemon/wake contract
- [`automation/PARTICIPANT_SPEC.md`](./automation/PARTICIPANT_SPEC.md) — participant intelligence contract
- [`automation/LESSONS.md`](./automation/LESSONS.md) — wake-loop lessons and implemented filter changes
- [`clv-ledger.md`](./clv-ledger.md) — fast-feedback market ledger
- [`participant-ledger.md`](./participant-ledger.md) — shadow participant-signal ledger
- [`scorecard.md`](./scorecard.md) — final calibration ledger

## Operating priorities

1. **Wake events first.** If the user message starts with `[wake:<id>]`, process exactly that event before any build work.
2. **Queued AC tasks second.** If auto-continue has a concrete task, execute it with tests/docs/commits as appropriate.
3. **Bounded maintenance third.** Check resolutions, daemon health, or docs only when explicitly queued or requested.
4. **No idle market scanning.** Do not keep the model alive looking for markets. Cheap daemons do polling.

## Wake-event mode

If the current user message starts with `[wake:<id>]`, treat it as extension-generated, not Greg.

Steps:

1. Read the wake event file named in the message.
2. Inspect `type`, `payload`, and `prompt`.
3. Process exactly that event.
4. Update repo files only if the event produced durable information.
5. If the event teaches a reusable filter/automation lesson, update `automation/LESSONS.md`. If the lesson is validated by repeated wakes or an obvious fail-loud bad candidate, implement the filter/test change before continuing normal operation.
6. Call `wake_done({id, outcome, notes?})` when complete, or `wake_fail({id, reason})` if blocked.

Market event handling:

- `candidate_found`: evaluate the market against the methodology. If it clears, write a prediction file and update scorecard/journal/CLV ledger. If it does not clear, usually just `wake_done` with a skip outcome; journal only if the skip teaches something.
- `price_moved`: update `clv-ledger.md` or reasoning notes only if the move teaches something. Otherwise acknowledge.
- `clv_checkpoint_due`: update `clv-ledger.md` with price and signed CLV. Mark late if the checkpoint was missed and only current price is available.
- `resolution_changed`: verify finality, append Resolution section to the reasoning file, update scorecard, commit/push.

Participant event handling:

- `participant_signal_candidate`: evaluate whether the observed trader/wallet action is a useful **shadow signal** after detection delay and current executable price. If useful, append/update `participant-ledger.md` and `journal.jsonl`; do **not** write a normal prediction unless rime independently clears the market edge/confidence/economics bar.
- `participant_clv_checkpoint_due`: update participant-ledger CLV for the simulated copy entry.
- `participant_resolution_changed`: update participant-ledger final outcome and any trader scorecard summaries.

## Maintenance/manual mode

If this prompt is invoked without a wake event and without an AC task, do not perform open-ended market scanning. Use this only for bounded maintenance:

1. Check `scripts/check-resolutions.py` for newly resolved existing predictions.
2. Verify daemon health/config if asked or queued.
3. Improve automation/tests/docs if asked or queued.
4. If no concrete work exists, call `ac off` and stop.

## Starting daemons

Requires an explicit pi session id. No cwd/latest-session fallback.

Market daemon smoke:

```bash
scripts/polymarket-daemon.py --dry-run --pages 1 --page-limit 20
scripts/kalshi-daemon.py --dry-run --pages 1 --page-limit 50
scripts/polymarket-daemon.py --session-id <pi-session-id> --once
scripts/kalshi-daemon.py --session-id <pi-session-id> --once
```

Participant daemon smoke (once implemented):

```bash
scripts/polymarket-participant-daemon.py --dry-run --limit 100
scripts/polymarket-participant-daemon.py --session-id <pi-session-id> --once
```

Background loop:

```bash
mkdir -p automation/state
nohup scripts/polymarket-daemon.py \
  --session-id <pi-session-id> \
  --loop \
  --interval-sec 900 \
  >> automation/state/polymarket-daemon.log 2>&1 &
nohup scripts/kalshi-daemon.py \
  --session-id <pi-session-id> \
  --loop \
  --interval-sec 900 \
  >> automation/state/kalshi-daemon.log 2>&1 &
# participant daemon interval can be shorter once signal filters are conservative:
nohup scripts/polymarket-participant-daemon.py \
  --session-id <pi-session-id> \
  --loop \
  --interval-sec 300 \
  >> automation/state/polymarket-participant-daemon.log 2>&1 &
```

`<pi-session-id>` can be obtained explicitly from `/wake status` in the target pi session. Do not script a fallback that guesses it.

## Market candidate methodology

### Fast-feedback candidate ladder

Daemon candidate events maximize validation speed:

1. **Primary:** resolves in 1–7 days. Highest priority (`80`).
2. **Secondary:** resolves in 8–21 days. Medium priority (`65`).
3. **Tertiary:** resolves in 22–45 days. Low priority (`45`) and only emitted when liquidity ≥ $25k or volume ≥ $100k.

Markets under 1 day are skipped by default because there may not be time for careful reasoning and documentation. Manual exceptions are allowed, but the daemon should not wake the model for them.

### Venue equality, with real-money validation priority

Manifold, Kalshi, and Polymarket are all valid deal-flow sources, but the experiment's economic question is real-money tradeability. Real-money venues should drive validation when possible; Manifold remains useful for broad market discovery and cross-venue signal.

Do not skip a candidate merely because it is single-venue. Do record cross-venue prices when the same question exists elsewhere.

### Edge threshold

Only predict if one of:

- `abs(my probability − market price) ≥ 10pp` **and** confidence ≥ 3/5
- confidence ≥ 4/5 with a specific novel information claim
- the prediction captures a mechanism that is itself a testable thesis with confidence ≥ 3/5

Low-confidence threshold-edge calls are skipped. Sub-10pp base-rate vibes are skipped.

### Moved-market edge discount

If current price has moved ≥20pp from initial/creation level in the direction opposite my prediction, discount effective edge by 50% before applying the threshold.

Large adverse moves encode information. Fighting them with generic base-rate reasoning is dangerous.

## Participant-signal methodology

Participant intelligence is **shadow-only**. It is not live copytrading.

Treat trader/wallet behavior as noisy, adversarial, and domain-specific:

- Raw realized PnL is a lead, not proof of edge.
- Score signals on **copy-after-delay** executable prices, not the trader's historical entry.
- Prefer prospective CLV and final outcomes after observation over leaderboard ROI.
- Apply Bayesian shrinkage toward zero edge, especially for small samples.
- Track domain/horizon separately: politics/source adjudication, crypto microstructure, earnings, sports, macro, culture, etc.
- Exclude or downweight tiny trades, self-evidently hedged/arb trades, micro-duration up/down markets, empty books, and copy entries where spread/liquidity erase the signal.
- Cap any future simulated portfolio by trader, market, theme, and hidden correlation cluster.

A participant signal is useful only if it answers:

> Given we observed this wallet at this time, could a real trader still enter at the current book with positive expected CLV/final value after spread and slippage?

Do not produce a normal rime forecast merely because a participant signal exists. Use participant signals to learn who is informative and when; only write a market prediction if rime's independent methodology clears.

## Prediction file requirements

Every market prediction file must include:

```markdown
# <Market title> — resolves <YYYY-MM-DD>

**Primary venue**: Manifold | Kalshi | Polymarket
**Primary URL**: <url>
**Polymarket market slug**: <slug if any>
**Other venues (same question, if any)**:
- Kalshi: <url or n/a>
- Polymarket: <url or n/a>
- Manifold: <url or n/a>
**Written**: <ISO timestamp>
**Prediction**: <%>
**Primary venue price at writing**: <%>
**Other venue prices at writing (aligned to YES direction)**: <list or "single-venue">
**Edge vs primary venue**: <pp>
**Cross-venue spread (if any)**: <pp>
**Confidence**: <1-5>

## Market question
## Base rate
## Where I differ from base rate (and why)
## What would change my mind
## Economics at this edge

---

## Resolution (added after market resolves, never editing above)
```

Frozen pre-resolution content stays frozen.

## CLV update format

When updating `clv-ledger.md`, use aligned CLV — positive means the market moved toward rime's forecast:

```text
<price>% (<signed aligned CLV>pp)
```

For below-market / NO-side predictions, include raw YES movement when useful:

```text
<price>% (+1.4pp toward prediction; raw YES -1.4pp)
```

If late:

```text
<price>% (<signed aligned CLV>pp, late)
```

CLV is not a substitute for final scoring. It is a faster signal about whether the market moved toward the forecast before resolution.

## Journaling

After substantive forecast, participant, or automation work, append to `journal.jsonl`:

```json
{"ts":"<iso>","action":"predict|resolve|clv|skip|automation|participant","files":["<filename>"],"edge_pp":<number or null>,"notes":"<brief>"}
```

Commit behavior:

- prediction/resolution/automation docs/tests: commit and push
- participant scaffold / participant ledger updates: commit and push at useful checkpoints
- CLV ledger updates: commit if they add durable learning; otherwise batch with next substantive commit
- pure no-op skips: do not commit

## Stop / pause criteria

Call `ac off` or leave `ac` disabled when:

- no wake event, no AC task, and no concrete maintenance task is present
- the participant-signal scaffold checkpoint has been committed/pushed and there is no next explicit task
- OAuth/model limits are near exhaustion
- 15+ predictions are resolved and the scorecard supports a graduate/iterate/archive decision
- Greg explicitly halts

Do not use drain-time `ac` as a market polling loop. Use `wake-pi` events and daemon polling.

## Context to read each substantive event

- This file
- The wake event payload (if any)
- `automation/SPEC.md`
- `automation/PARTICIPANT_SPEC.md` when participant-related
- `automation/LESSONS.md`
- Relevant `reasoning/*.md`
- `scorecard.md`
- `clv-ledger.md`
- `participant-ledger.md` when participant-related
- `journal.jsonl` tail

## Find-work on AC drain

When AC injects this prompt because the queue is empty:

1. Check for unprocessed wake events only if they were explicitly delivered as `[wake:<id>]`; do not scan wake inbox manually as a polling substitute.
2. Inspect `git status --short` and recent `journal.jsonl` tail.
3. If the v4 participant scaffold is incomplete, push one concrete next task to AC and execute it. Incomplete means any of:
   - `automation/PARTICIPANT_SPEC.md` missing or stale
   - `participant-ledger.md` missing
   - `automation/participants.py` missing tests for scoring/economics
   - `scripts/polymarket-participant-daemon.py` missing dry-run/fixture support
   - tests fail
4. If scaffold is complete and committed/pushed, call `ac off` and stop.

## Post-validation path

If signal exists:

1. Graduate to `fruits/` as a mature venture.
2. Register a domain.
3. Complete Kalshi KYC.
4. Stand up subscription infrastructure.
5. Begin positioned publishing.

This drive validates; a successor drive operates capitalized publishing.
