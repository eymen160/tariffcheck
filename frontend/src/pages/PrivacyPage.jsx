import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { usePageMeta } from '../lib/usePageMeta'

export default function PrivacyPage() {
  usePageMeta({
    title: 'Privacy',
    description:
      'What TariffCheck processes, what it never stores, and who touches your data. Short, because there is not much to disclose.',
    path: '/privacy',
  })
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <Navbar />
      <main className="legal-page">
        <h1>Privacy Policy</h1>
        <div className="legal-updated">Last updated: July 13, 2026</div>

        <section>
          <h2><span className="legal-num">01</span>What we process</h2>
          <p>
            Invoice and entry-line content you submit for auditing (processed in memory, never stored
            server-side); an email address and optional firm details if you submit a contact form; and
            standard server logs (timestamps, status codes, request sizes — never invoice content).
          </p>
        </section>

        <section>
          <h2><span className="legal-num">02</span>What we do not do</h2>
          <p>
            We do not store your documents. We do not sell or share data with advertisers or data
            brokers. We do not run third-party ad trackers. We do not use your data to train AI models,
            and Anthropic's commercial API — the only AI subprocessor — does not train on API inputs or
            outputs by default.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">03</span>Where your audit history lives</h2>
          <p>
            In your browser. The "My Audits" page reads from your device's localStorage; nothing is
            synced to our servers. Clearing your browser storage deletes it permanently — we could not
            recover it if we wanted to.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">04</span>Contact-form data</h2>
          <p>
            When you request access, your email and the details you provide are forwarded to the
            founders' inbox so we can respond. We use them to talk to you about TariffCheck and for
            nothing else. Ask us to delete them at any time.
          </p>
        </section>

        <section>
          <h2><span className="legal-num">05</span>Subprocessors and questions</h2>
          <p>
            Vercel (hosting) and Anthropic (AI analysis on the single-invoice path only). Questions or
            deletion requests: <a href="mailto:hello@tariffcheck.app">hello@tariffcheck.app</a>.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
