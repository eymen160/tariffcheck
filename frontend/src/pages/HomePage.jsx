import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { analyzeInvoice, fetchDemo, ApiError } from '../lib/api'
import { saveAudit, setLastResult, newAuditId, buildAuditSummary } from '../lib/audits'

const DEMOS = [
  { id: 1, code: '9403.90', label: 'Office furniture — Mexico', tag: 'USMCA missed', savings: '$3,392', desc: 'Parts code used for finished chairs; USMCA never claimed' },
  { id: 2, code: '6404.19', label: 'Athletic footwear — Vietnam', tag: 'Misclassified', savings: '$10,850', desc: 'Sports footwear provision applies — 37.5% paid vs 20% owed' },
  { id: 3, code: '8419.89', label: 'Coffee equipment — Colombia', tag: 'FTA missed', savings: '$4,338', desc: 'US–Colombia TPA not applied — 4.5% paid vs 0% owed' },
  { id: 4, code: '8708.99', label: 'Auto parts — South Korea', tag: 'FTA missed', savings: '$1,970', desc: 'KORUS preference not claimed at entry — 2.5% to 0%' },
  { id: 5, code: '8477.80', label: 'Pharma equipment — India', tag: 'Misclassified', savings: '$7,105', desc: 'Principal-use provision applies — 3.5% to 0%' },
  { id: 6, code: '9403.60', label: 'Kitchen cabinets — Vietnam', tag: 'Audit risk', savings: 'Exposure', desc: 'Wrong furniture subheading — same rate, CBP scrutiny risk' },
  { id: 7, code: '9617.00', label: 'Stainless tumblers — China', tag: 'Section 301', savings: '$377', desc: 'Vacuum-flask vs stainless-article codes carry different rates' },
  { id: 8, code: '6109.90', label: 'Cotton t-shirts — Bangladesh', tag: 'Misclassified', savings: '$1,302', desc: 'Synthetic code used for chief-weight cotton — 32% vs 16.5%' },
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

function StampSeal() {
  return (
    <svg className="stamp-seal" viewBox="0 0 120 120" aria-hidden="true">
      <defs>
        <path id="seal-arc" d="M 60,60 m -41,0 a 41,41 0 1,1 82,0 a 41,41 0 1,1 -82,0" />
      </defs>
      <circle cx="60" cy="60" r="54" fill="none" stroke="#0A5C3E" strokeWidth="2.5" opacity="0.85" />
      <circle cx="60" cy="60" r="50" fill="none" stroke="#0A5C3E" strokeWidth="1" opacity="0.7" />
      <circle cx="60" cy="60" r="30" fill="none" stroke="#0A5C3E" strokeWidth="1" opacity="0.7" />
      <text fill="#0A5C3E" fontFamily="'IBM Plex Mono', monospace" fontSize="10.5" fontWeight="600" letterSpacing="2.6">
        <textPath href="#seal-arc" startOffset="0">RE-VERIFIED · USITC HTS 2026 ·</textPath>
      </text>
      <path d="M 47,60 l 9,9 l 17,-18" fill="none" stroke="#0A5C3E" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
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
      <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
        <Navbar />
        <div className="loading-outer">
          <div className="loading-card">
            <div className="loading-spinner-big" />
            <div className="loading-title">Auditing your invoice</div>
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
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />

      <section className="hero">
        <div className="hero-inner">
          <div className="hero-grid">
            <div>
              <div className="hero-eyebrow">Customs duty audit · 19 U.S.C. §1514</div>
              <h1 className="hero-title">
                Find the duty you overpaid. <em>Then take it back.</em>
              </h1>
              <p className="hero-sub">
                TariffCheck audits your import invoices against all <strong>29,755 codes</strong> in
                the official USITC tariff schedule, recomputes every dollar server-side, and drafts
                the protest your broker files. You have <strong>180 days</strong> from liquidation.
              </p>
              <div className="hero-ctas">
                <a href="#analyze" className="btn-primary" style={{ padding: '14px 28px', fontSize: 15 }}>Audit an invoice — free</a>
                <Link to="/hts-lookup" className="btn-secondary" style={{ padding: '14px 28px', fontSize: 15 }}>Look up an HTS code</Link>
              </div>
              <div className="hero-facts">
                <span className="hero-fact"><b>29,755</b> USITC codes in-product</span>
                <span className="hero-fact"><b>Every finding</b> re-verified</span>
                <span className="hero-fact"><b>No signup</b> for your first audit</span>
              </div>
            </div>

            <div className="specimen" aria-label="Example audit finding: misclassified office chairs from Mexico, $3,392 recoverable">
              <div className="specimen-head">
                <span className="specimen-head-label">Audit specimen · Entry line 001</span>
                <span className="specimen-sample-tag">Sample</span>
              </div>
              <div className="specimen-body">
                <div className="spec-reveal-1">
                  <div className="specimen-row">
                    <span className="specimen-key">Merchandise</span>
                    200 × Executive office chairs — Mexico · $64,000.00
                  </div>
                </div>
                <div className="spec-reveal-2">
                  <div className="specimen-code-row">
                    <span className="code-struck">9403.90.8040</span>
                    <span className="code-corrected">9403.10 + USMCA</span>
                  </div>
                  <div className="specimen-note">Parts code used for finished chairs · USMCA preference never claimed</div>
                </div>
                <div className="tally spec-reveal-3">
                  <div className="tally-row">
                    <span>Duty paid at entry</span><span className="leader" /><span className="tally-amount">$3,392.00</span>
                  </div>
                  <div className="tally-row">
                    <span>Duty owed under USMCA</span><span className="leader" /><span className="tally-amount">$0.00</span>
                  </div>
                  <div className="tally-row recovered">
                    <span className="tally-label">Recoverable via §1514 protest</span><span className="leader" /><span className="tally-amount">$3,392.00</span>
                  </div>
                </div>
              </div>
              <div className="specimen-foot">
                Recomputed server-side against USITC HTS 2026 · Filed by the importer of record or a licensed broker
              </div>
              <StampSeal />
            </div>
          </div>
        </div>
      </section>

      <section className="upload-section" id="analyze">
        <div className="upload-card">
          <div className="upload-kicker">Free audit — no signup</div>
          <div className="upload-title">Audit your invoice</div>
          <div className="upload-sub">Paste or upload a commercial invoice, or open a sample scenario to see a full audit.</div>

          {error && <div className="inline-error"><span>⚠</span><span>{error}</span></div>}

          <div className="tabs" role="tablist">
            <button role="tab" aria-selected={tab === 'demo'} className={`tab-btn ${tab === 'demo' ? 'active' : ''}`} onClick={() => setTab('demo')}>Sample scenarios</button>
            <button role="tab" aria-selected={tab === 'text'} className={`tab-btn ${tab === 'text' ? 'active' : ''}`} onClick={() => setTab('text')}>Paste text</button>
            <button role="tab" aria-selected={tab === 'file'} className={`tab-btn ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>Upload PDF</button>
          </div>

          {tab === 'demo' && (
            <div className="ledger-list">
              {DEMOS.map(d => (
                <button key={d.id} onClick={() => runDemo(d.id)} className={`ledger-row ${activeDemo === d.id ? 'active' : ''}`}>
                  <div className="ledger-row-main">
                    <span className="ledger-row-code">{d.code}</span>
                    <span style={{ minWidth: 0 }}>
                      <span className="ledger-row-title">{d.label}</span>
                      <span className="ledger-row-desc" style={{ display: 'block' }}>{d.desc}</span>
                    </span>
                  </div>
                  <div className="ledger-row-right">
                    <span className="ledger-row-tag">{d.tag}</span>
                    <span className={`ledger-row-amount ${d.savings === 'Exposure' ? 'risk' : ''}`}>{d.savings}</span>
                    <span className="ledger-row-arrow">→</span>
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
                    {d.label}
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
                <div className="drop-title">{file ? file.name : 'Drag and drop your invoice PDF here'}</div>
                <div className="drop-sub">{file ? 'Click to choose a different file' : 'or click to browse — PDF or TXT accepted'}</div>
                <input ref={fileRef} type="file" accept=".pdf,.txt" onChange={e => setFile(e.target.files[0])} />
              </div>
              <button className="submit-btn" onClick={handleSubmit} disabled={!file}>
                Audit uploaded invoice
              </button>
            </>
          )}
        </div>
      </section>

      <section className="how-section">
        <div className="section-label">How it works</div>
        <h2 className="section-title">From invoice to protest letter</h2>
        <div className="steps-grid">
          {[
            { num: '01', title: 'Submit the invoice', desc: 'Paste a commercial invoice or upload a PDF. Include HTS codes, product descriptions, declared values, and country of origin.' },
            { num: '02', title: 'Audit, then re-verify', desc: 'AI reviews every line for misclassification, missed FTA claims, and Section 301 exposure. Each finding is then recomputed against the complete 29,755-code USITC HTS 2026 schedule — an unverified number never reaches your report.' },
            { num: '03', title: 'File the protest', desc: 'You receive a draft protest under 19 U.S.C. §1514, ready for the importer of record or your licensed broker to review and file. The window is 180 days from liquidation.' },
          ].map(s => (
            <div className="step-card" key={s.num}>
              <div className="step-num">{s.num}</div>
              <div className="step-title">{s.title}</div>
              <div className="step-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="niche-callout-section">
        <h2 className="niche-callout-title">Where overpayment hides</h2>
        <p className="niche-callout-sub">
          Four patterns account for most of the duty importers never should have paid. Every audit checks all of them, line by line.
        </p>
        <div className="niche-callout-points">
          <div className="niche-point">
            <span className="niche-point-code">Ch. 94 — furniture</span>
            Finished goods entered under parts codes (9403.90 vs 9403.10/.60) — the single most common furniture error, and a CBP audit trigger even when rates match.
          </div>
          <div className="niche-point">
            <span className="niche-point-code">FTA never claimed</span>
            USMCA, KORUS, and 19 other free-trade preferences left unclaimed at entry — duty paid at the full MFN rate on goods that qualified for 0%.
          </div>
          <div className="niche-point">
            <span className="niche-point-code">Section 301 stacking</span>
            China-origin goods where a wrong base code pulls in a 25% List 3 surcharge — or keeps one that no longer applies after the 2025–26 rate changes.
          </div>
          <div className="niche-point">
            <span className="niche-point-code">Material & use provisions</span>
            Chief-weight fiber rules in apparel, principal-use provisions in machinery — distinctions that shift rates by 10–20 points and are easy to file wrong.
          </div>
        </div>
      </section>

      <section className="broker-band">
        <div className="broker-band-inner">
          <div>
            <div className="broker-band-title">Customs broker? Scan a client's last 90 days in minutes.</div>
            <div className="broker-band-sub">
              Batch-audit entire client portfolios against the official USITC schedule and turn declined protest work into a billable service line.
            </div>
          </div>
          <Link to="/brokers" className="btn-secondary" style={{ whiteSpace: 'nowrap' }}>Batch audit for brokers →</Link>
        </div>
      </section>

      <div className="trust-section">
        <div className="trust-badges">
          <div className="trust-item">Official USITC 2026 data</div>
          <div className="trust-item">§1514-compliant drafts</div>
          <div className="trust-item">USMCA · KORUS · 21 FTAs</div>
          <div className="trust-item">CBP Form 19 ready</div>
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
