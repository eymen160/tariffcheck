import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
        <div className="error-card">
          <div className="formlabel" style={{ color: 'var(--stamp)', marginBottom: 14 }}>Unexpected error</div>
          <div className="error-title">Something went wrong on this page</div>
          <div className="error-sub">Your audit history is safe in this browser. Reload the page or return to the audit desk.</div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/" className="btn-primary">Back to audit</a>
            <button className="btn-secondary" onClick={() => window.location.reload()}>Reload</button>
          </div>
        </div>
      </div>
    )
  }
}
