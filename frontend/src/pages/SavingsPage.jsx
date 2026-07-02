import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { analyzeInvoice, fetchDemo, ApiError } from '../lib/api'
import {
  listAudits, deleteAudit, saveAudit, newAuditId, buildAuditSummary,
  setLastResult, auditDeadline, daysUntil,
} from '../lib/audits'
import { money, date } from '../lib/format'
import { usePageTitle } from '../lib/usePageTitle'

function DeadlineChip({ deadlineTs }) {
  const days = daysUntil(deadlineTs)
  const cls = days < 30 ? 'red' : days < 60 ? 'amber' : ''
  const label = days <= 0 ? 'Window likely closed' : `${days} day${days !== 1 ? 's' : ''} left`
  return (
    <span className={`summary-chip ${cls}`} title={`180-day protest window measured from the audit date — confirm against your liquidation date. Deadline: ${date(deadlineTs)}`}>
      {label} · {date(deadlineTs)}
    </span>
  )
}

export default function SavingsPage() {
  const navigate = useNavigate()
  const [audits, setAudits] = useState(() => listAudits())
  const [loadingSample, setLoadingSample] = useState(false)
  const [error, setError] = useState('')

  usePageTitle('My Audits')

  const totalFound = audits.reduce((sum, a) => sum + (Number(a.summary?.totalSavings) || 0), 0)
  const nearestDeadline = audits.length > 0 ? Math.min(...audits.map(a => auditDeadline(a))) : null

  function viewAudit(audit) {
    setLastResult(audit.fullResponse)
    navigate('/results')
  }

  function removeAudit(id) {
    deleteAudit(id)
    setAudits(listAudits())
  }

  async function loadSample() {
    setLoadingSample(true)
    setError('')
    try {
      let data
      try {
        data = await analyzeInvoice({ demoId: 1 })
      } catch (err) {
        if (err instanceof ApiError && (err.status === 404 || err.status === 400 || err.status === 405)) {
          data = await fetchDemo(1)
        } else {
          throw err
        }
      }
      data.meta = { ...(data.meta || {}), demo: true }
      saveAudit({
        id: newAuditId(),
        ts: Date.now(),
        sourceName: 'Sample: Office Furniture — Mexico',
        summary: buildAuditSummary(data),
        fullResponse: data,
      })
      setAudits(listAudits())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not load the sample audit. Please try again.')
    } finally {
      setLoadingSample(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px 64px', width: '100%', flex: 1 }}>
        <h1 style={{ fontSize: 30, letterSpacing: '-0.75px', color: 'var(--slate-900)', marginBottom: 6 }}>My Audits</h1>
        <p style={{ fontSize: 15, color: 'var(--slate-500)', marginBottom: 28 }}>
          Your audit history lives in this browser — nothing is stored on our servers.
        </p>

        {/* Stat row */}
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 28 }}>
          <div className="stat-card">
            <div className="stat-card-label">Total found</div>
            <div className="stat-card-value" style={{ color: 'var(--green)' }}>{money(totalFound)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Audits run</div>
            <div className="stat-card-value">{audits.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Nearest protest deadline</div>
            <div className="stat-card-value" style={{ fontSize: 20 }}>
              {nearestDeadline ? date(nearestDeadline) : '—'}
            </div>
          </div>
        </div>

        {error && <div className="inline-error"><span>⚠</span><span>{error}</span></div>}

        {audits.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '56px 32px' }}>
            <div style={{ fontFamily: 'var(--font-serif)', color: 'var(--slate-300)', fontSize: 44, marginBottom: 14 }}>§</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--slate-900)', marginBottom: 8 }}>Run your first audit</div>
            <div style={{ fontSize: 14, color: 'var(--slate-500)', marginBottom: 24, maxWidth: 420, margin: '0 auto 24px' }}>
              Audit an invoice and your verified savings, findings, and protest deadlines will show up here.
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/" className="btn-primary">Run your first audit</Link>
              <button className="btn-secondary" onClick={loadSample} disabled={loadingSample}>
                {loadingSample ? 'Loading…' : 'Load sample audit'}
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {audits.map(a => (
              <div key={a.id} className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 220 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                    <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--slate-900)' }}>{a.sourceName || 'Invoice audit'}</span>
                    {a.summary?.demo && <span className="badge-sample" style={{ fontSize: 9, padding: '2px 8px' }}>Sample data</span>}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--slate-500)' }}>
                    {date(a.ts)} · {a.summary?.findingsCount ?? 0} finding{(a.summary?.findingsCount ?? 0) !== 1 ? 's' : ''}
                    {a.summary?.totalCount > 0 && ` · ${a.summary.verifiedCount} of ${a.summary.totalCount} verified`}
                  </div>
                </div>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--green)', whiteSpace: 'nowrap' }}>
                  {money(a.summary?.totalSavings || 0)}
                </div>
                <DeadlineChip deadlineTs={auditDeadline(a)} />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: 13 }} onClick={() => viewAudit(a)}>View</button>
                  <button
                    className="btn-secondary"
                    style={{ padding: '8px 14px', fontSize: 13, color: 'var(--red)', borderColor: '#E5C0BA' }}
                    onClick={() => removeAudit(a.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Footer />
    </div>
  )
}
