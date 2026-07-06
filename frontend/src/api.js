const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.status === 204 ? null : res.json()
}

export const api = {
  listRegulations: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/regulations${qs ? `?${qs}` : ''}`)
  },
  getRegulation: (id) => request(`/regulations/${id}`),
  getAuditTrail: (id) => request(`/regulations/${id}/audit`),
  markReviewed: (id) => request(`/regulations/${id}/review`, { method: 'POST' }),
  listAlerts: (acknowledged) =>
    request(`/alerts${acknowledged !== undefined ? `?acknowledged=${acknowledged}` : ''}`),
  acknowledgeAlert: (id) => request(`/alerts/${id}/acknowledge`, { method: 'POST' }),
  runIngestNow: () => request('/ingest/run', { method: 'POST' }),
  getIngestStatus: () => request('/ingest/status'),
}
