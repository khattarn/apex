import { useCallback, useEffect, useRef, useState } from 'react'
import { ExternalLink, Eye, Send, Edit3, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { getLeads, patchLead, deleteLead, previewMessage, sendToLead } from '../api'
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
        <p className="ml-auto text-xs text-slate-500 self-center">{count} leads</p>
      </div>

      {/* Table */}
      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead>
              <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
                {['Name', 'City', 'Type', 'Phone', 'Website', 'Status', 'Outreach', 'Added', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-500 text-xs">Loading…</td></tr>
              )}
              {!loading && leads.length === 0 && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-500 text-xs">No leads found</td></tr>
              )}
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-2.5 font-medium max-w-[160px] truncate">{lead.name}</td>
                  <td className="px-4 py-2.5 text-slate-400">{lead.city}</td>
                  <td className="px-4 py-2.5 text-slate-400 capitalize">{lead.business_type}</td>
                  <td className="px-4 py-2.5 text-slate-400 text-xs">{lead.phone || '—'}</td>
                  <td className="px-4 py-2.5">
                    {lead.website
                      ? <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-xs"><ExternalLink size={11} /> Link</a>
                      : <span className="text-slate-600 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-2.5"><StatusBadge status={lead.status} /></td>
                  <td className="px-4 py-2.5 text-xs">
                    {lead.outreach_sent
                      ? <span className="text-green-400">Sent</span>
                      : <span className="text-slate-600">No</span>}
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
