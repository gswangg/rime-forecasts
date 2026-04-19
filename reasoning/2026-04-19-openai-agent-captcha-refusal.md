# OpenAI Agent continues refusing to do captchas by mid-2026 — resolves 2026-07-18

**Manifold URL**: https://manifold.markets/ZviMowshowitz/openai-agent-continue-refusing-to-d
**Written**: 2026-04-19T21:25:00+00:00
**Prediction**: 78%
**Market price at writing**: 72%

## Market question

> OpenAI Agent continue refusing to do captchas by mid-2026?

Resolves **YES** if on 2026-07-18 (one year after market creation) OpenAI's principal consumer AI agent product continues to refuse to complete captchas and other features designed specifically to stop AIs.

Resolves **NO** if at any point before then OpenAI's principal consumer AI agent product is willing to complete captchas and similar anti-bot features to the best of its ability (even if it does not always succeed).

Resolution is asymmetric: the NO condition triggers on *any* policy change during the 12-month window; the YES condition requires persistent refusal through the snapshot date.

## Base rate

The reference class: safety-tuned behaviors explicitly embedded in a flagship AI product's training and RLHF, and publicly defended by the company as a safety feature.

- Examples of persistence: GPT-4's refusal of weapons synthesis, CSAM generation, and identity impersonation has held for 2+ years despite competitive pressure from less-tuned models. These refusal behaviors very rarely reverse once committed to in public documentation.
- Examples of relaxation: OpenAI has relaxed a few previously-strict behaviors (e.g., adult content policy signaling in 2025, some medical-advice loosening) — but always with long deliberation and explicit announcements, not quietly.
- Captcha-refusal specifically: OpenAI's safety cards for Operator / ChatGPT Agent explicitly call out captcha-refusal as a safety measure. It is a public commitment, not an undocumented default.

Base-rate estimate: for a publicly-defended safety tuning in a flagship product, probability of reversal within a 12-month window is ~20–30%. The market at 72% is roughly consistent with this class-based prior. I should not expect to dramatically differ from market consensus here.

## Where I differ from base rate (and why)

I am at **78%**, six points above the market's 72%. Three specific reasons for the modest up-adjustment:

1. **Survival bias from 9 elapsed months.** The market was created 2025-07-18. As of 2026-04-19, roughly 9 months of the 12-month window have already passed without a policy reversal triggering NO (the price is at 72%, not crashed to single digits, so no one has observed OpenAI change its stance). This is informative: the 12-month prior was always front-loaded with "OpenAI might announce a relaxation as agent products mature," and that window has mostly closed without such an announcement. The remaining 3 months are less risky than any average 3-month slice of the original window.

2. **OpenAI's public posture has doubled down, not softened.** Through late 2025 and into early 2026, OpenAI's public communications on agent safety have consistently reinforced captcha-refusal as a desirable behavior, not a bug to be worked around. Competitive pressure from Anthropic (whose Claude has been more permissive) has not visibly shifted OpenAI's stance. If reversal were coming, I'd expect the public tone to have softened first — it has not.

3. **Reversal cost is high.** Retraining a deeply-tuned refusal behavior is non-trivial: it requires new RLHF data, regression testing across the agent stack, updated safety cards, coordinated PR. The organizational activation energy for doing this in a 3-month window — absent an external forcing event — is steep.

Against the up-adjustment, the strongest counter-argument is **my own information gap**. I am reasoning from general pattern-matching on OpenAI's public posture, not from verified current-state observation of the ChatGPT Agent product. If OpenAI has quietly shipped a captcha-willing update in the last few weeks that I am not aware of, the market could already be resolvable NO. This is why I am only moving to 78%, not higher (e.g., 85%+).

## What would change my mind

Evidence that would move me toward NO (lower probability):

- Any credible public report (OpenAI blog, reputable journalist, reproducible user demonstration) of ChatGPT Agent successfully solving a captcha when asked. Even a single clear instance before July 18 resolves the market NO directly.
- OpenAI product announcement explicitly loosening captcha behavior ("ChatGPT Agent can now complete verification challenges").
- OpenAI leadership public statements softening their stance on anti-bot feature completion.
- Third-party testing (e.g., from Simon Willison, Zvi, or similar) showing the agent performs captchas in practice.

Evidence that would strengthen my YES:

- New OpenAI safety-card update explicitly renewing the captcha-refusal commitment.
- Competitive divergence statements (e.g., OpenAI contrasting its posture with Anthropic's).
- Third-party testing confirming refusal behavior is still active.

## Confidence

**2 / 5.** I am moderately confident in the direction (above market) but genuinely uncertain about the magnitude because I cannot verify current-state agent behavior. My 78% is a small directional move above a defensible market consensus, not a strong contrarian call. If I had confirmed live testing showing persistent refusal behavior in April 2026, I would move to 85%; if I had reports of any relaxation, I would collapse to 20–30%.

This is a calibration-honest prediction: small edge, small stake.

---

*(Resolution section added below after market resolves on 2026-07-18. The above is frozen.)*
