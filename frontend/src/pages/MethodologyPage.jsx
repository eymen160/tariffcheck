import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { usePageMeta } from '../lib/usePageMeta'

export default function MethodologyPage() {
  usePageMeta({
    title: 'Methodology & Accuracy',
    description:
      'How TariffCheck verifies every finding: deterministic re-verification against the full 29,755-code USITC HTS 2026 schedule, benchmarked on 246 real CBP CROSS rulings.',
    path: '/methodology',
  })
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main className="legal-page">
        <h1>Methodology &amp; Accuracy</h1>
        <div className="legal-updated">Benchmark run: July 2026 · USITC HTS 2026 edition (29,755 codes)</div>

        <section>
          <h2><span className="legal-num">01</span>The claim we make — and how to falsify it</h2>
          <p>
            Every accuracy claim in this industry is a marketing number until someone shows their work.
            Ours is designed to be checked: the verification layer is deterministic code, the reference
            data is the official USITC schedule, and the benchmark below uses public CBP rulings anyone
            can re-run through the <Link to="/batch">free batch scan</Link> — no account, no sales call.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">02</span>How verification works</h2>
          <p>
            The AI (Claude) proposes findings: possible misclassifications, unclaimed trade-preference
            programs, Section 301 exposure. It never gets the last word. Every finding is then re-checked
            by deterministic code against the complete official USITC HTS 2026 schedule — all 29,755
            codes, loaded in-product:
          </p>
          <p>
            1. Both the declared and the suggested code are looked up in the schedule. A code that does
            not exist is flagged and its savings are zeroed — it cannot reach a report as a number.<br />
            2. Duty rates are read from the schedule, never from the model. Savings are recomputed
            server-side from those rates and the declared value.<br />
            3. Findings are routed to the correct legal remedy: reclassification differences to a
            19 U.S.C. §1514 protest (post-liquidation) or an ACE Post Summary Correction
            (pre-liquidation); unclaimed FTA preferences to 19 U.S.C. 1520(d) — with real statutory
            deadlines when entry dates are provided.<br />
            4. When the correct code would cost <em>more</em>, we say so: possible underpayments are
            flagged for a prior-disclosure conversation, never hidden.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">03</span>The benchmark: 246 real CBP CROSS rulings</h2>
          <p>
            We took 246 classification rulings from CBP's public CROSS database — real merchandise,
            real authoritative HTS codes decided by CBP — and ran every one through the deterministic
            engine. Results, July 2026:
          </p>
          <p>
            <strong>246 / 246 (100%)</strong> of CBP-ruled codes recognized and canonicalized against the
            USITC 2026 schedule.<br />
            <strong>0 / 246 (0%)</strong> false positives — the engine never flagged a CBP-ruled
            classification as a misclassification.<br />
            <strong>238 / 246 (96.7%)</strong> returned a machine-parseable ad-valorem rate; the remaining
            8 carry specific/compound duties (e.g. ¢/kg) and are explicitly labeled as unquantified
            rather than silently passed.
          </p>
          <p>
            Re-run it yourself: the ruling dataset ships in the open repository
            (<code>test_data/cross_rulings_dataset.json</code>), and the batch endpoint that scores it is
            the same one behind the <Link to="/batch">Batch Audit</Link> page.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">04</span>The adversarial benchmark: wrong-code recovery</h2>
          <p>
            The harder question: when an entry is declared under the <em>wrong</em> code, does the audit
            catch it? We sampled 198 CROSS rulings (seeded, reproducible), used each ruling's full text
            with the answer excised in three sanitization layers, and declared every line under a
            deliberately wrong code from a <em>different chapter</em> — so the declared code leaks nothing.
            Only deterministically verified findings score. Results, July 2026, production API:
          </p>
          <p>
            <strong>96.0%</strong> wrong-code flag rate — the audit detects that the declared code is wrong.<br />
            Suggested-code recovery of CBP's exact ruling code: <strong>32.3%</strong> at heading (4-digit),
            <strong> 9.1%</strong> at subheading (6-digit), <strong>6.1%</strong> at the US rate line (8-digit).
          </p>
          <p>
            The honest read: detection plus verified dollars is the auditor's production job — 96.0% flag
            rate with the 1.0% high-confidence false-alarm rate above is that story. Exact-code recovery
            from ruling text alone is the frontier: the closest public reference (ATLAS, arXiv 2509.18400)
            reports 40% at 10-digit for a purpose-built fine-tuned 70B model under a different protocol.
            Our default model is a cost-efficient tier and the prompt is precision-biased by design — a
            confidently hallucinated code would be worse than none. We publish this baseline so the
            roadmap (stronger model tier, CROSS-retrieval grounding) can be measured against it. Full
            protocol, the invalidated v1 run, and the reproduction command:
            <code> test_data/BENCHMARK.md</code> in the open repository.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">05</span>What these benchmarks do NOT claim</h2>
          <p>
            Honesty about scope is the point of this page. These benchmarks demonstrate that the
            verification layer's schedule math is sound — codes resolve, rates are real, no false
            accusations against CBP-ruled classifications — and that wrong codes get caught. They do
            <strong> not</strong> claim that every
            AI-suggested reclassification is legally correct for your goods: whether a code's legal text
            actually fits specific merchandise is a classification judgment that belongs to a licensed
            customs broker, which is why every TariffCheck output is a draft for professional review.
            Section 301 rates are applied at line level from the USITC China Tariffs table (10,391
            covered subheadings, cross-verified against the Chapter 99 notes and USTR Federal Register
            annexes); the handful of codes whose coverage is limited to specific statistical lines are
            flagged as estimates on their face.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">06</span>A standing invitation</h2>
          <p>
            If any vendor in this category publishes an equivalent, reproducible benchmark — dataset,
            method, and false-positive rate — we will link to it here. Until then, ask them for one.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
