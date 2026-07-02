import { useState } from 'react'
import { submitLead, isFeatureUnavailable } from '../lib/api'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Stateless email-capture form → POST /api/leads.
 * Degrades to a mailto fallback if the endpoint is not deployed.
 */
export default function LeadForm({ source, placeholder = 'you@company.com', buttonLabel = 'Request access' }) {
  const [email, setEmail] = useState('')
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
      const res = await submitLead({ email: value, source })
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
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder={placeholder}
          aria-label="Work email"
          style={{
            flex: 1, minWidth: 220, padding: '11px 16px', fontSize: 14,
            border: '1.5px solid var(--slate-200)', borderRadius: 'var(--radius-sm)', outline: 'none',
          }}
        />
        <button type="submit" className="btn-primary" disabled={state === 'sending'}>
          {state === 'sending' ? 'Sending…' : buttonLabel}
        </button>
      </div>
      {state === 'error' && (
        <div style={{ fontSize: 13, color: 'var(--red)' }}>⚠ {message}</div>
      )}
      {state === 'fallback' && (
        <div style={{ fontSize: 13, color: 'var(--slate-600)' }}>
          This form is rolling out — {message}
        </div>
      )}
    </form>
  )
}
