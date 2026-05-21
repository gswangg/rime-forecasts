# Options ledger

Shadow-only options-contract and options-derived-distribution ledger.

Options are not scored with prediction-market Brier. Track mark-to-market CLV, realized/expiry P/L after spread and fees, return on max risk, and whether the thesis mechanism was right. Live options trading is disabled until broker access, policy, approvals, and reconciliation exist.

Current build phase: active thesis fixtures under `options/theses/`, dry-run options tickets under `execution/options-tickets/`, provider interfaces, candidate/CLV/expiry wake events, and markout helpers. Prediction-market daemons are paused while this is built.

Use `scripts/options-markout.py --append-ledger` after reviewing a current mark to append a row here.

| Opened | Underlying | Structure | Thesis | Entry | +1h | +6h | +24h | Exit/expiry | P/L | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 2026-05-21 | NVDA | debit_vertical +1 call 240.0 / -1 call 250.0 | NVIDIA frontier-compute upside; target 250.22 by 2026-06-18 after Q1 FY27 print, with IV-crushed Jun18 240/250 call vertical clearing edge/probability gates. | debit $168.00; max loss $168.00; max gain $832.00; edge $102.00 / 60.7%; reward/risk 4.95x | $139.00 ($-29.00 / -17.3%; spot $219.32 vs entry ~$221.56; gap to BE $241.68 still +10.2%; IV crush + sell-the-news rotation) |  |  |  |  | paper_open; signal id `sa-nvda-frontier_compute-up-2026-06-18-250.22:debit_vertical:1:NVDA260618C002400`; no live order |
