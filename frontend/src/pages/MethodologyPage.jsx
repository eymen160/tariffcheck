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
          <h2><span className="legal-num">04</span>What this benchmark does NOT claim</h2>
          <p>
            Honesty about scope is the point of this page. The benchmark demonstrates that the
            verification layer's schedule math is sound — codes resolve, rates are real, no false
            accusations against CBP-ruled classifications. It does <strong>not</strong> claim that every
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
          <h2><span className="legal-num">05</span>A standing invitation</h2>
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
