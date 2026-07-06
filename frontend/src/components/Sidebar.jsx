import React from 'react'

const URGENCIES = ['high', 'medium', 'low']
const DOMAINS = ['banking & finance', 'taxation', 'agriculture', 'defence', 'healthcare', 'education', 'infrastructure', 'digital & IT', 'environment', 'foreign affairs', 'other']

export default function Sidebar({ filters, setFilters, counts }) {
  const toggle = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: prev[key] === value ? null : value }))
  }

  return (
    <div className="sidebar">
      <div className="sidebar-section">
        <div className="sidebar-label">Urgency</div>
        {URGENCIES.map((u) => (
          <div
            key={u}
            className={`filter-option ${filters.urgency === u ? 'active' : ''}`}
            onClick={() => toggle('urgency', u)}
          >
            <span style={{ textTransform: 'capitalize' }}>{u}</span>
            <span className="count">{counts.urgency?.[u] || 0}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Domain</div>
        {DOMAINS.map((d) => (
          <div
            key={d}
            className={`filter-option ${filters.domain === d ? 'active' : ''}`}
            onClick={() => toggle('domain', d)}
          >
            <span style={{ textTransform: 'capitalize' }}>{d}</span>
            <span className="count">{counts.domain?.[d] || 0}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
