import React, { useState } from 'react'
import { api } from '../api'

export default function TopBar({ pendingAlerts, lastRun, onRefresh }) {
  const [running, setRunning] = useState(false)

  const handleRun = async () => {
    setRunning(true)
    try {
      await api.runIngestNow()
      onRefresh()
    } catch (e) {
      console.error(e)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="topbar">
      <div className="topbar-brand">
        <span className="dot" />
        INDGOVWATCH
      </div>
      <div className="topbar-status">
        <span>PENDING ALERTS: {pendingAlerts}</span>
        <span>LAST CYCLE: {lastRun || '—'}</span>
        <button className="btn-primary" onClick={handleRun} disabled={running}>
          {running ? 'RUNNING…' : 'RUN INGESTION NOW'}
        </button>
      </div>
    </div>
  )
}
