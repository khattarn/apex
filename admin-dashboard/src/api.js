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
    return new Promise(() => {})  // hang until reload; prevents callers from destructuring undefined
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

export const fetchAgentStats = (token) => request('/api/agents/stats')

export const fetchProductStats = (token) => request('/api/products/stats')

export const previewEmail = (emailNum, businessType, market) =>
  request(`/api/preview/email?email_num=${emailNum}&business_type=${businessType}&market=${market}`)

export const clearAllLeads = () =>
  request('/api/admin/leads', { method: 'DELETE' })

export const resetOutreach = () =>
  request('/api/admin/reset-outreach', { method: 'POST' })

export const createLead = (data) => request('/api/leads', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

export const callLead = (id) => request(`/api/leads/${id}/call`, { method: 'POST' })

export const getLeadActivities = (id) => request(`/api/leads/${id}/activities`)

export const fetchTwilioToken = () => request('/api/twilio/token')

export const startBridgeCall = (to) =>
  request('/api/bridge/call', { method: 'POST', body: JSON.stringify({ to }) })

export const getBridgeStatus = (bridgeId) =>
  request(`/api/bridge/status/${bridgeId}`)

export const getTemplateStatuses = () => request('/api/templates')

export const submitTemplates = (name = 'all') =>
  request('/api/templates/submit', { method: 'POST', body: JSON.stringify({ name }) })

export function streamEnrich(onLine, onDone, onError) {
  const token = localStorage.getItem('pd_token')
  const ctrl = new AbortController()

  fetch(`${BASE}/api/leads/enrich-emails`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
    },
    signal: ctrl.signal,
  })
    .then((res) => {
      if (!res.ok) throw new Error('Enrich request failed')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let resolved = false
      function processBuffer(flush) {
        const parts = buffer.split(/\r?\n\r?\n/)
        buffer = flush ? '' : parts.pop()
        for (const part of parts) {
          const dataLine = part.split('\n').find((l) => l.startsWith('data:'))
          if (!dataLine) continue
          try {
            const msg = JSON.parse(dataLine.slice(5).trim())
            if (msg.type === 'log') onLine(msg.line)
            else if (msg.type === 'done') { resolved = true; onDone(msg) }
            else if (msg.type === 'error') { resolved = true; onError(msg.message) }
          } catch { /* ignore malformed */ }
        }
      }
      function read() {
        reader.read().then(({ done, value }) => {
          if (value) buffer += decoder.decode(value, { stream: !done })
          processBuffer(done)
          if (done) { if (!resolved) onDone({}); return }
          read()
        })
      }
      read()
    })
    .catch((err) => { if (err.name !== 'AbortError') onError(err.message) })

  return () => ctrl.abort()
}

export const emailLead = (id) => request(`/api/leads/${id}/email`, { method: 'POST' })

export function streamEmailCampaign(onLine, onDone, onError) {
  const token = localStorage.getItem('pd_token')
  const ctrl = new AbortController()

  fetch(`${BASE}/api/leads/email-campaign`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
    },
    signal: ctrl.signal,
  })
    .then((res) => {
      if (!res.ok) throw new Error('Email campaign request failed')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let resolved = false
      function processBuffer(flush) {
        const parts = buffer.split(/\r?\n\r?\n/)
        buffer = flush ? '' : parts.pop()
        for (const part of parts) {
          const dataLine = part.split('\n').find((l) => l.startsWith('data:'))
          if (!dataLine) continue
          try {
            const msg = JSON.parse(dataLine.slice(5).trim())
            if (msg.type === 'log') onLine(msg.line)
            else if (msg.type === 'done') { resolved = true; onDone(msg) }
            else if (msg.type === 'error') { resolved = true; onError(msg.message) }
          } catch { /* ignore malformed */ }
        }
      }
      function read() {
        reader.read().then(({ done, value }) => {
          if (value) buffer += decoder.decode(value, { stream: !done })
          processBuffer(done)
          if (done) { if (!resolved) onDone({}); return }
          read()
        })
      }
      read()
    })
    .catch((err) => { if (err.name !== 'AbortError') onError(err.message) })

  return () => ctrl.abort()
}

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
      let resolved = false
      function processBuffer(flush) {
        const parts = buffer.split(/\r?\n\r?\n/)
        buffer = flush ? '' : parts.pop()
        for (const part of parts) {
          const dataLine = part.split('\n').find((l) => l.startsWith('data:'))
          if (!dataLine) continue
          try {
            const msg = JSON.parse(dataLine.slice(5).trim())
            if (msg.type === 'log') onLine(msg.line)
            else if (msg.type === 'done') { resolved = true; onDone(msg) }
            else if (msg.type === 'error') { resolved = true; onError(msg.message) }
          } catch { /* ignore malformed */ }
        }
      }
      function read() {
        reader.read().then(({ done, value }) => {
          if (value) buffer += decoder.decode(value, { stream: !done })
          processBuffer(done)
          if (done) { if (!resolved) onDone({}); return }
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

export const getWaInbox = () => request('/api/inbox/wa')
export const replyWaInbox = (id, text) =>
  request(`/api/inbox/wa/${id}/reply`, { method: 'POST', body: JSON.stringify({ text }) })
export const markWaRead = (id) =>
  request(`/api/inbox/wa/${id}/reply`, { method: 'POST', body: JSON.stringify({ text: '' }) })

export const getActiveCalls = () => request('/api/active-calls')
export const getCalledIds = () => request('/api/leads/called-ids')
export const getCallSessions = (params = {}) => {
  const q = new URLSearchParams(params).toString()
  return request(`/api/call-sessions${q ? '?' + q : ''}`)
}

export const getLiveActivity = () => request('/api/activity/live')
export const getObservatoryLatest = () => request('/api/observatory/latest')

export function streamWaBlast(payload, onLine, onDone, onError) {
  const token = localStorage.getItem('pd_token')
  const ctrl  = new AbortController()

  fetch(`${BASE}/api/leads/wa-blast`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
    body:    JSON.stringify(payload),
    signal:  ctrl.signal,
  })
    .then(res => {
      if (!res.ok) throw new Error('WA blast request failed')
      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let resolved = false
      function processBuffer(flush) {
        const parts = buffer.split(/\r?\n\r?\n/)
        buffer = flush ? '' : parts.pop()
        for (const part of parts) {
          const dataLine = part.split('\n').find(l => l.startsWith('data:'))
          if (!dataLine) continue
          try {
            const msg = JSON.parse(dataLine.slice(5).trim())
            if (msg.type === 'log')   onLine(msg.line)
            else if (msg.type === 'done')  { resolved = true; onDone(msg) }
            else if (msg.type === 'error') { resolved = true; onError(msg.message) }
          } catch { /* ignore */ }
        }
      }
      function read() {
        reader.read().then(({ done, value }) => {
          if (value) buffer += decoder.decode(value, { stream: !done })
          processBuffer(done)
          if (done) { if (!resolved) onDone({}); return }
          read()
        })
      }
      read()
    })
    .catch(err => { if (err.name !== 'AbortError') onError(err.message) })

  return () => ctrl.abort()
}

// ── Content Agent (Agent 8) ───────────────────────────────────────────────────

export const generateContent = (payload) =>
  request('/api/content/generate', { method: 'POST', body: JSON.stringify(payload) })

export const getContentModules = () => request('/api/content/modules')

// ── Agent 11: Affiliates ──────────────────────────────────────────────────────

export const getAffiliates = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
  ).toString()
  return request(`/api/affiliates${qs ? `?${qs}` : ''}`)
}

export const getAffiliateStats = () => request('/api/affiliates/stats')

export const inviteAffiliate = (id) =>
  request(`/api/affiliates/${id}/invite`, { method: 'POST' })

export const onboardAffiliate = (id, upi_id, bar_enrollment = '') =>
  request(`/api/affiliates/${id}/onboard`, {
    method: 'POST',
    body: JSON.stringify({ upi_id, bar_enrollment }),
  })

export const patchAffiliate = (id, data) =>
  request(`/api/affiliates/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

export const getCommissions = (status) => {
  const qs = status ? `?status=${status}` : ''
  return request(`/api/affiliates/commissions${qs}`)
}

export const payCommission = (id, notes = '') =>
  request(`/api/affiliates/commissions/${id}/pay`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  })

export const scrapeAffiliates = (maxPerHashtag = 30) =>
  request(`/api/affiliates/scrape?max_per_hashtag=${maxPerHashtag}`, { method: 'POST' })
