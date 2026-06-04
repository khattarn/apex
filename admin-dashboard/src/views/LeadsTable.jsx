import { useCallback, useEffect, useRef, useState } from 'react'
import { ExternalLink, Eye, Send, Edit3, ChevronLeft, ChevronRight, X, Phone, Mail, RefreshCw } from 'lucide-react'
import { getLeads, patchLead, deleteLead, previewMessage, sendToLead, callLead, streamEnrich, emailLead, streamEmailCampaign } from '../api'
import StatusBadge from '../components/StatusBadge'

const PAGE_SIZE = 25
const BUSINESS_TYPES = ['dentist', 'salon', 'accountant', 'physiotherapist', 'lawyer']
const STATUSES = ['new', 'contacted', 'replied', 'converted', 'dead']

function Modal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1e293b] border border-slate-700 rounded-lg w-full max-w-md p-5 shadow-xl"
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
  const [filters, setFilters] = useState({ business_type: '', status: '', city: '', outreach_sent: '' })
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [preview, setPreview] = useState(null)
  const [editNotes, setEditNotes] = useState(null)
  const [notesVal, setNotesVal] = useState('')
  const [enrich, setEnrich] = useState(null)   // null | { running, logs, done }
  const enrichAbort = useRef(null)
  const [campaign, setCampaign] = useState(null) // null | { running, logs, done }
  const campaignAbort = useRef(null)
  const searchTimer = useRef(null)

  const load = useCallback(() => {
    setLoading(true)
    const params = {
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      ...(filters.business_type && { business_type: filters.business_type }),
      ...(filters.status && { status: filters.status }),
      ...(filters.city && { city: filters.city }),
      ...(filters.outreach_sent !== '' && { outreach_sent: filters.outreach_sent === 'true' }),
      ...(search && { search }),
    }
    getLeads(params)
      .then((res) => { setLeads(res.data || []); setCount(res.count || 0) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page, filters, search])

  useEffect(() => { load() }, [load])

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

  async function saveNotes() {
    if (!editNotes) return
    await patchLead(editNotes.id, { notes: notesVal })
    setEditNotes(null)
    load()
  }

  const totalPages = Math.ceil(count / PAGE_SIZE)

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-base font-semibold">Leads</h2>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          placeholder="Search name or city…"
          onChange={(e) => handleSearch(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <select
          onChange={(e) => setFilter('business_type', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All types</option>
          {BUSINESS_TYPES.map((t) => <option key={t} value={t} className="capitalize">{t}</option>)}
        </select>
        <select
          onChange={(e) => setFilter('status', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          onChange={(e) => setFilter('outreach_sent', e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">Outreach — all</option>
          <option value="true">Sent</option>
          <option value="false">Not sent</option>
        </select>
        <div className="ml-auto flex items-center gap-3">
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

      {/* Table */}
      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
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
                  <td className="px-4 py-2.5"><StatusBadge status={lead.status} /></td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.outreach_sent
                      ? <span className="text-green-400">Sent</span>
                      : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.email_bounced
                      ? <span className="text-red-400" title="Email bounced">Bounced</span>
                      : lead.email_clicked
                        ? <span className="text-green-400" title="Clicked a link">Clicked</span>
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
                          title="Place voice call"
                          className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-indigo-400 transition-colors"
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
