// Single API layer for TariffCheck.
// Every call checks res.ok, parses the shared error shape {error, message},
// and throws an ApiError carrying .code (snake_case machine code) and .status.

const API = ''

export class ApiError extends Error {
  constructor(message, code, status, body = null) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.body = body
  }
}

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${API}${path}`, options)
  } catch (e) {
    if (e && e.name === 'AbortError') {
      throw new ApiError('The request was cancelled because it took too long.', 'client_timeout', 0)
    }
    throw new ApiError('We could not reach the server. Please check your connection and try again.', 'network_error', 0)
  }

  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }

  if (!res.ok) {
    const code = (body && body.error) || (res.status === 404 ? 'not_found' : 'unknown_error')
    const message =
      (body && body.message) ||
      (res.status === 404
        ? 'This feature is not available on this deployment yet.'
        : 'Something went wrong. Please try again.')
    throw new ApiError(message, code, res.status, body)
  }

  return body
}

/**
 * POST /api/analyze — invoice text, file upload, or explicit demo scenario.
 * opts: { text?, file?, demoId?, signal? }
 */
export function analyzeInvoice({ text, file, demoId, entryDate, liquidationDate, liquidationStatus, signal } = {}) {
  // Optional entry facts drive the backend's remedy router (PSC vs §1514 vs
  // 1520(d)) and produce real statutory deadlines instead of estimates.
  const facts = {}
  if (entryDate) facts.entry_date = entryDate
  if (liquidationDate) facts.liquidation_date = liquidationDate
  if (liquidationStatus) facts.liquidation_status = liquidationStatus

  if (demoId != null) {
    return request('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_id: String(demoId) }),
      signal,
    })
  }
  if (file) {
    const fd = new FormData()
    fd.append('file', file)
    for (const [k, v] of Object.entries(facts)) fd.append(k, v)
    return request('/api/analyze', { method: 'POST', body: fd, signal })
  }
  return request('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, ...facts }),
    signal,
  })
}

/** GET /api/demo/<id> — legacy sample endpoint, used as a fallback for demo scenarios. */
export function fetchDemo(id, signal) {
  return request(`/api/demo/${id}`, { signal })
}

/** POST /api/analyze-batch — deterministic broker screen, rows: [{row_id, hts_code, ...}] */
export function analyzeBatch(rows, signal) {
  return request('/api/analyze-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rows }),
    signal,
  })
}

/** POST /api/analyze-batch with a CBP Form 7501 PDF (multipart). The entry
 * summary is parsed server-side to ES-003 rows and audited; the response
 * carries a `source` block (entry_no, rows_parsed, warnings). */
export function analyzeBatch7501(file, signal) {
  const form = new FormData()
  form.append('file', file)
  return request('/api/analyze-batch', { method: 'POST', body: form, signal })
}

/** GET /api/landed-cost?code=&origin=&value=&mode= */
export function landedCost({ code, origin = '', value, mode = 'ocean' }, signal) {
  const params = new URLSearchParams({ code, origin, value: String(value), mode })
  return request(`/api/landed-cost?${params.toString()}`, { signal })
}

/** POST /api/leads — email capture with optional broker-qualification
 * fields. `website` is a honeypot: real users never fill it. */
export function submitLead({ email, source, context = '', firm = '', entriesPerMonth = '', software = '', website = '' }, signal) {
  return request('/api/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email, source, context,
      firm, entries_per_month: entriesPerMonth, software, website,
    }),
    signal,
  })
}

/** POST /api/hts-lookup */
export function htsLookup({ code, origin = '' }, signal) {
  return request('/api/hts-lookup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, country_of_origin: origin }),
    signal,
  })
}

/** GET /api/hts-search?q= */
export function htsSearch(q, limit = 25, signal) {
  const params = new URLSearchParams({ q, limit: String(limit) })
  return request(`/api/hts-search?${params.toString()}`, { signal })
}

/** True when the error means "this endpoint is not deployed / unreachable" — show the rollout fallback. */
export function isFeatureUnavailable(err) {
  if (!(err instanceof ApiError)) return true
  return err.code === 'network_error' || (err.status === 404 && err.code === 'not_found') || err.status === 405
}
