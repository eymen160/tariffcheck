# TariffCheck — Investor Pitch

> Brokers can file but can't afford to audit; importers can audit but need help preparing. TariffCheck scans invoices against the full USITC schedule, finds overpaid duty, and hands a licensed human a ready-to-file protest.

**Live product:** https://tariffcheck-zeta.vercel.app · **Repo:** github.com/eymen160/tariffcheck

---

## 1. Problem

US importers systematically overpay customs duties — misclassified HTS codes, unclaimed FTA/USMCA preferences, and wrongly applied Section 301 rates. Every number below is from a public government source, not a vendor estimate:

- **$509.7B of 2024 US imports entered with no USMCA claim** (USITC import data) — duty paid at full rates on goods that could have qualified for 0%. When IEEPA tariffs suddenly made claiming worth 25%, USMCA utilization jumped **from 44.8% (Jan 2025) to 88.7% (Nov 2025)** — proof that roughly 40 points of import value sat eligible-but-unclaimed until someone ran the numbers.
- **~45,000 protests reach CBP per year, from only ~3,750 filers** (CBP, 87 FR 34894). Protest capability is concentrated in a tiny sophisticated population; the long tail of ~330K importers lets the 180-day window close.
- **CBP duty collections jumped from $88B (FY2024) to $217B (FY2025)** (CBP Trade Statistics) — every error class now costs 2.5x more.
- The tariff schedule was revised **32 times in 2025, versus 10 in 2024** (USITC), and HS 2028 will re-map ~8% of all subheadings on a known date. **Every static classification goes stale.** A code that was right in 2024 is wrong in 2026.

The parties who could fix this don't: brokers file entries but almost never audit them retrospectively — protest work is manual and hourly-unprofitable at SMB entry values, so it goes to trade lawyers at $500+/hr or simply doesn't happen. Importers feel the pain on their P&L but have no way to check their broker's work. The 180-day protest window under 19 U.S.C. §1514 quietly expires.

## 2. Why Now

The Supreme Court's *Learning Resources v. Trump* decision (Feb 2026) voided the IEEPA tariffs, and the Court of International Trade ordered **~$165B in IEEPA refunds**. CBP's CAPE refund portal went live in April 2026 and logged **75,300+ filings covering 11.2M entries in its first week**.

That is proof, at national scale, that importers act on refund tooling when it exists. We say this plainly: **the CAPE/IEEPA wave is one-time, and we model it as customer acquisition, not run-rate revenue.** The wave hands us the importer's attention (and their entry history); the durable product is continuous classification audit — every future tariff change re-creates the need, so the subscription renews itself.

## 3. Product

One artifact, one flow, nobody else owns it end to end:

1. **Invoice in** — upload a PDF or paste entry lines.
2. **AI findings** — Claude audits every line: misclassification, missed FTA claims, Section 301 exposure, with legal basis (GRI reasoning) per finding.
3. **Deterministic re-verification** — every finding is checked against the complete **29,755-code official USITC HTS 2026 schedule that ships inside the product**. Rates and savings are recomputed server-side; a hallucinated number physically cannot reach a legal artifact.
4. **Ready-to-file §1514 protest letter** — generated only from verified numbers, handed to the importer of record or their licensed broker to file. *We prepare; a licensed human files.*

Around that core:

- **Batch client-portfolio scanning** for brokers — up to 100 entry lines per request, fully deterministic against the USITC schedule, built for "scan one client's last 90 days in minutes."
- **Landed-cost calculator** — MFN + Section 301 + MPF/HMF + FTA comparison per code/origin/value.
- **Free HTS lookup** on the full schedule — the PLG top-of-funnel that Descartes paywalls.

## 4. Moat

The model proposes; our data layer disposes. Every AI finding is deterministically re-verified against the official 29,755-code USITC schedule running in-process, so a hallucinated rate physically cannot reach a protest letter — the anti-"GPT-wrapper" proof is architectural, not aspirational. The schedule rebuilds from USITC source with every tariff change, which turns 2025–26 volatility from a maintenance cost into a customer-value event. On top of the schedule we compound an evaluation set of verified findings and, as broker partners come online, a filing-outcome loop: which findings got filed, which protests were granted. The model layer stays swappable — as frontier models improve, our audit gets better for free while the data and outcome layers stay ours. That stack — schedule + eval set + broker outcome loop — is what an incumbent or a wrapper cannot copy by calling the same API.

## 5. Market

Honest math, built to survive diligence — the recurring recoverable pool is **single-digit billions per year** (CBP paid $6.7–9.3B/yr in total refunds, FY2024–25, DHS audited financials), not the inflated "tens of billions" folklore vendors circulate:

- **TAM — $1.5–3B/yr.** The recovered-money fee pool: 10–30% contingency on the recurring recoverable pool (the fee band the drawback/recovery industry actually charges today) ≈ $0.5–1B/yr in service fees, plus the $1.2–2.7B global trade-management-software category an AI-native challenger takes share from. The one-time ~$166B IEEPA refund event sits on top of this as 2026 customer acquisition, not run-rate.
- **SAM — $400–700M/yr.** What our mechanism (classification audit → §1514 protest package) and motion (broker-first, US-only) actually address: ~3,000 active brokerage firms ($300–500M at realistic ACVs) plus the recovery fees flowing through them. Honestly excluded: duty drawback (§1313), non-US regimes, filing itself (license wall), and CAPE-mechanical IEEPA refunds.
- **SOM — $8–12M revenue by end of year 3.** Bottom-up: 150 broker-firm accounts (~5% of the 3,000-firm universe) at ~$25K ACV + 1,500 self-serve importer subscriptions at ~$3.5K + $1–2M in success fees on managed recoveries. Note the mix: at maturity roughly half of this is recovery-linked, not pure SaaS — we price the way this market demonstrably pays.

## 6. Business Model

**Hybrid: SaaS backbone + success-fee accelerant.**

| Tier | Price | For |
|---|---|---|
| Free | $0 | Unlimited HTS lookup, 2 audits/mo — the PLG funnel |
| Pro | **$349/mo** ($299/mo annual) | SMB importers: 300 entries/mo, full verified findings, protest packages |
| Enterprise / Broker | **from $1,750/mo** | Brokerages: unlimited entries, bulk client-portfolio scanning, white-label drafts |

Plus a **10% success fee** charged only on managed recoveries filed via partner brokers (8% or waived for brokers filing themselves).

Why not pure contingency? Because we don't file — the importer of record or a licensed broker does, and recovery closes 60–180+ days later, outside our control. Building the P&L on cash we can't collect is structurally unsound for a non-filer: fee leakage, unenforceable collection, lumpy non-recurring revenue valued at 1–2x instead of software multiples — and contingency pricing would poison the broker channel, since brokers hate revenue-sharing and love per-seat tools. Subscriptions monetize the durable product (continuous audit + tariff-change monitoring); the success fee still delivers the "we sell the outcome" upside where a partner broker closes the loop.

Full pricing detail: [docs/PRICING.md](docs/PRICING.md).

## 7. Path to $1M ARR

**"$1M ARR = 25 broker firms + 150 importers — 0.8% of brokers, 0.1% of regular importers."**

| Milestone | Composition | ARR |
|---|---|---|
| M0–4: PLG proof | Free lookup live (done), 5K MAU on lookup, 40 Pro self-serve @ $3.6K | **$144K** |
| M4–9: Broker wedge | 8 broker Enterprise @ $22K (design partners → paid; zero design partners today — this is the plan) + 90 Pro | **$500K** |
| M9–15: $1M | 25 broker firms @ $22K ($550K) + 150 Pro @ $3.6K ($540K) + ~$75–100K realized success fees | **~$1.15M** |

Why credible: (a) the buyer universe is enumerable — 3,000 broker firms is a spreadsheet, not a market-sizing exercise; (b) the product's first output is a dollar figure ("we found $X across your last 12 months of entries"), which collapses sales cycles; (c) tariff volatility re-creates the audit need with every rate change.

## 8. Competition

| Player | What they are | Threat | Where we win |
|---|---|---|---|
| **Caspian** ($5.4M seed, licensed broker + ABI vendor, lists §1514 protests as a product) | Full-stack AI duty recovery: audit + PSC + protests + drawback, files end-to-end | **Highest** | We are channel-safe for brokers — Caspian *is* a brokerage, so selling to brokers means arming a rival. Our deterministic re-verification and transparent pricing vs their service-flavored stack |
| **Amari AI** ($4.5M seed, First Round/Pear; 30+ brokerages) | AI copilot for broker *entry operations* (pre-entry) | High | Same buyer, different moment: they optimize filing, we recover money already lost. Post-entry audit→protest is a product they'd have to build; we ship it today |
| **Gaia Dynamics** (AI Fund) | AI classification + "Tariff Audit Engine"; protest templates advertised on blog only | High | Protest capability appears aspirational; no deterministic verification story; no broker-first motion |
| **Flexport** | Free "Audit Your Customs Broker" tool; files as broker of record | Ecosystem | Structurally cannot sell to independent brokers — it's their predator. *"Flexport gives your clients a free tool to audit you. We give you the same audit, plus drafted protests, first."* |
| **Pax AI** (YC S24, $4.5M) | Drawback-led recovery, 1–30% contingency, licensed broker | Medium | Their audit is reconciliation, not schedule-wide misclassification; our 8–10% fee undercuts their band; brokers distrust a rival brokerage |
| **Reform** (YC W24) | PSC audit + filing for brokers (pre-liquidation) | Medium | PSC-only — no §1514, no recovery economics. We are the post-liquidation half they lack |
| **Quickcode** (broker tier from $749/mo) | Explainable-AI HTS classification, embedded in Magaya | Medium | Catalog classification, not paid-entry audit; no overpayment math, no protests |
| **Trava** (YC W25) | AI entry audits for importers | Medium | Stops at "evidence your broker can act on" — no protest drafting; importer-facing |
| **ONESOURCE / Descartes / CargoWise** | Incumbent GTM suites + broker rails; shipped pre-entry AI assist only in 2025–26 | Watch | No post-entry refund-finding, no protest drafting, no SMB price point — but Descartes owns the NetCHB rails and is a serial acquirer |

As of July 2026, **no competitor verifiably ships the full flow we do**: schedule-wide misclassification audit → deterministically verified dollars → ready-to-file §1514 protest package, sold broker-first and never filing. But Caspian lists protests, Gaia markets templates, and Amari owns our buyer — the window is measured in quarters. Our answer is speed to referenceable broker case studies, published verification accuracy, and entry-data integrations (NetCHB/CargoWise import).

## 9. YC RFS Fit

Primary: **AI-Native Service Companies** (Gustaf Alströmer, Summer 2026) — "they don't sell software, they just do the work," with accounting/tax/audit, compliance, and brokerage as named verticals. Customs-duty audit sits at the intersection of three of the four. We sell the audit outcome on software margins; the license wall (only the IOR or an LCB can file) is exactly the regulatory-moat defensibility YC's 2026 framing prizes. Supporting motifs: Supply Chain 2.0's "rules change quarterly" volatility wedge and the SaaS-Challenger posture against the ONESOURCE/Descartes codebase class.

## 10. Honesty Ledger

Said before it's asked:

- **Zero design partners today.** The broker design-partner motion is the plan, not the traction.
- **Success-fee revenue lags 60–180 days** behind bookings — CBP liquidation timelines are outside our control.
- **CAPE/IEEPA revenue is one-time and we don't take success fees on CAPE-mechanical refunds** — the free CBP portal handles those; our fee base is misclassification / missed-FTA / Section 301 recoveries, which CAPE cannot touch.
- **We prepare filings; the importer of record or a licensed broker files.** We never file with CBP and never claim to. We know 19 CFR 111.1 defines "customs business" broadly (see CBP ruling H350722 on AI classification) — a formal counsel opinion and/or CBP ruling request on the self-file + broker-in-the-loop model is a funded-day-one item, and a partner-broker network is the 12-month structural answer.
- **The category is contested, not empty.** Caspian, Amari, Gaia, Pax, Reform and Flexport all moved into adjacent lanes in 2025–26; our specific flow is unoccupied but the window is quarters, not years.
- **AI classification is a screen, not an oracle.** Published benchmarks put autonomous 10-digit accuracy below 50%; that's exactly why every finding is deterministically re-verified against the schedule and priced for human broker review — and why wrong-code candidates die before reaching a letter.
- No fabricated customers, logos, or testimonials — every market number above traces to a public government source (USITC, CBP, DHS AFR, Federal Register), not vendor folklore.

## 11. Roadmap

Next 90 days (the three experiments that most reduce uncertainty):

1. **Broker-workbench pilots** — 5 licensed brokers/trade attorneys running the tool on real backlogs (protective protests on the contested ~$30B finally-liquidated IEEPA segment + Section 232/301 classification reviews). Metric: $ of protests drafted-and-filed per broker-hour vs baseline.
2. **FOIA CBP for protest grant rates, recovery amounts, and PSC volumes** — this data exists nowhere publicly; owning it is both the honest pitch slide and a marketing moat. In parallel: counsel opinion / CBP ruling request to convert the 19 CFR 111.1 gray zone into a documented safe harbor.
3. **Precision-on-real-data benchmark** — free audits for 10 importers in exchange for entry data; publish validated-recovery-per-review-hour and the audit's precision after broker review. This becomes the accuracy page brokers cite in their own compliance files.

Then:

4. **CROSS rulings corpus** — ground every finding in cited CBP rulings, raising defensibility and ASP.
5. **ACE report ingestion + NetCHB/CargoWise entry-data import** — audit actual filed-entry data, not just invoices; the integration is also the distribution channel.
6. **Tariff-change monitoring** — per-SKU alerts turning every rate change (32 in 2025 alone; HS 2028 re-map incoming) into a customer-value event; the retention layer.
7. **EU/UK/CA schedules** — same architecture, new customs regimes.

## 12. Team

*Placeholder — founder bios and relevant credentials to be added.*

| Name | Role |
|---|---|
| Eymen Keyvan | Full-Stack & Deployment |
| Esat Sarac | Backend & AI Integration |
| Selcuk Kandemir | Frontend & UI/UX |

---

*TariffCheck prepares classification audits and §1514 protest packages. The importer of record or a licensed customs broker files. Nothing here is legal or customs advice.*
