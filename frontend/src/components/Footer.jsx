import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="site-footer no-print">
      <div className="site-footer-inner">
        <div className="site-footer-brand">Tariff<span>Check</span></div>
        <div className="site-footer-links">
          <Link to="/brokers">For Brokers</Link>
          <Link to="/batch">Batch Audit</Link>
          <Link to="/calculator">Landed Cost</Link>
          <Link to="/hts-lookup">HTS Lookup</Link>
          <Link to="/cape-refund">CAPE Refunds</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/terms">Terms</Link>
        </div>
        <div className="site-footer-legal">
          TariffCheck prepares classification audits and draft protest packages; it does not file with CBP and is not
          a licensed customs broker. All findings should be reviewed by the importer of record or a licensed customs
          broker before filing. Nothing on this site is legal or customs advice.
        </div>
        <div className="site-footer-legal">
          Duty rates sourced from the official USITC Harmonized Tariff Schedule of the United States, 2026 edition
          (29,755 codes) —{' '}
          <a href="https://hts.usitc.gov" target="_blank" rel="noopener noreferrer">hts.usitc.gov</a>.
          Section 301 figures are chapter-level estimates.
        </div>
        <div className="site-footer-legal">© 2026 TariffCheck</div>
      </div>
    </footer>
  )
}
