# Participant ledger

Shadow ledger for participant-signal / copy-after-delay validation.

This is not a trading log. No capital is allocated. Entries here record whether public trader/wallet actions would have been useful if copied at the executable price available after rime detected them.

## Scoring convention

- **Observed trade**: price/side/size from the public venue feed.
- **Copy entry**: price a real follower could plausibly get after detection, using current actionable bid/ask.
- **Aligned CLV**: positive means the market moved in the copied direction after the shadow entry.
- **Final PnL**: computed from the copy entry, not the original trader entry.
- **Score**: shrunk participant/domain/horizon signal score, not raw ROI.

## Aggregate participant scores

| Wallet / pseudonym | Venue | Domain | Horizon | Samples | Raw CLV | Copy-after-delay CLV | Shrunk score | Notes |
|--------------------|-------|--------|---------|---------|---------|----------------------|--------------|-------|
| _none yet_ | | | | | | | | Participant intelligence scaffold pending. |

## Shadow signals

| Detected | Wallet / pseudonym | Market | Signal | Observed trade | Copy entry | +1h | +6h | +24h | Close | Outcome | Notes |
|----------|--------------------|--------|--------|----------------|------------|-----|-----|------|-------|---------|-------|
| _none yet_ | | | | | | | | | | | Signals will be added only after post-detection economics clear quality gates. |

## Lessons

- Raw leaderboard/wallet PnL is only a discovery lead. Score copyability using prices available after detection.
- Empty or very wide books can make a smart trader impossible to copy economically.
- Domain and horizon matter; a wallet can be informative in source-adjudication markets and useless in crypto microstructure, or vice versa.
