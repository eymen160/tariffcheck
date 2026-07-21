import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { analyzeBatch, analyzeBatch7501, isFeatureUnavailable } from '../lib/api'
import { money, rate } from '../lib/format'
import { usePageTitle } from '../lib/usePageTitle'

const CHUNK_SIZE = 100

const FIELD_OPTIONS = [
  { value: '', label: '— Ignore —' },
  { value: 'hts_code', label: 'HTS code' },
  { value: 'description', label: 'Description' },
  { value: 'declared_value', label: 'Declared value (USD)' },
  { value: 'origin', label: 'Country of origin' },
  { value: 'entry_no', label: 'Entry number' },
  { value: 'line_no', label: 'Line number' },
  { value: 'entry_date', label: 'Entry date' },
  { value: 'liquidation_date', label: 'Liquidation date' },
  { value: 'liquidation_status', label: 'Liquidation status' },
  { value: 'duty_paid', label: 'Duty amount paid (USD)' },
  { value: 'spi_claimed', label: 'SPI (program claimed)' },
]

// Exact-match presets for the reports brokers actually export (ACE ES-003 /
// entry-summary line reports, CargoWise/NetCHB exports). Exact matches always
// beat regex guesses — "Duty Amount" must never land in declared_value.
const HEADER_PRESETS = {
  'entry summary number': 'entry_no', 'entry number': 'entry_no', 'entry no': 'entry_no',
  'entry summary line number': 'line_no', 'line number': 'line_no', 'line no': 'line_no',
  'entry date': 'entry_date', 'entry summary date': 'entry_date',
  'liquidation date': 'liquidation_date',
  'liquidation status': 'liquidation_status', 'entry liquidation status': 'liquidation_status',
  'duty amount': 'duty_paid', 'duty paid': 'duty_paid', 'total duty': 'duty_paid',
  'spi': 'spi_claimed', 'special program indicator': 'spi_claimed', 'special programs indicator': 'spi_claimed',
  'hts number': 'hts_code', 'hts code': 'hts_code', 'hts': 'hts_code', 'tariff number': 'hts_code', 'tariff ordinal': '',
  'country of origin': 'origin', 'country of origin code': 'origin', 'origin': 'origin',
  'country of export': '', 'country of export code': '',
  'line goods value': 'declared_value', 'entered value': 'declared_value',
  'goods value': 'declared_value', 'declared value': 'declared_value', 'value': 'declared_value',
  'description': 'description', 'commodity description': 'description',
}

const SAMPLE_CSV = `hts_code,description,declared_value,origin
9403.40.9060,"Wooden kitchen cabinets, shaker style",12000,China
6109.90.1090,"Men's t-shirts, 60/40 cotton-poly blend",8000,Vietnam
9403.60.8093,"Solid oak dining tables",22500,Vietnam
6404.19.3560,"Athletic shoes, textile upper, rubber sole",44000,Vietnam
8708.99.8180,"Transmission housings, cast aluminum",43500,South Korea
8419.89.1000,"Coffee roasting machines, 60kg batch",74000,Colombia
7323.93.0080,"Stainless steel kitchenware, polished",6200,China
9617.00.9000,"Vacuum-insulated tumblers, 20oz",4250,China
6802.91.0500,"Polished marble countertop slabs",31000,India
6802.21.1000,"Rough travertine blocks",9800,India
9403.90.8041,"Metal chair bases and parts",5400,Mexico
8477.80.0000,"Tablet coating machines, pharma grade",126000,India
6109.10.0012,"Crew neck t-shirts, 100% cotton",7600,Bangladesh
8483.40.5000,"Gear boxes and speed reducers",31500,South Korea
9403.20.0050,"Steel shelving units, boltless",14200,China
4202.92.3131,"Backpacks with outer surface of textile",18700,Vietnam
8516.60.4070,"Countertop electric ovens",23900,China
7013.37.2000,"Drinking glasses, machine-made",5100,Mexico
9401.61.4011,"Upholstered wooden chairs",27300,Vietnam
3924.10.4000,"Plastic tableware and kitchenware",4400,China`

// Hand-rolled CSV parser: quoted fields, commas and newlines inside quotes, "" escapes.
function parseCSV(text) {
  const rows = []
  let row = []
  let field = ''
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++ } else { inQuotes = false }
      } else {
        field += c
      }
    } else if (c === '"') {
      inQuotes = true
    } else if (c === ',') {
      row.push(field); field = ''
    } else if (c === '\n') {
      row.push(field); rows.push(row); row = []; field = ''
    } else if (c !== '\r') {
      field += c
    }
  }
  if (field !== '' || row.length > 0) { row.push(field); rows.push(row) }
  return rows.filter(r => r.some(cell => String(cell).trim() !== ''))
}

function guessField(header) {
  const h = String(header).toLowerCase().replace(/[_\s]+/g, ' ').trim()
  if (Object.prototype.hasOwnProperty.call(HEADER_PRESETS, h)) return HEADER_PRESETS[h]
  if (/country of export|export country/.test(h)) return ''
  if (/liquidation/.test(h)) return /date/.test(h) ? 'liquidation_date' : 'liquidation_status'
  if (/\bspi\b|special program/.test(h)) return 'spi_claimed'
  if (/duty/.test(h)) return 'duty_paid'
  if (/entry.*date/.test(h)) return 'entry_date'
  if (/entry/.test(h)) return 'entry_no'
  if (/hts|tariff|code/.test(h)) return 'hts_code'
  if (/origin|country/.test(h)) return 'origin'
  if (/value|amount|total|price|cost/.test(h)) return 'declared_value'
  if (/desc|product|item|merchandise|goods/.test(h)) return 'description'
  return ''
}

function csvEscape(v) {
  let s = v == null ? '' : String(v)
  // Neutralize spreadsheet formula injection (OWASP): a cell starting with
  // =, +, -, @, tab or CR executes when the exported report opens in Excel.
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

function ConfidencePill({ level }) {
  const map = {
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
  }
  const className = map[level] || map.medium
  return (
    <span className={className} style={{ whiteSpace: 'nowrap', textTransform: 'capitalize' }}>
      {level || 'medium'}
    </span>
  )
}

const SORT_KEYS = {
  row_id: r => r.row_id,
  description: r => String(r.description || ''),
  estimated_savings: r => Number(r.estimated_savings) || 0,
  rate_delta: r => (Number(r.total_current_rate) || 0) - (Number(r.total_suggested_rate) || 0),
  confidence: r => ({ high: 3, medium: 2, low: 1 }[r.confidence] || 0),
}

export default function BatchPage() {
  const [csvText, setCsvText] = useState('')
  const [isSample, setIsSample] = useState(false)
  const [mapping, setMapping] = useState({}) // colIndex -> field
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState(null) // merged results array
  const [summary, setSummary] = useState(null) // merged summary
  const [skipped, setSkipped] = useState(0)
  const [error, setError] = useState('')
  const [unavailable, setUnavailable] = useState(false)
  const [showOk, setShowOk] = useState(false)
  const [sort, setSort] = useState({ key: 'estimated_savings', dir: 'desc' })
  const [pdfSource, setPdfSource] = useState(null) // 7501 upload: {entry_no, rows_parsed, warnings}
  const fileRef = useRef()

  usePageTitle('Batch Audit')

  const parsed = useMemo(() => (csvText.trim() ? parseCSV(csvText) : []), [csvText])
  const headers = parsed.length > 0 ? parsed[0] : []
  const dataRows = parsed.length > 1 ? parsed.slice(1) : []

  const effectiveMapping = useMemo(() => {
    const m = {}
    headers.forEach((h, i) => {
      m[i] = mapping[i] !== undefined ? mapping[i] : guessField(h)
    })
    // Deduplicate auto-guesses: first column wins per field.
    const seen = new Set()
    Object.keys(m).forEach(i => {
      if (m[i] && seen.has(m[i]) && mapping[i] === undefined) m[i] = ''
      else if (m[i]) seen.add(m[i])
    })
    return m
  }, [headers, mapping])

  const hasHtsColumn = Object.values(effectiveMapping).includes('hts_code')

  function loadCsvString(text, sample) {
    setCsvText(text)
    setIsSample(sample)
    setMapping({})
    setResults(null)
    setSummary(null)
    setError('')
    setUnavailable(false)
    setPdfSource(null)
  }

  async function onPdf(f) {
    // CBP Form 7501: parsed server-side to ES-003 rows — no column mapping
    // step, results land directly.
    setError('')
    setUnavailable(false)
    setResults(null)
    setSummary(null)
    setPdfSource(null)
    setRunning(true)
    try {
      const data = await analyzeBatch7501(f)
      setResults(data.results || [])
      setSummary(data.summary || null)
      setPdfSource(data.source || null)
    } catch (err) {
      if (isFeatureUnavailable(err)) setUnavailable(true)
      else setError(err.message || 'We could not read that 7501. Try the CSV path instead.')
    } finally {
      setRunning(false)
    }
  }

  function onFile(e) {
    const f = e.target.files[0]
    if (!f) return
    const name = (f.name || '').toLowerCase()
    if (name.endsWith('.pdf')) {
      onPdf(f)
      e.target.value = ''
      return
    }
    if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
      // ACE exports arrive as Excel; convert the first sheet to CSV
      // client-side (lazy-loaded so the landing bundle stays small).
      const reader = new FileReader()
      reader.onload = async ev => {
        try {
          const XLSX = await import('xlsx')
          const wb = XLSX.read(ev.target.result, { type: 'array' })
          const sheet = wb.Sheets[wb.SheetNames[0]]
          loadCsvString(XLSX.utils.sheet_to_csv(sheet), false)
        } catch {
          setError('We could not read that Excel file. Save it as CSV and try again.')
        }
      }
      reader.onerror = () => setError('We could not read that file. Save it as CSV and try again.')
      reader.readAsArrayBuffer(f)
      return
    }
    const reader = new FileReader()
    reader.onload = ev => loadCsvString(String(ev.target.result || ''), false)
    reader.onerror = () => setError('We could not read that file. Try pasting the CSV as text instead.')
    reader.readAsText(f)
  }

  async function runAudit() {
    setError('')
    setUnavailable(false)
    setResults(null)
    setSummary(null)
    setPdfSource(null)
    setRunning(true)
    setProgress(0)

    // Build API rows from mapping.
    const apiRows = []
    let skippedCount = 0
    dataRows.forEach((r, idx) => {
      const row = { row_id: idx + 1 }
      headers.forEach((_, ci) => {
        const field = effectiveMapping[ci]
        if (!field) return
        const raw = (r[ci] || '').trim()
        if (field === 'declared_value' || field === 'duty_paid') {
          const num = parseFloat(raw.replace(/[$,\s]/g, ''))
          if (!isNaN(num)) row[field] = num
        } else if (raw) {
          row[field] = raw
        }
      })
      if (row.hts_code) apiRows.push(row)
      else skippedCount++
    })
    setSkipped(skippedCount)

    if (apiRows.length === 0) {
      setRunning(false)
      setError('No rows with an HTS code found. Map the HTS code column and try again.')
      return
    }

    const chunks = []
    for (let i = 0; i < apiRows.length; i += CHUNK_SIZE) chunks.push(apiRows.slice(i, i + CHUNK_SIZE))

    const mergedResults = []
    const mergedSummary = { rows: 0, flagged: 0, total_estimated_exposure: 0, source: '', disclaimer: '' }

    try {
      for (let i = 0; i < chunks.length; i++) {
        const data = await analyzeBatch(chunks[i])
        mergedResults.push(...(data.results || []))
        const s = data.summary || {}
        mergedSummary.rows += Number(s.rows) || 0
        mergedSummary.flagged += Number(s.flagged) || 0
        mergedSummary.total_estimated_exposure += Number(s.total_estimated_exposure) || 0
        mergedSummary.source = s.source || mergedSummary.source
        mergedSummary.disclaimer = s.disclaimer || mergedSummary.disclaimer
        setProgress(Math.round(((i + 1) / chunks.length) * 100))
      }
      setResults(mergedResults)
      setSummary(mergedSummary)
    } catch (err) {
      if (isFeatureUnavailable(err)) {
        setUnavailable(true)
      } else {
        setError(err.message || 'The batch audit failed. Please try again.')
      }
    } finally {
      setRunning(false)
    }
  }

  function downloadReport() {
    if (!results) return
    const header = ['row_id', 'entry_no', 'status', 'description', 'origin', 'declared_value', 'duty_paid', 'current_code', 'total_current_rate', 'issue', 'suggested_code', 'total_suggested_rate', 'estimated_savings', 'remedy_vehicle', 'protest_by', 'confidence', 'verified', 'note']
    const lines = [header.join(',')]
    results.forEach(r => {
      lines.push(header.map(k => csvEscape(r[k])).join(','))
    })
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tariffcheck-batch-report.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function toggleSort(key) {
    setSort(s => (s.key === key ? { key, dir: s.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'desc' }))
  }

  const flaggedRows = useMemo(() => {
    if (!results) return []
    const rows = results.filter(r => r.status === 'flagged' || r.status === 'error')
    const getter = SORT_KEYS[sort.key] || SORT_KEYS.estimated_savings
    rows.sort((a, b) => {
      const va = getter(a); const vb = getter(b)
      const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
      return sort.dir === 'desc' ? -cmp : cmp
    })
    return rows
  }, [results, sort])

  const okRows = useMemo(() => (results ? results.filter(r => r.status === 'ok') : []), [results])

  const sortArrow = key => (sort.key === key ? (sort.dir === 'desc' ? ' ↓' : ' ↑') : '')
  const ariaSort = key => (sort.key === key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none')
  const sortBtnStyle = { background: 'none', border: 'none', font: 'inherit', cursor: 'pointer', padding: 0, color: 'inherit', textTransform: 'inherit', letterSpacing: 'inherit' }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ maxWidth: 1080, margin: '0 auto', padding: '40px 24px 64px', width: '100%', flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 6 }}>
          <h1 style={{ fontSize: 30, letterSpacing: '-0.75px', color: 'var(--slate-900)' }}>Batch Audit</h1>
          {isSample && <span className="badge-sample">Sample data</span>}
        </div>
        <p style={{ fontSize: 15, color: 'var(--slate-500)', marginBottom: 28, maxWidth: 720 }}>
          Screen an entire entry portfolio against the official USITC HTS 2026 schedule — deterministic checks for
          misclassification patterns, missed FTA claims, and Section 301 exposure. Built for brokers bulk-scanning
          client invoices.
        </p>

        {/* Input card */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
            <button className="btn-secondary" onClick={() => fileRef.current.click()}>Upload CSV / Excel / 7501 PDF</button>
            <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls,.pdf,text/csv,application/pdf" style={{ display: 'none' }} onChange={onFile} />
            <button className="btn-secondary" onClick={() => loadCsvString(SAMPLE_CSV, true)}>
              Load sample portfolio <span className="badge-sample" style={{ fontSize: 9, padding: '2px 7px' }}>Sample data</span>
            </button>
          </div>

          <textarea
            className="invoice-textarea"
            style={{ minHeight: 140, fontFamily: 'var(--font-mono)', fontSize: 12.5 }}
            placeholder={'Paste CSV here — first row is headers, e.g.\nhts_code,description,declared_value,origin\n9403.40.9060,"Wooden kitchen cabinets",12000,China'}
            value={csvText}
            onChange={e => loadCsvString(e.target.value, false)}
          />

          {/* Column mapping */}
          {headers.length > 0 && (
            <div style={{ marginTop: 18 }}>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--slate-500)', marginBottom: 10 }}>
                Column mapping — {dataRows.length} data row{dataRows.length !== 1 ? 's' : ''} detected
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {headers.map((h, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--slate-600)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h || `(column ${i + 1})`}</span>
                    <select
                      value={effectiveMapping[i] || ''}
                      onChange={e => setMapping(m => ({ ...m, [i]: e.target.value }))}
                      style={{ padding: '7px 10px', fontSize: 13, border: '1.5px solid var(--slate-200)', borderRadius: 8, background: 'white', color: 'var(--slate-700)' }}
                    >
                      {FIELD_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                ))}
              </div>
              {!hasHtsColumn && (
                <div style={{ marginTop: 10, fontSize: 13, color: 'var(--amber)' }}>
                  ⚠ Map one column to "HTS code" to run the audit.
                </div>
              )}
            </div>
          )}

          {error && <div className="inline-error" style={{ marginTop: 16 }}><span>⚠</span><span>{error}</span></div>}

          <button
            className="btn-primary"
            style={{ marginTop: 18, padding: '13px 28px', fontSize: 15 }}
            onClick={runAudit}
            disabled={running || dataRows.length === 0 || !hasHtsColumn}
          >
            {running ? 'Auditing…' : `Run audit${dataRows.length ? ` — ${dataRows.length} rows` : ''}`}
          </button>

          {running && (
            <div style={{ marginTop: 14 }}>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
              <div style={{ fontSize: 12, color: 'var(--slate-500)', marginTop: 6 }}>
                Screening rows against the USITC schedule… {progress}%
              </div>
            </div>
          )}
        </div>

        {/* Rollout fallback */}
        {unavailable && (
          <div className="rollout-card" style={{ marginBottom: 24 }}>
            <strong>This feature is rolling out — try the invoice audit instead.</strong>
            <div style={{ marginTop: 6 }}>
              Batch screening is not available on this deployment yet.{' '}
              <Link to="/" style={{ color: 'var(--blue)', fontWeight: 600 }}>Run a single-invoice audit →</Link>
            </div>
          </div>
        )}

        {/* Empty pre-upload ghost table */}
        {!results && !unavailable && dataRows.length === 0 && (
          <div className="card" style={{ opacity: 0.75 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--slate-500)', marginBottom: 12 }}>
              Expected columns — upload or paste a CSV to begin
            </div>
            <table className="batch-table">
              <thead>
                <tr>
                  <th style={{ cursor: 'default' }}>hts_code</th>
                  <th style={{ cursor: 'default' }}>description</th>
                  <th style={{ cursor: 'default' }}>declared_value</th>
                  <th style={{ cursor: 'default' }}>origin</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['9403.40.9060', 'Wooden kitchen cabinets', '12,000', 'China'],
                  ['6109.90.1090', "Men's cotton t-shirts", '8,000', 'Vietnam'],
                  ['8708.99.8180', 'Transmission housings', '43,500', 'South Korea'],
                ].map((r, i) => (
                  <tr key={i} style={{ color: 'var(--slate-300)' }}>
                    {r.map((c, j) => <td key={j} style={{ color: 'var(--slate-400)' }}>{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Results */}
        {results && summary && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 18 }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--slate-900)', letterSpacing: '-0.4px' }}>
                {summary.rows} line{summary.rows !== 1 ? 's' : ''} · {summary.flagged} flagged ·{' '}
                <span style={{ color: 'var(--green)' }}>{money(summary.total_estimated_exposure)} estimated exposure</span>
              </div>
              {isSample && <span className="badge-sample">Sample data</span>}
              <button className="btn-secondary" style={{ marginLeft: 'auto' }} onClick={downloadReport}>Download report</button>
            </div>

            {skipped > 0 && (
              <div style={{ fontSize: 13, color: 'var(--slate-500)', marginBottom: 12 }}>
                {skipped} row{skipped !== 1 ? 's' : ''} skipped (no HTS code).
              </div>
            )}

            {pdfSource && (
              <div style={{ fontSize: 13, color: 'var(--slate-600)', marginBottom: 12, background: 'var(--slate-50)', border: '1px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', padding: '10px 14px' }}>
                Parsed from CBP Form 7501{pdfSource.entry_no ? <> — entry <span style={{ fontFamily: 'var(--font-mono)' }}>{pdfSource.entry_no}</span></> : null} · {pdfSource.rows_parsed} line{pdfSource.rows_parsed !== 1 ? 's' : ''} extracted.
                {(pdfSource.warnings || []).length > 0 && (
                  <ul style={{ margin: '6px 0 0', paddingLeft: 18, color: 'var(--amber)', lineHeight: 1.6 }}>
                    {pdfSource.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                )}
              </div>
            )}

            {flaggedRows.length > 0 ? (
              <div className="card" style={{ padding: 0, overflowX: 'auto', marginBottom: 20 }}>
                <table className="batch-table">
                  <thead>
                    <tr>
                      <th aria-sort={ariaSort('row_id')}>
                        <button type="button" style={sortBtnStyle} onClick={() => toggleSort('row_id')}>Row{sortArrow('row_id')}</button>
                      </th>
                      <th aria-sort={ariaSort('description')}>
                        <button type="button" style={sortBtnStyle} onClick={() => toggleSort('description')}>Description{sortArrow('description')}</button>
                      </th>
                      <th style={{ cursor: 'default' }}>Current → Suggested</th>
                      <th aria-sort={ariaSort('rate_delta')}>
                        <button type="button" style={sortBtnStyle} onClick={() => toggleSort('rate_delta')}>Rate Δ{sortArrow('rate_delta')}</button>
                      </th>
                      <th aria-sort={ariaSort('estimated_savings')}>
                        <button type="button" style={sortBtnStyle} onClick={() => toggleSort('estimated_savings')}>Est. Savings{sortArrow('estimated_savings')}</button>
                      </th>
                      <th aria-sort={ariaSort('confidence')}>
                        <button type="button" style={sortBtnStyle} onClick={() => toggleSort('confidence')}>Confidence{sortArrow('confidence')}</button>
                      </th>
                      <th style={{ cursor: 'default' }}>Verified</th>
                      <th style={{ cursor: 'default' }}>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {flaggedRows.map((r, i) => (
                      <tr key={i}>
                        <td>{r.row_id}</td>
                        <td style={{ maxWidth: 200 }}>{r.description || '—'}</td>
                        <td className="mono" style={{ whiteSpace: 'nowrap' }}>
                          {r.current_code}
                          {r.suggested_code ? <> → <strong>{r.suggested_code}</strong></> : null}
                          {r.issue === 'code_not_found' && <span style={{ color: 'var(--red)', fontWeight: 600 }}> (not found)</span>}
                        </td>
                        <td style={{ whiteSpace: 'nowrap' }}>
                          {r.total_current_rate != null && r.total_suggested_rate != null
                            ? `${rate(r.total_current_rate)} → ${rate(r.total_suggested_rate)}`
                            : r.total_current_rate != null ? rate(r.total_current_rate) : '—'}
                        </td>
                        <td style={{ fontWeight: 700, color: r.estimated_savings > 0 ? 'var(--green)' : 'var(--slate-400)' }}>
                          {r.estimated_savings > 0 ? money(r.estimated_savings) : '—'}
                        </td>
                        <td><ConfidencePill level={r.confidence} /></td>
                        <td>
                          {r.verified === true
                            ? <span className="badge-verified">✓ USITC 2026</span>
                            : <span className="badge-unverified" title={r.note || 'Manual review'}>⚠ Review</span>}
                        </td>
                        <td style={{ fontSize: 12, color: 'var(--slate-500)', maxWidth: 260 }}>{r.note || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="card" style={{ marginBottom: 20, fontSize: 14, color: 'var(--slate-600)' }}>
                ✓ No flagged rows — every line matched the official schedule with no exceptions found.
              </div>
            )}

            {/* Collapsed OK rows */}
            {okRows.length > 0 && (
              <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 20 }}>
                <button
                  onClick={() => setShowOk(v => !v)}
                  style={{ width: '100%', background: 'var(--slate-50)', border: 'none', padding: '14px 20px', fontSize: 14, fontWeight: 600, color: 'var(--slate-600)', cursor: 'pointer', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                >
                  <span>✓ {okRows.length} row{okRows.length !== 1 ? 's' : ''} passed with no exceptions</span>
                  <span>{showOk ? '▲' : '▼'}</span>
                </button>
                {showOk && (
                  <div style={{ overflowX: 'auto' }}>
                    <table className="batch-table">
                      <thead>
                        <tr>
                          <th style={{ cursor: 'default' }}>Row</th>
                          <th style={{ cursor: 'default' }}>Description</th>
                          <th style={{ cursor: 'default' }}>Code</th>
                          <th style={{ cursor: 'default' }}>Total Rate</th>
                          <th style={{ cursor: 'default' }}>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {okRows.map((r, i) => (
                          <tr key={i}>
                            <td>{r.row_id}</td>
                            <td>{r.description || '—'}</td>
                            <td className="mono">{r.current_code}</td>
                            <td>{rate(r.total_current_rate)}</td>
                            <td>{r.declared_value != null ? money(r.declared_value) : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {summary.disclaimer && (
              <div className="disclaimer" style={{ marginBottom: 0 }}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>⚠</span>
                <span>{summary.disclaimer}{summary.source ? ` Source: ${summary.source}.` : ''}</span>
              </div>
            )}
          </>
        )}
      </div>

      <Footer />
    </div>
  )
}
