import { useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LeadForm from '../components/LeadForm'
import { hs2028CheckBatch } from '../lib/api'
import { usePageMeta } from '../lib/usePageMeta'

const STATUS_STYLE = {
  unchanged: { color: 'var(--green)', label: 'Unchanged' },
  renumbered: { color: 'var(--amber)', label: 'Renumbered' },
  split: { color: 'var(--red, #c0392b)', label: 'Splits — review' },
  invalid: { color: 'var(--slate-400)', label: 'Invalid code' },
}

export default function Hs2028Page() {
  usePageMeta({
    title: 'HS 2028 Code Checker — Will Your HTS Codes Survive?',
    description: 'Free check against the official WCO HS2022→HS2028 correlation tables: which of your HTS codes get renumbered or split on January 1, 2028.',
    path: '/hs2028',
  })
  const [input, setInput] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function runCheck() {
    const codes = input.split(/[\s,;]+/).map(s => s.trim()).filter(Boolean).slice(0, 500)
    if (!codes.length) { setError('Paste at least one HTS code.'); return }
    setError('')
    setBusy(true)
    setData(null)
    try {
      setData(await hs2028CheckBatch(codes))
    } catch (err) {
      setError(err.message || 'The check failed. Please retry.')
    } finally {
      setBusy(false)
    }
  }

  const s = data?.summary

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div style={{ maxWidth: 820, margin: '0 auto', padding: '48px 24px', width: '100%', flex: 1 }}>

        <h1 style={{ fontSize: 32, color: 'var(--ink)', marginBottom: 12 }}>
          Will your HTS codes survive HS 2028?
        </h1>
        <p style={{ fontSize: 16, color: 'var(--slate-600)', marginBottom: 8, lineHeight: 1.7 }}>
          On <strong>January 1, 2028</strong> the World Customs Organization renumbers the Harmonized System:
          hundreds of subheadings are transferred or split. A code that is correct today files wrong entries in 2028 —
          and one-to-many splits are exactly where blind crosswalks misclassify.
        </p>
        <p style={{ fontSize: 13, color: 'var(--slate-500)', marginBottom: 28, lineHeight: 1.6 }}>
          Checked against the official WCO HS2022→HS2028 correlation tables (April 2026, incl. the July 2026 corrigendum),
          at the international 6-digit level. US 10-digit lines arrive with the USITC 2028 schedule in late 2027 —
          a “renumbered” verdict here means your 10-digit code will change.
        </p>

        <div className="card" style={{ marginBottom: 24 }}>
          <textarea
            className="invoice-textarea"
            style={{ minHeight: 110, fontFamily: 'var(--font-mono)', fontSize: 13 }}
            placeholder={'Paste HTS codes — one per line or comma-separated, e.g.\n0306.15.0000\n8471.30.0100\n9403.40.9060'}
            value={input}
            onChange={e => setInput(e.target.value)}
          />
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 12 }}>
            <button className="btn-primary" onClick={runCheck} disabled={busy}>
              {busy ? 'Checking…' : 'Check my codes — free'}
            </button>
            <span style={{ fontSize: 12.5, color: 'var(--slate-500)' }}>Up to 500 codes. No signup.</span>
          </div>
          {error && <div style={{ color: 'var(--red, #c0392b)', fontSize: 13.5, marginTop: 10 }}>{error}</div>}
        </div>

        {data && s && (
          <>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 14 }}>
              {s.codes} code{s.codes !== 1 ? 's' : ''} checked —{' '}
              <span style={{ color: s.action_needed ? 'var(--amber)' : 'var(--green)' }}>
                {s.action_needed ? `${s.action_needed} need action before 2028` : 'no 6-digit changes found'}
              </span>
            </div>

            <div className="summary-table-wrap" style={{ overflowX: 'auto', marginBottom: 24 }}>
              <table className="summary-table" style={{ width: '100%', fontSize: 13 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Your code</th>
                    <th style={{ textAlign: 'left' }}>HS 2028 status</th>
                    <th style={{ textAlign: 'left' }}>Where it goes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((r, i) => {
                    const st = STATUS_STYLE[r.status] || STATUS_STYLE.invalid
                    return (
                      <tr key={i}>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{r.code}</td>
                        <td style={{ color: st.color, fontWeight: 600 }}>{st.label}</td>
                        <td style={{ color: 'var(--slate-600)', lineHeight: 1.5 }}>
                          {r.targets
                            ? r.targets.map((t, j) => (
                                <div key={j}>
                                  <span style={{ fontFamily: 'var(--font-mono)' }}>{t.code}</span>
                                  {t.partial ? ' (part)' : ''}{t.note ? ` — ${t.note}` : ''}
                                </div>
                              ))
                            : r.status === 'unchanged' ? 'No 6-digit transfer' : r.message}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {s.action_needed > 0 && (
              <div className="card" style={{ border: '2px solid var(--ledger)', marginBottom: 24 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 6 }}>
                  {s.split > 0
                    ? `${s.split} of your codes split into multiple 2028 subheadings.`
                    : 'Your renumbered codes need a migration plan.'}
                </div>
                <p style={{ fontSize: 13.5, color: 'var(--slate-600)', lineHeight: 1.7, marginBottom: 14 }}>
                  Splits can’t be crosswalked automatically — classification depends on what the product actually is.
                  Leave an email and we’ll send the full per-code migration worksheet, and re-check your list against
                  the USITC 2028 schedule the day it publishes.
                </p>
                <div style={{ maxWidth: 380 }}>
                  <LeadForm source="hs2028_checker" buttonLabel="Send my migration worksheet" />
                </div>
              </div>
            )}
          </>
        )}

        <div style={{ fontSize: 13, color: 'var(--slate-500)', lineHeight: 1.7 }}>
          While you’re here: HS 2028 is tomorrow’s problem — <Link to="/" style={{ color: 'var(--ledger)' }}>misclassified
          entries are costing you duty today</Link>. Audit an invoice free, or <Link to="/batch" style={{ color: 'var(--ledger)' }}>screen
          a whole portfolio</Link> (7501 PDF or ACE ES-003 CSV in).
        </div>
      </div>
      <Footer />
    </div>
  )
}
