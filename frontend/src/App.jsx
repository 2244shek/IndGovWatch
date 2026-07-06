import React, { useEffect, useMemo, useState, useCallback } from 'react'
import TopBar from './components/TopBar.jsx'
import Sidebar from './components/Sidebar.jsx'
import SignalFeed from './components/SignalFeed.jsx'
import DetailPanel from './components/DetailPanel.jsx'
import SourceHealth from './components/SourceHealth.jsx'
import { api } from './api'

export default function App() {
  const [regulations, setRegulations] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [filters, setFilters] = useState({ domain: null, urgency: null })
  const [lastRun, setLastRun] = useState(null)
  const [healthKey, setHealthKey] = useState(0)

  const load = useCallback(() => {
    const params = {}
    if (filters.domain) params.domain = filters.domain
    if (filters.urgency) params.urgency = filters.urgency
    api.listRegulations(params).then(setRegulations).catch(console.error)
    setLastRun(new Date().toLocaleTimeString())
    setHealthKey((k) => k + 1)
  }, [filters])

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000) // poll every 30s
    return () => clearInterval(interval)
  }, [load])

  const counts = useMemo(() => {
    const c = { urgency: {}, domain: {} }
    for (const r of regulations) {
      if (r.urgency) c.urgency[r.urgency] = (c.urgency[r.urgency] || 0) + 1
      if (r.domain) c.domain[r.domain] = (c.domain[r.domain] || 0) + 1
    }
    return c
  }, [regulations])

  const pendingAlerts = regulations.filter((r) => r.urgency === 'high' && !r.reviewed).length
  const selected = regulations.find((r) => r.id === selectedId) || null

  return (
    <div className="app-shell">
      <TopBar pendingAlerts={pendingAlerts} lastRun={lastRun} onRefresh={load} />
      <SourceHealth refreshKey={healthKey} />
      <Sidebar filters={filters} setFilters={setFilters} counts={counts} />
      <div className="main">
        <div className="feed">
          <div className="feed-header">
            <span>{regulations.length} SIGNALS</span>
          </div>
          <SignalFeed regulations={regulations} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
        <DetailPanel regulation={selected} onReviewed={load} />
      </div>
    </div>
  )
}
