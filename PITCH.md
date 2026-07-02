# TariffCheck — Investor Pitch

> Brokers can file but can't afford to audit; importers can audit but need help preparing. TariffCheck scans invoices against the full USITC schedule, finds overpaid duty, and hands a licensed human a ready-to-file protest.

**Live product:** https://tariffcheck-zeta.vercel.app · **Repo:** github.com/eymen160/tariffcheck

---

## 1. Problem

US importers overpay an estimated **~$26 billion per year** in customs duties — misclassified HTS codes, unclaimed FTA/USMCA preferences, and wrongly applied Section 301 rates. The demand signal is not hypothetical:

- Misclassification drives **~42% of CBP penalties**.
- CBP found **$310M in lost revenue in a single month**.
- The 2025–26 tariff regime changes (Section 301 expansions, IEEPA tariffs imposed then voided, de minimis changes) mean **every static classification goes stale**. A code that was right in 2024 is wrong in 2026.

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

- **TAM — $5–6B/yr.** Value-capture math: $26B/yr overpayment pool × the 15–20% take-rate that trade law firms, Big 4 trade practices, and protest specialists bill today = $3.9–5.2B, plus $1–1.5B of US trade-compliance software spend (Descartes, ONESOURCE, SAP GTS class) an AI-native challenger cannibalizes. Total spend on the *service* is many times larger than spend on software.
- **SAM — ~$1.4B/yr.** What our mechanism (classification audit → §1514 protest package) and motion (broker-facing + SMB self-serve, US-only) actually address: ~3,000 active brokerage firms ($300–500M) plus ~130K regular importers at $5–8K blended willingness-to-pay ($800M–1B). Honestly excluded: duty drawback, non-US regimes, and filing itself (license wall).
- **SOM — $8–12M ARR by end of year 3.** Bottom-up: 150 broker-firm accounts (~5% of the 3,000-firm universe) at ~$25K ACV + 1,500 self-serve importer subscriptions at ~$3.5K + $1–2M in success fees on managed recoveries.

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

| Player | What they are | Why we win |
|---|---|---|
| **TariffLens** | Tariff intelligence/classification tooling | No detection → verified dollars → ready-to-file §1514 letter in a single pass |
| **Quickcode** | AI HTS classification | Forward-looking classification, not backward-looking recovery of money already overpaid |
| **Thomson Reuters ONESOURCE** | Fortune-1000 ERP-integrated trade suite (their AI passed the CBP broker exam at 85–86% — proof the accuracy frontier is reachable) | Heavy implementation, enterprise cycles; SMBs and regional brokers can't self-serve; our edge is grounding + deterministic verification, not raw model trust |
| **Descartes CustomsInfo** | Largest commercial duty database | Data layer, not workflow; paywalls the lookup we give away as PLG |
| **Trava** (YC, adjacent) | AI entry auditing sold top-down to mid-market compliance teams | Our differentiation: the broker channel as customer *and* filing path, plus the single-artifact finding → savings → protest-letter flow |

**Caspian and Pax are not competitors** — they are duty-drawback companies (drawback requires exports; our protest/misclassification market covers importers with no exports). We cite their ~$10M in combined recent funding as proof the adjacent recovered-money market is fundable, nothing more.

None of the real competitors owns the single-artifact flow: misclassification found → savings computed and verified → ready-to-file protest letter.

## 9. YC RFS Fit

Primary: **AI-Native Service Companies** (Gustaf Alströmer, Summer 2026) — "they don't sell software, they just do the work," with accounting/tax/audit, compliance, and brokerage as named verticals. Customs-duty audit sits at the intersection of three of the four. We sell the audit outcome on software margins; the license wall (only the IOR or an LCB can file) is exactly the regulatory-moat defensibility YC's 2026 framing prizes. Supporting motifs: Supply Chain 2.0's "rules change quarterly" volatility wedge and the SaaS-Challenger posture against the ONESOURCE/Descartes codebase class.

## 10. Honesty Ledger

Said before it's asked:

- **Zero design partners today.** The broker design-partner motion is the plan, not the traction.
- **Success-fee revenue lags 60–180 days** behind bookings — CBP liquidation timelines are outside our control.
- **CAPE/IEEPA revenue is one-time.** We model it as customer acquisition, never as run-rate.
- **We prepare filings; the importer of record or a licensed broker files.** We never file with CBP and never claim to.
- No fabricated customers, logos, or testimonials — the numbers above are market math and public CBP/court figures, not traction claims.

## 11. Roadmap

1. **CROSS rulings corpus** — ground every finding in cited CBP rulings, raising defensibility and ASP.
2. **Two-pass grounded classification** — candidate generation, then adjudication against schedule + rulings.
3. **ACE report ingestion** — audit actual CBP entry data (importer-authorized), not just invoices.
4. **Tariff-change monitoring** — per-SKU alerts turning every rate change into a customer-value event; the retention layer.
5. **EU/UK/CA schedules** — same architecture, new customs regimes.

## 12. Team

*Placeholder — founder bios and relevant credentials to be added.*

| Name | Role |
|---|---|
| Eymen Keyvan | Full-Stack & Deployment |
| Esat Sarac | Backend & AI Integration |
| Selcuk Kandemir | Frontend & UI/UX |

---

*TariffCheck prepares classification audits and §1514 protest packages. The importer of record or a licensed customs broker files. Nothing here is legal or customs advice.*
