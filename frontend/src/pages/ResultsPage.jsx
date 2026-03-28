import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

const API = 'http://localhost:8000'

function fmt(n) {
  return Number(n).toLocaleString('en-US')
}


function getHtsUrl(code) {
  if (!code) return null
  return `https://hts.usitc.gov/?query=${encodeURIComponent(String(code).split('.').slice(0,2).join('.'))}`
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

  const data = location.state?.data

  const [demoError, setDemoError] = useState('')

  async function loadDemo() {
    setDemoError('')
    try {
      const res = await fetch(`${API}/demo/2`)
      const d = await res.json()
      navigate('/results', { state: { data: d }, replace: true })
    } catch {
      setDemoError('Could not reach backend on port 8000. Run: PORT=8000 python3 app.py')
    }
  }

  if (!data) {
    return (
      <div style={{minHeight:'100vh', background:'var(--slate-50)'}}>
        <Navbar />
        <div className="error-outer">
          <div className="error-card">
            <div className="error-icon">📋</div>
            <div className="error-title">No Analysis Data</div>
            <div className="error-sub">Go back and submit an invoice to see your duty savings analysis.</div>
            {demoError && (
          <div className="inline-error" style={{ marginBottom: 12, textAlign: 'left' }}>
            <span>⚠</span><span>{demoError}</span>
          </div>
        )}
          <button className="try-demo-btn" onClick={loadDemo} style={{marginBottom:12}}>
              Load Demo Results
            </button>
            <div style={{marginTop:12}}>
              <button onClick={()=>navigate('/')} style={{background:'none',border:'none',color:'var(--slate-500)',cursor:'pointer',fontSize:14,fontWeight:500}}>
                Go back to home
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const { findings=[], total_savings=0, fta_eligible, fta_type, country_of_origin, protest_letter='' } = data
  const hasSavings = total_savings > 0
  const itemsWithSavings = findings.filter(f => f.savings > 0)

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



  function toggleCard(i) {
    setOpenCards(prev => ({ ...prev, [i]: !prev[i] }))
  }

  return (
    <div className="results-page">
      <Navbar />

      <div className="results-topbar">
        <button className="back-btn" onClick={() => navigate('/')}>
          ← New Analysis
        </button>
        <div className="results-heading">Duty Savings Analysis</div>
      </div>

      <div className="results-body">

        {/* Savings Banner */}
        <div className="savings-banner">
          <div className="savings-left">
            <div className="savings-label">Total Potential Duty Savings</div>
            <div className="savings-amount">
              {hasSavings ? `$${total_savings.toLocaleString('en-US')}` : '$0'}
            </div>
            <div className="savings-sub">
              {hasSavings
                ? `${itemsWithSavings.length} misclassified item${itemsWithSavings.length !== 1 ? 's' : ''} identified`
                : 'No misclassifications detected in this invoice'}
            </div>
          </div>
          <div className="savings-right">
            {fta_eligible && fta_type && (
              <div className="fta-badge">
                ✓ {fta_type} Free Trade Agreement
              </div>
            )}
            {country_of_origin && (
              <div className="fta-badge">
                🌍 Origin: {country_of_origin}
              </div>
            )}
            {hasSavings && (
              <div className="deadline-badge">
                ⏰ 180 days to file CBP protest
              </div>
            )}
          </div>
        </div>

        {/* Findings */}
        {findings.length > 0 && (
          <div style={{marginBottom: 40}}>
            <div className="section-header">
              <div className="section-heading">
                HTS Code Analysis
                <span className="count-badge">{findings.length} item{findings.length!==1?'s':''} analyzed</span>
              </div>
              <a
                href="https://hts.usitc.gov"
                target="_blank"
                rel="noopener noreferrer"
                style={{fontSize:13, color:'var(--blue)', fontWeight:500, textDecoration:'none', display:'flex', alignItems:'center', gap:5}}
              >
                Official USITC Schedule ↗
              </a>
            </div>

            <div className="findings-grid">
              {findings.map((f, i) => (
                <div className="finding-card" key={i}>
                  <div className="codes-row">
                    <div className="code-block">
                      <div className="code-label">Current Code</div>
                      <div className="code-value">{f.hts_code}</div>
                      <span className={`rate-badge ${f.current_rate > 0 ? 'bad' : 'neutral'}`}>
                        {f.current_rate}%
                      </span>
                      <div>
                        <a
                          className="code-link"
                          href={getHtsUrl(f.hts_code)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          USITC ↗
                        </a>
                        <span style={{color:'var(--slate-300)',margin:'0 6px'}}>|</span>
                        <a
                          className="code-link"
                          href={getCbpRulingUrl(f.hts_code)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          CBP Rulings ↗
                        </a>
                      </div>
                    </div>

                    <div className="code-arrow">→</div>

                    <div className="code-block">
                      <div className="code-label">Suggested Code</div>
                      <div className="code-value">{f.suggested_code}</div>
                      <span className="rate-badge good">{f.suggested_rate}%</span>
                      <div>
                        <a
                          className="code-link"
                          href={getHtsUrl(f.suggested_code)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          USITC ↗
                        </a>
                        <span style={{color:'var(--slate-300)',margin:'0 6px'}}>|</span>
                        <a
                          className="code-link"
                          href={getCbpRulingUrl(f.suggested_code)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          CBP Rulings ↗
                        </a>
                      </div>
                    </div>
                  </div>

                  <div className="finding-desc">{f.description}</div>

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
                          {f.savings > 0 ? `$${fmt(f.savings)} savings` : 'No savings on this item'}
                        </div>
                        {f.declared_value > 0 && (
                          <div className="shipment-val">on ${fmt(f.declared_value)} shipment value</div>
                        )}
                      </div>
                      {f.savings > 0 && (
                        <span style={{fontSize:20}}>💰</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary table if multiple items */}
        {findings.length > 1 && (
          <div style={{marginBottom:40}}>
            <div className="section-header" style={{marginBottom:16}}>
              <div className="section-heading">Savings Summary</div>
            </div>
            <div className="summary-table-wrap">
              <table className="summary-table">
                <thead>
                  <tr>
                    {['Product','Current HTS','Rate','Suggested HTS','Rate','Savings'].map(h => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {findings.map((f,i) => (
                    <tr key={i}>
                      <td style={{maxWidth:160, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{f.description}</td>
                      <td><span className="mono">{f.hts_code}</span></td>
                      <td><span className={`rate-badge ${f.current_rate > 0 ? 'bad' : 'neutral'}`}>{f.current_rate}%</span></td>
                      <td><span className="mono">{f.suggested_code}</span></td>
                      <td><span className="rate-badge good">{f.suggested_rate}%</span></td>
                      <td style={{fontWeight:700, color: f.savings > 0 ? 'var(--green)' : 'var(--slate-400)'}}>
                        {f.savings > 0 ? `$${fmt(f.savings)}` : 'None'}
                      </td>
                    </tr>
                  ))}
                  <tr className="total-row">
                    <td colSpan={5} style={{textAlign:'right', fontSize:13}}>Total potential savings</td>
                    <td style={{color:'var(--green)', fontSize:17}}>${fmt(total_savings)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Protest Letter */}
        {protest_letter && hasSavings && (
          <div className="letter-section">
            <div className="section-header" style={{marginBottom:16}}>
              <div className="section-heading">
                CBP Protest Letter
                <span className="ready-badge">Ready to file</span>
              </div>
            </div>
            <div className="letter-card">
              <div className="letter-card-header">
                <div style={{fontSize:14, color:'var(--slate-600)', lineHeight:1.5}}>
                  <strong>Filing:</strong> CBP Form 19 or ACE Protest Module at cbp.gov
                </div>
                <div style={{fontSize:13, color:'var(--slate-500)'}}>
                  Deadline: 180 days from liquidation per 19 U.S.C. 1514
                </div>
              </div>
              <div className="letter-info-bar">
                <span>📋</span>
                <span>
                  This letter is based on 19 U.S.C. 1514(a)(2). US law gives importers 180 days from liquidation to file a protest with CBP. This deadline is uniform and does not vary by country of origin.
                </span>
              </div>
              <pre className="letter-body">{protest_letter}</pre>
              <div className="letter-actions">
                <button
                  className={`action-btn ${copied ? 'success' : 'primary'}`}
                  onClick={copyLetter}
                >
                  {copied ? '✓ Copied!' : '📋 Copy Letter'}
                </button>
                <button className="action-btn secondary" onClick={downloadLetter}>
                  ⬇ Download .txt
                </button>


              </div>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="disclaimer">
          <span style={{fontSize:16, flexShrink:0}}>⚠</span>
          <span>
            <strong>Disclaimer:</strong> TariffCheck provides analysis assistance only. This is not legal advice. All HTS classifications should be verified by a licensed customs broker or attorney before filing a formal protest with US Customs and Border Protection. The 180-day protest deadline under 19 U.S.C. 1514 applies uniformly to all entries made on or after December 18, 2004, regardless of country of origin.
          </span>
        </div>

        {/* Official sources */}
        <div style={{background:'var(--slate-100)', borderRadius:'var(--radius-md)', padding:'16px 20px', fontSize:13, color:'var(--slate-600)', display:'flex', flexWrap:'wrap', gap:'16px', alignItems:'center'}}>
          <span style={{fontWeight:600, color:'var(--slate-700)'}}>Official Sources:</span>
          <a href="https://hts.usitc.gov" target="_blank" rel="noopener noreferrer" style={{color:'var(--blue)', textDecoration:'none', fontWeight:500}}>USITC HTS Schedule ↗</a>
          <a href="https://www.cbp.gov/trade/programs-administration/entry-summary/protests" target="_blank" rel="noopener noreferrer" style={{color:'var(--blue)', textDecoration:'none', fontWeight:500}}>CBP Protest Guide ↗</a>
          <a href="https://rulings.cbp.gov" target="_blank" rel="noopener noreferrer" style={{color:'var(--blue)', textDecoration:'none', fontWeight:500}}>CBP Rulings ↗</a>
          <a href="https://www.ecfr.gov/current/title-19/chapter-I/part-174" target="_blank" rel="noopener noreferrer" style={{color:'var(--blue)', textDecoration:'none', fontWeight:500}}>19 CFR Part 174 ↗</a>
        </div>

      </div>
    </div>
  )
}
