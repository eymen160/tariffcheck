import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { usePageMeta } from '../lib/usePageMeta'

export default function SecurityPage() {
  usePageMeta({
    title: 'Security & Data Handling',
    description:
      'TariffCheck is stateless by design: invoices are processed in memory and never stored. Data flow, subprocessors, and security posture, in plain language.',
    path: '/security',
  })
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main className="legal-page">
        <h1>Security &amp; Data Handling</h1>
        <div className="legal-updated">Last updated: July 13, 2026</div>

        <section>
          <h2><span className="legal-num">01</span>Stateless by design</h2>
          <p>
            TariffCheck has no database of your documents. An uploaded invoice is processed in memory,
            audited, verified, returned — and gone. Nothing you upload is written to disk on our side,
            and invoice content is deliberately excluded from server logs. Your audit history lives in
            your own browser (localStorage), where you can clear it at any time.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">02</span>The data flow, end to end</h2>
          <p>
            <strong>AI audit path</strong> (single-invoice analysis): your invoice text is sent from your
            browser to our serverless function on Vercel, forwarded once to Anthropic's Claude API for
            analysis, deterministically re-verified in-process, and returned. Anthropic's commercial API
            does not use API inputs or outputs to train models by default, with a standard 30-day
            retention window (zero-data-retention available on request).
          </p>
          <p>
            <strong>Deterministic batch path</strong> (the broker feature): entry lines are screened
            entirely in-process against the USITC schedule that ships inside the product.{' '}
            <strong>This path makes zero AI calls — client entry data never touches a language model.</strong>
          </p>
        </section>

        <section>
          <h2><span className="legal-num">03</span>Subprocessors</h2>
          <p>
            Vercel, Inc. (hosting and serverless compute, USA) and Anthropic, PBC (AI analysis on the
            single-invoice path only, USA). That is the complete list. No analytics pixels, no ad
            trackers, no data brokers.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">04</span>Application security</h2>
          <p>
            All traffic is TLS-encrypted with HSTS. The site ships a Content-Security-Policy,
            X-Content-Type-Options, X-Frame-Options and Referrer-Policy headers. Uploads are capped and
            validated; PDF parsing is sandboxed to text extraction; API error responses never echo
            document content. Exported CSV reports neutralize spreadsheet formula injection. The
            verification layer is covered by an automated test suite that runs on every change.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">05</span>Where we are honest about maturity</h2>
          <p>
            We are an early-stage company. We do not yet hold a SOC 2 attestation; the stateless
            architecture above is our compensating posture, and a formal compliance program is planned
            as broker pilots scale. If your security review needs specifics — data-flow diagrams,
            subprocessor terms, a signed DPA — email us and a founder will answer directly.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
