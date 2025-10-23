import { useState } from 'react'
import './ValidationResults.css'

function ValidationResults({ results }) {
  const [expandedSections, setExpandedSections] = useState({
    output: true,
    errors: false,
  })

  if (!results) {
    return null
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const { status, filing_url, validation_output, validation_errors } = results

  // Parse validation output to categorize messages
  const parseValidationOutput = (output) => {
    if (!output) return { info: [], warnings: [], errors: [], dqc: [] }
    
    const lines = output.split('\n').filter(line => line.trim())
    const categorized = { info: [], warnings: [], errors: [], dqc: [] }
    
    lines.forEach(line => {
      if (line.includes('[info]')) {
        categorized.info.push(line)
      } else if (line.includes('[warn]')) {
        categorized.warnings.push(line)
      } else if (line.includes('[error]') || line.includes('[EFM.')) {
        categorized.errors.push(line)
      } else if (line.includes('[DQC.')) {
        categorized.dqc.push(line)
      } else if (line.trim().length > 0) {
        categorized.info.push(line)
      }
    })
    
    return categorized
  }

  const messages = parseValidationOutput(validation_output)
  const hasErrors = messages.errors.length > 0 || messages.dqc.length > 0 || messages.warnings.length > 0
  const isSuccess = status === 'success' && !hasErrors

  return (
    <div className="validation-results">
      <div className={`results-header ${isSuccess ? 'success' : 'has-issues'}`}>
        <div className="status-icon">
          {isSuccess ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
        </div>
        <div className="status-content">
          <h2>{isSuccess ? 'Validation Successful' : 'Validation Issues Found'}</h2>
          <p className="filing-url">{filing_url}</p>
        </div>
      </div>

      <div className="results-summary">
        <div className="summary-item">
          <span className="summary-label">Status:</span>
          <span className={`summary-value ${status}`}>{status.toUpperCase()}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Errors:</span>
          <span className="summary-value">{messages.errors.length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">DQC Issues:</span>
          <span className="summary-value">{messages.dqc.length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Warnings:</span>
          <span className="summary-value">{messages.warnings.length}</span>
        </div>
      </div>

      {messages.errors.length > 0 && (
        <div className="message-section error-section">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Errors ({messages.errors.length})
          </h3>
          <div className="message-list">
            {messages.errors.map((msg, idx) => (
              <div key={idx} className="message-item error">
                {msg}
              </div>
            ))}
          </div>
        </div>
      )}

      {messages.dqc.length > 0 && (
        <div className="message-section dqc-section">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            DQC Rule Violations ({messages.dqc.length})
          </h3>
          <div className="message-list">
            {messages.dqc.map((msg, idx) => (
              <div key={idx} className="message-item dqc">
                {msg}
              </div>
            ))}
          </div>
        </div>
      )}

      {messages.warnings.length > 0 && (
        <div className="message-section warning-section">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Warnings ({messages.warnings.length})
          </h3>
          <div className="message-list">
            {messages.warnings.map((msg, idx) => (
              <div key={idx} className="message-item warning">
                {msg}
              </div>
            ))}
          </div>
        </div>
      )}

      {messages.info.length > 0 && (
        <div className="message-section info-section">
          <button
            className="section-toggle"
            onClick={() => toggleSection('output')}
          >
            <span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Information Messages ({messages.info.length})
            </span>
            <svg 
              className={`chevron ${expandedSections.output ? 'expanded' : ''}`}
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.output && (
            <div className="message-list">
              {messages.info.map((msg, idx) => (
                <div key={idx} className="message-item info">
                  {msg}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {validation_errors && (
        <div className="message-section error-section">
          <button
            className="section-toggle"
            onClick={() => toggleSection('errors')}
          >
            <span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              System Errors
            </span>
            <svg 
              className={`chevron ${expandedSections.errors ? 'expanded' : ''}`}
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.errors && (
            <pre className="error-details">{validation_errors}</pre>
          )}
        </div>
      )}

      <div className="results-actions">
        <button 
          className="action-btn secondary"
          onClick={() => {
            const dataStr = JSON.stringify(results, null, 2)
            const dataBlob = new Blob([dataStr], { type: 'application/json' })
            const url = URL.createObjectURL(dataBlob)
            const link = document.createElement('a')
            link.href = url
            link.download = `validation-results-${Date.now()}.json`
            link.click()
            URL.revokeObjectURL(url)
          }}
        >
          Download Results (JSON)
        </button>
      </div>
    </div>
  )
}

export default ValidationResults
