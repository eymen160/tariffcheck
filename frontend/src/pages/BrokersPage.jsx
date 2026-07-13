import { useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Reveal from '../components/Reveal'
import LeadForm from '../components/LeadForm'
import { usePageMeta } from '../lib/usePageMeta'

const money = n =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

/** Illustrative ROI math, stated openly so a broker can argue with it. */
function RoiCalculator() {
  const [entries, setEntries] = useState(2400)
  const [avgValue, setAvgValue] = useState(45000)
  const [errorRate, setErrorRate] = useState(2)
  const [feePct, setFeePct] = useState(15)

  const annualValue = entries * avgValue
  // Assumption shown in the caption: flagged lines overpay ~5 points of duty.
  const recoverable = annualValue * (errorRate / 100) * 0.05
  const brokerFee = recoverable * (feePct / 100)
  const protests = Math.max(1, Math.round(entries * (errorRate / 100) / 10))
  const hoursSaved = protests * 12

  const field = { display: 'flex', flexDirection: 'column', gap: 4, minWidth: 170, flex: 1 }
  const input = { padding: '10px 12px', border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', fontSize: 14, width: '100%' }
  const label = { fontSize: 11, fontFamily: 'var(--font-mono)', letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--slate-500)' }

  return (
    <div className="card" style={{ padding: '22px 24px' }}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 18 }}>
        <label style={field}>
          <span style={label}>Client entries / year</span>
          <input style={input} type="number" min="0" value={entries} onChange={e => setEntries(Number(e.target.value) || 0)} />
        </label>
        <label style={field}>
          <span style={label}>Avg entry value (USD)</span>
          <input style={input} type="number" min="0" value={avgValue} onChange={e => setAvgValue(Number(e.target.value) || 0)} />
        </label>
        <label style={field}>
          <span style={label}>Assumed error rate (%)</span>
          <input style={input} type="number" min="0" max="100" step="0.5" value={errorRate} onChange={e => setErrorRate(Number(e.target.value) || 0)} />
        </label>
        <label style={field}>
          <span style={label}>Your recovery fee (%)</span>
          <input style={input} type="number" min="0" max="100" value={feePct} onChange={e => setFeePct(Number(e.target.value) || 0)} />
        </label>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        <div style={{ borderTop: '2px solid var(--slate-200)', paddingTop: 10 }}>
          <div style={label}>Est. recoverable duty / yr</div>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 30, fontWeight: 700, color: 'var(--green)' }}>{money(recoverable)}</div>
        </div>
        <div style={{ borderTop: '2px solid var(--slate-200)', paddingTop: 10 }}>
          <div style={label}>Your new fee line @ {feePct}%</div>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 30, fontWeight: 700, color: 'var(--slate-900)' }}>{money(brokerFee)}</div>
        </div>
        <div style={{ borderTop: '2px solid var(--slate-200)', paddingTop: 10 }}>
          <div style={label}>Prep hours you don't spend</div>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 30, fontWeight: 700, color: 'var(--slate-900)' }}>~{hoursSaved.toLocaleString()}</div>
        </div>
      </div>
      <div style={{ fontSize: 11.5, color: 'var(--slate-500)', marginTop: 14, lineHeight: 1.5 }}>
        Illustrative math, stated so you can argue with it: recoverable = entries × avg value × error rate × 5-point
        average overpayment on flagged lines; hours assume ~12 attorney-hours per manually prepared protest
        (≈10 flagged lines each). Your portfolio will differ — that's what the free scan is for.
      </div>
    </div>
  )
}

export default function BrokersPage() {
  usePageMeta({
    title: 'For Customs Brokers',
    description:
      "TariffCheck never files — it turns your clients' entry history into verified findings and filing-ready remedy packages that YOUR license files. Join the 5-firm pilot.",
    path: '/brokers',
  })

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main>
        {/* Hero: the counter-story to "audit your customs broker" tools */}
        <section className="how-section" style={{ paddingTop: 72 }}>
          <Reveal>
            <div className="section-label">For customs brokers</div>
            <h1 className="section-title" style={{ fontSize: 'clamp(28px, 4.4vw, 44px)', maxWidth: 780 }}>
              Flexport gave your clients a free tool to audit you.
            </h1>
            <p style={{ fontSize: 17, color: 'var(--slate-600)', maxWidth: 680, lineHeight: 1.65, marginTop: 14 }}>
              We give <strong>you</strong> the same audit — plus the drafted remedy package — first.
              TariffCheck never files, never touches your client relationship, and never will:
              your license, your client, your fee. We're the engine; the filing revenue is yours.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 20 }}>
              <a href="#pilot" className="btn-primary">Join the 5-firm pilot</a>
              <Link to="/batch" className="btn-secondary">Run a batch scan now — free</Link>
            </div>
            <div className="trust-badges" style={{ marginTop: 26 }}>
              <div className="trust-item">We prepare — you file</div>
              <div className="trust-item">Batch path makes zero AI calls</div>
              <div className="trust-item">Verified against USITC HTS 2026</div>
              <div className="trust-item"><Link to="/methodology" style={{ color: 'inherit' }}>Published accuracy benchmark →</Link></div>
            </div>
          </Reveal>
        </section>

        {/* Why brokers use it */}
        <section className="how-section">
          <Reveal>
            <div className="section-label">Sec. 01 — Why brokerages run it</div>
            <h2 className="section-title">Post-entry work that was hourly-unprofitable becomes a fee line</h2>
          </Reveal>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14, marginTop: 22 }}>
            <Reveal><div className="card" style={{ height: '100%' }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>Turn declined protest work into revenue</h3>
              <p style={{ fontSize: 14, color: 'var(--slate-600)', lineHeight: 1.6 }}>
                Manual protest prep runs ~12 hours per filing, so small recoveries get declined and the
                180-day window closes. The deterministic engine drafts the §1514 / PSC / 1520(d) package
                from verified numbers in minutes — suddenly a $3K recovery is worth filing, at your fee.
              </p>
            </div></Reveal>
            <Reveal><div className="card" style={{ height: '100%' }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>Audit your book before someone else does</h3>
              <p style={{ fontSize: 14, color: 'var(--slate-600)', lineHeight: 1.6 }}>
                Freight giants now market free "audit your customs broker" tools directly to your
                clients — and every finding those tools surface is a pitch to replace you. Running the
                same audit first, and walking in with the drafted recovery, turns the threat into a
                client-retention story.
              </p>
            </div></Reveal>
            <Reveal><div className="card" style={{ height: '100%' }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>ES-003 in, remedy package out</h3>
              <p style={{ fontSize: 14, color: 'var(--slate-600)', lineHeight: 1.6 }}>
                Upload the ACE entry-summary export you already pull (CSV or Excel). The screen is
                SPI-aware — it will never accuse you of missing a program you claimed — computes each
                entry's real protest window from its liquidation date, and routes every finding to the
                correct vehicle: PSC, §1514, or 1520(d).
              </p>
            </div></Reveal>
          </div>
        </section>

        {/* ROI */}
        <section className="how-section">
          <Reveal>
            <div className="section-label">Sec. 02 — The math</div>
            <h2 className="section-title">What one client portfolio is worth</h2>
            <div style={{ marginTop: 18 }}>
              <RoiCalculator />
            </div>
          </Reveal>
        </section>

        {/* Deliverable */}
        <section className="how-section">
          <Reveal>
            <div className="section-label">Sec. 03 — The deliverable</div>
            <h2 className="section-title">See the artifact before you talk to anyone</h2>
            <p style={{ fontSize: 15, color: 'var(--slate-600)', maxWidth: 640, lineHeight: 1.65, marginTop: 12 }}>
              Run a sample scenario and open the result: verified findings with the AI's claim struck
              through and the recomputed number beside it, remedy routing with statutory deadlines, and
              a print-ready draft your office completes and files. The whole flow is self-serve — no
              demo call, no sales thread.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
              <Link to="/" className="btn-secondary">Open a sample audit</Link>
              <Link to="/methodology" className="btn-secondary">Read the verification methodology</Link>
            </div>
          </Reveal>
        </section>

        {/* Pricing strip */}
        <section className="how-section">
          <Reveal>
            <div className="section-label">Sec. 04 — Pricing</div>
            <h2 className="section-title">Published, flat, and never a cut of your recovery</h2>
            <p style={{ fontSize: 15, color: 'var(--slate-600)', maxWidth: 640, lineHeight: 1.65, marginTop: 12 }}>
              Broker Audit is <strong>$795/month</strong> — batch portfolio scanning, verified findings,
              remedy-routed drafts. Enterprise (white-label, API, unlimited client workspaces) from
              $1,750. Success fees on recoveries stay where they belong: with the filer. Full details on
              the <Link to="/pricing">pricing page</Link>.
            </p>
          </Reveal>
        </section>

        {/* Pilot CTA */}
        <section className="how-section" id="pilot" style={{ paddingBottom: 90 }}>
          <Reveal>
            <div className="section-label">Sec. 05 — The pilot</div>
            <h2 className="section-title">Join the 5-firm pilot: one client's last 90 days, scanned free</h2>
            <p style={{ fontSize: 15, color: 'var(--slate-600)', maxWidth: 640, lineHeight: 1.65, margin: '12px 0 18px' }}>
              We're onboarding five brokerage firms. You pull one client's ES-003; we scan it with you
              on a call; the findings are yours either way. If the numbers are real, you file the
              recoveries and keep the fee. Ten minutes to find out.
            </p>
            <div style={{ maxWidth: 640 }}>
              <LeadForm source="brokers_page" placeholder="you@brokerage.com" buttonLabel="Request pilot access" detailed />
            </div>
          </Reveal>
        </section>
      </main>
      <Footer />
    </div>
  )
}
