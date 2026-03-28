import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

const API = 'http://localhost:8000'

const DEMOS = [
  { id: 1, label: 'Office Furniture — Mexico', tag: 'USMCA + Misclass', color: '#059669', savings: '$3,392', desc: 'HTS 9403.90 vs 9403.10 — USMCA not claimed' },
  { id: 2, label: 'Athletic Footwear — Vietnam', tag: 'Classification', color: '#2563EB', savings: '$10,850', desc: 'HTS 6404.19 vs 6404.11 — 37.5% vs 20%' },
  { id: 3, label: 'Coffee Equipment — Colombia', tag: 'CTPA FTA', color: '#7C3AED', savings: '$4,338', desc: 'US-Colombia FTA not applied — 4.5% to 0%' },
  { id: 4, label: 'Auto Parts — South Korea', tag: 'KORUS FTA', color: '#B45309', savings: '$1,970', desc: 'KORUS preference not claimed — 2.5% to 0%' },
  { id: 5, label: 'Pharma Equipment — India', tag: 'Principal Use', color: '#DC2626', savings: '$7,105', desc: 'HTS 8477.80 vs 8479.89 — 3.5% to 0%' },
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
}


const DEMO_ICONS = { 1: '🪑', 2: '👟', 3: '☕', 4: '⚙️', 5: '💊' }

const STEPS = [
  'Parsing invoice document...',
  'Comparing to USITC tariff schedule...',
  'Identifying misclassifications...',
  'Generating CBP protest letter...',
]

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
  const navigate = useNavigate()

  function startSteps(ms=700) {
    setLoading(true); setError(''); setStep(0)
    const t = setInterval(() => setStep(s => s < STEPS.length-1 ? s+1 : s), ms)
    return t
  }

  async function runDemo(id) {
    setActiveDemo(id)
    const t = startSteps(600)
    try {
      const res = await fetch(`${API}/demo/${id}`)
      const data = await res.json()
      clearInterval(t)
      setTimeout(() => navigate('/results', { state: { data, demoId: id } }), 300)
    } catch {
      clearInterval(t)
      setLoading(false)
      setError('Backend not reachable on port 8000. Run: PORT=8000 python3 app.py')
    }
  }

  async function handleSubmit() {
    if (tab==='text' && !text.trim()) return
    if (tab==='file' && !file) return
    const t = startSteps(800)
    try {
      let data
      if (tab==='text') {
        const res = await fetch(`${API}/analyze`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text}) })
        data = await res.json()
      } else {
        const fd = new FormData(); fd.append('file', file)
        const res = await fetch(`${API}/analyze`, { method:'POST', body:fd })
        data = await res.json()
      }
      clearInterval(t)
      setTimeout(() => navigate('/results', { state: { data } }), 300)
    } catch {
      clearInterval(t)
      setLoading(false)
      setError('Cannot connect to backend on port 8000. Run: PORT=8000 python3 app.py')
    }
  }

  function onDrop(e) {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]; if (f) setFile(f)
  }

  if (loading) {
    return (
      <div style={{minHeight:'100vh',background:'var(--slate-50)'}}>
        <Navbar />
        <div className="loading-outer">
          <div className="loading-card">
            <div className="loading-spinner-big" />
            <div className="loading-title">Analyzing Your Invoice</div>
            <div className="loading-sub">Comparing against the official US Harmonized Tariff Schedule</div>
            <ul className="loading-steps">
              {STEPS.map((s,i) => (
                <li key={i} className={`loading-step ${i<step?'done':i===step?'active':''}`}>
                  <div className="step-dot" />
                  <span>{i<step?'✓ ':''}{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{minHeight:'100vh',background:'var(--slate-50)'}}>
      <Navbar />

      <section className="hero">
        <div className="hero-inner">
          <h1 className="hero-title">Stop Overpaying<br /><span>Customs Duties</span></h1>
          <p className="hero-sub">
            Upload your commercial invoice. Our AI compares your HTS codes against the official US tariff schedule, finds misclassifications, and generates a ready-to-file CBP protest letter in seconds.
          </p>
          <div className="stats-row">
            <div className="stat-item"><span className="stat-num">$26B</span><span className="stat-label">overpaid in duties annually</span></div>
            <div className="stat-item"><span className="stat-num">14M+</span><span className="stat-label">customs entries per year</span></div>
            <div className="stat-item"><span className="stat-num">180</span><span className="stat-label">days to file CBP protest</span></div>
          </div>
        </div>
      </section>

      <section className="upload-section">
        <div className="upload-card">
          <div className="upload-title">Analyze Your Invoice</div>
          <div className="upload-sub">Choose a demo scenario or upload your own invoice</div>

          {error && <div className="inline-error"><span>⚠</span><span>{error}</span></div>}

          <div className="tabs">
            <button className={`tab-btn ${tab==='demo'?'active':''}`} onClick={()=>setTab('demo')}>⚡ Quick Demo</button>
            <button className={`tab-btn ${tab==='text'?'active':''}`} onClick={()=>setTab('text')}>📝 Paste Text</button>
            <button className={`tab-btn ${tab==='file'?'active':''}`} onClick={()=>setTab('file')}>📄 Upload PDF</button>
          </div>

          {tab === 'demo' && (
            <div style={{display:'flex',flexDirection:'column',gap:10}}>
              {DEMOS.map(d => (
                <button
                  key={d.id}
                  onClick={() => runDemo(d.id)}
                  style={{
                    display:'flex', alignItems:'center', justifyContent:'space-between',
                    padding:'16px 20px', background:'var(--slate-50)',
                    border:`1.5px solid var(--slate-200)`, borderRadius:'var(--radius-md)',
                    cursor:'pointer', transition:'all 0.15s', textAlign:'left',
                    ...(activeDemo===d.id ? {borderColor:'var(--blue)',background:'var(--blue-light)'} : {})
                  }}
                  onMouseEnter={e=>{e.currentTarget.style.borderColor='var(--blue)';e.currentTarget.style.background='var(--blue-light)'}}
                  onMouseLeave={e=>{if(activeDemo!==d.id){e.currentTarget.style.borderColor='var(--slate-200)';e.currentTarget.style.background='var(--slate-50)'}}}
                >
                  <div style={{display:'flex',alignItems:'center',gap:14}}>
                    <div style={{width:40,height:40,borderRadius:10,background:d.color+'18',display:'flex',alignItems:'center',justifyContent:'center',fontSize:18,flexShrink:0}}>
                      {DEMO_ICONS[d.id]}
                    </div>
                    <div>
                      <div style={{fontSize:15,fontWeight:600,color:'var(--slate-900)',marginBottom:2}}>{d.label}</div>
                      <div style={{fontSize:13,color:'var(--slate-500)'}}>{d.desc}</div>
                    </div>
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10,flexShrink:0}}>
                    <span style={{fontSize:11,fontWeight:700,padding:'3px 9px',borderRadius:20,background:d.color+'18',color:d.color,border:`1px solid ${d.color}30`}}>{d.tag}</span>
                    <span style={{fontSize:13,fontWeight:700,color:d.color}}>{d.savings}</span>
                    <span style={{color:'var(--slate-300)',fontSize:18}}>→</span>
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
                onChange={e=>setText(e.target.value)}
              />
              <div style={{marginTop:10,display:'flex',flexWrap:'wrap',gap:8}}>
                {DEMOS.map(d => (
                  <button key={d.id} className="demo-link" onClick={()=>setText(DEMO_TEXTS[d.id])}>
                    {DEMO_ICONS[d.id]} {d.label}
                  </button>
                ))}
              </div>
              <button className="submit-btn" onClick={handleSubmit} disabled={!text.trim()}>
                Analyze My Customs Entry
              </button>
            </>
          )}

          {tab === 'file' && (
            <>
              <div
                className={`drop-zone ${dragging?'dragging':''}`}
                onDragOver={e=>{e.preventDefault();setDragging(true)}}
                onDragLeave={()=>setDragging(false)}
                onDrop={onDrop}
                onClick={()=>fileRef.current.click()}
              >
                <div className="drop-icon">{file?'✅':'📄'}</div>
                <div className="drop-title">{file?file.name:'Drag and drop your invoice PDF here'}</div>
                <div className="drop-sub">{file?'Click to change file':'or click to browse — PDF or TXT accepted'}</div>
                <input ref={fileRef} type="file" accept=".pdf,.txt" onChange={e=>setFile(e.target.files[0])} />
              </div>
              <div style={{marginTop:12,background:'var(--blue-light)',borderRadius:'var(--radius-md)',padding:'12px 16px',fontSize:13,color:'var(--blue)',border:'1px solid var(--blue-mid)'}}>
                📎 Use the sample PDFs: demo1_mexico_furniture.pdf through demo5_india_pharma.pdf from the demo/ folder.
              </div>
              <button className="submit-btn" onClick={handleSubmit} disabled={!file}>
                Analyze Uploaded Invoice
              </button>
            </>
          )}
        </div>
      </section>

      <section className="how-section">
        <div className="section-label">How it works</div>
        <h2 className="section-title">Three steps to reclaim your duties</h2>
        <div className="steps-grid">
          {[
            {num:'01',icon:'📄',title:'Upload Invoice',desc:'Paste your commercial invoice or upload a PDF. Include HTS codes, product descriptions, declared values, and country of origin.'},
            {num:'02',icon:'🔍',title:'AI Analysis',desc:'Our AI compares every HTS code against the official USITC tariff schedule and finds misclassification opportunities automatically.'},
            {num:'03',icon:'⚖️',title:'Claim Your Refund',desc:'Receive a ready-to-file CBP protest letter citing 19 U.S.C. 1514. Under US law, you have 180 days from liquidation to file.'},
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
          <div className="trust-item">⚖ 19 U.S.C. 1514 Compliant</div>
          <div className="trust-item">🌎 USMCA and KORUS FTA Checks</div>
          <div className="trust-item">🏛 CBP Form 19 Ready</div>
        </div>
        <div className="trust-disclaimer">
          TariffCheck provides analysis assistance only. Consult a licensed customs broker before filing formal protests with CBP.
        </div>
      </div>
    </div>
  )
}

