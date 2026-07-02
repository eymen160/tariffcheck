import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { htsSearch, landedCost, ApiError, isFeatureUnavailable } from '../lib/api'
import { money, rate } from '../lib/format'
import { usePageTitle } from '../lib/usePageTitle'

const ORIGINS = ['China', 'Vietnam', 'India', 'Mexico', 'Canada', 'South Korea', 'Japan', 'Colombia', 'Other / not listed']

export default function CalculatorPage() {
  const [code, setCode] = useState('')
  const [suggestions, setSuggestions] = useState(null)
  const [origin, setOrigin] = useState('China')
  const [value, setValue] = useState('50000')
  const [mode, setMode] = useState('ocean')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [unavailable, setUnavailable] = useState(false)
  const debounce = useRef()
  const skipSearch = useRef(false)

  usePageTitle('Landed Cost Calculator')

  useEffect(() => {
    clearTimeout(debounce.current)
    if (skipSearch.current) { skipSearch.current = false; return }
    const q = code.trim()
    if (q.length < 2) { setSuggestions(null); return }
    debounce.current = setTimeout(async () => {
      try {
        const data = await htsSearch(q, 8)
        setSuggestions(data.results || [])
      } catch {
        setSuggestions(null) // typeahead is best-effort; manual code entry still works
      }
    }, 300)
    return () => clearTimeout(debounce.current)
  }, [code])

  function pickSuggestion(c) {
    skipSearch.current = true
    setCode(c)
    setSuggestions(null)
  }

  async function calculate() {
    const num = parseFloat(String(value).replace(/[$,\s]/g, ''))
    if (!code.trim() || isNaN(num) || num <= 0) {
      setError('Enter an HTS code and a positive shipment value.')
      return
    }
    setError('')
    setUnavailable(false)
    setLoading(true)
    setResult(null)
    try {
      const originParam = origin.startsWith('Other') ? '' : origin
      const data = await landedCost({ code: code.trim(), origin: originParam, value: num, mode })
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'code_not_found') {
        setError(err.message || `HTS code ${code.trim()} was not found in the USITC schedule.`)
      } else if (isFeatureUnavailable(err)) {
        setUnavailable(true)
      } else {
        setError(err.message || 'The calculation failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const b = result?.breakdown

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ maxWidth: 720, margin: '0 auto', padding: '40px 24px 64px', width: '100%', flex: 1 }}>
        <h1 style={{ fontSize: 30, letterSpacing: '-0.75px', color: 'var(--slate-900)', marginBottom: 6 }}>Landed Cost Calculator</h1>
        <p style={{ fontSize: 15, color: 'var(--slate-500)', marginBottom: 28 }}>
          Full duty stack for any shipment — MFN duty, Section 301, MPF and HMF — straight from the official
          USITC HTS 2026 schedule.
        </p>

        <div className="card" style={{ marginBottom: 24 }}>
          {/* HTS code with typeahead */}
          <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--slate-600)', display: 'block', marginBottom: 6 }}>HTS code</label>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="e.g. 9403.40.9060 — or search: kitchen cabinets"
              style={{ width: '100%', padding: '12px 16px', fontSize: 15, border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', outline: 'none', fontFamily: 'var(--font-mono)' }}
            />
            {suggestions && suggestions.length > 0 && (
              <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30, background: 'white', border: '1px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', boxShadow: 'var(--shadow-lg)', maxHeight: 280, overflowY: 'auto', marginTop: 4 }}>
                {suggestions.map(s => (
                  <button
                    key={s.code}
                    onClick={() => pickSuggestion(s.code)}
                    style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 14px', background: 'white', border: 'none', borderBottom: '1px solid var(--slate-100)', cursor: 'pointer' }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'var(--blue-light)' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'white' }}
                    onFocus={e => { e.currentTarget.style.background = 'var(--blue-light)' }}
                    onBlur={e => { e.currentTarget.style.background = 'white' }}
                  >
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color: 'var(--blue)' }}>{s.code}</span>
                    <span style={{ fontSize: 12.5, color: 'var(--slate-600)', marginLeft: 10 }}>
                      {String(s.description || '').slice(0, 90)}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 14, marginTop: 16, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 160 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--slate-600)', display: 'block', marginBottom: 6 }}>Country of origin</label>
              <select
                value={origin}
                onChange={e => setOrigin(e.target.value)}
                style={{ width: '100%', padding: '12px 14px', fontSize: 14, border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', background: 'white', color: 'var(--slate-700)' }}
              >
                {ORIGINS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 160 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--slate-600)', display: 'block', marginBottom: 6 }}>Shipment value (USD)</label>
              <input
                type="text"
                inputMode="decimal"
                value={value}
                onChange={e => setValue(e.target.value)}
                placeholder="50000"
                style={{ width: '100%', padding: '12px 14px', fontSize: 14, border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--slate-600)', display: 'block', marginBottom: 6 }}>Transport</label>
              <div style={{ display: 'flex', border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                {['ocean', 'air'].map(m => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    style={{
                      padding: '12px 20px', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer',
                      background: mode === m ? 'var(--blue)' : 'white',
                      color: mode === m ? 'white' : 'var(--slate-600)',
                    }}
                  >
                    {m === 'ocean' ? 'Ocean' : 'Air'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {error && <div className="inline-error" style={{ marginTop: 16, marginBottom: 0 }}><span>⚠</span><span>{error}</span></div>}

          <button className="btn-primary" style={{ marginTop: 18, padding: '13px 28px', fontSize: 15 }} onClick={calculate} disabled={loading}>
            {loading ? 'Calculating…' : 'Calculate landed duty'}
          </button>
        </div>

        {unavailable && (
          <div className="rollout-card" style={{ marginBottom: 24 }}>
            <strong>This feature is rolling out — try the invoice audit instead.</strong>
            <div style={{ marginTop: 6 }}>
              The landed-cost calculator is not available on this deployment yet.{' '}
              <Link to="/" style={{ color: 'var(--blue)', fontWeight: 600 }}>Run an invoice audit →</Link>{' '}
              or <Link to="/hts-lookup" style={{ color: 'var(--blue)', fontWeight: 600 }}>look up the code's duty rate →</Link>
            </div>
          </div>
        )}

        {result && result.found && b && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ marginBottom: 4, display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 600, color: 'var(--slate-900)' }}>{result.code}</span>
              <span style={{ fontSize: 13, color: 'var(--slate-500)' }}>
                {result.origin || 'Any origin'} · {money(result.value)} · {result.mode === 'air' ? 'Air' : 'Ocean'}
              </span>
            </div>
            {result.matched_note && (
              <div style={{ fontSize: 12, color: 'var(--amber)', marginBottom: 6 }}>⚠ {result.matched_note}</div>
            )}
            <div style={{ fontSize: 13.5, color: 'var(--slate-600)', marginBottom: 18, lineHeight: 1.5 }}>{result.description}</div>

            <div className="receipt-row">
              <span>MFN duty <span style={{ color: 'var(--slate-400)' }}>({b.mfn_rate_raw || rate(b.mfn_rate)})</span></span>
              <span style={{ fontWeight: 600 }}>{money(b.mfn_duty)}</span>
            </div>
            {b.section_301_rate > 0 && (
              <div className="receipt-row" style={{ flexWrap: 'wrap' }}>
                <span>
                  Section 301 <span style={{ color: 'var(--slate-400)' }}>({rate(b.section_301_rate)})</span>
                  {b.section_301_note && <div className="receipt-fineprint">{b.section_301_note}</div>}
                </span>
                <span style={{ fontWeight: 600, color: 'var(--red)' }}>{money(b.section_301_duty)}</span>
              </div>
            )}
            <div className="receipt-row">
              <span>
                Merchandise Processing Fee <span style={{ color: 'var(--slate-400)' }}>({rate(b.mpf_rate)})</span>
                <div className="receipt-fineprint">2026 bounds: min {money(b.mpf_min)}, max {money(b.mpf_max)}</div>
              </span>
              <span style={{ fontWeight: 600 }}>{money(b.mpf)}</span>
            </div>
            {result.mode !== 'air' && (
              <div className="receipt-row">
                <span>Harbor Maintenance Fee <span style={{ color: 'var(--slate-400)' }}>({rate(b.hmf_rate)})</span></span>
                <span style={{ fontWeight: 600 }}>{money(b.hmf)}</span>
              </div>
            )}
            <div className="receipt-row total">
              <span>Total landed duty <span style={{ fontWeight: 500, fontSize: 13, color: 'var(--slate-500)' }}>· effective {rate(result.effective_rate)} of value</span></span>
              <span style={{ color: 'var(--slate-900)' }}>{money(result.total_landed_duty)}</span>
            </div>

            {result.fta && (
              <div style={{ background: 'var(--green-light)', border: '1px solid var(--green-mid)', borderRadius: 'var(--radius-md)', padding: '14px 18px', marginTop: 18, fontSize: 14, color: 'var(--green)' }}>
                <strong>✓ With {result.fta.form} under {result.fta.name}: save {money(result.fta.savings)}</strong>
                <div style={{ fontSize: 12.5, marginTop: 4, color: 'var(--ledger-deep)' }}>
                  Preferential rate {rate(result.fta.rate)} — duty drops to {money(result.fta.duty_with_fta)}.
                </div>
              </div>
            )}

            {result.disclaimer && (
              <div style={{ fontSize: 12, color: 'var(--slate-400)', marginTop: 16, lineHeight: 1.55 }}>{result.disclaimer}</div>
            )}
          </div>
        )}

        {/* CTA */}
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <Link to="/" className="btn-primary" style={{ padding: '13px 26px', fontSize: 15 }}>
            Think you overpaid on past entries like this? Run an audit →
          </Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
