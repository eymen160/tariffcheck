import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="site-footer no-print">
      <div className="site-footer-inner">
        <div className="site-footer-links">
          <Link to="/cape-refund">CAPE Refunds</Link>
          <Link to="/brokers">For Brokers</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/hts-lookup">HTS Lookup</Link>
          <Link to="/batch">Batch Audit</Link>
          <Link to="/calculator">Landed Cost</Link>
        </div>
        <div className="site-footer-legal">
          TariffCheck prepares filings; it does not file with CBP. Not a licensed customs broker.
          Findings should be reviewed by the importer of record or a licensed customs broker before filing.
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
