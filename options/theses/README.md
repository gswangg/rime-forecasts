# Options theses

Active shadow options thesis fixtures can live here as JSON files consumed by:

```bash
scripts/options-daemon.py --fixture-dir options/theses --dry-run
```

Each JSON file can either:

1. include a `chain` object plus `theses[]` and/or hand-authored `signals[]`, or
2. include `underlying` plus `theses[]` and rely on a provider-backed daemon run, e.g. `--provider tradier` with local `TRADIER_TOKEN`.

Do not put provider credentials, account identifiers, broker metadata, or private notes in these files.

Prediction-market daemons remain paused during options-build mode; this directory is for options-only fixture/thesis work.

Provider-backed example shape:

```json
{
  "underlying": "NVDA",
  "theses": [
    {
      "id": "nvda-guidance-upside",
      "direction": "up",
      "targetPrice": 250,
      "targetProbability": 0.35,
      "eventDate": "2026-05-22",
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
