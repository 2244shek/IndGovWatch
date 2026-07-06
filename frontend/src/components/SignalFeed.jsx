import React from 'react'

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export function SignalCard({ reg, selected, onClick, unacked }) {
  const urgency = reg.urgency || 'low'
  return (
    <div className={`signal-card ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="signal-card-top">
        <span className={`pulse-dot ${urgency} ${unacked ? 'unacked' : ''}`} />
        <span className="signal-source">{reg.source.replace('_', ' ')} · {timeAgo(reg.ingested_at)}</span>
        <span className="signal-domain">{reg.domain || 'unclassified'}</span>
      </div>
      <div className="signal-title">{reg.title}</div>
      <div className="signal-summary">{reg.summary || 'Processing…'}</div>
    </div>
  )
}

export default function SignalFeed({ regulations, selectedId, onSelect }) {
  if (!regulations.length) {
    return <div className="empty-state">No signals match the current filters yet.<br />Try running ingestion, or clear filters.</div>
  }
  return (
    <>
      {regulations.map((reg) => (
        <SignalCard
          key={reg.id}
          reg={reg}
          selected={reg.id === selectedId}
          unacked={reg.urgency === 'high' && !reg.reviewed}
          onClick={() => onSelect(reg.id)}
        />
      ))}
    </>
  )
}
