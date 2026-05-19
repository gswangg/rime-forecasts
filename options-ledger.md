# Options ledger

Shadow-only options-contract and options-derived-distribution ledger.

Options are not scored with prediction-market Brier. Track mark-to-market CLV, realized/expiry P/L after spread and fees, return on max risk, and whether the thesis mechanism was right. Live options trading is disabled until broker access, policy, approvals, and reconciliation exist.

Current build phase: active thesis fixtures under `options/theses/`, dry-run options tickets under `execution/options-tickets/`, provider interfaces, candidate/CLV/expiry wake events, and markout helpers. Prediction-market daemons are paused while this is built.

Use `scripts/options-markout.py --append-ledger` after reviewing a current mark to append a row here.

| Opened | Underlying | Structure | Thesis | Entry | +1h | +6h | +24h | Exit/expiry | P/L | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| _none yet_ | | | | | | | | | | |
