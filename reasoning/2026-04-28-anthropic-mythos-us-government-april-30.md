# Anthropic Mythos to US government by April 30 — resolves 2026-04-30

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/will-anthropic-provide-mythos-to-the-us-government-by-april-30-2026
**Polymarket market slug**: will-anthropic-provide-mythos-to-the-us-government-by-april-30-2026
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-04-28T23:48:16+00:00
**Prediction**: 60% YES
**Primary venue price at writing**: 5.5% YES (best bid 2%, best ask 9%; no last trade shown)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +54.5pp (YES-side)
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether Anthropic grants any department, agency, or subset of the United States federal government access to Claude Mythos, including Mythos Preview, by April 30, 2026 at 11:59 PM ET.

The rules say an official Anthropic or US government announcement that Anthropic has agreed to grant access is sufficient, even if actual access begins later. A consensus of credible reporting that Anthropic has agreed to grant access also suffices. Suggestions, negotiations, or general public availability do not qualify.

## Base rate

If there were no access reports, I would be close to the market: a new official Anthropic/USG access announcement inside roughly two days would be a low-probability event, and the Bloomberg/CSO reporting on April 16 by itself only said OMB was setting up protections and did not commit agencies or provide a timeline.

But this is no longer a clean prospective event. The main question is whether existing reporting already satisfies the market standard.

Relevant reporting at writing:

- Axios, April 19: `The National Security Agency is using Anthropic's most powerful model yet, Mythos Preview`, based on two sources; it also says Anthropic restricted access to roughly 40 organizations, named only 12, and one source said NSA was among the unnamed agencies with access.
- TechCrunch, April 20, repeated the Axios report and framed NSA as an undisclosed Mythos recipient: `The NSA appears to be among the undisclosed recipients, and is said to be using Mythos primarily for scanning environments for exploitable vulnerabilities.`
- Reuters headlines/newswire summaries also carried the Axios claim: `US security agency is using Anthropic's Mythos despite blacklist, Axios reports.`
- A later Axios-reprinted story on CISA said CISA does **not** have access, but explicitly contrasted that with `some other government agencies are using it`; it also said Commerce's Center for AI Standards and Innovation had reportedly been testing Mythos and again named NSA as among the organizations using Mythos.
- Separate BBC/Guardian/TechCrunch reports about unauthorized third-party/forum access do not themselves qualify. They do, however, raise the ambiguity that not every `access` story is necessarily an Anthropic grant.

## Where I differ from base rate (and why)

I am at **60% YES**, far above the 5.5% market.

The market seems to be pricing this as if no qualifying event has occurred and only a last-minute public deal can make YES. I think that misses the resolution-language interaction with the Axios reporting. The market does not require broad civilian rollout. It says **any department, agency, or subset** of the US federal government. NSA is a US federal agency. If NSA is among Anthropic's undisclosed Mythos recipients and is using Mythos Preview, that looks like Anthropic granting access to a subset of the federal government.

The reason this is not 80–90% is adjudication risk:

- Axios is the root source; TechCrunch/Reuters/Security Magazine mostly relay it rather than independently confirm it.
- The rules ask for a `consensus of credible reporting that Anthropic has agreed to grant access`, and the strongest article says `is using` / `among the unnamed agencies with access`, not a clean sentence that Anthropic signed or agreed to grant NSA access.
- Anthropic, NSA, ODNI, and the White House did not give official confirmation in the accessible reports I checked.
- The unauthorized-access stories create a possible NO argument if adjudicators treat some Mythos access as non-granted or vendor-mediated misuse.

Even after those discounts, the live probability should be dominated by resolution-source risk, not by the base rate of a new agreement. I put roughly half the mass on current Axios-plus-syndicated reporting being enough, plus some chance of further official/credible confirmation before the deadline.

## What would change my mind

Signals that would move me toward NO:

- official Anthropic or USG denial that NSA, Commerce CAISI, Treasury, or any other US federal agency has Anthropic-granted Mythos access
- credible follow-up saying the NSA/other-agency usage was unauthorized, indirect, vendor-only, or not Claude Mythos / Mythos Preview
- Polymarket/UMA guidance that a single Axios scoop plus relayed wire coverage is not a `consensus of credible reporting`

Signals that would move me toward YES:

- official statement from Anthropic, OMB, NSA, Commerce, Treasury, or another federal agency confirming access or an access agreement
- independent Bloomberg/Reuters/Politico reporting, not merely quoting Axios, that a US federal agency has Mythos access
- additional reporting that identifies Commerce CAISI or Treasury as already testing/using Mythos under Anthropic authorization

## Economics at this edge

At 60% true probability versus a 5.5% Polymarket midpoint, the headline edge is **+54.5pp**. The executable ask was much higher, about **9%**, but even paying the ask leaves about **+51pp** of pre-friction YES-side edge.

The book is wide at 2% / 9%, so the quoted midpoint understates trading cost. Liquidity is still meaningful for this experiment (~$10k liquidity, ~$35k volume), and the spread does not come close to erasing the source-driven edge. The real risk is binary adjudication: if the market refuses to count Axios-rooted reporting as consensus or grant evidence, the apparent edge is fake.

---

*(Resolution section added below after the market resolves. The above is frozen.)*

## Post-writing watch notes

- 2026-04-30T01:51Z: Polymarket rebounded to **8.1% YES** (2.2% bid / 14.0% ask; last trade 8.8%), up from the +24h checkpoint at 1.05% and **+2.6pp from entry**, but still on a wide book after the nominal market deadline. The move appears tied to April 29 Axios/Nextgov/Reuters-followed reporting that the White House is drafting guidance to let federal agencies bypass the Anthropic risk designation and onboard Anthropic tools including Mythos; Axios also repeats that agencies are clamoring for Mythos access and that NSA is already using it. This strengthens the credible-reporting backdrop, but much of the new reporting is still about draft/future guidance rather than an official access grant, so the main adjudication risk remains.
