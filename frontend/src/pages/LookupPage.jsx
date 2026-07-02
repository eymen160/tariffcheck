import { useEffect, useRef, useState } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { htsSearch, htsLookup } from '../lib/api'
import { usePageTitle } from '../lib/usePageTitle'

const EXAMPLES = ['9403.40', 'kitchen cabinets', 'stainless steel tumbler', 'cotton t-shirts', '6404.11', 'coffee roasting']

function RateBadge({ raw, rate }) {
  const label = raw || (rate != null ? `${rate}%` : '—')
  const free = label.toLowerCase() === 'free'
  return (
    <span style={{
      fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 'var(--radius-sm)', whiteSpace: 'nowrap',
      fontFamily: 'var(--font-mono)',
      background: free ? 'var(--green-light)' : 'var(--amber-light)',
      color: free ? 'var(--ledger)' : 'var(--amber)',
      border: `1px solid ${free ? 'var(--green-mid)' : '#E3D3A8'}`,
    }}>
      {label.length > 28 ? label.slice(0, 28) + '…' : label}
    </span>
  )
}

export default function LookupPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [detail, setDetail] = useState(null)
  const [origin, setOrigin] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const debounce = useRef()

  usePageTitle('HTS Lookup')

  // Close the detail modal with Escape while it is open.
  useEffect(() => {
    if (!detail) return
    const onKey = e => { if (e.key === 'Escape') setDetail(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [detail])

  useEffect(() => {
    clearTimeout(debounce.current)
    if (query.trim().length < 2) { setResults(null); return }
    debounce.current = setTimeout(async () => {
      setLoading(true); setError('')
      try {
        const data = await htsSearch(query.trim(), 25)
        setResults(data.results || [])
      } catch {
        setError('Search is temporarily unavailable. Please try again in a moment.')
        setResults(null)
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => clearTimeout(debounce.current)
  }, [query])

  async function openDetail(code, originOverride) {
    const o = originOverride !== undefined ? originOverride : origin
    try {
      const data = await htsLookup({ code, origin: o })
      if (data.found) setDetail(data)
    } catch {
      setError('Lookup is temporarily unavailable. Please try again in a moment.')
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />

      <section className="upload-section" style={{ paddingTop: 40 }}>
        <div className="upload-card">
          <div className="upload-title">HTS Code Lookup</div>
          <div className="upload-sub">
            Search the full 2026 US Harmonized Tariff Schedule — 29,000+ codes with official duty rates and FTA eligibility
          </div>

          {error && <div className="inline-error"><span>⚠</span><span>{error}</span></div>}

          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type an HTS code (9403.40) or keywords (kitchen cabinets)…"
            autoFocus
            style={{
              width: '100%', padding: '14px 18px', fontSize: 16,
              border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-md)',
              outline: 'none', boxSizing: 'border-box',
            }}
          />

          <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--slate-500)' }}>Try:</span>
            {EXAMPLES.map(ex => (
              <button key={ex} className="demo-link" onClick={() => setQuery(ex)}>{ex}</button>
            ))}
          </div>

          <div style={{ marginTop: 14, display: 'flex', gap: 10, alignItems: 'center' }}>
            <label style={{ fontSize: 13, color: 'var(--slate-600)', fontWeight: 500 }}>Country of origin (optional):</label>
            <input
              type="text"
              value={origin}
              onChange={e => setOrigin(e.target.value)}
              placeholder="e.g. Mexico, South Korea, China"
              style={{
                flex: 1, padding: '8px 12px', fontSize: 14,
                border: '1.5px solid var(--slate-200)', borderRadius: 8, outline: 'none',
              }}
            />
          </div>

          {loading && <div style={{ marginTop: 18, fontSize: 14, color: 'var(--slate-500)' }}>Searching…</div>}

          {results && !loading && (
            <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {results.length === 0 && (
                <div style={{ fontSize: 14, color: 'var(--slate-500)', padding: '20px 0', textAlign: 'center' }}>
                  No matching codes. Try fewer or more general keywords.
                </div>
              )}
              {results.map(r => (
                <button
                  key={r.code}
                  onClick={() => openDetail(r.code)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                    padding: '12px 16px', background: 'var(--slate-50)', textAlign: 'left',
                    border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--blue)'; e.currentTarget.style.background = 'var(--blue-light)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--slate-200)'; e.currentTarget.style.background = 'var(--slate-50)' }}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--blue)'; e.currentTarget.style.background = 'var(--blue-light)' }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--slate-200)'; e.currentTarget.style.background = 'var(--slate-50)' }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--blue)', fontFamily: 'var(--font-mono)' }}>{r.code}</div>
                    <div style={{ fontSize: 13, color: 'var(--slate-600)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {r.description}
                    </div>
                  </div>
                  <RateBadge raw={r.general_rate_raw} rate={r.general_rate} />
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      {detail && (
        <div
          onClick={() => setDetail(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: 20 }}
        >
          <div
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="HTS code details"
            style={{ background: 'var(--sheet)', borderRadius: 'var(--radius-2xl)', padding: 28, maxWidth: 560, width: '100%', maxHeight: '85vh', overflowY: 'auto', boxShadow: 'var(--shadow-xl)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
              <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--slate-900)' }}>{detail.code}</div>
              <button onClick={() => setDetail(null)} aria-label="Close" style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: 'var(--slate-400)' }}>×</button>
            </div>
            <div style={{ fontSize: 14, color: 'var(--slate-600)', marginBottom: 18, lineHeight: 1.5 }}>{detail.description}</div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 18 }}>
              <div style={{ background: 'var(--slate-50)', borderRadius: 'var(--radius-md)', padding: '12px 16px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: 0.5 }}>General (MFN) rate</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--slate-900)' }}>{detail.base_rate_raw || (detail.base_rate != null ? `${detail.base_rate}%` : '—')}</div>
              </div>
              <div style={{ background: detail.section_301_rate > 0 ? 'var(--red-light)' : 'var(--slate-50)', borderRadius: 'var(--radius-md)', padding: '12px 16px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Section 301 (China)</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: detail.section_301_rate > 0 ? 'var(--stamp)' : 'var(--slate-900)' }}>
                  {detail.section_301_rate > 0 ? `+${detail.section_301_rate}%` : origin.toLowerCase().includes('china') ? '0%' : 'n/a'}
                </div>
              </div>
            </div>

            {detail.fta_eligible && (
              <div style={{ background: 'var(--green-light)', border: '1px solid var(--green-mid)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ledger)' }}>✓ FTA eligible: {detail.fta_name} — preferential rate {detail.fta_rate}%</div>
                {detail.fta_form && <div style={{ fontSize: 12, color: 'var(--ledger-deep)', marginTop: 4 }}>Required documentation: {detail.fta_form}</div>}
              </div>
            )}

            {detail.notes && (
              <div style={{ background: 'var(--blue-light)', border: '1px solid var(--blue-mid)', borderRadius: 'var(--radius-sm)', padding: '12px 16px', marginBottom: 14, fontSize: 13, color: 'var(--ledger-deep)' }}>
                {detail.notes}
              </div>
            )}

            {detail.special_rates && Object.keys(detail.special_rates).length > 0 && (
              <details style={{ fontSize: 13, color: 'var(--slate-600)' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Special-rate programs ({Object.keys(detail.special_rates).length})</summary>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                  {Object.entries(detail.special_rates).map(([prog, rate]) => (
                    <span key={prog} style={{ fontSize: 12, padding: '2px 8px', background: 'var(--slate-100)', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
                      {prog}: {rate != null ? `${rate}%` : 'see schedule'}
                    </span>
                  ))}
                </div>
              </details>
            )}
          </div>
        </div>
      )}

      <div className="trust-section">
        <div className="trust-disclaimer">
          Rates from the official USITC 2026 Harmonized Tariff Schedule. Section 301 figures are chapter-level estimates — verify list membership with a licensed customs broker before filing.
        </div>
      </div>

      <Footer />
    </div>
  )
}
