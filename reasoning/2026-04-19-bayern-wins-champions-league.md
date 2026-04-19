# FC Bayern wins the 2025-26 Champions League — resolves 2026-06-29

**Manifold URL**: https://manifold.markets/Maxxxx/will-fc-bayern-win-the-champions-le
**Written**: 2026-04-19T21:42:00+00:00
**Prediction**: 30%
**Market price at writing**: 35%

## Market question

> Will Fc Bayern win the Champions League?

Resolves **YES** if FC Bayern Munich win the 2025-26 UEFA Champions League (Final is May 30, 2026). Resolves **NO** otherwise. Market description is minimal but the meaning is unambiguous: did Bayern lift the trophy this season?

## Base rate

Current bracket state as of 2026-04-19 (ESPN UCL scoreboard):

**Quarterfinals (completed April 7–15):**
- Bayern beat Real Madrid 6–4 on aggregate (4–3 second leg)
- PSG beat Liverpool 4–0 on aggregate
- Atlético beat Barcelona 3–2 on aggregate
- Arsenal beat Sporting 1–0 on aggregate

**Semifinals (scheduled):**
- Bayern vs PSG — 1st leg April 28 at PSG, 2nd leg May 6 at Bayern
- Arsenal vs Atlético — 1st leg April 29 at Atlético, 2nd leg May 5 at Arsenal

**Final:** May 30, 2026.

Bayern's path to win: must beat PSG in the semifinal (two legs), then beat the winner of Arsenal/Atlético in the final.

Reference-class base rate for a "team currently in the semifinal" winning the whole thing:

- Among the four semifinalists, historical win probability should sum to ~100%. Assuming roughly equal coin-flip in each two-leg tie, each team starts with ~25% baseline.
- Adjusting for team strength: Bayern and PSG are the stronger pair (both top-tier European clubs with strong recent form); Arsenal and Atlético are strong but typically slightly below that tier in raw squad strength.
- Baseline probabilistic estimates: Bayern 28%, PSG 28%, Arsenal 22%, Atlético 22%.

This puts my base-rate estimate around 28–30%. Market at 35% is modestly above this.

## Where I differ from base rate (and why)

I am at **30%**, five points below the market's 35%. The reasoning is a disciplined two-stage calculation, not a contrarian call.

**Stage 1 — beat PSG in semifinal (52–55%):**

- Bayern's form is strong: a 6–4 aggregate win over Real Madrid is a major result. Historical H2H (2020 final, knockout ties) favors Bayern.
- PSG is also in strong form: 4–0 vs Liverpool is a dominant display. Luis Enrique has PSG playing cohesive football.
- Bayern has the advantage of the 2nd leg at home (Allianz Arena) — marginal edge.
- On balance: Bayern slight favorite. My estimate: **53%**.

**Stage 2 — beat Final opponent (55%):**

- If Arsenal (slight SF favorite, maybe ~55%): Bayern is stronger team on paper. P(Bayern beats Arsenal in final) ≈ 58%.
- If Atlético (~45% SF probability): Simeone's defensive style is tough for Bayern's attacking system. P(Bayern beats Atlético) ≈ 50%.
- Weighted: 0.55 × 0.58 + 0.45 × 0.50 = 0.319 + 0.225 = **0.544**, ~54%.

**Combined:** 0.53 × 0.54 ≈ 0.286, so approximately **29%**.

I round to **30%** to account for residual form uncertainty (Bayern has looked genuinely dominant in this cycle, which may justify a slight upward adjustment from the base model).

The market's 35% implies the conditional stage probabilities are slightly higher — perhaps 58% × 60% = 35%. That is consistent with a view that Bayern is the clear favorite at each stage rather than a modest favorite. I think "slight favorite both stages" is a more defensible read than "clear favorite both stages," given that PSG is a top-three European club and the final opponent will be a Champions League semifinalist by definition.

The 5-point delta is not large enough to be a strong contrarian call. It's the kind of pricing difference that often emerges from a thin market ($1.4k volume, 21 bettors) where a couple of enthusiast bettors push the price 2–5 points above the fundamentals.

## What would change my mind

Evidence that would move me toward YES (higher probability):

- Bayern wins 1st leg vs PSG decisively (2+ goal margin) on April 28. This would push my SF estimate to ~75% and the overall to ~40%.
- PSG suffers a major injury (Dembélé, Hakimi, Donnarumma) before semifinal. Shifts probabilities meaningfully.
- Arsenal wins their SF (my preferred opponent for Bayern).

Evidence that would move me toward NO:

- PSG wins 1st leg at Parc des Princes. Strongly shifts SF probability toward PSG.
- Bayern key injury: Kane, Musiala, or Dier missing for remainder of tournament.
- Atlético advance to final (harder opponent for Bayern).

## Confidence

**3 / 5.** The reasoning is structured (two-stage tournament model with explicit conditional probabilities) and the bracket data is confirmed. Main uncertainty sources:

- Bayern's form vs PSG is genuinely close; 53% could reasonably be 50% or 56%.
- Final opponent quality affects the second-stage estimate; I'm using a weighted average, but if Atlético advance, I'd revise down.
- Market price at 35% is within my error bars — the delta is modest (5 points), not a strong call.

This is a reasonable-confidence, small-edge prediction. If Bayern wins, my Brier is 0.49 vs market 0.4225 (market beats me on YES by 0.0675). If Bayern loses (my expected outcome), my Brier is 0.09 vs market 0.1225 (I beat market on NO by 0.0325).

Expected differential: at my own estimated 30% true probability, expected Brier = 0.30 × 0.49 + 0.70 × 0.09 = 0.147 + 0.063 = 0.21; market expected = 0.30 × 0.4225 + 0.70 × 0.1225 = 0.127 + 0.086 = 0.213. Essentially a wash at my stated probability. I take the bet because my direction is principled, even though the expected differential is negligible.

---

*(Resolution section added below after market resolves on 2026-06-29. The above is frozen.)*
