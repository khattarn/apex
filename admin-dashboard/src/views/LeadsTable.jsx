import { useCallback, useEffect, useRef, useState } from 'react'
import { ExternalLink, Eye, Send, Edit3, ChevronLeft, ChevronRight, X, Phone, Mail, RefreshCw, Activity } from 'lucide-react'
import { getLeads, patchLead, deleteLead, previewMessage, sendToLead, callLead, streamEnrich, emailLead, streamEmailCampaign, getLeadActivities, getCalledIds } from '../api'
import StatusBadge from '../components/StatusBadge'

const PAGE_SIZE = 25
const BUSINESS_TYPES = ['dentist', 'salon', 'accountant', 'physiotherapist', 'lawyer']
const STATUSES = ['new', 'contacted', 'replied', 'converted', 'dead']

function Modal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4" onClick={onClose}>
      <div
        className="bg-[#1e293b] border border-slate-700 rounded-lg w-full max-w-md p-5 shadow-xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium">{title}</p>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function LeadsTable() {
  const [leads, setLeads] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(0)
  const [filters, setFilters] = useState({ business_type: '', status: '', city: '', outreach_sent: '', email_engagement: '', voice_called: '' })
  const [calledIds, setCalledIds] = useState(new Set())
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [preview, setPreview] = useState(null)
  const [editNotes, setEditNotes] = useState(null)
  const [notesVal, setNotesVal] = useState('')
  const [activityModal, setActivityModal] = useState(null) // null | { lead, loading, items }
  const [enrich, setEnrich] = useState(null)   // null | { running, logs, done }
  const enrichAbort = useRef(null)
  const [campaign, setCampaign] = useState(null) // null | { running, logs, done }
  const campaignAbort = useRef(null)
  const searchTimer = useRef(null)

  const [loadError, setLoadError] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setLoadError(null)
    const params = {
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      ...(filters.business_type && { business_type: filters.business_type }),
      ...(filters.status && { status: filters.status }),
      ...(filters.city && { city: filters.city }),
      ...(filters.outreach_sent !== '' && { outreach_sent: filters.outreach_sent === 'true' }),
      ...(filters.email_engagement && { email_engagement: filters.email_engagement }),
      ...(filters.voice_called !== '' && { voice_called: filters.voice_called === 'true' }),
      ...(search && { search }),
    }

    getLeads(params)
      .then((res) => { setLeads(res.data || []); setCount(res.count || 0) })
      .catch((err) => { console.error(err); setLoadError(err.message || 'Failed to load leads') })
      .finally(() => setLoading(false))
  }, [page, filters.business_type, filters.status, filters.city, filters.outreach_sent, filters.email_engagement, filters.voice_called, search])

  useEffect(() => {
    getCalledIds().then(r => setCalledIds(new Set(r?.ids || []))).catch(() => {})
  }, [])

  useEffect(() => { load() }, [load])

  // cleanup timers and in-flight streams on unmount
  useEffect(() => () => {
    clearTimeout(searchTimer.current)
    enrichAbort.current?.()
    campaignAbort.current?.()
  }, [])

  function handleSearch(val) {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => { setSearch(val); setPage(0) }, 350)
  }

  function setFilter(key, val) {
    setFilters((f) => ({ ...f, [key]: val }))
    setPage(0)
  }

  async function openPreview(lead) {
    setPreview({ lead, loading: true, message: null, error: null })
    try {
      const { message } = await previewMessage(lead.id)
      setPreview((p) => ({ ...p, loading: false, message }))
    } catch (e) {
      setPreview((p) => ({ ...p, loading: false, error: e.message }))
    }
  }

  async function handleSend(lead) {
    if (!confirm(`Send WhatsApp message to ${lead.name}?`)) return
    try {
      await sendToLead(lead.id)
      load()
    } catch (e) {
      alert(`Failed: ${e.message}`)
    }
  }

  async function handleCall(lead) {
    if (!confirm(`Place outbound call to ${lead.name} at ${lead.phone}?`)) return
    try {
      await callLead(lead.id)
      load()
    } catch (e) {
      alert(`Call failed: ${e.message}`)
    }
  }

  function startEmailCampaign() {
    if (!confirm('Send personalised emails to all leads that have an email address?')) return
    setCampaign({ running: true, logs: [], done: null })
    campaignAbort.current = streamEmailCampaign(
      (line) => setCampaign((c) => ({ ...c, logs: [...c.logs, line] })),
      (result) => { setCampaign((c) => ({ ...c, running: false, done: result })); load() },
      (err) => setCampaign((c) => ({ ...c, running: false, logs: [...c.logs, `Error: ${err}`] })),
    )
  }

  function closeCampaign() {
    if (campaignAbort.current) campaignAbort.current()
    setCampaign(null)
  }

  async function handleEmailLead(lead) {
    if (!confirm(`Send email to ${lead.name} at ${lead.email}?`)) return
    try {
      await emailLead(lead.id)
      load()
    } catch (e) {
      alert(`Failed: ${e.message}`)
    }
  }

  function startEnrich() {
    if (!confirm('Scrape and validate emails for all leads with a website but no email?')) return
    setEnrich({ running: true, logs: [], done: null })
    enrichAbort.current = streamEnrich(
      (line) => setEnrich((e) => ({ ...e, logs: [...e.logs, line] })),
      (result) => { setEnrich((e) => ({ ...e, running: false, done: result })); load() },
      (err) => setEnrich((e) => ({ ...e, running: false, logs: [...e.logs, `Error: ${err}`] })),
    )
  }

  function closeEnrich() {
    if (enrichAbort.current) enrichAbort.current()
    setEnrich(null)
  }

  async function openActivity(lead) {
    setActivityModal({ lead, loading: true, items: [] })
    try {
      const res = await getLeadActivities(lead.id)
      setActivityModal((m) => ({ ...m, loading: false, items: res?.data || [] }))
    } catch (e) {
      setActivityModal((m) => ({ ...m, loading: false, error: e.message }))
    }
  }

  async function saveNotes() {
    if (!editNotes) return
    await patchLead(editNotes.id, { notes: notesVal })
    setEditNotes(null)
    load()
  }

  const totalPages = Math.ceil(count / PAGE_SIZE)

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h2 className="text-base font-semibold">Leads</h2>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          placeholder="Search name or city…"
          onChange={(e) => handleSearch(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-full sm:w-auto"
        />
        <select
          value={filters.business_type}
          onChange={(e) => setFilter('business_type', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All types</option>
          {BUSINESS_TYPES.map((t) => <option key={t} value={t} className="capitalize">{t}</option>)}
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilter('status', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={filters.outreach_sent}
          onChange={(e) => setFilter('outreach_sent', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">WA outreach — all</option>
          <option value="true">WA sent</option>
          <option value="false">WA not sent</option>
        </select>
        <select
          value={filters.email_engagement}
          onChange={(e) => setFilter('email_engagement', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">Email — all</option>
          <option value="clicked">Clicked a link</option>
          <option value="opened">Opened only</option>
          <option value="sent">Sent (any)</option>
        </select>
        <select
          value={filters.voice_called}
          onChange={(e) => setFilter('voice_called', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">Aria calls — all</option>
          <option value="true">Called by Aria</option>
          <option value="false">Not yet called</option>
        </select>
        <div className="flex items-center gap-3 flex-wrap sm:ml-auto">
          <button
            onClick={startEnrich}
            className="flex items-center gap-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-1.5 rounded transition-colors"
          >
            <RefreshCw size={12} />
            Enrich emails
          </button>
          <button
            onClick={startEmailCampaign}
            className="flex items-center gap-1.5 text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-3 py-1.5 rounded transition-colors"
          >
            <Mail size={12} />
            Email campaign
          </button>
          <p className="text-xs text-slate-500">{count} leads</p>
        </div>
      </div>

      {loadError && (
        <div className="text-xs text-red-400 bg-red-900/20 border border-red-700/40 rounded px-3 py-2">
          Filter error: {loadError}
        </div>
      )}

      {/* Mobile card list — shown below md */}
      <div className="md:hidden space-y-3">
        {loading && <p className="text-xs text-slate-500 text-center py-6">Loading…</p>}
        {!loading && leads.length === 0 && <p className="text-xs text-slate-500 text-center py-6">No leads found</p>}
        {leads.map((lead) => (
          <div key={lead.id} className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{lead.name}</p>
                <p className="text-xs text-slate-400 mt-0.5 capitalize">{lead.city} · {lead.business_type}</p>
              </div>
              <StatusBadge status={lead.status} />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
              {lead.phone && <span>{lead.phone}</span>}
              {lead.email
                ? <a href={`mailto:${lead.email}`} className="text-indigo-400 truncate max-w-[180px]">{lead.email}</a>
                : null}
              {lead.website
                ? <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-indigo-400 flex items-center gap-0.5"><ExternalLink size={10} /> Site</a>
                : null}
            </div>
            <div className="flex items-center gap-0.5 pt-1 border-t border-slate-700/40">
              <button onClick={() => openPreview(lead)} title="Preview message" className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-white transition-colors">
                <Eye size={13} />
              </button>
              {!lead.outreach_sent && (
                <button onClick={() => handleSend(lead)} title="Send WA" className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-green-400 transition-colors">
                  <Send size={13} />
                </button>
              )}
              {lead.phone && (
                <button onClick={() => handleCall(lead)} title="Call" className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-indigo-400 transition-colors">
                  <Phone size={13} />
                </button>
              )}
              {lead.email && (
                <button onClick={() => handleEmailLead(lead)} title="Send email" className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-indigo-400 transition-colors">
                  <Mail size={13} />
                </button>
              )}
              <button onClick={() => { setEditNotes(lead); setNotesVal(lead.notes || '') }} title="Edit notes" className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-white transition-colors">
                <Edit3 size={13} />
              </button>
              <button onClick={() => openActivity(lead)} title="Activity" className={`p-1.5 rounded transition-colors ${lead.status === 'replied' || lead.status === 'converted' ? 'text-indigo-400 hover:bg-slate-700' : 'text-slate-600 hover:bg-slate-700 hover:text-slate-400'}`}>
                <Activity size={13} />
              </button>
              <span className="ml-auto text-[11px] text-slate-600">{fmt(lead.created_at)}</span>
            </div>
          </div>
        ))}
        {totalPages > 1 && (
          <div className="flex items-center gap-3 justify-center py-2">
            <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} className="p-1.5 rounded text-slate-400 hover:bg-slate-700 disabled:opacity-30 transition-colors">
              <ChevronLeft size={16} />
            </button>
            <p className="text-xs text-slate-400">Page {page + 1} of {totalPages}</p>
            <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="p-1.5 rounded text-slate-400 hover:bg-slate-700 disabled:opacity-30 transition-colors">
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Table — hidden on mobile, shown on md+ */}
      <div className="hidden md:block bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead>
              <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
                {['Name', 'City', 'Type', 'Phone', 'Email', 'Website', 'Status', 'WA', 'Emailed', 'Added', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500 text-xs">Loading…</td></tr>
              )}
              {!loading && leads.length === 0 && (
                <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500 text-xs">No leads found</td></tr>
              )}
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-2.5 font-medium max-w-[160px] truncate">{lead.name}</td>
                  <td className="px-4 py-2.5 text-slate-400">{lead.city}</td>
                  <td className="px-4 py-2.5 text-slate-400 capitalize">{lead.business_type}</td>
                  <td className="px-4 py-2.5 text-slate-400 text-xs">{lead.phone || '—'}</td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.email
                      ? <a href={`mailto:${lead.email}`} className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1"><Mail size={11} />{lead.email}</a>
                      : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-2.5">
                    {lead.website
                      ? <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-xs"><ExternalLink size={11} /> Link</a>
                      : <span className="text-slate-600 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-2.5">
                    <select
                      value={lead.status}
                      onChange={async (e) => {
                        try {
                          await patchLead(lead.id, { status: e.target.value })
                          load()
                        } catch (err) {
                          alert(`Status update failed: ${err.message}`)
                        }
                      }}
                      className="bg-transparent border-0 text-xs cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500 rounded px-0"
                      style={{ color: { new:'#94a3b8', contacted:'#818cf8', replied:'#fbbf24', converted:'#4ade80', dead:'#f87171' }[lead.status] || '#94a3b8' }}
                    >
                      {STATUSES.map(s => <option key={s} value={s} className="bg-slate-800 text-white">{s}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.outreach_sent
                      ? <span className="text-green-400">Sent</span>
                      : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.email_bounced
                      ? <span className="text-red-400" title="Email bounced">Bounced</span>
                      : lead.email_clicked
                        ? (
                          <span className="text-green-400 cursor-help" title={lead.email_clicked_link ? `Clicked: ${lead.email_clicked_link}` : 'Clicked a link'}>
                            Clicked {lead.email_clicked_link && <span className="text-green-600">↗</span>}
                          </span>
                        )
                        : lead.email_opened
                          ? <span className="text-yellow-400" title="Opened email">Opened</span>
                          : lead.email_sent
                            ? <span className="text-indigo-400" title={lead.email_sent_date ? fmt(lead.email_sent_date) : ''}>Sent</span>
                            : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-2.5 text-slate-500 text-xs whitespace-nowrap">{fmt(lead.created_at)}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => openPreview(lead)}
                        title="Preview message"
                        className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        <Eye size={13} />
                      </button>
                      {!lead.outreach_sent && (
                        <button
                          onClick={() => handleSend(lead)}
                          title="Send now"
                          className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-green-400 transition-colors"
                        >
                          <Send size={13} />
                        </button>
                      )}
                      {lead.phone && (
                        <button
                          onClick={() => handleCall(lead)}
                          title={calledIds.has(String(lead.id)) ? 'Called by Aria — place another call' : 'Place voice call'}
                          className={`p-1.5 rounded transition-colors ${calledIds.has(String(lead.id)) ? 'text-green-400 hover:bg-slate-700' : 'text-slate-400 hover:bg-slate-700 hover:text-indigo-400'}`}
                        >
                          <Phone size={13} />
                        </button>
                      )}
                      {lead.email && (
                        <button
                          onClick={() => handleEmailLead(lead)}
                          title="Send email"
                          className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-indigo-400 transition-colors"
                        >
                          <Mail size={13} />
                        </button>
                      )}
                      <button
                        onClick={() => { setEditNotes(lead); setNotesVal(lead.notes || '') }}
                        title="Edit notes"
                        className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        <Edit3 size={13} />
                      </button>
                      <button
                        onClick={() => openActivity(lead)}
                        title="View activity"
                        className={`p-1.5 rounded transition-colors ${
                          lead.status === 'replied' || lead.status === 'converted'
                            ? 'text-indigo-400 hover:bg-slate-700'
                            : calledIds.has(String(lead.id)) || lead.email_clicked
                              ? 'text-sky-500 hover:bg-slate-700'
                              : 'text-slate-600 hover:bg-slate-700 hover:text-slate-400'
                        }`}
                      >
                        <Activity size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-slate-700/40 flex items-center gap-3">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded text-slate-400 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <p className="text-xs text-slate-400">Page {page + 1} of {totalPages}</p>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded text-slate-400 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Preview modal */}
      {preview && (
        <Modal title={`Message preview — ${preview.lead.name}`} onClose={() => setPreview(null)}>
          {preview.loading && <p className="text-xs text-slate-400">Generating…</p>}
          {preview.error && <p className="text-xs text-red-400">{preview.error}</p>}
          {preview.message && (
            <p className="text-sm text-slate-200 leading-6 bg-slate-800 rounded p-4 border border-slate-700">
              {preview.message}
            </p>
          )}
        </Modal>
      )}

      {/* Enrich debug modal */}
      {enrich && (
        <Modal title="Email Enrichment — Debug Log" onClose={closeEnrich}>
          <div className="bg-slate-900 rounded p-3 h-64 overflow-y-auto font-mono text-xs text-slate-300 space-y-0.5">
            {enrich.logs.map((line, i) => (
              <p key={i} className={
                line.includes('✓') ? 'text-green-400' :
                line.includes('✗') ? 'text-red-400' :
                line.startsWith('→') ? 'text-indigo-300 font-bold mt-1' :
                line.includes('Saved:') ? 'text-green-300' :
                line.includes('Error') ? 'text-red-400' :
                'text-slate-400'
              }>{line}</p>
            ))}
            {enrich.running && <p className="text-slate-500 animate-pulse">Running…</p>}
          </div>
          {enrich.done && (
            <div className="mt-3 text-xs flex gap-4">
              {enrich.done.enriched != null ? (
                <>
                  <span className="text-green-400">Enriched: {enrich.done.enriched}</span>
                  <span className="text-slate-400">Checked: {enrich.done.total}</span>
                </>
              ) : (
                <span className="text-slate-400">Complete — check Email column for results</span>
              )}
            </div>
          )}
          {!enrich.running && (
            <div className="flex justify-end mt-3">
              <button onClick={closeEnrich} className="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded transition-colors">
                Close
              </button>
            </div>
          )}
        </Modal>
      )}

      {/* Email campaign modal */}
      {campaign && (
        <Modal title="Email Campaign" onClose={closeCampaign}>
          <div className="bg-slate-900 rounded p-3 h-56 overflow-y-auto font-mono text-xs text-slate-300 space-y-0.5">
            {campaign.logs.map((line, i) => (
              <p key={i} className={line.includes('✓') ? 'text-green-400' : line.includes('✗') ? 'text-red-400' : ''}>{line}</p>
            ))}
            {campaign.running && <p className="text-slate-500 animate-pulse">Running…</p>}
          </div>
          {campaign.done && (
            <div className="mt-3 text-xs flex gap-4">
              {campaign.done.sent != null ? (
                <>
                  <span className="text-green-400">Sent: {campaign.done.sent}</span>
                  <span className="text-red-400">Failed: {campaign.done.failed}</span>
                  <span className="text-slate-400">Total: {campaign.done.total}</span>
                </>
              ) : (
                <span className="text-slate-400">Complete — check Campaigns tab for stats</span>
              )}
            </div>
          )}
          {!campaign.running && (
            <div className="flex justify-end mt-3">
              <button onClick={closeCampaign} className="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded transition-colors">
                Close
              </button>
            </div>
          )}
        </Modal>
      )}

      {/* Activity modal */}
      {activityModal && (
        <Modal title={`Activity — ${activityModal.lead.name}`} onClose={() => setActivityModal(null)}>
          {activityModal.loading && <p className="text-xs text-slate-400">Loading…</p>}
          {activityModal.error && <p className="text-xs text-red-400">{activityModal.error}</p>}
          {activityModal.lead.email_clicked && (
            <div className="mb-3 bg-green-900/30 border border-green-700/40 rounded p-2.5 text-xs">
              <p className="text-green-400 font-medium mb-0.5">Clicked email link</p>
              {activityModal.lead.email_clicked_link
                ? <a href={activityModal.lead.email_clicked_link} target="_blank" rel="noopener noreferrer" className="text-green-300 underline break-all">{activityModal.lead.email_clicked_link}</a>
                : <span className="text-green-600">Link not recorded</span>}
              {activityModal.lead.email_clicked_at && <p className="text-slate-500 mt-0.5">{fmt(activityModal.lead.email_clicked_at)}</p>}
            </div>
          )}
          {!activityModal.loading && activityModal.items.length === 0 && !activityModal.lead.email_clicked && (
            <p className="text-xs text-slate-500">No activity recorded yet.</p>
          )}
          <div className="space-y-3 max-h-72 overflow-y-auto">
            {activityModal.items.map((item) => {
              const d = item.detail || {}
              const ts = new Date(item.created_at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
              if (item.type === 'inbound_call') return (
                <div key={item.id} className="bg-slate-800 rounded p-3 text-xs space-y-1 border-l-2 border-indigo-500">
                  <div className="flex items-center justify-between">
                    <span className="text-indigo-300 font-medium flex items-center gap-1"><Phone size={11} /> Inbound call</span>
                    <span className="text-slate-500">{ts}</span>
                  </div>
                  {d.caller && <p className="text-slate-400">From: {d.caller}</p>}
                  {d.ended_reason && <p className="text-slate-400">Ended: {d.ended_reason}</p>}
                  {d.summary && <p className="text-slate-300 italic">"{d.summary}"</p>}
                  {d.recording_url && (
                    <a href={d.recording_url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 underline">
                      Listen to recording →
                    </a>
                  )}
                </div>
              )
              if (item.type === 'email_sent') return (
                <div key={item.id} className="bg-slate-800 rounded p-3 text-xs space-y-1 border-l-2 border-green-600">
                  <div className="flex items-center justify-between">
                    <span className="text-green-400 font-medium flex items-center gap-1"><Mail size={11} /> Email sent</span>
                    <span className="text-slate-500">{ts}</span>
                  </div>
                  {d.subject && <p className="text-slate-400">{d.subject}</p>}
                  {d.email_num != null && <p className="text-slate-500">Sequence #{d.email_num}</p>}
                </div>
              )
              if (item.type === 'outbound_call' || item.type === 'outbound_call_completed') return (
                <div key={item.id} className="bg-slate-800 rounded p-3 text-xs space-y-1 border-l-2 border-violet-500">
                  <div className="flex items-center justify-between">
                    <span className="text-violet-300 font-medium flex items-center gap-1"><Phone size={11} /> Outbound call {item.type === 'outbound_call_completed' ? '(completed)' : '(initiated)'}</span>
                    <span className="text-slate-500">{ts}</span>
                  </div>
                  {d.ended_reason && <p className="text-slate-400">Ended: {d.ended_reason}</p>}
                  {d.summary && <p className="text-slate-300 italic">"{d.summary}"</p>}
                  {d.transcript && <p className="text-slate-500 text-xs mt-1 max-h-20 overflow-y-auto whitespace-pre-wrap">{d.transcript}</p>}
                  {d.recording_url
                    ? <a href={d.recording_url} target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:text-violet-300 underline">Listen to recording →</a>
                    : item.type === 'outbound_call_completed' && <span className="text-slate-600">No recording</span>
                  }
                </div>
              )
              return (
                <div key={item.id} className="bg-slate-800 rounded p-3 text-xs border-l-2 border-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 font-medium capitalize">{item.type.replace(/_/g, ' ')}</span>
                    <span className="text-slate-500">{ts}</span>
                  </div>
                  {d.reason && <p className="text-slate-500">{d.reason}</p>}
                </div>
              )
            })}
          </div>
          <div className="flex justify-end mt-3">
            <button onClick={() => setActivityModal(null)} className="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded transition-colors">
              Close
            </button>
          </div>
        </Modal>
      )}

      {/* Edit notes modal */}
      {editNotes && (
        <Modal title={`Notes — ${editNotes.name}`} onClose={() => setEditNotes(null)}>
          <textarea
            value={notesVal}
            onChange={(e) => setNotesVal(e.target.value)}
            rows={4}
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            placeholder="Add notes…"
          />
          <div className="flex justify-end gap-2 mt-3">
            <button
              onClick={() => setEditNotes(null)}
              className="text-xs text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={saveNotes}
              className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded transition-colors"
            >
              Save
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}
