import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LeadForm from '../components/LeadForm'
import { usePageTitle } from '../lib/usePageTitle'

export default function CapePage() {
  usePageTitle('CAPE / IEEPA Refunds')
  const navigate = useNavigate()

  return (
    <div style={{minHeight:'100vh', background:'var(--paper)', display:'flex', flexDirection:'column'}}>
      <Navbar />
      <div style={{maxWidth:780, margin:'0 auto', padding:'48px 24px', width:'100%', flex:1}}>

        <div style={{background:'var(--amber-light)', border:'1px solid var(--amber)', borderRadius:'var(--radius-sm)', padding:'16px 20px', marginBottom:32}}>
          <strong style={{color:'var(--amber)'}}>Important:</strong> <span style={{color:'var(--amber)'}}>IEEPA refunds are processed by CBP — TariffCheck does not process these refunds. We help you find separate HTS misclassification savings.</span>
        </div>

        <h1 style={{fontSize:32, color:'var(--ink)', marginBottom:12}}>
          IEEPA Tariff Refunds: ~$165B Ordered Refunded
        </h1>
        <p style={{fontSize:16, color:'var(--slate-600)', marginBottom:32}}>
          The US Supreme Court struck down the IEEPA-based tariffs in February 2026. CBP is now processing refunds through the CAPE system.
        </p>

        <div className="card" style={{marginBottom:24}}>
          <h2 style={{fontSize:20, marginBottom:16}}>What happened?</h2>
          <p style={{color:'var(--slate-600)', lineHeight:1.7, marginBottom:16}}>
            In a 6-3 decision (February 20, 2026), the Supreme Court ruled that the broad tariffs imposed under the International Emergency Economic Powers Act (IEEPA) exceeded presidential authority. CBP launched the CAPE (Consolidated Administration and Processing of Entries) system in ACE to process refund claims. As of late June 2026, CBP had authorized roughly $104B in refunds and paid about $71B.
          </p>
          <div style={{display:'flex', flexDirection:'column', gap:10}}>
            {[
              {phase:'Phase 1', date:'Apr 20, 2026', text:'Live — unliquidated entries, plus entries liquidated within 80 days of submission (~63% of affected entries).'},
              {phase:'Phase 2', date:'Jun 29, 2026', text:'Live — adds reconciliation-flagged entries.'},
              {phase:'Phase 3', date:'late Jul 2026', text:'Expected — finally liquidated entries, only for importers who filed at the Court of International Trade.'},
            ].map(p => (
              <div key={p.phase} style={{display:'flex', gap:12, alignItems:'baseline'}}>
                <span style={{fontFamily:'var(--font-mono)', fontSize:11, fontWeight:600, letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--ledger)', whiteSpace:'nowrap', flexShrink:0}}>{p.phase} · {p.date}</span>
                <span style={{color:'var(--slate-600)', fontSize:13.5, lineHeight:1.6}}>{p.text}</span>
              </div>
            ))}
          </div>
          <p style={{color:'var(--slate-500)', fontSize:12.5, lineHeight:1.6, marginTop:14, marginBottom:0}}>
            Note: the government appealed the refund order in June 2026, so mechanics may still shift — another reason not to sit on eligible claims. Separately, the replacement 10% global tariff under Section 122 expires by statute on July 24, 2026.
          </p>
        </div>

        <div className="card" style={{marginBottom:24}}>
          <h2 style={{fontSize:20, marginBottom:16}}>How to claim your IEEPA refund</h2>
          {[
            {step:'01', text:'Log into your ACE Portal account at cbp.gov'},
            {step:'02', text:'Navigate to the new CAPE tab in your Importer sub-account'},
            {step:'03', text:'Download the CAPE Declaration CSV template'},
            {step:'04', text:'Enter your entry numbers (up to 9,999 per CSV file)'},
            {step:'05', text:'Upload the CSV — CBP will validate and process'},
            {step:'06', text:'Expect refunds within 60-90 days after acceptance'},
          ].map(item => (
            <div key={item.step} style={{display:'flex', gap:16, marginBottom:12, alignItems:'baseline'}}>
              <span style={{fontFamily:'var(--font-mono)', fontSize:11, fontWeight:500, letterSpacing:'0.14em', textTransform:'uppercase', color:'var(--slate-400)', whiteSpace:'nowrap', flexShrink:0}}>Step {item.step}</span>
              <span style={{color:'var(--slate-700)'}}>{item.text}</span>
            </div>
          ))}
          <a href="https://www.cbp.gov/trade/programs-administration/trade-remedies/ieepa-duty-refunds" target="_blank" rel="noopener noreferrer" className="btn-primary" style={{marginTop:16}}>
            Go to CBP CAPE Portal →
          </a>
        </div>

        <div className="card" style={{marginBottom:24}}>
          <h2 style={{fontSize:20, marginBottom:16}}>IEEPA vs HTS Misclassification: Key Difference</h2>
          <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(260px, 1fr))', gap:16}}>
            <div style={{background:'var(--green-light)', border:'1px solid var(--green-mid)', borderRadius:'var(--radius-sm)', padding:16}}>
              <div style={{fontWeight:600, color:'var(--ledger)', marginBottom:8}}>IEEPA Refunds (CAPE)</div>
              <ul style={{color:'var(--ledger-deep)', fontSize:13, paddingLeft:16, margin:0, lineHeight:1.7}}>
                <li>Refunds ordered following the Supreme Court ruling</li>
                <li>Filed through CBP ACE Portal</li>
                <li>Covers IEEPA duties paid Feb 2025 – Feb 2026</li>
                <li>60-90 day processing time</li>
                <li>Free to claim yourself</li>
              </ul>
            </div>
            <div style={{background:'var(--blue-light)', border:'1px solid var(--blue-mid)', borderRadius:'var(--radius-sm)', padding:16}}>
              <div style={{fontWeight:600, color:'var(--ledger-deep)', marginBottom:8}}>HTS Misclassification (TariffCheck)</div>
              <ul style={{color:'var(--ledger-deep)', fontSize:13, paddingLeft:16, margin:0, lineHeight:1.7}}>
                <li>Wrong HTS code used at entry</li>
                <li>Filed as CBP protest (Form 19)</li>
                <li>180-day window from liquidation</li>
                <li>Applies to any tariff type</li>
                <li>Can stack with IEEPA refund</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="card" style={{marginBottom:24, border:'2px solid var(--ledger)'}}>
          <h2 style={{fontSize:20, marginBottom:8}}>CAPE Readiness Check — $149 flat per claim batch</h2>
          <p style={{color:'var(--slate-600)', lineHeight:1.7, marginBottom:14}}>
            One malformed CSV row can bounce a whole declaration. Before you upload, we screen your entry list — IEEPA Chapter 99 lines, entry-date windows, phase eligibility, liquidation timing — and hand back a validated declaration checklist. You still file yourself, free, in ACE; brokers charge $500–$2,000 for the same review. Flat fee, no percentage of your refund.
          </p>
          <div style={{maxWidth:380}}>
            <LeadForm source="cape_readiness" buttonLabel="Check my batch" />
          </div>
        </div>

        <button onClick={() => navigate('/')} className="btn-primary">
          ← Analyze My Invoice for Misclassification Savings
        </button>
      </div>
      <Footer />
    </div>
  )
}
