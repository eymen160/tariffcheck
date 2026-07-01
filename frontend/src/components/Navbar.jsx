import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
        <div className="logo-icon">🛃</div>
        <div className="logo-text-wrap">
          <div className="logo-name">
            <span className="logo-tariff">Tariff</span>
            <span className="logo-check">Check</span>
          </div>
          <span className="logo-tagline">AI Customs Duty Auditor</span>
        </div>
      </Link>
      <div style={{display:'flex', gap:18, alignItems:'center'}}>
        <Link to="/" style={{color:'var(--slate-600)', textDecoration:'none', fontSize:14, fontWeight:500}}>Home</Link>
        <Link to="/hts-lookup" style={{color:'var(--slate-600)', textDecoration:'none', fontSize:14, fontWeight:500}}>🔍 HTS Lookup</Link>
        <Link to="/cape-refund" style={{color:'#92400e', textDecoration:'none', fontSize:14, fontWeight:600, background:'#fef3c7', padding:'6px 12px', borderRadius:6, border:'1px solid #fcd34d'}}>💡 IEEPA Refunds</Link>
      </div>
    </nav>
  )
}
