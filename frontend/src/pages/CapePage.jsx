import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

export default function CapePage() {
  const navigate = useNavigate()

  return (
    <div style={{minHeight:'100vh', background:'var(--slate-50)'}}>
      <Navbar />
      <div style={{maxWidth:780, margin:'0 auto', padding:'48px 24px'}}>

        <div style={{background:'#fffbeb', border:'1px solid #fcd34d', borderRadius:12, padding:'16px 20px', marginBottom:32}}>
          <strong style={{color:'#92400e'}}>Important:</strong> <span style={{color:'#78350f'}}>IEEPA refunds are processed by CBP — TariffCheck does not process these refunds. We help you find separate HTS misclassification savings.</span>
        </div>

        <h1 style={{fontSize:32, fontWeight:800, color:'var(--slate-900)', marginBottom:12}}>
          IEEPA Tariff Refunds: $166B Being Returned
        </h1>
        <p style={{fontSize:16, color:'var(--slate-600)', marginBottom:32}}>
          The US Supreme Court struck down the IEEPA-based tariffs in February 2026. CBP is now processing refunds through the CAPE system.
        </p>

        <div style={{background:'white', border:'1px solid var(--slate-200)', borderRadius:12, padding:'24px', marginBottom:24}}>
          <h2 style={{fontSize:20, fontWeight:700, marginBottom:16}}>What happened?</h2>
          <p style={{color:'var(--slate-600)', lineHeight:1.7}}>
            The Supreme Court ruled 6-3 that President Trump's broad tariffs imposed under the International Emergency Economic Powers Act (IEEPA) exceeded presidential authority. CBP launched the CAPE (Consolidated Administration and Processing of Entries) system on April 20, 2026 to process refund claims. As of May 2026, $35.46 billion in refunds have been calculated.
          </p>
        </div>

        <div style={{background:'white', border:'1px solid var(--slate-200)', borderRadius:12, padding:'24px', marginBottom:24}}>
          <h2 style={{fontSize:20, fontWeight:700, marginBottom:16}}>How to claim your IEEPA refund</h2>
          {[
            {step:'1', text:'Log into your ACE Portal account at cbp.gov'},
            {step:'2', text:'Navigate to the new CAPE tab in your Importer sub-account'},
            {step:'3', text:'Download the CAPE Declaration CSV template'},
            {step:'4', text:'Enter your entry numbers (up to 9,999 per CSV file)'},
            {step:'5', text:'Upload the CSV — CBP will validate and process'},
            {step:'6', text:'Expect refunds within 60-90 days after acceptance'},
          ].map(item => (
            <div key={item.step} style={{display:'flex', gap:16, marginBottom:12, alignItems:'flex-start'}}>
              <div style={{minWidth:28, height:28, borderRadius:'50%', background:'var(--blue)', color:'white', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13, fontWeight:700}}>{item.step}</div>
              <span style={{color:'var(--slate-700)', paddingTop:4}}>{item.text}</span>
            </div>
          ))}
          <a href="https://www.cbp.gov/trade/programs-administration/trade-remedies/ieepa-duty-refunds" target="_blank" rel="noopener noreferrer" style={{display:'inline-block', marginTop:16, background:'var(--blue)', color:'white', padding:'10px 20px', borderRadius:8, fontWeight:600, textDecoration:'none'}}>
            Go to CBP CAPE Portal →
          </a>
        </div>

        <div style={{background:'white', border:'1px solid var(--slate-200)', borderRadius:12, padding:'24px', marginBottom:24}}>
          <h2 style={{fontSize:20, fontWeight:700, marginBottom:16}}>IEEPA vs HTS Misclassification: Key Difference</h2>
          <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(260px, 1fr))', gap:16}}>
            <div style={{background:'#f0fdf4', border:'1px solid #bbf7d0', borderRadius:8, padding:16}}>
              <div style={{fontWeight:700, color:'#166534', marginBottom:8}}>IEEPA Refunds (CAPE)</div>
              <ul style={{color:'#15803d', fontSize:13, paddingLeft:16, margin:0, lineHeight:1.7}}>
                <li>Supreme Court-ordered refunds</li>
                <li>Filed through CBP ACE Portal</li>
                <li>Covers tariffs from Jan 2026</li>
                <li>60-90 day processing time</li>
                <li>Free to claim yourself</li>
              </ul>
            </div>
            <div style={{background:'#eff6ff', border:'1px solid #bfdbfe', borderRadius:8, padding:16}}>
              <div style={{fontWeight:700, color:'#1e40af', marginBottom:8}}>HTS Misclassification (TariffCheck)</div>
              <ul style={{color:'#1d4ed8', fontSize:13, paddingLeft:16, margin:0, lineHeight:1.7}}>
                <li>Wrong HTS code used at entry</li>
                <li>Filed as CBP protest (Form 19)</li>
                <li>180-day window from liquidation</li>
                <li>Applies to any tariff type</li>
                <li>Can stack with IEEPA refund</li>
              </ul>
            </div>
          </div>
        </div>

        <button onClick={() => navigate('/')} style={{background:'var(--blue)', color:'white', border:'none', borderRadius:8, padding:'14px 28px', fontSize:15, fontWeight:700, cursor:'pointer'}}>
          ← Analyze My Invoice for Misclassification Savings
        </button>
      </div>
    </div>
  )
}
