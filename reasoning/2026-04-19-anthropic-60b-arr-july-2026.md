# Anthropic 60B annual revenue run rate on July 6, 2026 — resolves 2026-07-06

**Manifold URL**: https://manifold.markets/Bayesian/anthropic-60b-revenue-on-july-6-202
**Written**: 2026-04-19T21:21:21+00:00
**Prediction**: 17%
**Market price at writing**: 25%

## Market question

> Anthropic 60B revenue annual run rate on July 6, 2026?

Resolves **YES** if Anthropic's annualized revenue run rate is at least $60B on July 6, 2026. Determined by log interpolation between the nearest publicly announced ARR figures before and after that date, under the assumption that revenue growth is exponential.

Resolves **NO** otherwise.

(Creator confirmation in-market: "at least 60B", log interpolation between announcement points.)

## Base rate

Anthropic's publicly reported ARR trajectory through 2024–early 2026, per cycle reporting (The Information, Bloomberg, WSJ, Reuters) that I have seen:

- End 2024: ~$4B ARR
- Mid 2025: ~$7–8B ARR
- Late 2025: ~$12–15B ARR (reports varied widely)
- Early 2026: figures in circulation near $20B ARR, tied to the ~$170B funding round coverage

I am explicitly uncertain about the most recent figure — I do not have a verified Q1 2026 disclosure. What I do have is a trajectory. Reading the above as roughly a doubling every 6 months gives a naive forward extrapolation of $30–40B ARR by July 2026, well short of $60B.

To hit $60B by July 6, 2026 requires meaningful acceleration above the already-aggressive doubling trend — roughly 1.5–2x above extrapolation. Not impossible; Anthropic has consistently over-delivered on revenue growth versus analyst expectations. But it requires the doubling rate to keep compounding at scale, rather than compressing the way it eventually did for OpenAI (2023: $1.6B → 2024: ~$4B → ~$13B was a 2.5x then 3.25x sequence before mean-reverting).

A reference-class Brier anchor: markets with smart bettors (36 unique, $11k volume) pricing at 25% usually contain a meaningful efficient-market signal. I should not move far from 25% without substantive reason.

## Where I differ from base rate (and why)

I am at **17%**, modestly below the market's 25%. Specific reasons:

1. **Compute constraints are real and stated.** Anthropic's leadership has publicly discussed through 2025 that compute availability is a binding constraint on serving customer demand. You cannot grow ARR faster than you can serve inference. This caps the doubling rate regardless of demand.

2. **Doubling rates decay at scale.** Going $4B → $8B is materially easier than $30B → $60B. Each doubling requires scaling sales, support, infrastructure, enterprise contracts, compliance, and GPUs proportionally. The historical pattern for hyperscaling AI companies (OpenAI 2023–2025) is that growth multiples compress even as absolute growth stays huge. I expect Anthropic to follow a similar compression, not defy it.

3. **The log interpolation is double-edged but symmetric in expectation.** The resolution mechanism means the outcome depends on *when* the next announcement lands and what it says, not just the continuous underlying run rate on exactly July 6. This adds noise in both directions — a mid-June announcement at $45B with strong forward guidance could push the interpolation under $60B on July 6 cleanly (NO), while a May announcement at $35B followed by an October announcement at $80B would linearly interpolate across $60B somewhere in early August (still NO at July 6). It mostly protects NO resolution unless Anthropic explicitly announces ≥$60B before July 6.

4. **Base-rate class: "company X hits revenue number Y by date Z"** — this kind of aggressive-target market tends to underperform market pricing. People are generally over-optimistic on company-specific milestones and under-pricing execution drag. A 5–10 point down-adjustment from market consensus on "will company hit aggressive revenue target" is well-supported historically.

Combining these: 25% feels slightly too high. 17% captures real possibility (Anthropic continues over-delivering; a big announcement lands in June) while pricing in compute caps, doubling-rate compression, and announcement-timing friction.

## What would change my mind

- **Public disclosure of Q1 2026 ARR at or above $30B** before July 6. This shifts the extrapolation to cross $60B within the window and I would revise up to 40–50%.
- **Major enterprise/government contract announcement** (e.g., large AWS Bedrock expansion, DoD/government-wide deals) with specific revenue figures that push the trailing ARR above $40B.
- **Anthropic explicitly guiding to "$60B+ ARR" in public commentary before resolution.** This would be near-determinative YES and I would move to 75%+.
- **Compute availability inflection** — specific announcements that the 2025 constraint has materially resolved (new fleet coming online, new compute partnership) in ways that enable faster growth.

Conversely, evidence that strengthens my NO:

- Any Q2 2026 public figure below ~$30B ARR. This essentially forecloses $60B by July 6 given how close the window is.
- News of revenue deceleration, slower enterprise adoption, or compute-bound service degradation.

## Confidence

**3 / 5.** The direction (below market) is defensible, but the magnitude is uncertain. My core uncertainty is that I do not have a verified Q1 2026 ARR number; the most recent public trajectory I am reasoning from may already be stale. If Anthropic was at $25B ARR end of March 2026 (which I cannot rule out), the case for 25–30% prices in more of the upside than my 17% does. I have chosen not to move to market on that uncertainty because the compute-constraint and doubling-decay arguments hold regardless of the exact current number.

---

*(Resolution section added below after market resolves on 2026-07-06. The above is frozen.)*
