import { useEffect, useState, useRef } from 'react'
import {
  Send, MessageSquare, Phone, Mail, Calendar,
  CheckCircle, XCircle, Clock, RefreshCw, Activity,
  TrendingUp, Eye, MousePointer, Zap, Radio,
} from 'lucide-react'
import { getLiveActivity } from '../api'

// ── Activity type config ───────────────────────────────────────────────────────

const ACT_CONFIG = {
  outreach_sent:           { icon: Send,         color: 'text-indigo-400',  label: 'WA Sent' },
  wa_followup_sent:        { icon: RefreshCw,     color: 'text-indigo-300',  label: 'WA Follow-up' },
  wa_reply_received:       { icon: MessageSquare, color: 'text-green-400',   label: 'WA Reply' },
  email_sent:              { icon: Mail,          color: 'text-sky-400',     label: 'Email Sent' },
  email_opened:            { icon: Eye,           color: 'text-sky-300',     label: 'Email Opened' },
  email_clicked:           { icon: MousePointer,  color: 'text-amber-400',   label: 'Email Clicked' },
  outbound_call:           { icon: Phone,         color: 'text-violet-400',  label: 'Aria Called' },
  voice_followup_placed:   { icon: Phone,         color: 'text-violet-300',  label: 'Voice Follow-up' },
  outbound_call_completed: { icon: CheckCircle,   color: 'text-green-400',   label: 'Call Completed' },
  demo_booking_sent:       { icon: Calendar,      color: 'text-amber-400',   label: 'Demo Link Sent' },
  demo_booked:             { icon: CheckCircle,   color: 'text-green-400',   label: 'Demo Booked' },
  marked_not_interested:   { icon: XCircle,       color: 'text-red-400',     label: 'Not Interested' },
  observatory_sent:        { icon: Activity,      color: 'text-slate-400',   label: 'Observatory' },
  email_campaign_auto:     { icon: Zap,           color: 'text-sky-400',     label: 'Email Batch' },
  signal_weekly_report:    { icon: TrendingUp,    color: 'text-emerald-400', label: 'Signal Report' },
}

function actConfig(type) {
  return ACT_CONFIG[type] || { icon: Activity, color: 'text-slate-500', label: type }
}

// ── Time helpers ───────────────────────────────────────────────────────────────

function timeAgo(iso) {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (diff < 5)   return 'just now'
  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function timeUntil(iso) {
  if (!iso) return ''
  const diff = Math.floor((new Date(iso) - Date.now()) / 1000)
  if (diff <= 0)    return 'now'
  if (diff < 60)    return `in ${diff}s`
  if (diff < 3600)  return `in ${Math.floor(diff / 60)}m`
  if (diff < 86400) return `in ${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`
  return `in ${Math.floor(diff / 86400)}d`
}

function fmtUtc(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toUTCString().replace(' GMT', ' UTC').slice(0, -4)
}

// ── Queue card ─────────────────────────────────────────────────────────────────

function QueueCard({ label, count, icon: Icon, color, description }) {
  const isEmpty = count === 0
  return (
    <div className={`bg-[#1e293b] border rounded-lg p-4 flex flex-col gap-2 ${isEmpty ? 'border-slate-700/30' : 'border-indigo-500/30'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={14} className={isEmpty ? 'text-slate-600' : color} />
          <span className="text-xs text-slate-400">{label}</span>
        </div>
        <span className={`text-xl font-bold tabular-nums ${isEmpty ? 'text-slate-600' : 'text-white'}`}>
          {count}
        </span>
      </div>
      <p className="text-xs text-slate-600 leading-relaxed">{description}</p>
    </div>
  )
}

// ── Schedule row ───────────────────────────────────────────────────────────────

function ScheduleRow({ job, next_run, queue, description }) {
  const hasQueue = queue > 0
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-700/30 last:border-0">
      <div className="w-2 h-2 mt-1.5 rounded-full shrink-0 bg-slate-600" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-slate-200">{job}</span>
          {hasQueue && (
            <span className="text-xs bg-indigo-900/50 text-indigo-400 border border-indigo-700/40 px-1.5 py-0.5 rounded-full">
              {queue} queued
            </span>
          )}
        </div>
        <p className="text-xs text-slate-500 mt-0.5">{description}</p>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-xs font-medium text-amber-400">{timeUntil(next_run)}</p>
        <p className="text-xs text-slate-600 mt-0.5">{fmtUtc(next_run)}</p>
      </div>
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
    <div className={`flex items-start gap-3 py-2.5 border-b border-slate-700/20 last:border-0 transition-opacity duration-500 ${isNew ? 'bg-indigo-950/30' : ''}`}>
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
  const knownIds              = useRef(new Set())
  const token                 = localStorage.getItem('pd_token')

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
    const t = setInterval(refresh, 15000)
    return () => clearInterval(t)
  }, [token])

  const queue    = data?.queue    || {}
  const schedule = data?.schedule || []
  const recent   = data?.recent   || []

  const totalQueued = (queue.wa_followup || 0) + (queue.voice_followup || 0) + (queue.email || 0) + (queue.click_calls || 0)

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
            <span className="text-xs text-slate-600">Updated {timeAgo(lastFetch.toISOString())}</span>
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

      {/* Queue cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending actions</p>
          {totalQueued > 0
            ? <span className="text-xs text-indigo-400">{totalQueued} leads waiting</span>
            : <span className="text-xs text-slate-600">All queues empty</span>
          }
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <QueueCard
            label="WA Follow-up"
            count={queue.wa_followup || 0}
            icon={RefreshCw}
            color="text-indigo-400"
            description="Contacted 3+ days ago, no reply yet. Fires 9am UTC."
          />
          <QueueCard
            label="Voice Follow-up"
            count={queue.voice_followup || 0}
            icon={Phone}
            color="text-violet-400"
            description="Contacted 5+ days ago, no reply. Aria call fires 9am UTC."
          />
          <QueueCard
            label="Email Drip"
            count={queue.email || 0}
            icon={Mail}
            color="text-sky-400"
            description="Leads due for their next email in the 6-step sequence."
          />
          <QueueCard
            label="Aria Click Calls"
            count={queue.click_calls || 0}
            icon={Zap}
            color="text-amber-400"
            description="Email-clicked leads. Aria calls hourly in business hours."
          />
        </div>
      </div>

      {/* Two columns: feed + schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Live feed */}
        <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio size={13} className="text-green-400" />
              <span className="text-xs font-medium text-slate-300">Activity Feed</span>
            </div>
            <span className="text-xs text-slate-600">{recent.length} events</span>
          </div>
          <div className="overflow-y-auto max-h-[480px] divide-y divide-transparent px-4 py-2">
            {recent.length === 0 ? (
              <p className="text-xs text-slate-600 py-6 text-center">No recent activity</p>
            ) : (
              recent.map(item => (
                <FeedItem key={item.id} item={item} isNew={newIds.has(item.id)} />
              ))
            )}
          </div>
        </div>

        {/* Schedule */}
        <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={13} className="text-amber-400" />
              <span className="text-xs font-medium text-slate-300">Upcoming Jobs</span>
            </div>
            <span className="text-xs text-slate-600">All times UTC</span>
          </div>
          <div className="px-4 py-2">
            {schedule.length === 0 ? (
              <p className="text-xs text-slate-600 py-6 text-center">Schedule unavailable</p>
            ) : (
              [...schedule]
                .sort((a, b) => new Date(a.next_run) - new Date(b.next_run))
                .map(job => (
                  <ScheduleRow key={job.job} {...job} />
                ))
            )}
          </div>

          {/* WA workflow explanation */}
          <div className="border-t border-slate-700/40 px-4 py-4">
            <p className="text-xs font-medium text-slate-400 mb-2">WA Outreach Timeline</p>
            <div className="space-y-1.5">
              {[
                { day: 'Day 0',  icon: Send,        color: 'text-indigo-400', text: 'Initial WA sent (manual pipeline run)' },
                { day: 'Day 3',  icon: RefreshCw,   color: 'text-indigo-300', text: 'Follow-up WA if no reply' },
                { day: 'Day 5',  icon: Phone,       color: 'text-violet-400', text: 'Aria voice call if still silent' },
                { day: 'Any',    icon: MessageSquare,color:'text-green-400',  text: 'Reply → intent classification → demo booking' },
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

      </div>
    </div>
  )
}
