import React, { useEffect, useState } from 'react'
import { api } from '../api'

function renderMarkdown(text) {
  if (!text) return '';

  // Escape HTML to prevent XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Convert Bold (**text** or __text__)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

  // Convert inline code (`code`)
  html = html.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');

  // Convert lines starting with "* " or "- " to bullet points
  const lines = html.split('\n');
  let inList = false;
  const processedLines = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inList) {
        processedLines.push('<ul class="markdown-list">');
        inList = true;
      }
      const itemContent = trimmed.substring(2);
      processedLines.push(`<li>${itemContent}</li>`);
    } else {
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      processedLines.push(line);
    }
  }

  if (inList) {
    processedLines.push('</ul>');
  }

  return processedLines.join('\n');
}

export default function DetailPanel({ regulation, onReviewed }) {
  const [audit, setAudit] = useState([])
  const [easyView, setEasyView] = useState(false)

  useEffect(() => {
    if (!regulation) return
    setEasyView(false)
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

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <a className="source-link" href={regulation.url} target="_blank" rel="noreferrer">
          VIEW SOURCE DOCUMENT →
        </a>
      </div>

      <div className="easy-view-container">
        <span className="easy-view-label">
          ✨ Easy View (Public)
          <span
            className="info-icon"
            data-tooltip="Swaps between complex technical/legal drafts and plain English explanations highlighting direct everyday citizen impact."
          >
            i
          </span>
        </span>
        <label className="switch">
          <input
            type="checkbox"
            checked={easyView}
            onChange={(e) => setEasyView(e.target.checked)}
          />
          <span className="slider"></span>
        </label>
      </div>

      {/* Simplified Public View */}
      <div className={`easy-view-content ${!easyView ? 'hidden' : ''}`}>
        <div className="detail-section-label">Simplified Headline</div>
        <div
          className="easy-headline"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(regulation.easy_view_headline || 'Not yet processed.') }}
        />

        <div className="detail-section-label">Public Impact & Explanation</div>
        <div
          className="easy-explanation"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(regulation.easy_view_explanation || 'Not yet processed.') }}
        />
      </div>

      {/* Technical Analyst View */}
      <div className={`easy-view-content ${easyView ? 'hidden' : ''}`}>
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
      </div>

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
