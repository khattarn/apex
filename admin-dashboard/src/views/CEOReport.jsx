// CEO Report — every live conversation that produced an actionable outcome
// (a callback, a callback request, or a demo booking), with full transcript,
// recording, and whether the promised follow-up has actually happened.
import { useEffect, useState, useCallback } from 'react'
import { Phone, Mail, MapPin, ChevronDown, ChevronUp, CalendarClock, CheckCircle2, AlertTriangle } from 'lucide-react'
import { getCeoReport } from '../api'
import StatusBadge from '../components/StatusBadge'

const OUTCOME_LABEL = {
  callback_scheduled:   '📞 Callback scheduled',
  callback_requested:   '📞 Callback requested',
  booked_demo:          '🎉 Demo booked',
  booked_demo_manually: '🎉 Demo booked (manual)',
}

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function FollowUpBadge({ row }) {
  if (!row.callback_at) return null
  const isPast = new Date(row.callback_at) < new Date()
  if (row.followed_up) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-green-400">
        <CheckCircle2 size={12} /> Followed up
      </span>
    )
  }
  if (isPast) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400">
        <AlertTriangle size={12} /> Callback time passed — no follow-up call logged
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400">
      <CalendarClock size={12} /> Callback pending
    </span>
  )
}

function ReportCard({ row }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-[#1e293b] border border-slate-700/40 rounded-xl overflow-hidden">
      <div
        className="px-4 py-3 flex items-start justify-between gap-3 flex-wrap cursor-pointer hover:bg-slate-800/30 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-white">{row.lead_name}</span>
            <StatusBadge status={row.lead_status} />
            <span className="text-[11px] text-slate-500 capitalize">{row.business_type}</span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500 flex-wrap">
            {row.phone && (
              <a href={`tel:${row.phone}`} onClick={e => e.stopPropagation()} className="inline-flex items-center gap-1 hover:text-indigo-400">
                <Phone size={11} /> {row.phone}
              </a>
            )}
            {row.email && (
              <a href={`mailto:${row.email}`} onClick={e => e.stopPropagation()} className="inline-flex items-center gap-1 hover:text-indigo-400">
                <Mail size={11} /> {row.email}
              </a>
            )}
            {row.city && (
              <span className="inline-flex items-center gap-1"><MapPin size={11} /> {row.city}</span>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-[11px] font-semibold text-white whitespace-nowrap">
            {OUTCOME_LABEL[row.outcome] || row.outcome}
          </span>
          {row.preferred_day && (
            <span className="text-[11px] text-slate-400">
              Call back: {row.preferred_day} {row.preferred_time}
            </span>
          )}
          <FollowUpBadge row={row} />
          <span className="text-[10px] text-slate-600">{fmt(row.occurred_at)}</span>
        </div>
        <div className="text-slate-600">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-800/60 pt-3 space-y-3">
          {row.summary && (
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1">AI call summary</div>
              <p className="text-[12px] text-slate-300 leading-relaxed">{row.summary}</p>
            </div>
          )}
          {row.transcript && (
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1">Full transcript</div>
              <pre className="text-[12px] text-slate-300 leading-relaxed whitespace-pre-wrap font-sans bg-slate-900/50 rounded-lg p-3 border border-slate-800/60">
                {row.transcript}
              </pre>
            </div>
          )}
          {row.recording_url && (
            <div>
              <div className="text-[11px] font-semibold text-slate-400 mb-1">Recording</div>
              <audio controls src={row.recording_url} className="w-full h-9" />
            </div>
          )}
          {row.ended_reason && (
            <div className="text-[10px] text-slate-600">Call ended: {row.ended_reason}</div>
          )}
        </div>
      )}
    </div>
  )
}

export default function CEOReport() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    getCeoReport()
      .then(r => setRows(r.data || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const pendingFollowUp = rows.filter(r => r.callback_at && !r.followed_up && new Date(r.callback_at) < new Date()).length
  const demosBooked = rows.filter(r => r.outcome === 'booked_demo' || r.outcome === 'booked_demo_manually').length

  return (
    <div className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">
      <div>
        <h2 className="text-base font-semibold">CEO Report — Productive Conversations</h2>
        <p className="text-[12px] text-slate-500 mt-1">
          Every outbound call where a real person engaged and something actionable happened —
          a callback, a callback request, or a demo booking. Not a log of every dial; see Call Sessions for that.
        </p>
      </div>

      {rows.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { val: rows.length,       label: 'Productive conversations', color: 'text-white' },
            { val: pendingFollowUp,   label: 'Overdue callbacks',        color: pendingFollowUp > 0 ? 'text-amber-400' : 'text-slate-400' },
            { val: demosBooked,       label: 'Demos booked',             color: 'text-green-400' },
          ].map(s => (
            <div key={s.label} className="bg-[#1e293b] border border-slate-700/40 rounded-lg px-4 py-3">
              <div className={`text-2xl font-bold ${s.color}`}>{s.val}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {loading && <p className="text-slate-400 text-sm py-8 text-center">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && rows.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <CalendarClock size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No productive conversations yet</p>
          <p className="text-xs mt-1 text-slate-600">This fills in as Sophie's calls result in callbacks or booked demos</p>
        </div>
      )}

      <div className="space-y-3">
        {rows.map(row => <ReportCard key={row.activity_id} row={row} />)}
      </div>
    </div>
  )
}
