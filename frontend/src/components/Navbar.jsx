import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Audit' },
  { to: '/calculator', label: 'Landed Cost' },
  { to: '/hts-lookup', label: 'HTS Lookup' },
  { to: '/batch', label: 'Batch Audit' },
  { to: '/savings', label: 'My Audits' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/brokers', label: 'For Brokers' },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    let raf = 0
    const onScroll = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => setScrolled(window.scrollY > 8))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(raf) }
  }, [])

  const closeMenu = () => { if (menuRef.current) menuRef.current.open = false }

  return (
    <nav className={`navbar no-print ${scrolled ? 'scrolled' : ''}`}>
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
        <a href="/#analyze" className="nav-cta-primary">Start free audit</a>
      </div>

      <details className="nav-mobile" ref={menuRef}>
        <summary aria-label="Open navigation menu">
          <span className="nav-burger" aria-hidden="true" />
        </summary>
        <div className="nav-mobile-panel">
          {LINKS.map(l => (
            <Link key={l.to} to={l.to} onClick={closeMenu}>{l.label}</Link>
          ))}
          <a href="/#analyze" onClick={closeMenu} className="nav-mobile-cta">Start free audit</a>
        </div>
      </details>
    </nav>
  )
}
