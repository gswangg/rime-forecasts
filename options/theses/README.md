# Options theses

Active shadow options thesis fixtures can live here as JSON files consumed by:

```bash
scripts/options-daemon.py --fixture-dir options/theses --dry-run
```

Each JSON file should include a `chain` object plus `theses[]` and/or hand-authored `signals[]`. Do not put provider credentials, account identifiers, broker metadata, or private notes in these files.

Prediction-market daemons remain paused during options-build mode; this directory is for options-only fixture/thesis work.
