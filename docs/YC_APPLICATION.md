# TariffCheck — Y Combinator Application (Draft)

> Draft prepared Jul 22, 2026 against the standard YC application question set and the Summer 2026 RFS ("AI-Native Service Companies", Gustaf Alströmer). Every answer below is written to paste directly into apply.ycombinator.com. Items only the founders can answer are flagged **[FOUNDER INPUT NEEDED]**. Verify exact question wording and character limits against the live form before submitting — YC occasionally reorders or rephrases.

---

## Company

### Company name

TariffCheck

### Describe what your company does in 50 characters or less

Three options (all ≤50 chars — pick one):

1. `Finds overpaid customs duty, drafts the protest` (47)
2. `AI duty auditor for importers and their brokers` (47)
3. `Finds duty overpayments, drafts CBP protests` (44)

Recommendation: option 1 — verb-first, states both the detection and the artifact.

### Company URL

https://tariffcheck-zeta.vercel.app *(custom domain pending — resolve the tariff-check.com brand collision before submitting; see competitive sweep action #1)*

### Demo video (1 minute)

**[FOUNDER INPUT NEEDED]** — record a 60-second screen capture of the core flow: upload invoice → AI findings → deterministic verification badge → §1514 protest draft. No talking-head needed; narrate over the screen. The "$X found across these line items" moment should land by second 20.

### What is your company going to make? Please describe your product and what it does or will do.

TariffCheck is an AI customs-duty auditor. US importers upload a commercial invoice or CBP Form 7501; Claude audits every line for misclassified HTS codes, unclaimed FTA/USMCA preferences, and wrongly applied Section 301 rates; then — the part nobody else does — every AI finding is deterministically re-verified against the complete 29,755-code official USITC HTS 2026 schedule running in-process. Rates and savings are recomputed server-side, so a hallucinated number physically cannot reach a legal document. Verified findings become a ready-to-file 19 U.S.C. §1514 protest package (with unclaimed FTA preferences routed to their correct vehicle, a §1520(d) claim, and liquidation-aware remedy selection: PSC pre-liquidation, §1514 post-liquidation, flagged if expired).

We never file. The importer of record or a licensed customs broker files — which is why customs brokers are our first customers, not our competitors. Brokers file entries but almost never audit them retrospectively: protest work is manual and hourly-unprofitable at SMB entry values, so it goes to $500/hr trade lawyers or simply doesn't happen (only ~3,750 filers produce all ~45,000 CBP protests per year; the other ~330K importers let the 180-day window close). We turn declined protest work into a new billable service line for them: batch portfolio scans (ACE ES-003 fields), 7501 PDF ingestion, and white-label protest drafts with the broker's firm named as preparer.

The durable product is the subscription: the tariff schedule changed 32 times in 2025 (vs 10 in 2024), so every static classification goes stale and every rate change re-creates the audit need.

### Where do you live now, and where would the company be based after YC?

**[FOUNDER INPUT NEEDED]** — Eymen: US (university city/state); Esat: location. Post-YC base: state intent (SF vs remote-US). Note visa status honestly (Eymen is a Turkish citizen studying in the US — F-1/OPT/CPT details matter to YC ops; they fund international founders routinely, just answer plainly). Esat's status too.

---

## Progress

### How far along are you?

Live product at tariffcheck-zeta.vercel.app, v3.3.0. Born at the Hacklanta 2026 hackathon; we kept building. Shipped and working today:

- AI invoice audit with deterministic re-verification against the full in-process 29,755-code USITC HTS 2026 schedule (the anti-hallucination layer is architectural, not a prompt)
- §1514 protest draft generation with §1520(d) routing and liquidation-aware remedy selection (PSC / §1514 / expired)
- Batch audit with ACE ES-003 entry fields; CBP Form 7501 PDF ingestion
- Line-level Section 301 coverage (10,391 subheadings)
- White-label protest drafts for API-keyed brokerage firms
- Landed-cost calculator; free full-schedule HTS lookup (our PLG top-of-funnel — Descartes paywalls this)
- 102 passing tests

In progress: a published accuracy benchmark on public CROSS ground truth — wrong-code flag rate ~95%, high-confidence false-positive rate 1.0% (0 in manual spot-check); final numbers may shift slightly before publication. No competitor publishes accuracy at all, so publishing ours with methodology is a category move they can't copy without exposing their own marketing claims.

Honestly: zero paying customers and zero design partners today. Broker pilot outreach is starting now — the ask is "run a free misclassification scan on one client's last 90 days; if we find nothing you've lost 10 minutes."

### How long have each of you been working on this? Have you been part-time or full-time?

**[FOUNDER INPUT NEEDED]** — since Hacklanta 2026 (state the month). Both currently part-time alongside university; state the plan for full-time (e.g., "full-time from the start of the batch"). YC asks this directly — do not fudge it.

### Are people using your product?

Yes — the free HTS lookup and audit flow are live and publicly usable with no waitlist. **[FOUNDER INPUT NEEDED: real usage numbers — lookups/week, audits run, unique visitors from Vercel analytics. If small, say the small number; do not say "users love it."]**

### Do you have revenue?

No. Pricing is live (Free / $349 Pro / $795 Broker Audit / $1,750+ Enterprise, plus a $149 flat CAPE Readiness SKU), but no paying customers yet.

### If you've applied with this idea before, what's changed? / If you have already participated in YC, say so.

N/A — first application. **[FOUNDER INPUT NEEDED if either founder has applied to YC before with anything.]**

### What is your tech stack?

Python/Flask backend deployed as a Vercel serverless function; React 18 + Vite frontend. The full 29,755-code USITC HTS 2026 schedule ships inside the product as a gzipped JSON DB loaded in-process (parsed MFN rates + per-program FTA special rates — no external DB call in the verification path), rebuilt from USITC source with every tariff revision. AI layer: Anthropic Claude with structured outputs, prompt caching, and a per-invoice USITC grounding block; the model layer is swappable by design — as frontier models improve, our audit improves for free while the schedule, eval set, and (soon) broker filing-outcome data stay ours. PDF ingestion: pdfplumber + PyPDF2. 102 passing tests. Inference COGS is $0.05–0.30 per invoice audit → ~90% typical gross margin at Pro pricing.

---

## Idea

### Why did you pick this idea to work on? Do you have domain expertise in this area? How do you know people need what you're making?

We started it at Hacklanta 2026, in the middle of the most volatile tariff environment in modern US history, and it refused to stay a hackathon project: every week of 2026 news created new users' problems for free.

Domain expertise, honestly: we are two CS students, not customs brokers. What we have instead: (1) we've read the statutes and built them into software — §1514, §1520(d), PSC timing, liquidation rules — to the point where our product handles remedy-vehicle routing that no funded competitor even mentions (verified across every competitor site Jul 21, 2026: nobody mentions 1520(d)); (2) we shipped the deterministic-verification architecture that the funded incumbents ($4.5–5.4M raised) don't have and don't claim — published benchmarks put autonomous AI 10-digit classification below 50% accuracy, which is exactly why "LLM + trust" products are unfit for legal documents and why our schedule-grounded, server-side-recomputed pipeline matters; (3) we're publishing accuracy on public CROSS ground truth, which no commercial player has done. In a field where the incumbents' expertise is marketing claims, our expertise is the part that's checkable.

How we know people need it: every number is from a public government source. $509.7B of 2024 US imports entered with no USMCA claim; when IEEPA tariffs made claiming worth 25%, USMCA utilization jumped from 44.8% to 88.7% in ten months — ~40 points of import value sat eligible-but-unclaimed until someone ran the numbers. CBP duty collections went $88B (FY2024) → $217B (FY2025), so every error class costs 2.5x more. And when CBP's CAPE refund portal opened in April 2026, it logged 75,300+ filings covering 11.2M entries in the first week — national-scale proof that importers act on refund tooling the moment it exists.

### Why now?

Four dated forces, all 2026-real:

1. **The IEEPA aftermath.** SCOTUS voided the IEEPA tariffs (Feb 2026); ~$166B in refunds across ~330K importers is being processed through CAPE right now. CAPE handles only the mechanical IEEPA refunds — but it just trained 330K importers to expect refunds and hands us their attention (and entry history). We model this wave explicitly as customer acquisition, not run-rate revenue.
2. **Schedule volatility.** 32 tariff-schedule revisions in 2025 vs 10 in 2024; Section 301 exclusions (178 of them) expire Nov 10, 2026 — a hard Q4 audit event. Every static classification goes stale; volatility is our retention engine, not our maintenance cost.
3. **De minimis abolition.** Suspended for non-postal modes Jun 2026, statutorily abolished Jul 1, 2027 — ~1.3B packages/yr become formal entries, crushing broker capacity exactly when we sell brokers leverage.
4. **HS 2028 renumbering.** ~8% of all subheadings re-map on a known date (Jan 1, 2028; WCO correlation tables published Apr 2026). Zero AI-native competitors have announced anything for it; we have an 18-month head start on "will your codes survive 2028."

This also fits YC's own Summer 2026 RFS, "AI-Native Service Companies" (Gustaf Alströmer): "instead of giving you a tool, they just do the work," with accounting/tax/audit and compliance as named verticals. Duty audit is exactly that — we sell the audit outcome at software margins, and the license wall (only the importer of record or a licensed customs broker can file) is the regulatory-moat defensibility that framing prizes.

### Who are your competitors? What do you understand about your business that they don't?

The category is contested, not empty — we'll say that before you do. Caspian ($5.4M, licensed broker; live §1514 protest product at 2% of claim), Pax (YC S24, $4.5M, files end-to-end on contingency), Forge (YC W24, licensed brokerage), Flexport (free "Audit Your Customs Broker" AI agent), Amari ($4.5M, broker copilot but 100% pre-entry), Reform (YC W24, broker-first but pre-liquidation only), plus GingerControl, Gaia Dynamics, Trava, Quickcode, and the ONESOURCE/Descartes/CargoWise incumbents.

What we understand that they don't — verified against every competitor's live site in a six-agent sweep on Jul 21, 2026:

1. **The strongest players are structurally locked out of the broker channel.** Caspian, Pax, Forge, Flexport, and KlearNow are all licensed brokerages — selling their audit to an independent broker means arming that broker's direct competitor. We never file, so we're the only credible audit vendor to the ~3,000 independent US brokerage firms. Channel safety isn't our marketing; it's their corporate structure.
2. **Nobody combines the triad**: schedule-wide audit → deterministic full-schedule re-verification → broker-ready §1514/§1520(d) package. Reform stops at liquidation (we are the 180 days after); Amari is 100% pre-entry; Gaia/Trava stop at findings; Caspian ships priced protests but as a rival brokerage with zero protest case studies.
3. **Nobody claims deterministic verification, nobody mentions §1520(d), and nobody publishes accuracy.** Published research puts autonomous 10-digit classification below 50%; the competitors' answer is marketing numbers (one claims "nearly 100%" with no methodology). Our answer is an architecture where a hallucinated rate cannot reach a filing, plus a published benchmark on public CROSS ground truth — a move they can't follow without exposing their own claims.

The window is quarters, not years — Caspian and Pax both moved into protests in 2025–26. Our speed answers: published accuracy, 7501/ES-003 ingestion (shipped), and broker pilots now.

### How do or will you make money? How much could you make?

Hybrid: SaaS backbone + capped success-fee accelerant.

- **Tiers:** Free (unlimited HTS lookup, 2 audits/mo — the PLG funnel) / Pro $349/mo (SMB importers, 300 entries/mo, protest packages) / Broker Audit $795/mo (audit-only, your license files, no success fee) / Enterprise from $1,750/mo (unlimited entries, white-label drafts, bulk portfolio scans). One-time $149 CAPE Readiness SKU, time-boxed to the refund window.
- **Success fee: 2–3% of verified recovery, capped**, only on managed recoveries filed via partner brokers (3% Pro, $750 min/filing, $25K/yr cap; 2% Enterprise, $50K/yr cap; always 0% when the client's own broker files). Deliberately priced against Caspian's published 2% — we match the disruptive number while being the only player structurally incapable of competing with the filing broker. The drawback industry charges 10–25%; we are not that.
- **Why not pure contingency:** we don't file, and recovery closes 60–180+ days later outside our control — building the P&L on cash we can't collect is unsound, and contingency poisons the broker channel (brokers hate revenue-sharing). ~90% of the modeled revenue mix is recurring SaaS.
- **Unit economics:** inference COGS $0.05–0.30/audit → ~75% gross-margin floor, ~90% typical.
- **How much:** honest sizing — the recurring recoverable pool is single-digit billions/yr (CBP paid $6.7–9.3B/yr in total refunds, FY2024–25, DHS audited financials), not the "tens of billions" vendor folklore. TAM $1.5–3B/yr; SAM $400–700M/yr (what broker-first, US-only, §1514-mechanism actually addresses); SOM $7–11M revenue by end of year 3. $1M ARR = 25 broker firms + 150 importer subscriptions = 0.8% of the enumerable 3,000-firm broker universe and 0.1% of regular importers. The buyer universe is a spreadsheet, not a market-sizing exercise, and the product's first output is a dollar figure ("we found $X in your last 12 months"), which collapses sales cycles.

### Which category best applies to your company?

B2B SaaS — Fintech-adjacent / Compliance. RFS fit: AI-Native Service Companies (primary); Supply Chain 2.0 and SaaS Challengers (supporting).

---

## Equity

### Have you formed a legal entity? Have you taken any investment? What is the equity breakdown among founders?

**[FOUNDER INPUT NEEDED]** — as of this draft: pre-funding, pre-revenue, and (assumed) no entity formed yet. Founders must state: (1) whether any entity exists anywhere (US or Turkey); (2) equity split between Eymen and Esat — YC strongly prefers near-equal splits and asks for the exact percentages; (3) confirm zero outside investment; (4) any IP assignment questions (code written while enrolled — check university IP policy).

---

## Founders

### Founder profiles

**[FOUNDER INPUT NEEDED]** — each founder completes their own YC profile (education, work history, LinkedIn/GitHub, personal video). Skeleton from known facts:

- **Eymen Keyvan** — backend & full-stack. 3rd-year CS student in the US; Turkish citizen. Built the USITC schedule pipeline, deterministic verifier, protest-drafting engine, and API. [Add: university, notable projects/internships, GitHub.]
- **Esat Sarac** — frontend. Built the React product surface: audit flow, broker portal, lookup, dashboard. [Add: education, location, background.]

### How long have the founders known one another and how did you meet? Have any of the founders not met in person?

**[FOUNDER INPUT NEEDED]** — state plainly how you met and whether you teamed up at/before Hacklanta 2026.

### Who writes code, or does other technical work on your product? Was any of it done by a non-founder?

Both founders. Eymen: backend, data layer, AI pipeline, verification engine. Esat: frontend. **[FOUNDER INPUT NEEDED: confirm no non-founder contributors; disclose AI-assisted development plainly if asked — YC in 2026 expects founders to use AI tools and cares only that you understand every line you ship.]**

### Founder video (1 minute)

**[FOUNDER INPUT NEEDED]** — both founders on camera, unscripted tone: who you are, what TariffCheck does (use the 50-char line), the one thing that makes it different ("a hallucinated number cannot reach a protest letter"), and that you're already live.

---

## Curious

### What convinced you to apply to Y Combinator? Did someone encourage you to apply?

The Summer 2026 RFS describes our company: AI-native service companies in compliance and audit that "just do the work" instead of selling a tool. Also unavoidable: our four most dangerous competitors (Pax S24, Forge W24, Reform W24, Trava W25) are YC companies — the network that funded the category's filers is the right place to fund the category's non-filer. **[FOUNDER INPUT NEEDED: any personal encouragement story, YC alumni you've spoken to.]**

### How did you hear about Y Combinator?

**[FOUNDER INPUT NEEDED]** — answer honestly and briefly (Hacker News, a professor, a YC startup you used, etc.). This question has no wrong answer except an embellished one.

---

## Pre-submission checklist (not part of the application)

1. Resolve the tariff-check.com brand/domain collision (competitive sweep action #1) — ideally before the URL goes on the form.
2. Record demo video + founder video.
3. Fill every [FOUNDER INPUT NEEDED]: equity split, entity status, visa statuses, locations, full-time plan, usage numbers, bios, how-you-met.
4. Finalize and publish the CROSS benchmark numbers (currently "in publication" — update the Progress answer with final figures if they land before submission).
5. Pull real usage metrics from Vercel analytics for the "are people using it" answer.
6. Land at least one broker pilot conversation you can name-drop as "in progress" — even "5 outreach calls, 2 scans scheduled" beats a blank.
