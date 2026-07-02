import { useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LeadForm from '../components/LeadForm'
import { usePageTitle } from '../lib/usePageTitle'

const TIERS = [
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
  {
    name: 'Pro',
    price: '$349',
    period: '/mo',
    subtitle: '$299/mo billed annually',
    features: [
      '300 entries per month',
      '3 seats',
      'Full verified findings',
      '3 §1514 protest packages/mo, then $149 each',
      'Full-catalog rate alerts',
    ],
    cta: 'lead',
    highlight: true,
  },
  {
    name: 'Enterprise / Broker',
    price: 'from $1,750',
    period: '/mo',
    subtitle: 'For brokerages and high-volume importers',
    features: [
      'Unlimited entries and seats',
      'Bulk client-portfolio scanning',
      'White-label protest drafts',
      'API access',
      'Optional 8% success fee on managed recoveries (10% on Pro)',
      'Dedicated licensed-broker review tier',
    ],
    cta: 'lead',
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
      {tier.highlight && (
        <span style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: 'var(--ledger)', color: 'var(--sheet)', fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, padding: '3px 14px', borderRadius: 'var(--radius-sm)', letterSpacing: '0.12em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
          MOST POPULAR
        </span>
      )}
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 6 }}>{tier.name}</div>
      <div style={{ marginBottom: 4 }}>
        <span style={{ fontFamily: 'var(--font-serif)', fontSize: 34, fontWeight: 700, color: 'var(--slate-900)', letterSpacing: '-1px' }}>{tier.price}</span>
        <span style={{ fontSize: 15, color: 'var(--slate-500)', fontWeight: 500 }}>{tier.period}</span>
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--slate-500)', marginBottom: 18 }}>{tier.subtitle}</div>
      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 9, marginBottom: 22, flex: 1 }}>
        {tier.features.map(f => (
          <li key={f} style={{ fontSize: 13.5, color: 'var(--slate-600)', display: 'flex', gap: 8, lineHeight: 1.5 }}>
            <span style={{ color: 'var(--green)', fontWeight: 700, flexShrink: 0 }}>✓</span>{f}
          </li>
        ))}
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
  usePageTitle('Pricing')
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

        <div style={{ fontSize: 13, color: 'var(--slate-500)', textAlign: 'center', marginBottom: 10, lineHeight: 1.6 }}>
          Optional success fees on managed recoveries filed via partner brokers: 10% on Pro, 8% on Enterprise (waived when your firm files). $1,500 minimum.
        </div>
        <div style={{ fontSize: 13, color: 'var(--slate-500)', textAlign: 'center', fontWeight: 600 }}>
          TariffCheck prepares filings; the importer of record or a licensed customs broker files them.
        </div>
      </div>

      <Footer />
    </div>
  )
}
