import { useEffect, useState, useCallback } from 'react'
import { Phone, PhoneIncoming, PhoneOutgoing, PhoneMissed, ExternalLink, ChevronDown, ChevronUp, Headphones } from 'lucide-react'
import { getCallSessions } from '../api'
import StatusBadge from '../components/StatusBadge'

const OUTCOME_STYLE = {
  booked_demo:     { label: 'Demo Booked',    cls: 'bg-green-900/50 text-green-400' },
  interested:      { label: 'Interested',      cls: 'bg-green-900/50 text-green-400' },
  not_interested:  { label: 'Not Interested',  cls: 'bg-slate-800 text-slate-500 border border-slate-700' },
  voicemail:       { label: 'Voicemail',       cls: 'bg-slate-800 text-slate-400 border border-slate-700' },
  no_answer:       { label: 'No Answer',       cls: 'bg-slate-800 text-slate-400 border border-slate-700' },
  callback_later:  { label: 'Call Back Later', cls: 'bg-amber-900/50 text-amber-400' },
  question:        { label: 'Had Question',    cls: 'bg-blue-900/50 text-blue-400' },
  unknown:         { label: 'No Outcome',      cls: 'bg-slate-800 text-slate-500 border border-slate-700' },
  '':              { label: 'No Outcome',      cls: 'bg-slate-800 text-slate-500 border border-slate-700' },
}

function OutcomeBadge({ outcome }) {
  const key = outcome || ''
  const { label, cls } = OUTCOME_STYLE[key] || OUTCOME_STYLE['unknown']
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${cls}`}>
      {label}
    </span>
  )
}

function CallTypeIcon({ type }) {
  if (type === 'inbound_call')
    return <PhoneIncoming size={13} className="text-purple-400" />
  if (type === 'voice_followup_placed' || type === 'outbound_call')
    return <PhoneOutgoing size={13} className="text-blue-400" />
  return <Phone size={13} className="text-slate-400" />
}

function fmtDate(ts) {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
function fmtTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}
function fmtDay(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

function groupByDay(rows) {
  const groups = {}
  for (const r of rows) {
    const day = new Date(r.called_at).toDateString()
    if (!groups[day]) groups[day] = []
    groups[day].push(r)
  }
  return Object.entries(groups).map(([day, items]) => ({ day, items }))
}

function SessionRow({ row }) {
  const [expanded, setExpanded] = useState(false)
  const hasDetail = !!row.summary

  return (
    <>
      <tr
        className={`border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors ${hasDetail ? 'cursor-pointer' : ''}`}
        onClick={() => hasDetail && setExpanded(e => !e)}
      >
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-2">
            <CallTypeIcon type={row.call_type} />
            <div>
              <div className="text-sm font-medium text-white leading-tight">{row.lead_name}</div>
              <div className="text-[11px] text-slate-500">{row.phone}</div>
            </div>
          </div>
        </td>
        <td className="px-4 py-2.5 text-slate-400 text-sm hidden sm:table-cell">
          {row.city}
        </td>
        <td className="px-4 py-2.5 hidden md:table-cell">
          <span className="text-[11px] text-slate-400 capitalize">{row.business_type}</span>
        </td>
        <td className="px-4 py-2.5">
          <OutcomeBadge outcome={row.outcome} />
        </td>
        <td className="px-4 py-2.5 hidden sm:table-cell">
          <StatusBadge status={row.lead_status} />
        </td>
        <td className="px-4 py-2.5 text-slate-500 text-xs whitespace-nowrap">
          {fmtTime(row.called_at)}
        </td>
        <td className="px-4 py-2.5 text-center">
          {row.recording_url ? (
            <a
              href={row.recording_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              className="text-indigo-400 hover:text-indigo-300 transition-colors"
              title="Listen to recording"
            >
              <Headphones size={14} />
            </a>
          ) : (
            <span className="text-slate-700"><Headphones size={14} /></span>
          )}
        </td>
        <td className="px-4 py-2.5 text-slate-600 text-xs w-6">
          {row.summary && (expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
        </td>
      </tr>
      {expanded && hasDetail && (
        <tr className="border-b border-slate-800/60 bg-slate-900/40">
          <td colSpan={8} className="px-6 py-3">
            <p className="text-[12px] text-slate-300 leading-relaxed">{row.summary}</p>
            {row.dograh_run_id && (
              <span className="text-[10px] text-slate-600 mt-1 block">Run ID: {row.dograh_run_id}</span>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

function DayGroup({ day, items }) {
  const booked    = items.filter(r => r.outcome === 'booked_demo' || r.outcome === 'interested').length
  const negative  = items.filter(r => r.outcome === 'not_interested').length
  const noOutcome = items.filter(r => !r.outcome || r.outcome === 'unknown').length

  return (
    <div className="bg-[#1e293b] border border-slate-700/40 rounded-xl overflow-hidden mb-4">
      {/* Day header */}
      <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between flex-wrap gap-2">
        <div className="text-sm font-semibold text-white">{fmtDay(items[0]?.called_at)}</div>
        <div className="flex gap-3 text-[11px]">
          <span className="text-slate-400">{items.length} calls</span>
          {booked > 0   && <span className="text-green-400">● {booked} interested</span>}
          {negative > 0 && <span className="text-slate-500">✕ {negative} declined</span>}
          {noOutcome > 0 && <span className="text-slate-600">○ {noOutcome} no outcome</span>}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[480px]">
          <thead>
            <tr className="border-b border-slate-700/40 text-slate-500 text-[11px]">
              <th className="text-left px-4 py-2 font-medium">Lead</th>
              <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">City</th>
              <th className="text-left px-4 py-2 font-medium hidden md:table-cell">Type</th>
              <th className="text-left px-4 py-2 font-medium">Outcome</th>
              <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">Status</th>
              <th className="text-left px-4 py-2 font-medium">Time</th>
              <th className="text-center px-4 py-2 font-medium"><Headphones size={12} /></th>
              <th className="w-6" />
            </tr>
          </thead>
          <tbody>
            {items.map(row => <SessionRow key={row.activity_id} row={row} />)}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function CallSessions() {
  const [rows, setRows]       = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [page, setPage]       = useState(0)
  const PAGE = 100

  const load = useCallback((p) => {
    setLoading(true)
    getCallSessions({ limit: PAGE, offset: p * PAGE })
      .then(r => { setRows(r.data || []); setTotal(r.total || 0) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load(page) }, [load, page])

  const groups = groupByDay(rows)

  // Summary stats
  const booked   = rows.filter(r => r.outcome === 'booked_demo' || r.outcome === 'interested').length
  const declined = rows.filter(r => r.outcome === 'not_interested').length
  const noData   = rows.filter(r => !r.outcome || r.outcome === 'unknown').length

  return (
    <div className="p-4 md:p-6 space-y-5 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-base font-semibold">Call Sessions</h2>
        <span className="text-sm text-slate-400">{total} total calls logged</span>
      </div>

      {/* No-outcome notice */}
      {noData > 0 && noData === rows.length && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg px-4 py-3 text-[12px] text-amber-300 leading-relaxed">
          <strong>Note:</strong> These {rows.length} calls were placed on June 16–17 but no outcomes were captured —
          the Dograh end-of-call webhook was not delivering results back to Railway at that time.
          Recordings and transcripts are available directly in the{' '}
          <span className="text-amber-400 font-medium">Dograh dashboard</span>.
          Outcomes will appear here automatically for all calls going forward.
        </div>
      )}

      {/* Stats strip */}
      {rows.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { val: total,   label: 'Calls placed',    color: 'text-white' },
            { val: booked,  label: 'Interested / Demo booked', color: 'text-green-400' },
            { val: declined,label: 'Not interested',   color: 'text-slate-400' },
            { val: noData,  label: 'No outcome data',  color: 'text-slate-500' },
          ].map(s => (
            <div key={s.label} className="bg-[#1e293b] border border-slate-700/40 rounded-lg px-4 py-3">
              <div className={`text-2xl font-bold ${s.color}`}>{s.val}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {loading && <p className="text-slate-400 text-sm py-8 text-center">Loading…</p>}
      {error   && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && rows.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <Phone size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No call sessions yet</p>
          <p className="text-xs mt-1 text-slate-600">Calls will appear here as Sophie, Henry, and Priya place or receive them</p>
        </div>
      )}

      {groups.map(({ day, items }) => (
        <DayGroup key={day} day={day} items={items} />
      ))}

      {/* Pagination */}
      {total > PAGE && (
        <div className="flex justify-center gap-3 pt-2">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-400 disabled:opacity-30 hover:bg-slate-700 transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-slate-500 self-center">
            Page {page + 1} of {Math.ceil(total / PAGE)}
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={(page + 1) * PAGE >= total}
            className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-400 disabled:opacity-30 hover:bg-slate-700 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
