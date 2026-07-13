import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { usePageMeta } from '../lib/usePageMeta'

export default function AboutPage() {
  usePageMeta({
    title: 'About',
    description:
      'TariffCheck was built at Hacklanta 2026 by three founders on one principle: findings must be verifiable, and the auditor must never be the filer.',
    path: '/about',
  })
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main className="legal-page">
        <h1>About TariffCheck</h1>
        <div className="legal-updated">Atlanta, GA · founded 2026</div>

        <section>
          <h2><span className="legal-num">01</span>Why we exist</h2>
          <p>
            US importers systematically overpay customs duties — $509.7B of 2024 imports entered with no
            USMCA claim, and only ~3,750 filers produce all ~45,000 CBP protests a year while roughly
            330,000 importers let the window close. The recovery industry that exists serves Fortune-500
            drawback programs on contingency; the long tail gets nothing. TariffCheck exists to make a
            verified duty audit — and the filing-ready remedy package that follows it — something any
            importer can run in minutes.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">02</span>Two principles</h2>
          <p>
            <strong>Findings must be verifiable.</strong> Every AI finding is re-verified by
            deterministic code against the complete official USITC HTS 2026 schedule, and our accuracy
            claims are published with the dataset to reproduce them — see the{' '}
            <Link to="/methodology">methodology page</Link>.
          </p>
          <p>
            <strong>The auditor must never be the filer.</strong> TariffCheck does not file with CBP and
            never will while brokers are our channel. We prepare; the importer of record or their
            licensed customs broker files. That structural neutrality is why an importer can trust our
            findings about any broker's entries — and why brokers can hand us to their clients without
            arming a competitor.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">03</span>The team</h2>
          <p>
            TariffCheck was built by <strong>Eymen Keyvan</strong> (backend &amp; full-stack) and{' '}
            <strong>Esat Sarac</strong> (frontend) — two engineers who started it at Hacklanta 2026 and kept
            going when the first real invoices showed real money. We grew up around import businesses;
            the first users were the cabinet, stone and home-goods importers in our own community, which
            keeps the product honest: these are businesses that check the math.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">04</span>Talk to us</h2>
          <p>
            Founders read everything: <a href="mailto:hello@tariffcheck.app">hello@tariffcheck.app</a>.
            Brokerages interested in the pilot program should start at{' '}
            <Link to="/brokers">For Brokers</Link>.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
