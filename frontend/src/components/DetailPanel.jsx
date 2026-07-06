import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function DetailPanel({ regulation, onReviewed }) {
  const [audit, setAudit] = useState([])

  useEffect(() => {
    if (!regulation) return
    api.getAuditTrail(regulation.id).then(setAudit).catch(console.error)
  }, [regulation?.id])

  if (!regulation) {
    return <div className="detail-panel"><div className="detail-empty">Select a signal to inspect the agent's reasoning and audit trail.</div></div>
  }

  const handleReview = async () => {
    await api.markReviewed(regulation.id)
    onReviewed()
  }

  return (
    <div className="detail-panel">
      <div className="detail-meta">
        <span className={`badge ${regulation.urgency || 'neutral'}`}>{regulation.urgency || 'unscored'}</span>
        <span className="badge neutral">{regulation.domain || 'unclassified'}</span>
        <span className="badge neutral">{regulation.source}</span>
      </div>

      <div className="detail-title">{regulation.title}</div>
      <a className="source-link" href={regulation.url} target="_blank" rel="noreferrer">
        VIEW SOURCE DOCUMENT →
      </a>

      <div className="detail-section-label">Executive Summary</div>
      <div className="detail-body">{regulation.summary || 'Not yet processed.'}</div>

      <div className="detail-section-label">Impact Analysis</div>
      <div className="detail-body">{regulation.impact_analysis || 'Not yet processed.'}</div>

      <div className="detail-section-label">Agent Audit Trail</div>
      {audit.length === 0 && <div className="detail-body" style={{ color: 'var(--text-faint)' }}>No agent runs logged yet.</div>}
      {audit.map((step) => (
        <div key={step.id} className="audit-step">
          <div className="audit-step-header">
            <span>{step.agent_name.toUpperCase()}</span>
            <span>{step.model_used}</span>
          </div>
          <div className="audit-step-output">{step.output_snapshot}</div>
        </div>
      ))}

      <button
        className={`review-btn ${regulation.reviewed ? 'done' : ''}`}
        onClick={handleReview}
        disabled={regulation.reviewed}
      >
        {regulation.reviewed ? '✓ REVIEWED BY ANALYST' : 'MARK AS REVIEWED'}
      </button>
    </div>
  )
}
