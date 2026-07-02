// Client-side audit history (localStorage) + last-result rehydration (sessionStorage).
// Stateless backend — everything the dashboard shows lives here.

const STORE_KEY = 'tariffcheck_audits'
const SESSION_KEY = 'tariffcheck_last_result'
const MAX_AUDITS = 20

/** 180-day protest window, measured from the audit timestamp (confirm against liquidation date). */
export const PROTEST_WINDOW_DAYS = 180

export function newAuditId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

export function listAudits() {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    const arr = JSON.parse(raw || '[]')
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export function getAudit(id) {
  return listAudits().find(a => String(a.id) === String(id)) || null
}

/**
 * saveAudit({id, ts, sourceName, summary, fullResponse})
 * Capped at 20 entries, evicting oldest. Quota errors degrade by halving the list.
 */
export function saveAudit(audit) {
  let list = listAudits().filter(a => String(a.id) !== String(audit.id))
  list.unshift(audit)
  if (list.length > MAX_AUDITS) list = list.slice(0, MAX_AUDITS)
  while (list.length > 0) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(list))
      return true
    } catch {
      // Quota exceeded — drop the oldest entries and retry.
      list = list.slice(0, Math.ceil(list.length / 2) - 1 || 0)
      if (list.length === 0) {
        try { localStorage.removeItem(STORE_KEY) } catch { /* give up quietly */ }
        return false
      }
    }
  }
  return false
}

export function deleteAudit(id) {
  try {
    const list = listAudits().filter(a => String(a.id) !== String(id))
    localStorage.setItem(STORE_KEY, JSON.stringify(list))
  } catch {
    /* non-fatal */
  }
}

/** Build the small summary object stored alongside each audit. */
export function buildAuditSummary(data) {
  const findings = Array.isArray(data?.findings) ? data.findings : []
  const verification = data?.verification || {}
  return {
    findingsCount: findings.length,
    verifiedCount: verification.verified_count ?? findings.filter(f => f.verified === true).length,
    totalCount: verification.total_count ?? findings.length,
    totalSavings: Number(data?.total_savings) || 0,
    demo: Boolean(data?.meta?.demo),
    origin: data?.country_of_origin || null,
  }
}

/** Protest deadline timestamp for an audit (ms). */
export function auditDeadline(audit) {
  const ts = Number(audit?.ts) || Date.now()
  return ts + PROTEST_WINDOW_DAYS * 24 * 60 * 60 * 1000
}

/** Whole days until a deadline timestamp (can be negative). */
export function daysUntil(deadlineTs) {
  return Math.ceil((deadlineTs - Date.now()) / (24 * 60 * 60 * 1000))
}

// ---- sessionStorage rehydrate helpers (last analysis result) ----

export function setLastResult(data) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(data))
  } catch {
    /* quota — the results page will fall back to its empty state */
  }
}

export function getLastResult() {
  try {
    return JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null')
  } catch {
    return null
  }
}

export function clearLastResult() {
  try { sessionStorage.removeItem(SESSION_KEY) } catch { /* non-fatal */ }
}
