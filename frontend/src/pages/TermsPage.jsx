import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default function TermsPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main className="legal-page">
        <h1>Terms of Service</h1>
        <div className="legal-updated">Last updated: July 2, 2026</div>

        <section>
          <h2><span className="legal-num">01</span>What TariffCheck is</h2>
          <p>
            TariffCheck is a software tool that audits import documentation — commercial invoices and
            entry lines — against the official Harmonized Tariff Schedule of the United States published
            by the U.S. International Trade Commission (USITC). It identifies possible misclassifications,
            unclaimed trade-preference programs, and Section 301 exposure, computes the associated duty
            difference, and generates draft protest documents under 19 U.S.C. §1514.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">02</span>What TariffCheck is not</h2>
          <p>
            TariffCheck is not a licensed customs broker and is not a law firm. It does not file entries,
            protests, or any other document with U.S. Customs and Border Protection, and nothing it
            produces is legal or customs advice. Draft protest packages are prepared for review: only the
            importer of record or a licensed customs broker may decide whether and how to file them.
            You are responsible for having every finding reviewed by a qualified professional before
            relying on it.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">03</span>Accuracy and verification</h2>
          <p>
            Duty rates are sourced from the official USITC HTS 2026 schedule (29,755 codes), loaded
            in-product. Every AI-generated finding is deterministically re-verified against that schedule,
            and savings figures are recomputed server-side before they appear in a report. Even so,
            classification is fact-specific: rates change, Section 301 figures are chapter-level estimates
            unless otherwise noted, and the correct code for your goods depends on details an invoice may
            not capture. Findings are a starting point for professional review, not a guarantee of recovery.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">04</span>Sample scenarios</h2>
          <p>
            Scenarios labeled "Sample" use fictional invoices created to demonstrate the product. The
            companies, invoice numbers, and dollar amounts in them do not describe real transactions or
            real customers.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">05</span>Your data</h2>
          <p>
            The service is stateless. Invoices you submit are processed in memory to produce your audit and
            are not stored in a database on our servers. Your audit history is kept in your own browser's
            local storage, on your device, and you can clear it at any time. Invoice text is sent to our AI
            provider (Anthropic) solely to perform the analysis you requested.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">06</span>Acceptable use</h2>
          <ul>
            <li>Submit only documents you have the right to share.</li>
            <li>Do not attempt to probe, overload, or disrupt the service; rate limits apply.</li>
            <li>Do not resell or white-label the service without a written agreement.</li>
          </ul>
        </section>

        <section>
          <h2><span className="legal-num">07</span>Fees</h2>
          <p>
            Current plans and pricing are listed on the <a href="/pricing">Pricing</a> page. Free-tier
            usage is provided as-is and may be rate-limited.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">08</span>Limitation of liability</h2>
          <p>
            The service is provided "as is" without warranties of any kind. To the maximum extent permitted
            by law, TariffCheck is not liable for duties, penalties, missed deadlines, or other losses
            arising from use of the service or reliance on its output. Statutory deadlines — including the
            180-day protest window under 19 U.S.C. §1514 — are your responsibility to track and meet.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">09</span>Changes</h2>
          <p>
            We may update these terms as the product evolves; the date above reflects the latest revision.
            Continued use after a change means you accept the updated terms.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
