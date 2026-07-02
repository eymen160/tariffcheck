import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { getLastResult } from '../lib/audits'
import { money, rate, date } from '../lib/format'

function ConfidenceBadge({ level }) {
  const styles = {
    high: { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7', label: '✓ High Confidence' },
    medium: { bg: '#fef3c7', color: '#92400e', border: '#fcd34d', label: '~ Medium Confidence' },
    low: { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5', label: '⚠ Low Confidence' },
  }
  const s = styles[level] || styles.medium
  return (
    <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 20, background: s.bg, color: s.color, border: `1px solid ${s.border}`, whiteSpace: 'nowrap' }}>
      {s.label}
    </span>
  )
}

function VerificationBadge({ finding }) {
  if (finding.verified === true) {
    return <span className="badge-verified">✓ Verified against USITC 2026</span>
  }
  if (finding.verified === false) {
    return (
      <span className="badge-unverified" title={finding.verification_note || 'This finding could not be verified against the official schedule — manual review recommended.'}>
        ⚠ Unverified — manual review
      </span>
    )
  }
  return null
}

function getHtsUrl(code) {
  if (!code) return null
  return `https://hts.usitc.gov/?query=${encodeURIComponent(String(code).split('.').slice(0, 2).join('.'))}`
}

function getCbpRulingUrl(code) {
  if (!code) return null
  const term = String(code).split('.').slice(0, 2).join('.')
  return `https://rulings.cbp.gov/search?term=${encodeURIComponent(term)}&type=ALL`
}

export default function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)
  const [openCards, setOpenCards] = useState({})

  // Rehydrate: router state first, then the sessionStorage copy (survives refresh).
  const data = location.state?.data || getLastResult()

  if (!data) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--slate-50)' }}>
        <Navbar />
        <div className="error-outer">
          <div className="error-card">
            <div className="error-icon" style={{ fontFamily: 'var(--font-serif)', color: 'var(--slate-300)', fontSize: 44 }}>§</div>
            <div className="error-title">No Analysis Loaded</div>
            <div className="error-sub">Run an invoice audit to see verified findings and a draft protest letter here.</div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/" className="btn-primary">Run an audit</Link>
              <Link to="/savings" className="btn-secondary">View past audits</Link>
            </div>
          </div>
        </div>
        <Footer />
      </div>
    )
  }

  const {
    findings = [],
    total_savings = 0,
    fta_eligible,
    fta_type,
    country_of_origin,
    protest_letter = '',
    verification = null,
    meta = null,
    protest_deadline_note = '',
  } = data

  const isDemo = Boolean(meta && meta.demo)
  const hasSavings = total_savings > 0
  const itemsWithSavings = findings.filter(f => f.savings > 0)
  const verifiedCount = verification ? verification.verified_count : findings.filter(f => f.verified === true).length
  const totalCount = verification ? verification.total_count : findings.length

  function copyLetter() {
    navigator.clipboard.writeText(protest_letter).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  function downloadLetter() {
    const blob = new Blob([protest_letter], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'cbp-protest-letter.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function saveReport() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tariffcheck_report.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function toggleCard(i) {
    setOpenCards(prev => ({ ...prev, [i]: !prev[i] }))
  }

  return (
    <div className="results-page">
      <div className="no-print">
      <Navbar />

      <div className="results-topbar">
        <button className="back-btn" onClick={() => navigate('/')}>
          ← New Analysis
        </button>
        <div className="results-heading">Duty Savings Analysis</div>
      </div>

      <div className="results-body">

        {/* Sticky verification summary bar */}
        <div className="summary-bar">
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--slate-400)' }}>
              Verified savings
            </span>
            <span style={{ fontSize: 26, fontWeight: 800, color: 'var(--green)', letterSpacing: '-1px', lineHeight: 1.15 }}>
              {money(total_savings)}
            </span>
          </div>
          <span className="summary-chip">{findings.length} finding{findings.length !== 1 ? 's' : ''}</span>
          {totalCount > 0 && (
            <span className="summary-chip blue">
              ✓ {verifiedCount} of {totalCount} findings verified against USITC HTS 2026
            </span>
          )}
          <span className="summary-chip amber">⏰ {protest_deadline_note || '180 days from liquidation to file a protest'}</span>
          {isDemo && <span className="badge-sample" style={{ marginLeft: 'auto' }}>Sample data</span>}
        </div>

        {/* Savings Banner */}
        <div className="savings-banner">
          <div className="savings-left">
            <div className="savings-label">Total Verified Duty Savings</div>
            <div className="savings-amount">{money(total_savings)}</div>
            <div className="savings-sub">
              {hasSavings
                ? `${itemsWithSavings.length} misclassified item${itemsWithSavings.length !== 1 ? 's' : ''} identified — savings recomputed against the official USITC schedule`
                : 'No verified overpayment detected in this invoice'}
            </div>
          </div>
          <div className="savings-right">
            {fta_eligible && fta_type && (
              <div className="fta-badge">✓ {fta_type} Free Trade Agreement</div>
            )}
            {country_of_origin && (
              <div className="fta-badge">Origin: {country_of_origin}</div>
            )}
            {hasSavings && (
              <div className="deadline-badge">180 days to file CBP protest</div>
            )}
          </div>
        </div>

        {/* Findings */}
        {findings.length > 0 && (
          <div style={{ marginBottom: 40 }}>
            <div className="section-header">
              <div className="section-heading">
                HTS Code Analysis
                <span className="count-badge">{findings.length} item{findings.length !== 1 ? 's' : ''} analyzed</span>
              </div>
              <a
                href="https://hts.usitc.gov"
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: 13, color: 'var(--blue)', fontWeight: 500, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 5 }}
              >
                Official USITC Schedule ↗
              </a>
            </div>

            <div className="findings-grid">
              {findings.map((f, i) => (
                <div className="finding-card" key={i}>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14, alignItems: 'center' }}>
                    <VerificationBadge finding={f} />
                    {f.confidence && <ConfidenceBadge level={f.confidence} />}
                  </div>

                  {f.verified === false && f.verification_note && (
                    <div style={{ background: 'var(--amber-light)', border: '1px solid #FDE68A', borderRadius: 8, padding: '9px 13px', marginBottom: 14, fontSize: 12.5, color: 'var(--amber)', lineHeight: 1.55 }}>
                      {f.verification_note}
                    </div>
                  )}

                  <div className="codes-row">
                    <div className="code-block">
                      <div className="code-label">Current Code</div>
                      <div className="code-value">{f.hts_code}</div>
                      <span className={`rate-badge ${f.current_rate > 0 ? 'bad' : 'neutral'}`}>
                        {rate(f.current_rate)}
                      </span>
                      <div>
                        <a className="code-link" href={getHtsUrl(f.hts_code)} target="_blank" rel="noopener noreferrer">USITC ↗</a>
                        <span style={{ color: 'var(--slate-300)', margin: '0 6px' }}>|</span>
                        <a className="code-link" href={getCbpRulingUrl(f.hts_code)} target="_blank" rel="noopener noreferrer">CBP Rulings ↗</a>
                      </div>
                    </div>

                    <div className="code-arrow">→</div>

                    <div className="code-block">
                      <div className="code-label">Suggested Code</div>
                      <div className="code-value">{f.suggested_code}</div>
                      <span className="rate-badge good">{rate(f.suggested_rate)}</span>
                      <div>
                        <a className="code-link" href={getHtsUrl(f.suggested_code)} target="_blank" rel="noopener noreferrer">USITC ↗</a>
                        <span style={{ color: 'var(--slate-300)', margin: '0 6px' }}>|</span>
                        <a className="code-link" href={getCbpRulingUrl(f.suggested_code)} target="_blank" rel="noopener noreferrer">CBP Rulings ↗</a>
                      </div>
                    </div>
                  </div>

                  <div className="finding-desc">{f.description}</div>

                  {f.section_301_rate > 0 && (
                    <div className="rate-breakdown">
                      <div className="rate-row"><span>Base MFN Rate:</span><span>{rate(f.current_rate)}</span></div>
                      <div className="rate-row"><span>+ Section 301 (China):</span><span>{rate(f.section_301_rate)}</span></div>
                      <div className="rate-row total"><span>= Total Effective Rate:</span><span>{rate(f.total_current_rate ?? (f.current_rate + f.section_301_rate))}</span></div>
                    </div>
                  )}

                  {f.classification_risk === true && (!f.savings || f.savings === 0) && (
                    <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 8, padding: '10px 14px', marginTop: 8, fontSize: 13, color: '#9a3412' }}>
                      ⚠️ <strong>Audit Risk:</strong> Current classification may be incorrect even though rate is the same. Incorrect codes trigger CBP flags on future shipments. Correct for future entries.
                    </div>
                  )}

                  {f.legal_basis && (
                    <div style={{ marginTop: 8, fontSize: 12, color: 'var(--slate-500)' }}>
                      <strong style={{ color: 'var(--slate-600)' }}>Legal basis:</strong> {f.legal_basis}
                    </div>
                  )}

                  {f.action_required && (
                    <div style={{ marginTop: 6, fontSize: 12, color: 'var(--slate-500)' }}>
                      <strong style={{ color: 'var(--slate-600)' }}>Action:</strong> {f.action_required}
                    </div>
                  )}

                  {f.explanation && (
                    <>
                      <button className="explanation-toggle" onClick={() => toggleCard(i)}>
                        <span>Why this classification matters</span>
                        <span>{openCards[i] ? '▲' : '▼'}</span>
                      </button>
                      {openCards[i] && (
                        <div className="explanation-text">{f.explanation}</div>
                      )}
                    </>
                  )}

                  {(f.savings > 0 || f.declared_value) && (
                    <div className="finding-savings">
                      <div>
                        <div className="savings-amount-small">
                          {f.savings > 0 ? (
                            <>
                              {f.model_claimed_savings != null && Math.abs(f.model_claimed_savings - f.savings) > 1 && (
                                <span style={{ textDecoration: 'line-through', color: 'var(--slate-400)', fontWeight: 500, fontSize: 14, marginRight: 8 }}>
                                  AI claimed {money(f.model_claimed_savings)}
                                </span>
                              )}
                              {f.model_claimed_savings != null && Math.abs(f.model_claimed_savings - f.savings) > 1
                                ? `→ verified ${money(f.savings)}`
                                : `${money(f.savings)} savings`}
                            </>
                          ) : 'No savings on this item'}
                        </div>
                        {f.declared_value > 0 && (
                          <div className="shipment-val">on {money(f.declared_value)} shipment value</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary table if multiple items */}
        {findings.length > 1 && (
          <div style={{ marginBottom: 40 }}>
            <div className="section-header" style={{ marginBottom: 16 }}>
              <div className="section-heading">Savings Summary</div>
            </div>
            <div className="summary-table-wrap">
              <table className="summary-table">
                <thead>
                  <tr>
                    {['Product', 'Current HTS', 'Rate', 'Suggested HTS', 'Rate', 'Verified', 'Savings'].map(h => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {findings.map((f, i) => (
                    <tr key={i}>
                      <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.description}</td>
                      <td><span className="mono">{f.hts_code}</span></td>
                      <td><span className={`rate-badge ${f.current_rate > 0 ? 'bad' : 'neutral'}`}>{rate(f.current_rate)}</span></td>
                      <td><span className="mono">{f.suggested_code}</span></td>
                      <td><span className="rate-badge good">{rate(f.suggested_rate)}</span></td>
                      <td>
                        {f.verified === true ? <span className="badge-verified">✓</span> : f.verified === false ? <span className="badge-unverified" title={f.verification_note || 'Manual review'}>⚠</span> : '—'}
                      </td>
                      <td style={{ fontWeight: 700, color: f.savings > 0 ? 'var(--green)' : 'var(--slate-400)' }}>
                        {f.savings > 0 ? money(f.savings) : 'None'}
                      </td>
                    </tr>
                  ))}
                  <tr className="total-row">
                    <td colSpan={6} style={{ textAlign: 'right', fontSize: 13 }}>Total verified savings</td>
                    <td style={{ color: 'var(--green)', fontSize: 17 }}>{money(total_savings)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Protest Letter */}
        {protest_letter && hasSavings && (
          <div className="letter-section">
            <div className="section-header" style={{ marginBottom: 16 }}>
              <div className="section-heading">
                CBP Protest Letter
                <span className="ready-badge">Draft — ready for review</span>
              </div>
            </div>
            <div style={{ background: '#fef3c7', border: '1px solid #fcd34d', color: '#92400e', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: 12, fontSize: 14, fontWeight: 600 }}>
              ⚠️ Protest deadline: 180 days from your liquidation date
            </div>
            <div className="letter-card">
              <div className="letter-card-header">
                <div style={{ fontSize: 14, color: 'var(--slate-600)', lineHeight: 1.5 }}>
                  <strong>Filing:</strong> CBP Form 19 or ACE Protest Module at cbp.gov — filed by the importer of record or a licensed customs broker
                </div>
                <div style={{ fontSize: 13, color: 'var(--slate-500)' }}>
                  Deadline: 180 days from liquidation per 19 U.S.C. 1514
                </div>
              </div>
              <div className="letter-info-bar">
                <span>§</span>
                <span>
                  This letter is based on 19 U.S.C. 1514(a)(2). US law gives importers 180 days from liquidation to file a protest with CBP. This deadline is uniform and does not vary by country of origin.
                </span>
              </div>
              <pre className="letter-body">{protest_letter}</pre>
              <div className="letter-actions">
                <button className={`action-btn ${copied ? 'success' : 'primary'}`} onClick={copyLetter}>
                  {copied ? '✓ Copied' : 'Copy letter'}
                </button>
                <button className="action-btn secondary" onClick={downloadLetter}>
                  Download .txt
                </button>
                <button className="action-btn secondary" onClick={() => window.print()}>
                  Print / save as PDF
                </button>
                <button className="action-btn secondary" onClick={saveReport}>
                  Save report (JSON)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* CAPE / IEEPA info card */}
        <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 12, padding: '20px 24px', marginTop: 8, marginBottom: 24 }}>
          <div style={{ fontWeight: 700, color: '#92400e', marginBottom: 8 }}>A separate track: IEEPA tariff refunds</div>
          <p style={{ fontSize: 13, color: '#78350f', margin: 0, lineHeight: 1.6 }}>
            If you paid tariffs imposed under IEEPA in 2025, CBP is refunding those separately through the CAPE system after the courts voided them. That refund track is independent of the HTS misclassification savings shown here.{' '}
            <a href="/cape-refund" style={{ color: '#92400e', fontWeight: 600 }}>Check your IEEPA eligibility →</a>
          </p>
        </div>

        {/* Disclaimer */}
        <div className="disclaimer">
          <span style={{ fontSize: 16, flexShrink: 0 }}>⚠</span>
          <span>
            <strong>Disclaimer:</strong> TariffCheck provides analysis assistance only. This is not legal advice. TariffCheck prepares filings; it does not file with CBP. All HTS classifications should be verified by a licensed customs broker or attorney before the importer of record files a formal protest with US Customs and Border Protection. The 180-day protest deadline under 19 U.S.C. 1514 applies uniformly to all entries made on or after December 18, 2004, regardless of country of origin.
          </span>
        </div>

        {/* Official sources */}
        <div style={{ background: 'var(--slate-100)', borderRadius: 'var(--radius-md)', padding: '16px 20px', fontSize: 13, color: 'var(--slate-600)', display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
          <span style={{ fontWeight: 600, color: 'var(--slate-700)' }}>Official Sources:</span>
          <a href="https://hts.usitc.gov" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>USITC HTS Schedule ↗</a>
          <a href="https://www.cbp.gov/trade/programs-administration/entry-summary/protests" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>CBP Protest Guide ↗</a>
          <a href="https://rulings.cbp.gov" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>CBP Rulings ↗</a>
          <a href="https://www.ecfr.gov/current/title-19/chapter-I/part-174" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>19 CFR Part 174 ↗</a>
        </div>

      </div>
      <Footer />
      </div>

      {/* ===== Print-only protest letter (window.print) ===== */}
      <div className="print-only print-letter">
        <h1>PROTEST UNDER 19 U.S.C. § 1514 — CBP FORM 19 ATTACHMENT</h1>

        <div className="print-fill-block">
          <div className="print-fill-row"><span className="print-fill-label">Date:</span><span className="print-fill-line">&nbsp;{date(Date.now())}</span></div>
          <div className="print-fill-row"><span className="print-fill-label">Port of Entry:</span><span className="print-fill-line" /></div>
          <div className="print-fill-row"><span className="print-fill-label">Entry Number(s):</span><span className="print-fill-line" /></div>
          <div className="print-fill-row"><span className="print-fill-label">Date(s) of Liquidation:</span><span className="print-fill-line" /></div>
          <div className="print-fill-row"><span className="print-fill-label">Importer of Record / IOR Number:</span><span className="print-fill-line" /></div>
        </div>

        <div className="print-letter-body">{protest_letter}</div>

        {findings.length > 0 && (
          <>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Exhibit A — Classification Findings (verified rate deltas)</div>
            <table className="print-exhibit-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Merchandise</th>
                  <th>Entered HTS / Rate</th>
                  <th>Claimed HTS / Rate</th>
                  <th>Entered Value</th>
                  <th>Verified Savings</th>
                  <th>Verification</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{f.description}</td>
                    <td>{f.hts_code} / {rate(f.total_current_rate ?? f.current_rate)}</td>
                    <td>{f.suggested_code} / {rate(f.total_suggested_rate ?? f.suggested_rate)}</td>
                    <td>{f.declared_value ? money(f.declared_value) : '—'}</td>
                    <td>{f.savings > 0 ? money(f.savings) : '—'}</td>
                    <td>{f.verified === true ? 'Verified — USITC HTS 2026' : 'Unverified — manual review'}</td>
                  </tr>
                ))}
                <tr>
                  <td colSpan={5} style={{ textAlign: 'right', fontWeight: 700 }}>Total verified savings claimed</td>
                  <td style={{ fontWeight: 700 }}>{money(total_savings)}</td>
                  <td />
                </tr>
              </tbody>
            </table>
          </>
        )}

        <div className="print-signature">
          <div className="print-signature-label">
            For review and filing by the importer of record or a licensed customs broker.
          </div>
          <div className="print-signature-line" />
          <div className="print-signature-caption">Signature</div>
          <div className="print-signature-line" />
          <div className="print-signature-caption">Name and Title</div>
          <div className="print-signature-line" />
          <div className="print-signature-caption">Firm / Company</div>
          <div className="print-signature-line" />
          <div className="print-signature-caption">Date</div>
        </div>

        <div className="print-page-footer">
          Prepared by TariffCheck — TariffCheck prepares filings; it does not file with CBP.
        </div>
      </div>
    </div>
  )
}
