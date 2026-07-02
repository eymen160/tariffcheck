# TariffCheck — Go-to-Market

Positioning constraint honored throughout: **we prepare classification audits and §1514 protest packages; the importer of record or a licensed customs broker files.** No traction claims below — we have zero design partners today; everything here is the plan and the math behind it.

## 1. ICP

### Primary (the wedge buyer): small/mid customs brokerages, 2–50 licensed brokers

- **Firmographics:** independent US customs brokerages and freight forwarders with in-house brokerage — not the top-20 giants; regional shops in LA/Long Beach, Laredo, Newark, Savannah, Chicago filing 5,000–200,000 entries/year across 50–500 importer clients.
- **Buyer / user:** the **Licensed Customs Broker (LCB) principal/owner** is the economic buyer; Compliance Managers and Entry Operations Managers are the users.
- **Why them:** they're the only party besides the importer of record who can legally file with CBP — they're not a channel *around* the license wall, they're the customer *because of* it. Their pain: classification review is manual, protests are a money-loser they decline, and every declined protest is fee revenue left on the table. We turn "misclassification found → savings computed → draft §1514 protest letter" into a billable service line they can offer every client.

### Secondary (PLG self-serve): SMB e-commerce/DTC importers, $1–50M revenue

- **Categories with the highest misclassification density + Section 301 exposure:** furniture (Ch. 94), apparel/textiles (Ch. 61–63), consumer electronics accessories (Ch. 85), kitchenware/houseware (Ch. 39, 73), sporting goods (Ch. 95). Origins: China, Vietnam, India, Mexico.
- **Buyer:** Founder/CEO under $10M (tariffs hit their P&L personally); Head of Supply Chain / Ops Manager at $10–50M; occasionally a fractional Trade Compliance Manager. These people discovered in 2025–26 that tariffs are their #2 COGS line and have no idea whether their broker classified anything correctly.

### Disqualifiers (said out loud)

- **Fortune 1000** — ONESOURCE territory, 18-month cycles.
- **Pure drawback seekers** — Caspian/Pax/Zollback's market; we refer out.
- **Non-US importers** — v2.

## 2. Channel Plan (ranked)

1. **Programmatic SEO on the HTS dataset** (weeks 1–4, compounding). One landing page per HTS heading/chapter — "HTS Code for Wooden Bedroom Furniture (9403.50) — 2026 Duty Rate, Section 301, USMCA Eligibility" — ~1,000–2,000 pages targeting the long tail of "HTS code for ___" queries that Descartes paywalls. Each page: live rate data, common misclassification patterns for that heading, the audit CTA, schema markup, and a rate-change log as a freshness signal. Defensible *because we own the dataset*.
2. **Direct broker outreach + NCBFAA circles** (weeks 1–8, high-touch). LinkedIn + email to LCB principals at regional brokerages; hook: "Run a free misclassification scan across one client's last 90 days of invoices — if we find nothing, you've lost 10 minutes." Presence in NCBFAA and regional broker association meetings. Goal: 3–5 design-partner brokerages — we currently have zero, and this is the credibility gap to close first. Brokers are simultaneously customers *and* the filing path, which answers the regulatory question.
3. **Tariff-news-jacking content** (continuous, spiky). The IEEPA/CAPE refund wave (~$165B ordered refunded, 75,300+ CAPE filings in week one) is a live news event: fast explainers ("Is your entry CAPE-eligible? The 3-step check"), Section 301 review coverage, de minimis changes, new AD/CVD orders — each ending in the free lookup or an exposure check. Discipline: CAPE content is *timing proof* funneling into the durable classification-audit product, never the product itself.
4. **Operator communities** (continuous, low-cost). r/ecommerce, r/FulfillmentByAmazon, r/supplychain, Shopify/Amazon-seller groups, eCommerceFuel/MDS Slacks, supply-chain LinkedIn. Format: genuinely useful answers to "why is my duty bill so high" threads with the free lookup linked. Never lead with product; lead with the answer.
5. **Deferred: integrations/marketplaces.** ACE report ingestion partnerships, freight-platform app stores — real, but not first-100-users territory.

## 3. The Three Objections (with full answers)

### 1. "An AI protest letter that's wrong triggers a CBP audit. Who's liable for accuracy?"

Three layers. (1) Every finding is grounded in the official USITC schedule injected at inference time — the model is told "use these rates, not memory" — and savings are recomputed server-side against the schedule, never trusted from the model. (2) Every output cites its legal basis (GRI reasoning; CROSS rulings on the roadmap) and carries a confidence score; low-confidence findings are labeled, not hidden. (3) The filing decision always passes through a human — the importer or a licensed broker — because legally it must. We are the drafting layer, like TurboTax before you hit "file": we make the preparer dramatically faster and better-documented; a professional signs. And the accuracy frontier for this domain is proven — Thomson Reuters' AI passed the CBP broker exam at 85% — our edge is grounding + deterministic verification, not raw model trust.

### 2. "Brokers already do this. Why won't they just do it themselves?"

Brokers file entries; they almost never *audit* them retrospectively — protest work is manual (~12 attorney-hours per protest, filed through CBP's bare ACE Protest module) and hourly-unprofitable at SMB entry values, so it goes to trade lawyers at $500+/hr or simply doesn't happen. Only ~3,750 filers account for the ~45,000 protests CBP receives each year (CBP, 87 FR 34894) — the long tail never protests. We don't compete with brokers — **brokers are our first customers**: a bulk-scan tool that turns declined protest work into a new fee line, at a moment when 2025-26 tariff churn has broken their manual workflows (NCBFAA's own words) and SmartBorder's exit orphaned hundreds of small brokerages. Important 2026 update: **Caspian now lists §1514 protests as a product and is itself a licensed broker — it is a direct competitor, not an adjacent proof point.** Selling to brokers while being a brokerage is Caspian's structural weakness; being channel-safe is ours. Pax (drawback, 1-30% contingency) pivoted from direct-importer sales to broker partnerships because importer acquisition didn't convert — independent validation of the broker-first motion.

### 3. "Tariff rules change constantly / the IEEPA refund wave is one-time. What's the durable business?"

Volatility is the moat, not the risk. A static classification done in 2024 is wrong in 2026 — Section 301 lists shifted, IEEPA came and went, de minimis rules changed — and every change creates new misclassifications and new refund windows. Our architecture is a living schedule (rebuilt from USITC source) plus continuous per-SKU monitoring, so rule changes generate customer-value events ("your code's rate changed — here's the impact"), not maintenance cost. The IEEPA/CAPE wave is our why-now customer-acquisition event — it hands us the importer's full entry history — but the recurring product is the continuous audit subscription: land with found money, retain with "never overpay again."

## 4. First 100 Users

**The single wedge use case:** "Upload an invoice or entry doc → get a misclassification audit with dollar savings and a ready-to-file protest letter in 60 seconds." One artifact, one wow moment — the detection → dollars → draft-§1514-letter flow in a single pass, which none of TariffLens, Quickcode, ONESOURCE, or Descartes owns.

**Funnel structure:**

- **Top of funnel:** the free HTS lookup on the full 29,755-code USITC schedule. Every lookup page ends with the bridge CTA: "Importing under this code? Check if you've been overpaying — upload an invoice."
- **Conversion moment:** the audit result with a dollar number. "$84,000 in probable overpaid duty across these 12 line items" is the screenshot that gets forwarded.
- **First-100 math:** **60–70 users** from SEO lookup → audit conversion; **20–30** from direct broker outreach (10 brokerages × 2–3 users each); **10** from tariff-news-cycle content. The lookup→upload conversion rate is instrumented from day one.

**Copy discipline baked into the wedge:** a visible "We prepare filings; you or your licensed broker files them" line. Pre-empting the objection builds more trust than hiding it — it's a feature for brokers (we make them faster) and legally clean for importers (self-filing a §1514 protest is permitted for the IOR). No fabricated logos, testimonials, or "trusted by" walls: authority comes from the data ("built on the complete 2026 USITC schedule — 29,755 codes"), third-party market stats, and the verification claim ("every AI finding is re-verified against the official schedule before you see it").
