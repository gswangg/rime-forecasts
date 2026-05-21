# Options ledger

Shadow-only options-contract and options-derived-distribution ledger.

Options are not scored with prediction-market Brier. Track mark-to-market CLV, realized/expiry P/L after spread and fees, return on max risk, and whether the thesis mechanism was right. Live options trading is disabled until broker access, policy, approvals, and reconciliation exist.

Current build phase: active thesis fixtures under `options/theses/`, dry-run options tickets under `execution/options-tickets/`, provider interfaces, candidate/CLV/expiry wake events, and markout helpers. Prediction-market daemons are paused while this is built.

Use `scripts/options-markout.py --append-ledger` after reviewing a current mark to append a row here.

| Opened | Underlying | Structure | Thesis | Entry | +1h | +6h | +24h | Exit/expiry | P/L | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 2026-05-21 | NVDA | debit_vertical +1 call 240.0 / -1 call 250.0 | NVIDIA frontier-compute upside; target 250.22 by 2026-06-18 after Q1 FY27 print, with IV-crushed Jun18 240/250 call vertical clearing edge/probability gates. | debit $168.00; max loss $168.00; max gain $832.00; edge $102.00 / 60.7%; reward/risk 4.95x | $139.00 (-$29.00 / -17.3%; spot $219.32; gap to BE +10.2%) | $137.50 (-$30.50 / -18.2%; spot $219.48; closed near day low on 18.8x vol; ANET +5.7%/MU +3.7%/CORZ +6.7% rotation confirmed thesis; per planned-exit playbook flag for close at +24h) |  |  |  | paper_open; flagged-for-close-at-+24h; signal id `sa-nvda-frontier_compute-up-2026-06-18-250.22:debit_vertical:1:NVDA260618C002400`; no live order |
| 2026-05-21 | NVDA | debit_vertical +1 call 247.5 / -1 call 250.0 | Orphan ticket: daemon emitted this strike pair on the 2026-05-21T14:06:35Z poll after canonical 240/250 was accepted; review wake rejected the duplicate, but ticket file already on disk. Closed for audit. | debit $43.00; max loss $43.00; max gain $207.00; edge $24.50 / 57.0% | $27.00 (-$16.00 / -37.2%) | | | $27.00 (-$16.00 / -37.2%) | -$16.00 | paper_closed; orphan from cross-poll thesis emission pre-cap-fix; canonical position is the 240/250 |
| 2026-05-21 | PLTR | debit_vertical +1 call 155.0 / -1 call 157.5 | Rejected at review (not opened as canonical paper): target/implied ratio 1.54x with no catalyst in 28d window, enterprise/sovereign AI sector being actively distributed (NOW -3.4% on 6.7x vol, CRM -3.1%, SNOW -2.4%, C3.AI -2.1% on 5.7x vol), thin short-leg OI 103. PLTR thesis kept active but gates tightened. | debit $38.00; max loss $38.00; max gain $212.00; edge $24.50 / 64.5% | | | | $30.50 (-$7.50 / -19.7%) | -$7.50 | paper_closed; audit-only; daemon emitted because mechanical gates passed |
