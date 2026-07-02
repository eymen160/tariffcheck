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
export function analyzeInvoice({ text, file, demoId, signal } = {}) {
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
    return request('/api/analyze', { method: 'POST', body: fd, signal })
  }
  return request('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
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

/** GET /api/landed-cost?code=&origin=&value=&mode= */
export function landedCost({ code, origin = '', value, mode = 'ocean' }, signal) {
  const params = new URLSearchParams({ code, origin, value: String(value), mode })
  return request(`/api/landed-cost?${params.toString()}`, { signal })
}

/** POST /api/leads — stateless email capture. */
export function submitLead({ email, source, context = '' }, signal) {
  return request('/api/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, source, context }),
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
