import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { usePageTitle } from '../lib/usePageTitle'

export default function NotFoundPage() {
  usePageTitle('Page not found')
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div className="error-outer" style={{ flex: 1 }}>
        <div className="error-card">
          <div className="formlabel" style={{ color: 'var(--stamp)', marginBottom: 14 }}>Entry not found · 404</div>
          <div className="error-title">This page isn't in the schedule</div>
          <div className="error-sub">
            The address may have changed, or the link is out of date. The audit desk is still open.
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/" className="btn-primary">Run an audit</Link>
            <Link to="/hts-lookup" className="btn-secondary">Look up an HTS code</Link>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
