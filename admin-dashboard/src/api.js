const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function authHeaders() {
  const token = localStorage.getItem('pd_token')
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: authHeaders(),
    ...options,
  })
  if (res.status === 401) {
    localStorage.removeItem('pd_token')
    window.location.reload()
    return
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function login(email, password) {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error('Invalid credentials')
  return res.json()
}

export const getStats = () => request('/api/stats')

export const getLeads = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== '' && v !== null))
  ).toString()
  return request(`/api/leads${qs ? `?${qs}` : ''}`)
}

export const patchLead = (id, data) =>
  request(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

export const deleteLead = (id) => request(`/api/leads/${id}`, { method: 'DELETE' })

export const previewMessage = (lead_id) =>
  request('/api/message/preview', { method: 'POST', body: JSON.stringify({ lead_id }) })

export const sendToLead = (id) => request(`/api/leads/${id}/send`, { method: 'POST' })

export const getCampaigns = () => request('/api/campaigns')

export const getSetting = (key) => request(`/api/settings/${key}`)

export const putSetting = (key, value) =>
  request(`/api/settings/${key}`, { method: 'PUT', body: JSON.stringify({ value }) })

export const getHealth = () => request('/api/health')

export const clearAllLeads = () =>
  request('/api/admin/leads', { method: 'DELETE' })

export const resetOutreach = () =>
  request('/api/admin/reset-outreach', { method: 'POST' })

export function streamPipeline(payload, onLine, onDone, onError) {
  const token = localStorage.getItem('pd_token')
  const ctrl = new AbortController()

  fetch(`${BASE}/api/pipeline/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
    signal: ctrl.signal,
  })
    .then((res) => {
      if (!res.ok) throw new Error('Pipeline request failed')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) return
          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop()
          for (const part of parts) {
            const dataLine = part.split('\n').find((l) => l.startsWith('data:'))
            if (!dataLine) continue
            try {
              const msg = JSON.parse(dataLine.slice(5).trim())
              if (msg.type === 'log') onLine(msg.line)
              else if (msg.type === 'done') onDone(msg)
              else if (msg.type === 'error') onError(msg.message)
            } catch {
              // ignore malformed
            }
          }
          read()
        })
      }
      read()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message)
    })

  return () => ctrl.abort()
}
