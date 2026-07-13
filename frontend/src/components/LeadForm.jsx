import { useState } from 'react'
import { submitLead, isFeatureUnavailable } from '../lib/api'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const fieldStyle = {
  flex: 1, minWidth: 220, padding: '11px 16px', fontSize: 14,
  border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', outline: 'none',
}

/**
 * Lead-capture form → POST /api/leads.
 * `detailed` adds broker-qualification fields (firm, monthly entry volume,
 * entry software) so a brokerage lead can be routed, not just collected.
 * Includes a honeypot field for spam. Degrades to a mailto fallback if the
 * endpoint is not deployed.
 */
export default function LeadForm({ source, placeholder = 'you@company.com', buttonLabel = 'Request access', detailed = false }) {
  const [email, setEmail] = useState('')
  const [firm, setFirm] = useState('')
  const [entriesPerMonth, setEntriesPerMonth] = useState('')
  const [software, setSoftware] = useState('')
  const [website, setWebsite] = useState('') // honeypot — stays empty for humans
  const [state, setState] = useState('idle') // idle | sending | success | fallback | error
  const [message, setMessage] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    const value = email.trim()
    if (!EMAIL_RE.test(value)) {
      setState('error')
      setMessage('Provide a valid email address.')
      return
    }
    setState('sending')
    setMessage('')
    try {
      const res = await submitLead({
        email: value, source,
        firm: firm.trim(), entriesPerMonth: entriesPerMonth.trim(), software: software.trim(),
        website,
      })
      setState('success')
      setMessage((res && res.message) || "Thanks — we'll be in touch.")
    } catch (err) {
      if (isFeatureUnavailable(err)) {
        setState('fallback')
        setMessage('Email us at hello@tariffcheck.app and we will set you up.')
      } else {
        setState('error')
        setMessage(err.message || 'Something went wrong. Please try again.')
      }
    }
  }

  if (state === 'success') {
    return (
      <div style={{ background: 'var(--green-light)', border: '1px solid var(--green-mid)', borderRadius: 'var(--radius-md)', padding: '14px 18px', fontSize: 14, color: 'var(--green)', fontWeight: 600 }}>
        ✓ {message}
      </div>
    )
  }

  return (
    <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Honeypot: visually hidden, ignored by humans, filled by bots. */}
      <input
        type="text"
        name="website"
        value={website}
        onChange={e => setWebsite(e.target.value)}
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
        style={{ position: 'absolute', left: '-9999px', width: 1, height: 1, opacity: 0 }}
      />
      {detailed && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            type="text"
            value={firm}
            onChange={e => setFirm(e.target.value)}
            placeholder="Brokerage / firm name"
            aria-label="Brokerage or firm name"
            autoComplete="organization"
            style={fieldStyle}
          />
          <input
            type="text"
            value={entriesPerMonth}
            onChange={e => setEntriesPerMonth(e.target.value)}
            placeholder="Entries filed per month (approx.)"
            aria-label="Entries filed per month"
            inputMode="numeric"
            style={fieldStyle}
          />
          <input
            type="text"
            value={software}
            onChange={e => setSoftware(e.target.value)}
            placeholder="Entry software (CargoWise, NetCHB…)"
            aria-label="Entry filing software"
            style={fieldStyle}
          />
        </div>
      )}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder={placeholder}
          aria-label="Work email"
          autoComplete="email"
          aria-invalid={state === 'error' ? 'true' : undefined}
          aria-describedby={state === 'error' ? 'leadform-error' : undefined}
          style={fieldStyle}
        />
        <button type="submit" className="btn-primary" disabled={state === 'sending'}>
          {state === 'sending' ? 'Sending…' : buttonLabel}
        </button>
      </div>
      {state === 'error' && (
        <div id="leadform-error" role="status" style={{ fontSize: 13, color: 'var(--red)' }}>⚠ {message}</div>
      )}
      {state === 'fallback' && (
        <div role="status" style={{ fontSize: 13, color: 'var(--slate-600)' }}>
          This form is rolling out — {message}
        </div>
      )}
    </form>
  )
}
