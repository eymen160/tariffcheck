import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { analyzeInvoice, fetchDemo, ApiError } from '../lib/api'
import { saveAudit, setLastResult, newAuditId, buildAuditSummary } from '../lib/audits'

const DEMOS = [
  { id: 1, label: 'Office Furniture — Mexico', tag: 'USMCA + Misclass', color: '#059669', savings: '$3,392', desc: 'HTS 9403.90 vs 9403.10 — USMCA not claimed' },
  { id: 2, label: 'Athletic Footwear — Vietnam', tag: 'Classification', color: '#2563EB', savings: '$10,850', desc: 'HTS 6404.19 vs 6404.11 — 37.5% vs 20%' },
  { id: 3, label: 'Coffee Equipment — Colombia', tag: 'CTPA FTA', color: '#7C3AED', savings: '$4,338', desc: 'US-Colombia FTA not applied — 4.5% to 0%' },
  { id: 4, label: 'Auto Parts — South Korea', tag: 'KORUS FTA', color: '#B45309', savings: '$1,970', desc: 'KORUS preference not claimed — 2.5% to 0%' },
  { id: 5, label: 'Pharma Equipment — India', tag: 'Principal Use', color: '#DC2626', savings: '$7,105', desc: 'HTS 8477.80 vs 8479.89 — 3.5% to 0%' },
  { id: 6, label: 'Kitchen Cabinets — Vietnam', tag: 'Classification', color: '#0891b2', savings: 'Audit Risk', desc: 'HTS 9403.60 vs 9403.40 — wrong furniture subheading' },
  { id: 7, label: 'Stainless Tumblers — China', tag: 'Section 301', color: '#dc2626', savings: '$377', desc: '9617 vacuum flask vs 7323.93 stainless — rate difference' },
  { id: 8, label: 'Cotton T-shirts — Bangladesh', tag: 'Chief Weight', color: '#7c3aed', savings: '$1,302', desc: '6109.90 synthetic vs 6109.10 cotton — 32% vs 16.5%' },
]

const DEMO_TEXTS = {
  1: `COMMERCIAL INVOICE — INV: MX-INV-2026-0087
Seller: Grupo Muebles Monterrey S.A. de C.V., Monterrey, Mexico
Buyer: Atlanta Office Furnishings LLC, Atlanta, GA 30305
Country of Origin: Mexico | Incoterms: FOB Lazaro Cardenas

HTS Code: 9403.90.8040
Description: Executive office chairs, adjustable height, metal base, fabric upholstery
Quantity: 200 PCS | Unit Price: USD 320.00 | Total: USD 64,000.00

USMCA Certificate of Origin: Not attached`,

  2: `COMMERCIAL INVOICE — INV: VN-EXP-2026-2241
Seller: Hanoi Footwear Manufacturing Co. Ltd., Hanoi, Vietnam
Buyer: SportsGear USA Distributors Inc., Atlanta, GA 30336
Country of Origin: Vietnam | Incoterms: CIF Savannah

Item 1: HTS 6404.19.3560 — Athletic shoes, rubber sole, textile upper, size 6-13
Qty: 2,000 PRS | Unit: USD 22.00 | Total: USD 44,000.00

Item 2: HTS 6404.19.9060 — Walking shoes, rubber sole, mesh textile upper
Qty: 1,000 PRS | Unit: USD 18.00 | Total: USD 18,000.00

Grand Total: USD 62,000.00`,

  3: `COMMERCIAL INVOICE — INV: CO-COM-2026-0312
Seller: Industrias Tecnicas de Colombia S.A.S., Medellin, Colombia
Buyer: Specialty Coffee Roasters of America LLC, Atlanta, GA 30313
Country of Origin: Colombia | Incoterms: CIF Miami

Item 1: HTS 8419.89.1000 — Industrial coffee roasting machines, 60kg/batch capacity
Qty: 4 UNITS | Unit: USD 18,500.00 | Total: USD 74,000.00

Item 2: HTS 8419.89.1000 — Replacement drum assemblies and heating elements
Qty: 8 SETS | Unit: USD 2,800.00 | Total: USD 22,400.00

Grand Total: USD 96,400.00 | US-Colombia FTA applicable but not claimed`,

  4: `COMMERCIAL INVOICE — INV: KR-INV-2026-7734
Seller: Korea Precision Components Co. Ltd., Incheon, South Korea
Buyer: Peach State Auto Manufacturing Inc., Dacula, GA 30019
Country of Origin: South Korea | Incoterms: FOB Incheon

Item 1: HTS 8708.99.8180 — Precision transmission housings, cast aluminum
Qty: 300 PCS | Unit: USD 145.00 | Total: USD 43,500.00

Item 2: HTS 8483.40.5000 — Gear boxes and speed reducers, automotive
Qty: 150 PCS | Unit: USD 210.00 | Total: USD 31,500.00

Grand Total: USD 75,000.00 | KORUS FTA not applied at entry`,

  5: `COMMERCIAL INVOICE — INV: IN-EXP-2026-4489
Seller: Mumbai Pharma Equipment Exports Pvt. Ltd., Mumbai, India
Buyer: BioTech Processing Solutions LLC, Alpharetta, GA 30005
Country of Origin: India | Incoterms: CIF Charleston

Item 1: HTS 8477.80.0000 — Tablet coating machines, pharma grade, 316L SS
Qty: 3 UNITS | Unit: USD 42,000.00 | Total: USD 126,000.00

Item 2: HTS 8477.80.0000 — Fluid bed dryer/granulator systems, GMP 150L
Qty: 2 UNITS | Unit: USD 38,500.00 | Total: USD 77,000.00

Grand Total: USD 203,000.00`,

  6: `COMMERCIAL INVOICE — INV: VN-CAB-2026-0441
Seller: Vietnam Cabinet Manufacturing Co. Ltd., Ho Chi Minh City, Vietnam
Buyer: Southern Kitchen Supply LLC, Atlanta, GA 30349
Country of Origin: Vietnam | Incoterms: FOB Ho Chi Minh City

Item 1: HTS 9403.60.8040 — Kitchen cabinet sets, solid wood shaker style
Quantity: 36 SETS | Unit Price: USD 680.00 | Total: USD 24,480.00

Item 2: HTS 9403.60.8040 — Upper wall cabinet units, solid wood
Quantity: 48 PCS | Unit Price: USD 320.00 | Total: USD 15,360.00

Item 3: HTS 9403.90.8040 — Cabinet hardware and installation brackets
Quantity: 200 SETS | Unit Price: USD 45.00 | Total: USD 9,000.00

Grand Total: USD 48,840.00
Note: Vietnam origin. No FTA. No Section 301.`,

  7: `COMMERCIAL INVOICE — INV: CN-DRK-2026-0883
Seller: Shenzhen DrinkTech Manufacturing Co. Ltd., Shenzhen, China
Buyer: Atlanta Drinkware Imports LLC, Atlanta, GA 30318
Country of Origin: China | Incoterms: FOB Shenzhen

Item 1: HTS 9617.00.9000 — Stainless steel insulated tumblers, 20oz, powder coated, double-wall
Quantity: 500 PCS | Unit Price: USD 8.50 | Total: USD 4,250.00

Item 2: HTS 9617.00.9000 — Stainless steel insulated tumblers, 30oz, powder coated
Quantity: 300 PCS | Unit Price: USD 10.00 | Total: USD 3,000.00

Grand Total: USD 7,250.00
Note: China origin — Section 301 List 3 applies to Chapter 73 goods.`,

  8: `COMMERCIAL INVOICE — INV: BD-APR-2026-1142
Seller: Dhaka Premium Garments Ltd., Dhaka, Bangladesh
Buyer: Southeast Apparel Distributors Inc., Atlanta, GA 30336
Country of Origin: Bangladesh | Incoterms: CIF Savannah

Item 1: HTS 6109.90.1007 — Crew neck t-shirts, 60% cotton 40% polyester blend, unisex
Quantity: 2,000 PCS | Unit Price: USD 4.20 | Total: USD 8,400.00

Grand Total: USD 8,400.00
Note: Bangladesh origin. No FTA. No Section 301.`,
}

const DEMO_ICONS = { 1: '🪑', 2: '👟', 3: '☕', 4: '⚙️', 5: '💊', 6: '🪵', 7: '🥤', 8: '👕' }

const STEPS = [
  'Extracting invoice lines…',
  'Matching HTS codes against the USITC schedule…',
  'Auditing classifications…',
  'Verifying savings math against official rates…',
]

const CLIENT_TIMEOUT_MS = 45000

function friendlyError(err) {
  if (err instanceof ApiError) {
    switch (err.code) {
      case 'ai_unavailable':
        return "Live AI analysis isn't available right now — try a sample scenario below."
      case 'rate_limited':
        return 'Too many analyses from this address. Please wait a minute and retry.'
      case 'unreadable_file':
        return "We couldn't read this file. Try a PDF with selectable text, or paste the invoice as text."
      case 'text_too_short':
        return err.message || 'Invoice text too short. Include product descriptions, HTS codes, values, and country of origin.'
      case 'model_timeout':
        return 'Analysis took too long. Try a shorter invoice or retry.'
      case 'model_error':
        return 'The AI analysis failed. Please retry.'
      case 'client_timeout':
        return 'The analysis did not finish within 45 seconds, so we stopped it. Try a shorter invoice or retry in a moment.'
      case 'network_error':
        return 'We could not reach the analysis service. Please check your connection and try again.'
      default:
        return err.message || 'Something went wrong. Please try again.'
    }
  }
  if (err && err.name === 'AbortError') {
    return 'The analysis did not finish within 45 seconds, so we stopped it. Try a shorter invoice or retry in a moment.'
  }
  return 'Something went wrong. Please try again.'
}

export default function HomePage() {
  const [tab, setTab] = useState('demo')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')
  const [activeDemo, setActiveDemo] = useState(null)
  const fileRef = useRef()
  const timersRef = useRef([])
  const navigate = useNavigate()

  useEffect(() => () => timersRef.current.forEach(t => clearTimeout(t)), [])

  function beginProgress(intervalMs) {
    setLoading(true)
    setError('')
    setStep(0)
    const t = setInterval(() => setStep(s => (s < STEPS.length - 1 ? s + 1 : s)), intervalMs)
    timersRef.current.push(t)
    return t
  }

  async function runAnalysis({ demoId, sourceName }) {
    const stepTimer = beginProgress(demoId ? 600 : 3500)
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), CLIENT_TIMEOUT_MS)
    timersRef.current.push(timeout)
    try {
      let data
      if (demoId != null) {
        try {
          data = await analyzeInvoice({ demoId, signal: controller.signal })
        } catch (err) {
          // Contract path is POST /api/analyze {demo_id}; fall back to the legacy
          // GET /api/demo/<id> so sample scenarios never break during rollout.
          if (err instanceof ApiError && (err.status === 404 || err.status === 400 || err.status === 405)) {
            data = await fetchDemo(demoId, controller.signal)
          } else {
            throw err
          }
        }
        data.meta = { ...(data.meta || {}), demo: true }
      } else {
        data = await analyzeInvoice({ text: tab === 'text' ? text : undefined, file: tab === 'file' ? file : undefined, signal: controller.signal })
      }

      setLastResult(data)
      saveAudit({
        id: newAuditId(),
        ts: Date.now(),
        sourceName,
        summary: buildAuditSummary(data),
        fullResponse: data,
      })
      setStep(STEPS.length - 1)
      setTimeout(() => navigate('/results'), 250)
    } catch (err) {
      setLoading(false)
      setError(friendlyError(err))
    } finally {
      clearInterval(stepTimer)
      clearTimeout(timeout)
    }
  }

  function runDemo(id) {
    setActiveDemo(id)
    const demo = DEMOS.find(d => d.id === id)
    runAnalysis({ demoId: id, sourceName: `Sample: ${demo ? demo.label : `Scenario ${id}`}` })
  }

  function handleSubmit() {
    if (tab === 'text' && !text.trim()) return
    if (tab === 'file' && !file) return
    runAnalysis({ sourceName: tab === 'file' && file ? file.name : 'Pasted invoice' })
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--slate-50)' }}>
        <Navbar />
        <div className="loading-outer">
          <div className="loading-card">
            <div className="loading-spinner-big" />
            <div className="loading-title">Auditing Your Invoice</div>
            <div className="loading-sub">Every finding is re-verified against the official USITC HTS 2026 schedule</div>
            <ul className="loading-steps">
              {STEPS.map((s, i) => (
                <li key={i} className={`loading-step ${i < step ? 'done' : i === step ? 'active' : ''}`}>
                  <div className="step-dot" />
                  <span>{i < step ? '✓ ' : ''}{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--slate-50)' }}>
      <Navbar />

      <section className="hero">
        <div className="hero-inner">
          <h1 className="hero-title">You're probably overpaying tariffs.<br /><span>Find out in 60 seconds.</span></h1>
          <p className="hero-sub">
            TariffCheck audits your invoices against the full 29,755-code USITC tariff schedule, finds misclassifications
            and missed FTA claims, computes exactly what you overpaid, and drafts a ready-to-file CBP protest — before
            your 180-day window closes.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
            <a href="#analyze" className="btn-primary" style={{ padding: '13px 26px', fontSize: 15 }}>Audit an invoice — free</a>
            <Link to="/hts-lookup" className="btn-secondary" style={{ padding: '13px 26px', fontSize: 15 }}>Look up any HTS code</Link>
          </div>
          <div className="hero-trust-chips">
            <span className="hero-trust-chip">📊 Built on the complete 2026 USITC HTS — 29,755 codes</span>
            <span className="hero-trust-chip">✓ Every AI finding re-verified against the official schedule</span>
            <span className="hero-trust-chip">⚖ Misclassification drives ~42% of CBP penalties</span>
          </div>
        </div>
      </section>

      <section className="upload-section" id="analyze">
        <div className="upload-card">
          <div className="upload-title">Audit Your Invoice</div>
          <div className="upload-sub">Paste or upload a commercial invoice — or explore a sample scenario</div>

          {error && <div className="inline-error"><span>⚠</span><span>{error}</span></div>}

          <div className="tabs">
            <button className={`tab-btn ${tab === 'demo' ? 'active' : ''}`} onClick={() => setTab('demo')}>⚡ Sample Scenarios</button>
            <button className={`tab-btn ${tab === 'text' ? 'active' : ''}`} onClick={() => setTab('text')}>📝 Paste Text</button>
            <button className={`tab-btn ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>📄 Upload PDF</button>
          </div>

          {tab === 'demo' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {DEMOS.map(d => (
                <button
                  key={d.id}
                  onClick={() => runDemo(d.id)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '16px 20px', background: 'var(--slate-50)',
                    border: `1.5px solid var(--slate-200)`, borderRadius: 'var(--radius-md)',
                    cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left',
                    ...(activeDemo === d.id ? { borderColor: 'var(--blue)', background: 'var(--blue-light)' } : {}),
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--blue)'; e.currentTarget.style.background = 'var(--blue-light)' }}
                  onMouseLeave={e => { if (activeDemo !== d.id) { e.currentTarget.style.borderColor = 'var(--slate-200)'; e.currentTarget.style.background = 'var(--slate-50)' } }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{ width: 40, height: 40, borderRadius: 10, background: d.color + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
                      {DEMO_ICONS[d.id]}
                    </div>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--slate-900)', marginBottom: 2, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        {d.label}
                        <span className="badge-sample" style={{ fontSize: 9, padding: '2px 8px' }}>Sample data</span>
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--slate-500)' }}>{d.desc}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 20, background: d.color + '18', color: d.color, border: `1px solid ${d.color}30` }}>{d.tag}</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: d.color }}>{d.savings}</span>
                    <span style={{ color: 'var(--slate-300)', fontSize: 18 }}>→</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {tab === 'text' && (
            <>
              <textarea
                className="invoice-textarea"
                placeholder="Paste your commercial invoice here. Include HTS codes, product descriptions, declared values, and country of origin."
                value={text}
                onChange={e => setText(e.target.value)}
              />
              <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {DEMOS.map(d => (
                  <button key={d.id} className="demo-link" onClick={() => setText(DEMO_TEXTS[d.id])}>
                    {DEMO_ICONS[d.id]} {d.label}
                  </button>
                ))}
              </div>
              <button className="submit-btn" onClick={handleSubmit} disabled={!text.trim()}>
                Audit this invoice
              </button>
            </>
          )}

          {tab === 'file' && (
            <>
              <div
                className={`drop-zone ${dragging ? 'dragging' : ''}`}
                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileRef.current.click()}
              >
                <div className="drop-icon">{file ? '✅' : '📄'}</div>
                <div className="drop-title">{file ? file.name : 'Drag and drop your invoice PDF here'}</div>
                <div className="drop-sub">{file ? 'Click to change file' : 'or click to browse — PDF or TXT accepted'}</div>
                <input ref={fileRef} type="file" accept=".pdf,.txt" onChange={e => setFile(e.target.files[0])} />
              </div>
              <button className="submit-btn" onClick={handleSubmit} disabled={!file}>
                Audit uploaded invoice
              </button>
            </>
          )}
        </div>
      </section>

      {/* Broker banner */}
      <section style={{ maxWidth: 780, margin: '0 auto', padding: '0 24px 40px' }}>
        <Link
          to="/brokers"
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
            background: 'linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)',
            border: '1px solid var(--blue-mid)', borderRadius: 'var(--radius-lg)',
            padding: '20px 26px', textDecoration: 'none',
          }}
        >
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--slate-900)' }}>Customs broker? Bulk-scan your clients' invoices →</div>
            <div style={{ fontSize: 13, color: 'var(--slate-600)', marginTop: 4 }}>
              Screen entire client portfolios against the official USITC schedule and turn declined protest work into a new fee line.
            </div>
          </div>
          <span style={{ fontSize: 24 }}>🗂️</span>
        </Link>
      </section>

      <section className="niche-callout-section">
        <div className="niche-callout">
          <div className="niche-callout-icon">🪵</div>
          <div className="niche-callout-content">
            <h3 className="niche-callout-title">Furniture & Cabinet Importers: Vietnam and China Sourcing?</h3>
            <div className="niche-callout-points">
              <div className="niche-point">
                <span className="niche-dot">•</span>
                <span>Chapter 94 misclassification (9403.40 vs 9403.60 vs 9403.89) is the #1 error in furniture imports — same rate but wrong code creates audit exposure</span>
              </div>
              <div className="niche-point">
                <span className="niche-dot">•</span>
                <span>Vietnam-origin cabinets: No Section 301, but base rate misclassification still triggers CBP scrutiny</span>
              </div>
              <div className="niche-point">
                <span className="niche-dot">•</span>
                <span>China-origin furniture: 25% Section 301 (List 3) stacks on base rate — correct classification critical</span>
              </div>
              <div className="niche-point">
                <span className="niche-dot">•</span>
                <span>Marble/stone importers: polished countertops (6802.91) vs raw slabs (6802.21) — different rates, commonly confused</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="how-section">
        <div className="section-label">How it works</div>
        <h2 className="section-title">Three steps to reclaim your duties</h2>
        <div className="steps-grid">
          {[
            { num: '01', icon: '📄', title: 'Upload Invoice', desc: 'Paste your commercial invoice or upload a PDF. Include HTS codes, product descriptions, declared values, and country of origin.' },
            { num: '02', icon: '🔍', title: 'AI Audit + Verification', desc: 'Claude audits every line, then each finding is deterministically re-verified against the complete 29,755-code USITC HTS 2026 schedule — savings are recomputed server-side.' },
            { num: '03', icon: '⚖️', title: 'Ready-to-File Protest', desc: 'Receive a draft CBP protest citing 19 U.S.C. 1514 for the importer of record or your licensed broker to review and file. You have 180 days from liquidation.' },
          ].map(s => (
            <div className="step-card" key={s.num}>
              <div className="step-num">{s.num}</div>
              <span className="step-icon">{s.icon}</span>
              <div className="step-title">{s.title}</div>
              <div className="step-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="trust-section">
        <div className="trust-badges">
          <div className="trust-item">📊 Official USITC Tariff Data</div>
          <div className="trust-item">⚖ 19 U.S.C. 1514 Compliant Drafts</div>
          <div className="trust-item">🌎 USMCA and KORUS FTA Checks</div>
          <div className="trust-item">🏛 CBP Form 19 Ready</div>
        </div>
        <div className="trust-disclaimer">
          TariffCheck prepares filings; it does not file with CBP. All findings should be reviewed by the importer of
          record or a licensed customs broker before filing a formal protest.
        </div>
      </div>

      <Footer />
    </div>
  )
}
