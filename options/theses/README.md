# Options theses

Active shadow options thesis fixtures can live here as JSON files consumed by:

```bash
scripts/options-daemon.py --fixture-dir options/theses --dry-run
```

Each JSON file can either:

1. include a `chain` object plus `theses[]` and/or hand-authored `signals[]`, or
2. include `underlying` plus `theses[]` and rely on a provider-backed daemon run, e.g. `dotenvx run -- scripts/options-daemon.py --provider tradier ...` with local encrypted `TRADIER_API_KEY` or `TRADIER_TOKEN`.

Do not put provider credentials, account identifiers, broker metadata, or private notes in these files. Use `active: false` at fixture or thesis level for watch items that should be committed but not scanned/emitted yet. For active Situational Awareness fixtures, include fixture-level `reviewedAt` and update it during `options_thesis_refresh_due` handling so stale/no-signal lifecycle reviews are auditable.

Prediction-market daemons remain paused during options-build mode; this directory is for options-only fixture/thesis work. The initial staged strategy file is Cerebras/`CBRS`, tied to the Situational Awareness AI-scaling stack. It is inactive until deliberately promoted. New review candidates are generated upstream by `scripts/sa-thesis-scan.py` from `options/sa-watchlist.json` and local `automation/state/sa-thesis-candidates/*.json` artifacts.

The options daemon also reviews active search fixtures themselves. It emits `options_thesis_refresh_due` when `reviewedAt` is stale, no option signal has fired for the configured interval, expiry is near, spot/liquidity moved materially, or structure-search gates changed. Refresh wakes are thesis reviews, not paper-trade tickets.

Provider-backed example shape:

```json
{
  "underlying": "NVDA",
  "strategy": "situational-awareness-ai-stack",
  "reviewedAt": "2026-05-20T19:49:00Z",
  "theses": [
    {
      "id": "nvda-guidance-upside",
      "direction": "up",
      "targetPrice": 250,
      "targetProbability": 0.35,
      "eventDate": "2026-05-22",
      "optionExpiry": "2026-05-29",
      "maxLossCap": 100,
      "minRewardRisk": 3,
      "allowedStructures": ["debit_vertical"],
      "thesis": "guidance setup gives a higher probability of a move through $250 than options imply",
      "catalyst": "earnings guidance",
      "plannedExit": "first liquid mark after earnings call",
      "falsifier": "management keeps guidance unchanged"
    }
  ]
}
```
