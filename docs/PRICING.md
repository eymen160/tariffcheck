# TariffCheck — Pricing

TariffCheck prepares classification audits and 19 U.S.C. §1514 protest packages; the importer of record or a licensed customs broker files them. Pricing reflects that split: a SaaS backbone for the durable audit product, plus an optional success fee where a partner broker closes the recovery loop.

## Price Card

| | **Free** | **Pro — $349/mo** (annual: $299/mo) | **Enterprise / Broker — from $1,750/mo** |
|---|---|---|---|
| HTS lookup (29,755-code USITC 2026 schedule) | Unlimited | Unlimited + CROSS rulings citations | Unlimited + API access |
| Invoice/entry audits | 2/mo, 1 seat | 300 entries/mo, 3 seats | Unlimited entries, unlimited seats, bulk client-portfolio scanning |
| Findings detail | Summary only (savings shown, codes partially masked) | Full findings, verified against USITC rates, exportable | Full + white-label drafts under broker letterhead |
| §1514 protest packages | — | 3/mo included, then $149 each | Unlimited |
| Tariff-change alerts | 5 HTS codes | Full catalog (up to 2,500 SKUs) | Multi-client catalogs, ACE report ingestion |
| Success-fee recovery service (optional) | — | 10% of verified recovery, filed via partner broker, $1,500 min | 8%, or waived for brokers filing themselves |
| Support | Community | Email, 1-business-day | Dedicated CSM + licensed-broker review tier |

## Target ACVs

- **Pro:** ~$3.6–4.2K/yr (monthly vs annual mix, protest-package overage).
- **Enterprise/Broker:** ~$21–35K/yr; broker firms scanning 50–500 client accounts justify $50K+ at volume tiers.

## Unit Economics

COGS per audit is Claude inference. With prompt caching on the static system prompt already implemented, estimated inference cost is **$0.05–0.30 per invoice analysis** (instrumenting `message.usage`, including cache-hit rate, to state this precisely is a day-one metric). At $349/mo with even 300 audits/mo fully used, inference stays ≤ $90 — a **~75% gross-margin floor and ~90% typical gross margin**. Free-tier lookup traffic is near-zero marginal cost once CDN caching ships. On acquisition: PLG via the free HTS lookup (the "HTS code for ___" long-tail SEO that Descartes paywalls) targets blended CAC under $500 for Pro; broker Enterprise is founder-led sales at CAC ~$3–5K against ~$25K ACV — **under 3-month payback on both motions**.

## Why Hybrid — the Pricing-Model Defense

| Model | Pros | Cons |
|---|---|---|
| Pure SaaS tiers | Predictable; values at software multiples (8–12x); simple rev-rec | Undermonetizes the "we found you $84K" moment; friction for SMBs pre-proof; reads as "software vendor," not an AI-native service |
| Pure contingency (% of recovery) | Zero-friction ("$0 unless we find money"); proven acceptable to SMBs in the adjacent drawback market | **Fatal fit problem for a non-filer:** we cannot file — recovery closes 60–180+ days later via the IOR or their broker, outside our control. Fee leakage, unenforceable collection, lumpy non-recurring revenue valued at 1–2x; the one-time CAPE wave would make year-1 revenue look great and year-2 look like churn |
| **Hybrid (ours)** | SaaS backbone = recurring, software-multiple ARR; success fee captures found-money upside where a partner broker closes the loop | Slightly more complex billing |

Defense in four points:

1. **The regulatory wall makes pure contingency structurally unsound for a non-filer.** Never build the P&L on cash you can't collect.
2. **Subscriptions monetize the durable product** — continuous entry auditing and per-SKU tariff-change monitoring, the retention layer — rather than the one-time CAPE/IEEPA wave.
3. **The 10% success fee**, charged only on managed recoveries filed via our broker-partner network, still delivers the "we sell the outcome" narrative and lifts ACV without making revenue hostage to CBP liquidation timelines.
4. **Brokers — our wedge buyer — hate revenue-sharing and love per-seat/per-client tools.** Contingency pricing would poison the broker channel that solves our license wall; that's why brokers filing themselves get the fee waived.
