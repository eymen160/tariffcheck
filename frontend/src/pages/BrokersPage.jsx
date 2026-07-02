import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LeadForm from '../components/LeadForm'

const VALUE_PROPS = [
  {
    icon: '🗂️',
    title: 'Bulk client-invoice scanning',
    desc: 'Paste or upload entire client entry portfolios as CSV. Every line is screened against the complete 29,755-code USITC HTS 2026 schedule for misclassification patterns, missed FTA claims, and Section 301 exposure — in seconds, deterministically.',
  },
  {
    icon: '📄',
    title: 'Draft §1514 protest letters your firm files',
    desc: 'Every flagged exception becomes a ready-to-review 19 U.S.C. §1514 protest package with verified rate deltas and recomputed savings. Turn the protest work you used to decline into a new fee line.',
  },
  {
    icon: '✓',
    title: 'Verified against the official USITC schedule',
    desc: 'Savings math is recomputed server-side against official 2026 rates before it reaches any letter. A hallucinated number physically cannot reach a legal artifact your firm puts its name on.',
  },
]

export default function BrokersPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--slate-50)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <section className="hero" style={{ padding: '72px 32px 56px' }}>
        <div className="hero-inner">
          <div className="hero-badge">For customs brokerages</div>
          <h1 className="hero-title" style={{ fontSize: 'clamp(30px, 4.5vw, 48px)' }}>
            Scan every client invoice for misclassification.<br />
            <span>Bill for the protests you used to turn down.</span>
          </h1>
          <p className="hero-sub">
            TariffCheck audits your clients' entry lines against the full official USITC schedule and hands your firm
            review-ready §1514 protest drafts with server-verified savings.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid var(--green-mid)', borderRadius: 20, padding: '9px 20px', fontSize: 14, fontWeight: 700, color: 'var(--green)', boxShadow: 'var(--shadow-sm)' }}>
            ⚖ We prepare, you file — no license conflict.
          </div>
        </div>
      </section>

      <section style={{ maxWidth: 1000, margin: '0 auto', padding: '48px 24px', width: '100%' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 18 }}>
          {VALUE_PROPS.map(v => (
            <div key={v.title} className="card">
              <div style={{ fontSize: 30, marginBottom: 12 }}>{v.icon}</div>
              <div style={{ fontSize: 17, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 8 }}>{v.title}</div>
              <div style={{ fontSize: 14, color: 'var(--slate-500)', lineHeight: 1.65 }}>{v.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ maxWidth: 640, margin: '0 auto', padding: '8px 24px 64px', width: '100%' }}>
        <div className="card" style={{ padding: 36 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--slate-900)', marginBottom: 6, letterSpacing: '-0.4px' }}>
            Get broker access
          </div>
          <div style={{ fontSize: 14, color: 'var(--slate-500)', marginBottom: 20 }}>
            Bulk portfolio scanning, white-label protest drafts, and API access. Leave your work email and we'll reach out.
          </div>
          <LeadForm source="brokers_page" placeholder="you@brokerage.com" buttonLabel="Request broker access" />
          <div style={{ marginTop: 20, paddingTop: 18, borderTop: '1px solid var(--slate-100)', textAlign: 'center' }}>
            <Link to="/batch" style={{ color: 'var(--blue)', fontWeight: 600, fontSize: 14, textDecoration: 'none' }}>
              Or try the batch audit now — no signup →
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
