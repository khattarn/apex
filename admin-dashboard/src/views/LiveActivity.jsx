import { useEffect, useState, useRef } from 'react'
import {
  Send, MessageSquare, Phone, Mail, Calendar,
  CheckCircle, XCircle, Clock, RefreshCw, Activity,
  TrendingUp, Eye, MousePointer, Zap, Radio, AlarmClock,
} from 'lucide-react'
import { getLiveActivity } from '../api'

// ── Activity type config ───────────────────────────────────────────────────────

const ACT_CONFIG = {
  outreach_sent:           { icon: Send,          color: 'text-indigo-400',  label: 'WA Sent' },
  wa_followup_sent:        { icon: RefreshCw,      color: 'text-indigo-300',  label: 'WA Follow-up' },
  wa_reply_received:       { icon: MessageSquare,  color: 'text-green-400',   label: 'WA Reply' },
  email_sent:              { icon: Mail,           color: 'text-sky-400',     label: 'Email Sent' },
  email_opened:            { icon: Eye,            color: 'text-sky-300',     label: 'Email Opened' },
  email_clicked:           { icon: MousePointer,   color: 'text-amber-400',   label: 'Email Clicked' },
  outbound_call:           { icon: Phone,          color: 'text-violet-400',  label: 'Aria Called' },
  voice_followup_placed:   { icon: Phone,          color: 'text-violet-300',  label: 'Voice Follow-up' },
  outbound_call_completed: { icon: CheckCircle,    color: 'text-green-400',   label: 'Call Completed' },
  demo_booking_sent:       { icon: Calendar,       color: 'text-amber-400',   label: 'Demo Link Sent' },
  demo_booked:             { icon: CheckCircle,    color: 'text-green-400',   label: 'Demo Booked' },
  marked_not_interested:   { icon: XCircle,        color: 'text-red-400',     label: 'Not Interested' },
  observatory_sent:        { icon: Activity,       color: 'text-slate-400',   label: 'Observatory' },
  email_campaign_auto:     { icon: Zap,            color: 'text-sky-400',     label: 'Email Batch' },
  signal_weekly_report:    { icon: TrendingUp,     color: 'text-emerald-400', label: 'Signal Report' },
}

const JOB_ICON = {
  'WA Outreach':     { icon: Send,        color: 'text-indigo-400' },
  'Voice Follow-up': { icon: Phone,       color: 'text-violet-400' },
  'Email Campaign':  { icon: Mail,        color: 'text-sky-400'    },
  'Aria Click Calls':{ icon: Zap,         color: 'text-amber-400'  },
  'Callbacks':       { icon: AlarmClock,  color: 'text-slate-400'  },
  'Observatory':     { icon: Activity,    color: 'text-slate-400'  },
  'Signal Weekly':   { icon: TrendingUp,  color: 'text-emerald-400'},
}

function actConfig(type) {
  return ACT_CONFIG[type] || { icon: Activity, color: 'text-slate-500', label: type }
}

// ── Time helpers ───────────────────────────────────────────────────────────────

function timeAgo(iso) {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (diff < 5)    return 'just now'
  if (diff < 60)   return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function countdown(iso) {
  if (!iso) return { label: '—', urgent: false, imminent: false }
  const diff = Math.floor((new Date(iso) - Date.now()) / 1000)
  if (diff <= 0)    return { label: 'now',                      urgent: true,  imminent: true  }
  if (diff < 60)    return { label: `${diff}s`,                 urgent: true,  imminent: true  }
  if (diff < 300)   return { label: `${Math.floor(diff/60)}m ${diff%60}s`, urgent: true, imminent: false }
  if (diff < 3600)  return { label: `${Math.floor(diff/60)}m`, urgent: false, imminent: false }
  const h = Math.floor(diff / 3600), m = Math.floor((diff % 3600) / 60)
  return { label: m > 0 ? `${h}h ${m}m` : `${h}h`, urgent: false, imminent: false }
}

function fmtTime(iso, tz) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: tz })
}

function fmtDate(iso, tz) {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date().toLocaleDateString('en-GB', { timeZone: tz })
  const target = d.toLocaleDateString('en-GB', { timeZone: tz })
  if (target === today) return 'today'
  const tomorrow = new Date(Date.now() + 86400000).toLocaleDateString('en-GB', { timeZone: tz })
  if (target === tomorrow) return 'tomorrow'
  return d.toLocaleDateString('en-GB', { weekday: 'short', timeZone: tz })
}

// ── Schedule card ──────────────────────────────────────────────────────────────

function CityBreakdown({ title, total, byCity }) {
  if (!total) return null
  const entries = Object.entries(byCity || {}).slice(0, 10)
  return (
    <div className="mt-2">
      <p className="text-xs text-slate-500 mb-1">{title} <span className="text-slate-400 font-medium">{total}</span></p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
        {entries.map(([city, count]) => (
          <div key={city} className="flex items-center justify-between gap-2 text-xs">
            <span className="text-slate-500 truncate">{city}</span>
            <span className="text-slate-400 tabular-nums shrink-0">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ScheduleCard({ job, next_run, next_runs, queue, leads,
  broadcast_total, broadcast_by_city, followup_total, followup_by_city,
  frequency, last_ran, description, tick }) {
  const cfg   = JOB_ICON[job] || { icon: Clock, color: 'text-slate-400' }
  const Icon  = cfg.icon
  const { label, urgent, imminent } = countdown(next_run)
  const hot   = queue > 0
  const multi = next_runs && next_runs.length > 1
  const [showLeads, setShowLeads] = useState(false)
  const hasLeads = leads && leads.length > 0
  const hasCities = broadcast_total > 0 || followup_total > 0

  return (
    <div className={`bg-[#1e293b] border rounded-lg p-4 transition-all ${
      hot     ? 'border-indigo-500/50 shadow-[0_0_12px_rgba(99,102,241,0.08)]'
              : 'border-slate-700/30'
    }`}>
      {/* Top row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Icon size={14} className={hot ? cfg.color : 'text-slate-600'} />
          <span className={`text-sm font-medium truncate ${hot ? 'text-slate-100' : 'text-slate-400'}`}>
            {job}
          </span>
          {hot && (
            <span className="shrink-0 text-xs bg-indigo-900/60 text-indigo-300 border border-indigo-700/40 px-1.5 py-0.5 rounded-full">
              {queue} queued
            </span>
          )}
        </div>

        {/* Countdown */}
        <div className="text-right shrink-0">
          <span className={`text-lg font-bold tabular-nums ${
            imminent ? 'text-green-400 animate-pulse' :
            urgent   ? 'text-amber-400' :
            hot      ? 'text-white' : 'text-slate-500'
          }`}>
            {label}
          </span>
        </div>
      </div>

      {/* Times row */}
      <div className="mt-2 flex items-center gap-3 flex-wrap">
        {['UTC', 'Australia/Sydney', 'America/Toronto'].map((tz, i) => (
          <span key={tz} className="text-xs text-slate-500">
            <span className="text-slate-600">{['UTC', 'AEST', 'EDT'][i]}</span>{' '}
            <span className={hot ? 'text-slate-300' : 'text-slate-500'}>
              {fmtTime(next_run, tz)} {fmtDate(next_run, tz) !== 'today' ? `(${fmtDate(next_run, tz)})` : ''}
            </span>
          </span>
        ))}
      </div>

      {/* Upcoming runs (for high-frequency jobs) */}
      {multi && (
        <div className="mt-2 flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-600">Next:</span>
          {next_runs.slice(0, 6).map((t, i) => {
            const { label: lbl, urgent: u } = countdown(t)
            return (
              <span key={i} className={`text-xs px-1.5 py-0.5 rounded border ${
                i === 0
                  ? 'bg-slate-700/60 border-slate-600/60 text-slate-300'
                  : 'bg-slate-800/40 border-slate-700/20 text-slate-600'
              }`}>
                {lbl}
              </span>
            )
          })}
        </div>
      )}

      {/* Footer */}
      <div className="mt-2.5 flex items-center justify-between gap-2">
        <p className="text-xs text-slate-600 leading-relaxed flex-1">{description}</p>
        <div className="shrink-0 text-right">
          <p className="text-xs text-slate-600">{frequency}</p>
          {last_ran && (
            <p className="text-xs text-slate-700 mt-0.5">last: {timeAgo(last_ran)}</p>
          )}
        </div>
      </div>

      {/* WA city breakdown */}
      {hasCities && (
        <div className="mt-3 border-t border-slate-700/30 pt-2.5 space-y-2">
          <CityBreakdown title="Broadcast —" total={broadcast_total} byCity={broadcast_by_city} />
          <CityBreakdown title="Follow-up —" total={followup_total} byCity={followup_by_city} />
        </div>
      )}

      {/* Click call lead list */}
      {hasLeads && (
        <div className="mt-3 border-t border-slate-700/30 pt-2.5">
          <button
            onClick={() => setShowLeads(v => !v)}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <span className={`transition-transform ${showLeads ? 'rotate-90' : ''}`}>▸</span>
            {showLeads ? 'Hide' : 'Show'} {leads.length} lead{leads.length !== 1 ? 's' : ''}
          </button>
          {showLeads && (
            <div className="mt-2 space-y-1">
              {leads.map(l => {
                const s = l.call_status || ''
                const statusColor = s === 'ready'
                  ? 'text-green-400'
                  : s.includes('blocked')
                  ? 'text-red-400/70'
                  : 'text-amber-500/70'
                return (
                  <div key={l.id} className="flex items-center gap-2 text-xs">
                    <span className="text-slate-300 truncate flex-1">{l.name}</span>
                    <span className="text-slate-600 shrink-0">{l.city}</span>
                    <span className={`shrink-0 ${statusColor}`}>{s}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Activity feed item ─────────────────────────────────────────────────────────

function FeedItem({ item, isNew }) {
  const { icon: Icon, color, label } = actConfig(item.type)
  const detail = item.detail || {}

  let subtitle = ''
  if (item.lead_name) {
    subtitle = item.lead_name
    if (item.business_type) subtitle += ` · ${item.business_type}`
    if (item.city)          subtitle += ` · ${item.city}`
  } else if (detail.sent !== undefined) {
    subtitle = `Sent ${detail.sent}${detail.skipped ? ` · Skipped ${detail.skipped}` : ''}`
  } else if (detail.preview) {
    subtitle = detail.preview.slice(0, 80)
  }

  return (
    <div className={`flex items-start gap-3 py-2.5 border-b border-slate-700/20 last:border-0 ${isNew ? 'bg-indigo-950/30' : ''}`}>
      <div className="w-6 h-6 shrink-0 flex items-center justify-center mt-0.5">
        <Icon size={13} className={color} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-medium text-slate-300">{label}</span>
          <span className="text-xs text-slate-600">{timeAgo(item.created_at)}</span>
        </div>
        {subtitle && <p className="text-xs text-slate-500 truncate mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

// ── Main view ──────────────────────────────────────────────────────────────────

export default function LiveActivity() {
  const [data, setData]       = useState(null)
  const [newIds, setNewIds]   = useState(new Set())
  const [lastFetch, setLastFetch] = useState(null)
  const [tick, setTick]       = useState(0)      // increments every second — drives live countdowns
  const knownIds              = useRef(new Set())

  function refresh() {
    getLiveActivity()
      .then(res => {
        if (!res?.ok) return
        const incoming = new Set((res.recent || []).map(a => a.id))
        const fresh    = new Set([...incoming].filter(id => !knownIds.current.has(id)))
        knownIds.current = incoming
        setNewIds(fresh)
        setData(res)
        setLastFetch(new Date())
        if (fresh.size) setTimeout(() => setNewIds(new Set()), 3000)
      })
      .catch(() => {})
  }

  useEffect(() => {
    refresh()
    const dataTimer = setInterval(refresh, 15000)          // refresh data every 15s
    const tickTimer = setInterval(() => setTick(t => t + 1), 1000) // tick every 1s for countdowns
    return () => { clearInterval(dataTimer); clearInterval(tickTimer) }
  }, [])

  const queue    = data?.queue    || {}
  const schedule = data?.schedule || []
  const recent   = data?.recent   || []

  const sorted = [...schedule].sort((a, b) => new Date(a.next_run) - new Date(b.next_run))
  const totalQueued = Object.values(queue).reduce((s, v) => s + (v || 0), 0)

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-semibold">Live Activity</h2>
          <span className="flex items-center gap-1.5 text-xs text-green-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400" />
            </span>
            Live
          </span>
        </div>
        <div className="flex items-center gap-3">
          {lastFetch && (
            <span className="text-xs text-slate-600">Data updated {timeAgo(lastFetch.toISOString())}</span>
          )}
          <button
            onClick={refresh}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      {/* Schedule — primary focus */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Clock size={13} className="text-amber-400" />
            <span className="text-xs font-medium text-slate-300 uppercase tracking-wider">Upcoming — next 24h</span>
          </div>
          <div className="flex items-center gap-3">
            {totalQueued > 0 && (
              <span className="text-xs text-indigo-400">{totalQueued} leads queued</span>
            )}
            <span className="text-xs text-slate-600">Countdowns are live</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {sorted.map(job => (
            <ScheduleCard key={job.job} {...job} tick={tick} />
          ))}
        </div>
      </div>

      {/* Activity feed */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio size={13} className="text-green-400" />
            <span className="text-xs font-medium text-slate-300">Activity Feed</span>
          </div>
          <span className="text-xs text-slate-600">{recent.length} recent events</span>
        </div>
        <div className="overflow-y-auto max-h-[420px] px-4 py-2">
          {recent.length === 0 ? (
            <p className="text-xs text-slate-600 py-6 text-center">No recent activity</p>
          ) : (
            recent.map(item => (
              <FeedItem key={item.id} item={item} isNew={newIds.has(item.id)} />
            ))
          )}
        </div>
      </div>

      {/* WA outreach timeline legend */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg px-4 py-4">
        <p className="text-xs font-medium text-slate-400 mb-3">WA Outreach Sequence</p>
        <div className="flex flex-wrap gap-x-8 gap-y-2">
          {[
            { day: 'Day 0',  icon: Send,         color: 'text-indigo-400',  text: 'Initial WA (auto — 8:30am–7pm local)' },
            { day: 'Day 3',  icon: RefreshCw,    color: 'text-indigo-300',  text: 'WA follow-up if no reply (auto)' },
            { day: 'Day 5',  icon: Phone,        color: 'text-violet-400',  text: 'Aria voice call if still silent' },
            { day: 'Email',  icon: MousePointer, color: 'text-amber-400',   text: 'Click → Aria calls next working day' },
            { day: 'Reply',  icon: MessageSquare,color: 'text-green-400',   text: 'Intent classified → demo booking' },
          ].map(({ day, icon: Icon, color, text }) => (
            <div key={day} className="flex items-center gap-2">
              <span className="text-xs text-slate-600 w-10 shrink-0">{day}</span>
              <Icon size={11} className={color} />
              <span className="text-xs text-slate-500">{text}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
