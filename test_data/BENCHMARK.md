# TariffCheck Published Benchmarks — July 2026

Everything here is reproducible from this repository. No competitor in this
category publishes any accuracy number with a methodology (verified in the
July 21, 2026 competitive sweep, `docs/COMPETITIVE_LANDSCAPE_2026-07-21.md`);
this document is the standing answer to "prove it."

## 1. Deterministic verification benchmark (correct-code condition)

**Question:** does the verification layer ever falsely accuse a correct
classification, and is its schedule math sound?

**Protocol:** 246 real CBP CROSS rulings (binding classification decisions,
public record) run through the deterministic engine as declared. Dataset:
`cross_rulings_dataset.json`; the scoring endpoint is the production
`/api/analyze-batch`.

**Results (July 2026):**
- 246/246 (100%) CBP-ruled codes recognized and canonicalized against the
  USITC 2026 schedule
- **0/246 (0%) false positives** — a CBP-ruled classification was never
  flagged as a misclassification
- 238/246 (96.7%) machine-parseable ad-valorem rates; the 8 specific/compound
  duties (¢/kg) are labeled unquantified, never silently passed
- Live AI-audit condition (79 PDF invoices, full pipeline): high-confidence
  false-positive rate driven 3.3% → 1.0%, spot-check 0

## 2. Adversarial wrong-code recovery benchmark (v2, July 22 2026)

**Question:** when an entry is declared under the WRONG code, does the audit
(a) catch it, and (b) recover CBP's exact code?

**Protocol** (`run_wrongcode_benchmark.py`, seed=2026, single run):
- 200 rulings sampled reproducibly from the CROSS corpus (198 scored, 1 API
  error, 1 sample short due to corpus filtering)
- Each ruling's product description is its **full CROSS ruling text**, fetched
  from rulings.cbp.gov and sanitized against answer leakage in three layers:
  header block (contains `TARIFF NO.`) dropped; text cut before the decision
  sentence ("The applicable subheading…"); every surviving HTS-shaped token
  and heading/chapter reference excised
- Each invoice line is declared under a **different-chapter decoy code**
  (seeded rotation) so the declared code leaks nothing about the answer's
  neighborhood
- Scoring counts **verified findings only** — the deterministic verifier is
  part of the product being measured; an unverifiable suggestion scores zero

**Results (n=198, production API, default `claude-haiku-4-5`):**

| Metric | Result |
|---|---|
| Wrong-code flag rate | **96.0%** |
| Suggested-code recovery @4-digit (heading) | 32.3% |
| Recovery @6-digit (international subheading) | 9.1% |
| Recovery @8-digit (US rate line) | 6.1% |
| Recovery @10-digit (statistical line) | 0.5% |

Single run; binomial 95% CI at n=198 is roughly ±3 points near the extremes
and ±7 points mid-range.

**Honest read.** The auditor's production job is the first row: given a real
entry, detect that the declared code is wrong and hand a licensed broker a
verified, dollar-quantified finding — 96.0% with a 1.0% high-confidence false
alarm rate is that story. The recovery rows are the frontier we are naming so
we can be held to it: pinpointing CBP's exact subheading from ruling text
alone is genuinely hard — ATLAS (arXiv 2509.18400), the closest public
reference, reports **40% @10-digit / 57.5% @6-digit** for a purpose-built
fine-tuned LLaMA-3.3-70B (different protocol: no decoy, ATLAS's own splits;
comparable in spirit, not split-identical). Our default model is a
cost-efficient tier and the audit prompt is precision-biased by design (a
hallucinated confident code is worse for us than no code). Raising recovery —
stronger model tier on Enterprise audits, CROSS-retrieval grounding — is on
the roadmap, and this table is the baseline it will be measured against.

**Protocol v1 invalidation (transparency note).** The first run of this
benchmark used the corpus's one-line search-index descriptions ("spray
shield") instead of full ruling texts and measured description starvation,
not classification. It was stopped at n=12, archived unmodified as
`wrongcode_results_v1_INVALID_snippet_descriptions.jsonl`, and superseded by
v2. We publish the mistake because reproducibility without an error trail is
marketing.

## Reproduce

```bash
cd test_data
python3 run_wrongcode_benchmark.py 200          # against production
python3 run_wrongcode_benchmark.py 200 --base http://localhost:8000
```

Results stream to `wrongcode_results.jsonl` (resumable); summary lands in
`wrongcode_summary.json`.
