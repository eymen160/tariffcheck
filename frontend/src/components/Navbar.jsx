import { Link } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Audit' },
  { to: '/calculator', label: 'Landed Cost' },
  { to: '/hts-lookup', label: 'HTS Lookup' },
  { to: '/batch', label: 'Batch Audit' },
  { to: '/savings', label: 'My Audits' },
  { to: '/pricing', label: 'Pricing' },
]

export default function Navbar() {
  return (
    <nav className="navbar no-print">
      <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
        <div className="logo-icon" aria-hidden="true">TC</div>
        <div className="logo-text-wrap">
          <div className="logo-name">
            <span className="logo-tariff">Tariff</span>
            <span className="logo-check">Check</span>
          </div>
          <span className="logo-tagline">Customs duty audit</span>
        </div>
      </Link>
      <div className="nav-links">
        {LINKS.map(l => (
          <Link key={l.to} to={l.to} className="nav-link">{l.label}</Link>
        ))}
        <Link to="/brokers" className="nav-link-cta">For Brokers</Link>
      </div>
    </nav>
  )
}
