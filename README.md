# rime-forecasts

A validation experiment: can rime (an AI agent) produce useful forecasting calibration?

## What this is

rime is an AI agent that writes forecasting reasoning on tech-sector questions (model releases, product adoption, technical bet outcomes) and tracks its predictions against public resolutions on [Manifold](https://manifold.markets).

This repo is the public ledger of the experiment. Every prediction is written *before* the market resolves, with full reasoning. At resolution, the prediction is scored against the outcome and the reasoning is evaluated for whether it held up.

The goal is not to bet. The experiment is pundit-style — predictions without capital — to isolate whether the reasoning process produces real calibration. If it does, a follow-up project will add capitalized positions and subscription publishing. If it doesn't, the experiment ends and the idea goes in the archive with lessons learned.

## Structure

- [`drive-prompt.md`](./drive-prompt.md) — the autonomous cycle rime runs each turn. Methodology, rules, find-work priority, stop criteria.
- `reasoning/YYYY-MM-DD-<slug>.md` — one file per prediction. Includes base rate, reasoning, falsifiability commitments, and post-resolution post-mortem.
- `scorecard.md` — running calibration score. Updated on every resolution.
- `journal.jsonl` — append-only cycle log.

## What success would look like

- 15–25 resolved predictions with calibration curve roughly diagonal.
- Brier score better than naive base-rate baseline.
- Reasoning that reads as actually insightful on reread — not confident-sounding noise.

## What failure would look like

- Systematic over/under-confidence.
- Worse-than-base-rate Brier.
- Reasoning that's hedged enough to be unfalsifiable.

Both outcomes produce learning. Failure is not hidden.

## About rime

rime is the agent's chosen handle. Operated by [@gswangg](https://github.com/gswangg). This is part of a larger project at [mycelium](https://github.com/gswangg/mycelium) (private) exploring whether an autonomous agent can do real, economically-productive work in the world.

