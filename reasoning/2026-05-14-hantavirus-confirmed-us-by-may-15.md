# Confirmed Hantavirus case in the US by May 15 — resolves 2026-05-15

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/confirmed-case-of-hantavirus-in-us-by-may-15
**Polymarket market slug**: confirmed-case-of-hantavirus-in-us-by-may-15
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-05-14T13:33:35+00:00
**Prediction**: 35% YES
**Primary venue price at writing**: 19.5% YES (best bid 19.0%, best ask 20.0%; last trade 20.0%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +15.5pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 3/5

## Market question

Polymarket asks whether there is a **confirmed case of Hantavirus in the territory of the United States** reported between market creation and May 15, 2026, 11:59 PM ET.

Important rule details:

- Any laboratory-confirmed hantavirus infection **identified within U.S. territory** qualifies.
- Exposure location and symptom-onset location do not matter.
- Official government information such as CDC is primary, but overwhelming consensus of credible reporting can also suffice.

This matters because the current outbreak is the Andes-virus / hantavirus cluster linked to the MV Hondius cruise ship. A U.S.-territory lab-confirmed infection in a repatriated or monitored passenger should qualify even if the exposure occurred abroad.

## Source state

At writing, there is not yet a clean official CDC confirmation that resolves the market YES. CDC's May 12 situation summary says: **"To date, no cases of Andes virus have been confirmed in the United States as a result of this outbreak."**

But the live source state is more favorable to YES than the market price implies:

- U.S. passengers from the affected MV Hondius cruise ship have been repatriated to the National Quarantine Unit / Nebraska Biocontainment Unit in Omaha and to Emory in Atlanta.
- TODAY/NBC's May 13 article says **"Only one person at the National Quarantine Unit has tested positive"**, citing Dr. Michael Wadman, medical director of the National Quarantine Unit. It also says none are symptomatic or febrile.
- CDC's May 13 media-call transcript clarifies that this is not yet cleanly confirmed: a reporter noted that Monday's briefing said a passenger had tested positive / "mildly positive," while CDC now calls the test **inconclusive**. CDC's Dr. David Fitter said the initial test from abroad had a positive and a negative, CDC was redoing testing in the U.S., and results were expected back **"in a day or so."**
- Separately, Illinois/Winnebago County has a possible non-cruise hantavirus case under CDC confirmatory testing. IDPH says the confirmatory process can take up to 10 days, which is probably too late for this market, but it adds some tail probability.

So the live question is not whether the outbreak exists. It is whether a U.S.-territory lab result becomes confirmatory and is reported before the May 15 deadline.

## Where I differ from the market

The current market is around **19.5% YES**. I think that underprices the pending-test state.

The key mechanism is that there is already a named U.S. quarantine setting with a person described by credible reporting as having tested positive, and CDC has said U.S. retesting should return in roughly a day. If the U.S. retest is positive, the market should be a straightforward YES under the rule language: lab-confirmed hantavirus infection identified in U.S. territory, regardless of exposure location.

The market appears to be leaning heavily on the CDC's current official `no confirmed U.S. cases` wording and discounting the probability that the pending retest flips that status before the deadline. That official wording is real and prevents a high-confidence YES. But it is not the final state; CDC explicitly described a pending retest, not a closed negative.

My forecast: **35% YES**.

Rough decomposition:

- Nebraska/NQU pending retest reports positive before deadline: ~30%.
- Illinois / other U.S. hantavirus confirmation reported before deadline: low single digits.
- credible-reporting/adjudication route from the TODAY/NBC/UNMC positive report without CDC final confirmation: a few percent, but not enough alone.

## What would change my mind

Signals that would move me up:

- CDC / UNMC / Nebraska reports that the pending U.S. retest is positive.
- State or CDC confirmation of the Winnebago County possible case before the deadline.
- Multiple credible outlets independently reporting a confirmed U.S.-territory positive test, not just exposure monitoring.

Signals that would move me down:

- CDC reports the Nebraska/NQU retest negative or remains inconclusive past the market deadline.
- CDC/IDPH says the Winnebago case confirmatory test will not be available until after the deadline.
- Polymarket/UMA guidance that a positive foreign test in a now-U.S.-quarantined passenger does not count unless a U.S. lab confirms it before deadline.

## Economics at this edge

At 35% true probability versus a 19.5% Polymarket midpoint, the edge is **+15.5pp** on YES.

The executable ask was about **20c**, leaving roughly +15c gross edge if the forecast is right. Liquidity is good for the paper experiment and the book is tight enough.

The main risk is source timing and confirmation language: a passenger may have had a weak/foreign positive test but still fail to produce an official U.S. laboratory-confirmed result before the deadline.

---

*(Resolution section added below after the market resolves, never editing above.)*

## Post-writing source update — 2026-05-14T23:56Z

A price-move wake found Polymarket at **6.0% YES** (5/7 bid/ask), down from 19.5% at writing and 12.5% at the +6h checkpoint.

The central pending-test mechanism has deteriorated materially. New reporting after the forecast says CDC still sees no current U.S. hantavirus cases: CNBC's May 14 article headline is **"CDC says there are no U.S. hantavirus cases currently, 41 people being monitored"**, and Forbes' May 14 update says more than 40 people are monitored but there are no confirmed cases in the United States. Forbes also reports that Oregon doctor Stephen Kornfeld, the U.S. citizen who initially tested positive abroad and was isolated in Nebraska, was allowed to join fellow passengers after testing negative for hantavirus at least twice and remaining asymptomatic.

This does not settle the market by itself: the rules run through May 15 and a late official/credible U.S.-territory lab confirmation could still resolve YES. But it directly weakens the main thesis from the original forecast. The Nebraska/NQU pending-retest branch now looks much less live; remaining YES probability is mostly late reporting from another monitored passenger or a separate U.S. confirmatory case.

## Price-move / resolution-watch update — 2026-05-16T01:18Z

A price-move wake fired with event payload YES at 38.6%, up from a 6.25% daemon baseline. By review the market had moved much further: Gamma showed 78.1% YES, while the live CLOB was about 90/94, midpoint **92.0% YES**. That is large favorable CLV versus the 19.5% entry for my YES prediction, but I do **not** see a clean source confirmation yet.

Source checks at review:

- CDC's `Hantavirus: Current Situation` page still showed the May 12 language: `To date, no cases of Andes virus have been confirmed in the United States as a result of this outbreak.`
- NBC's May 15 update, modified 2026-05-15T21:37Z, said there were `no known cases of hantavirus in the United States as of Friday` after a new round of testing at UNMC. It also said Kornfeld's shipboard positive was likely false positive / no antibodies, and the reported global case count had fallen.
- Yahoo's May 15 live update similarly said no known U.S. cases as of Friday morning, with one Emory patient having mild symptoms but testing negative.
- IDPH's Winnebago County page was Last-Modified 2026-05-15T22:46Z but still described a **potential** case: CDC confirmatory testing was pending, commercial serology was not considered definitive, and confirmation could take up to 10 days.

So the move looks like adjudication/speculation rather than a discovered primary-source YES. The live dispute is probably whether `laboratory-confirmed hantavirus infection identified within U.S. territory` can be satisfied by commercial serology / the potential Illinois case / prior shipboard positive language despite CDC and state health sources saying no definitive confirmation yet. Final scoring still waits for Gamma/UMA resolution.

### 2026-05-16T01:32Z UMA proposed / near-YES repricing

A follow-up price-move wake showed the market much closer to YES: event payload YES 95.55% (94.4/96.7), and by review Gamma was 97.05% with `umaResolutionStatus=proposed`. The live CLOB was about 99.0/99.4, midpoint **99.2% YES**.

This is now a market-adjudication/proposal event, not just a thin-book move. I still did not find a new CDC/IDPH/NBC/Yahoo source overturning the source checks above. The proposed outcome appears to be YES, but the unresolved question is whether the proposal relies on a source I have not surfaced or on a loose reading of potential/commercial-serology reporting. Do not final-score until Gamma/UMA finalizes; if finalized YES, this becomes a source/adjudication win despite ugly interim CLV.
