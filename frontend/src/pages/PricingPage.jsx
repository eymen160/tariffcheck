import { useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LeadForm from '../components/LeadForm'
import { usePageMeta } from '../lib/usePageMeta'

// Broker-first ordering: the channel tiers lead, the importer self-serve
// lane follows. The $795 audit-only tier exists to close the $349→$1,750
// dead zone competitors' ~$749 classification-only tiers anchor into.
const TIERS = [
  {
    name: 'Broker Audit',
    price: '$795',
    period: '/mo',
    subtitle: 'For brokerage firms — audit-only, your license files',
    features: [
      'Batch portfolio scanning (ACE ES-003 CSV/Excel in)',
      'SPI-aware screen — never flags programs you claimed',
      'Per-entry protest windows from liquidation dates',
      'Remedy-routed drafts: §1514, PSC, 1520(d)',
      'Verified findings + API key for your office',
      'No success fee — recovery revenue is yours',
    ],
    cta: 'lead',
    highlight: true,
  },
  {
    name: 'Enterprise / Broker+',
    price: 'from $1,750',
    period: '/mo',
    subtitle: 'For brokerages and high-volume importers',
    features: [
      'Unlimited entries and seats',
      'White-label remedy drafts — your firm named as preparer on every draft',
      'API keys for your office',
      'Client workspaces (coming soon)',
      'Dedicated licensed-broker review tier',
      'Optional 2% success fee on managed recoveries (capped $50K/yr) — 0% when your firm files',
    ],
    cta: 'lead',
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$349',
    period: '/mo',
    subtitle: 'Self-serve for importers · $299/mo billed annually',
    features: [
      '300 entries per month',
      '3 seats',
      'Full verified findings',
      '3 remedy packages/mo, then $149 each',
      'Tariff-change alerts (coming soon)',
    ],
    cta: 'lead',
    highlight: false,
  },
  {
    name: 'Free',
    price: '$0',
    period: '',
    subtitle: 'For importers checking their first entries',
    features: [
      'Unlimited HTS lookup',
      '2 invoice audits per month',
      'Summary findings',
      'Landed-cost calculator',
    ],
    cta: 'free',
    highlight: false,
  },
]

function TierCard({ tier }) {
  const [showForm, setShowForm] = useState(false)
  return (
    <div
      className="card"
      style={{
        display: 'flex', flexDirection: 'column',
        border: tier.highlight ? '2px solid var(--ledger)' : '1px solid var(--slate-200)',
        boxShadow: tier.highlight ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
        position: 'relative',
      }}
    >
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 6 }}>{tier.name}</div>
      <div style={{ marginBottom: 4 }}>
        <span style={{ fontFamily: 'var(--font-serif)', fontSize: 34, fontWeight: 700, color: 'var(--slate-900)', letterSpacing: '-1px' }}>{tier.price}</span>
        <span style={{ fontSize: 15, color: 'var(--slate-500)', fontWeight: 500 }}>{tier.period}</span>
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--slate-500)', marginBottom: 18 }}>{tier.subtitle}</div>
      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 9, marginBottom: 22, flex: 1 }}>
        {tier.features.map(f => {
          // Roadmap items render honestly: hollow marker + muted text, never
          // the green check that means "ships today".
          const soon = f.includes('(coming soon)')
          return (
            <li key={f} style={{ fontSize: 13.5, color: soon ? 'var(--slate-400)' : 'var(--slate-600)', display: 'flex', gap: 8, lineHeight: 1.5 }}>
              <span style={{ color: soon ? 'var(--slate-400)' : 'var(--green)', fontWeight: 700, flexShrink: 0 }}>{soon ? '○' : '✓'}</span>{f}
            </li>
          )
        })}
      </ul>
      {tier.cta === 'free' ? (
        <Link to="/" className={tier.highlight ? 'btn-primary' : 'btn-secondary'} style={{ width: '100%' }}>
          Audit an invoice — free
        </Link>
      ) : showForm ? (
        <LeadForm source="pricing_page" buttonLabel="Get in touch" />
      ) : (
        <button className={tier.highlight ? 'btn-primary' : 'btn-secondary'} style={{ width: '100%' }} onClick={() => setShowForm(true)}>
          Talk to us
        </button>
      )}
    </div>
  )
}

export default function PricingPage() {
  usePageMeta({ title: 'Pricing', description: 'Published, flat pricing: free HTS lookup, $349 Pro for importers, $795 Broker Audit, Enterprise from $1,750. No demo call required.', path: '/pricing' })
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ maxWidth: 1020, margin: '0 auto', padding: '48px 24px 64px', width: '100%', flex: 1 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: 34, color: 'var(--slate-900)', marginBottom: 10 }}>Pricing</h1>
          <p style={{ fontSize: 16, color: 'var(--slate-500)', maxWidth: 560, margin: '0 auto' }}>
            Start free with the HTS lookup and invoice audits. Upgrade when the verified savings speak for themselves.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, alignItems: 'stretch', marginBottom: 28 }}>
          {TIERS.map(t => <TierCard key={t.name} tier={t} />)}
        </div>

        <div className="card" style={{ marginBottom: 28, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 16, border: '1px solid var(--slate-200)' }}>
          <div style={{ flex: '1 1 380px' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 4 }}>
              CAPE Readiness Check — <span style={{ fontFamily: 'var(--font-serif)' }}>$149</span> flat per claim batch
            </div>
            <div style={{ fontSize: 13, color: 'var(--slate-600)', lineHeight: 1.6 }}>
              Before you upload an IEEPA refund declaration to CBP's CAPE portal, we screen your entry list — IEEPA Chapter 99 lines, entry-date windows, phase eligibility — and hand back a validated declaration checklist. You file free in ACE; brokers charge $500–$2,000 for the same review. <Link to="/cape-refund" style={{ color: 'var(--ledger)' }}>How CAPE works →</Link>
            </div>
          </div>
          <div style={{ flex: '0 1 260px', minWidth: 220 }}>
            <LeadForm source="cape_readiness_pricing" buttonLabel="Check my batch" />
          </div>
        </div>

        <div style={{ fontSize: 13, color: 'var(--slate-500)', textAlign: 'center', marginBottom: 10, lineHeight: 1.6 }}>
          Optional success fees on managed recoveries filed via partner brokers: 3% on Pro ($750 min per filing, $25K/yr cap), 2% on Enterprise ($50K/yr cap) — always 0% when your own broker files. The drawback industry charges 10–25% for the same recovery.
        </div>
        <div style={{ fontSize: 13, color: 'var(--slate-500)', textAlign: 'center', fontWeight: 600 }}>
          TariffCheck prepares filings; the importer of record or a licensed customs broker files them.
        </div>
      </div>

      <Footer />
    </div>
  )
}
