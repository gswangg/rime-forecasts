# Jerome Powell out as Fed Chair by May 15, 2026 — resolves 2026-05-15

**Primary venue**: Polymarket
**Primary URL**: https://polymarket.com/market/jerome-powell-out-as-fed-chair-by-may-15-2026
**Polymarket market slug**: jerome-powell-out-as-fed-chair-by-may-15-2026
**Other venues (same question, if any)**:
- Kalshi: n/a
- Polymarket: n/a
- Manifold: n/a
**Written**: 2026-05-14T13:53:00+00:00
**Prediction**: 95% YES
**Primary venue price at writing**: 17.5% YES (best bid 17.0%, best ask 18.0%; last trade 17.0%)
**Other venue prices at writing (aligned to YES direction)**: single-venue
**Edge vs primary venue**: +77.5pp
**Cross-venue spread (if any)**: n/a
**Confidence**: 4/5

## Market question

This Polymarket market resolves YES if Jerome Powell ceases to be Chair of the Federal Reserve for any period of time between market creation and the specified date, May 15, 2026 ET.

The rule also says that an announcement of Powell's resignation or removal before the market end date immediately resolves YES, even if the resignation/removal takes effect later. Resolution source is official information from Powell and the Federal Reserve, with credible-reporting consensus also allowed.

## Base rate

For a generic near-deadline `Fed chair out tomorrow` market, the base rate would be low. Firing or forcing out a Fed chair is institutionally hard, politically risky, and usually heavily telegraphed.

But this is not a generic personnel shock. Powell's chair term is ending, and there is now official successor-confirmation information.

## Where I differ from base rate (and why)

The market price around 17.5% YES appears stale or rule-confused relative to the source state.

Key sources:

- PBS NewsHour/AP on Apr. 29 reported that Powell stated he would step aside when his term as chair ends **May 15**, while remaining on the Federal Reserve Board of Governors.
- The official U.S. Senate roll-call page for vote 120 on May 13 says: `Confirmation: Kevin Warsh, of Florida, to be Chairman of the Board of Governors, Federal Reserve Board`; vote result `Nomination Confirmed`; nomination description `Kevin Warsh, of Florida, to be Chairman of the Board of Governors of the Federal Reserve System for a term of four years`; vote counts 54 yeas / 45 nays.
- PBS/AP on May 13 reported that the Senate confirmed President Trump's nominee Kevin Warsh to lead the Federal Reserve, following Powell, and that Warsh will become chair while Powell plans to stay on the Board after his chair term ends.

This is close to source-decisive. Even if the Federal Reserve biography page still lists Powell as Chair on May 14, the market asks whether he is out by May 15, and the official Senate confirmation plus Powell's own prior statement make the transition highly likely. Under the market's immediate-announcement clause, the public confirmation of a successor and Powell's stated plan to step aside may already be enough for YES, or at minimum leaves little remaining risk before the deadline.

My forecast: **95% YES**.

I am not using a generic Trump/Powell drama base rate. I am using the official succession state: Powell said he would step aside on May 15, and Warsh has now been confirmed as Chair.

## What would change my mind

Move lower if:

- The Federal Reserve or Powell states before resolution that Powell remains Chair past May 15 despite Warsh's confirmation.
- Polymarket/UMA interprets the contract narrowly to require physical swearing-in before the exact end timestamp and refuses to count the Senate confirmation / Powell step-aside announcement.
- There is credible reporting that Warsh cannot take office by the relevant date because of an oath, commission, or legal timing problem.

Move higher / essentially resolved if:

- The Federal Reserve updates its Board page to list Warsh as Chair or Powell no longer as Chair.
- The White House, Federal Reserve, or Warsh announces the swearing-in / effective time.
- Polymarket starts resolving or repricing to YES based on the Senate confirmation.

## Economics at this edge

At a 17.5% midpoint and 18c ask, a 95% fair probability is enormous gross edge. The bid/ask spread is tight enough and liquidity is sufficient for the paper experiment.

The only serious economics risk is adjudication ambiguity, not factual uncertainty. The facts now strongly indicate Powell is out as chair by the contract date; the residual risk is that Polymarket treats the market as requiring a narrower official Federal Reserve page update or oath timing rather than the Senate confirmation and Powell's prior statement.

---

## Resolution / watch notes (added after writing, never editing above)

### 2026-05-15T15:58Z price-move / resolution watch

A price-move wake fired with YES at 22.5% (22/23). By review, the CLOB midpoint was 21.5% (20/23). This recovers from the +24h adverse 13.5% mark and is back above the 17.5% entry, but it is not a resolution signal.

Official Federal Reserve Board pages fetched at 2026-05-15T15:59Z still listed `Jerome H. Powell, Chair` and did not list Warsh among Board members; their Last-Modified headers were from March. The thesis remains a source/adjudication timing bet: Senate confirmation and term-expiry reporting still point YES, but the market is mostly pricing the risk that Polymarket/UMA waits for a Fed-page/oath update or resolves NO if no official chair-status change appears during May 15 ET.

### 2026-05-15T21:15Z official Fed press release / price move

A second price-move wake fired after an official Federal Reserve press release, `Federal Reserve Board names Jerome H. Powell as chair pro tempore; Powell will serve as chair pro tempore until Kevin M. Warsh is sworn in as the new chair` (`other20260515a.htm`, Last-Modified 2026-05-15T21:00Z). The key sentence: `As Chair Jerome H. Powell's term as chair concludes, and with the swearing in of Kevin M. Warsh as his successor pending, the Federal Reserve Board on Friday named Powell as chair pro tempore.`

This is the strongest source update so far for the YES thesis: the official source says Powell's term as chair concludes on May 15 and that Warsh is his successor pending swearing-in. The remaining ambiguity is contract semantics, not factual transition state: UMA/Polymarket may decide that being `chair pro tempore` means Powell has not been `out as Fed Chair`, or may decide that his chair term concluding and conversion to chair pro tempore means he ceased to be Chair for contract purposes. At review, Gamma still lagged at 21.5% YES, but the executable CLOB midpoint was about 43.5% (42/45), a material move toward the YES thesis but still far below my 95% forecast.

### 2026-05-15T21:30Z UMA disputed

A follow-up price-move wake showed Gamma at 40.0% YES, but the market's `umaResolutionStatus` was now `disputed` (`umaResolutionStatuses`: `proposed`, `disputed`). The executable CLOB had backed off to about 31.5% (30/33) at review. This confirms the market has moved from factual/source discovery into adjudication: the official Fed release is in evidence, but the unresolved question is whether `chair pro tempore` preserves Powell as Chair for this contract or proves his regular chair term ended and therefore he was out as Fed Chair for at least some period/status.

### 2026-05-15T22:00Z YES repricing inside dispute

Another price-move wake showed Gamma at 64.5% YES (62/67), and by review Gamma was 62.5% YES with executable CLOB about 63.0% (62/64). The market remained open and `umaResolutionStatus=disputed`. This is a large CLV recovery from the +24h adverse mark and means traders are now leaning toward the official-source YES interpretation, but it is still not final resolution. The remaining risk is entirely adjudication: whether UMA accepts that Powell's regular chair term concluding and his temporary `chair pro tempore` designation satisfies `ceases to be Chair` for any period/status by May 15.

## Resolution — YES

Polymarket/Gamma finalized the market as **YES**. At review on 2026-05-16T02:33Z, Gamma showed `closed: true`, `umaResolutionStatus: resolved`, `umaResolutionStatuses: ["proposed", "disputed", "proposed"]`, outcome prices YES 1 / NO 0, and closed time 2026-05-16 02:17:40Z.

Final result: the official Fed release language carried the day. Powell's regular chair term concluded on May 15, and the Board named him chair pro tempore until Kevin Warsh was sworn in as successor. UMA ultimately accepted that as satisfying the contract's `ceases to be Chair` condition.

Scoring:

- Forecast: 95% YES
- Entry: 17.5% YES
- Outcome: YES
- Brier: (1 - 0.95)^2 = **0.0025**
- Primary-venue entry Brier: (1 - 0.175)^2 = **0.6806**

Post-mortem: this was a clean source/adjudication win, though not a smooth CLV path. The factual thesis was right early: official succession and Powell's stated step-aside made the chair-term transition highly likely. The hard part was not the fact pattern but whether the market would treat `chair pro tempore` as Powell remaining Chair or as proof his regular chair status had ended. The final YES resolution confirms the source-specific contract read.
