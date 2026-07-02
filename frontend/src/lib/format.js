// Shared display formatters. All output is English/US-locale.

/** money(14220) → "$14,220" · money(62.5) → "$62.50" — no decimals at or above $100. */
export function money(n) {
  if (n == null || isNaN(Number(n))) return '—'
  const num = Number(n)
  if (Math.abs(num) >= 100) {
    return num.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  }
  return num.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** rate(7.9) → "7.9%" · rate(25) → "25%" · rate(null) → "—" */
export function rate(n) {
  if (n == null || isNaN(Number(n))) return '—'
  return `${Number(n)}%`
}

/** date(ts | Date | ISO string) → "Mar 4, 2026" */
export function date(d) {
  const dt = d instanceof Date ? d : new Date(d)
  if (isNaN(dt.getTime())) return '—'
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
