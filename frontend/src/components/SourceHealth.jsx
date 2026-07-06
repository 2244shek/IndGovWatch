import React, { useEffect, useState } from 'react'
import { api } from '../api'

const LABELS = {
  pib: 'PIB',
  rbi_notifications: 'RBI NOTIF',
  rbi_press: 'RBI PRESS',
  sebi: 'SEBI',
  egazette: 'E-GAZETTE',
}

export default function SourceHealth({ refreshKey }) {
  const [logs, setLogs] = useState([])

  useEffect(() => {
    api.getIngestStatus().then(setLogs).catch(console.error)
  }, [refreshKey])

  if (!logs.length) return null

  return (
    <div className="source-health">
      {logs.map((log) => (
        <div key={log.id} className={`source-health-item ${log.status}`} title={log.error_message || `${log.item_count} items`}>
          <span className={`source-health-dot ${log.status}`} />
          <span className="source-health-label">{LABELS[log.source] || log.source}</span>
          <span className="source-health-detail">
            {log.status === 'ok' ? `${log.item_count} items` : 'failed'}
          </span>
        </div>
      ))}
    </div>
  )
}
