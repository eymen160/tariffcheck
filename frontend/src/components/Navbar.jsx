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
      <div className="nav-right">
        <a
          href="https://nexlayer.com"
          target="_blank"
          rel="noopener noreferrer"
          className="nav-badge green"
          style={{ textDecoration: 'none', cursor: 'pointer' }}
        >
          ⚡ Nexlayer All-In
        </a>
      </div>
    </nav>
  )
}
