import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, ExternalLink, Clock, Zap } from 'lucide-react'
import { AGENTS } from './Agents'
import { fetchAgentStats } from '../api'

const STATUS_STYLE = {
  live:     { dot: 'bg-green-400',               text: 'text-green-400',  label: 'Live' },
  building: { dot: 'bg-amber-400 animate-pulse', text: 'text-amber-400', label: 'Building' },
  planned:  { dot: 'bg-slate-500',               text: 'text-slate-400', label: 'Planned' },
}

function timeAgo(iso) {
  if (!iso) return '—'
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-CA', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function StatBox({ label, value, sub }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg p-4 text-center">
      <p className="text-2xl font-semibold text-white">{value ?? '—'}</p>
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

function PipelineStats({ stats }) {
  const d = stats?.pipeline
  if (!d) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatBox label="Pipeline Runs" value={d.runs} />
      <StatBox label="Prospects Found" value={d.prospects_found?.toLocaleString()} />
      <StatBox label="New Leads" value={d.new_leads?.toLocaleString()} />
      <StatBox label="WA Sent" value={d.messages_sent?.toLocaleString()} />
    </div>
  )
}

function EnrichmentStats({ stats }) {
  const d = stats?.email_enrichment
  if (!d) return null
  const pct = d.total_leads ? Math.round((d.with_email / d.total_leads) * 100) : 0
  return (
    <div className="grid grid-cols-3 gap-3">
      <StatBox label="Total Leads" value={d.total_leads?.toLocaleString()} />
      <StatBox label="With Email" value={d.with_email?.toLocaleString()} />
      <StatBox label="Coverage" value={`${pct}%`} />
    </div>
  )
}

function EmailCampaignStats({ stats }) {
  const d = stats?.email_campaign
  if (!d) return null
  const openRate = d.emails_sent ? Math.round((d.email_opened / d.emails_sent) * 100) : 0
  const clickRate = d.emails_sent ? Math.round((d.email_clicked / d.emails_sent) * 100) : 0
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatBox label="Emails Sent" value={d.emails_sent?.toLocaleString()} />
      <StatBox label="Opened" value={d.email_opened?.toLocaleString()} sub={`${openRate}% rate`} />
      <StatBox label="Clicked" value={d.email_clicked?.toLocaleString()} sub={`${clickRate}% rate`} />
      <StatBox label="Campaign Runs" value={d.runs} />
    </div>
  )
}

function RecentRuns({ runs, type }) {
  if (!runs?.length) return <p className="text-xs text-slate-500">No runs recorded.</p>

  if (type === 'email') {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-500 border-b border-slate-700/40">
              <th className="text-left pb-2 font-medium">Date</th>
              <th className="text-right pb-2 font-medium">Sent</th>
              <th className="text-right pb-2 font-medium">Log</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/20">
            {runs.map((r) => (
              <tr key={r.id} className="text-slate-300">
                <td className="py-2">{fmtDate(r.created_at)}</td>
                <td className="py-2 text-right text-indigo-400">{r.emails_sent ?? 0}</td>
                <td className="py-2 text-right text-slate-500 truncate max-w-[200px]">{r.log ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500 border-b border-slate-700/40">
            <th className="text-left pb-2 font-medium">Date</th>
            <th className="text-left pb-2 font-medium">Cities</th>
            <th className="text-left pb-2 font-medium">Type</th>
            <th className="text-right pb-2 font-medium">Found</th>
            <th className="text-right pb-2 font-medium">New</th>
            <th className="text-right pb-2 font-medium">Sent</th>
            <th className="text-left pb-2 font-medium">Mode</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/20">
          {runs.map((r) => (
            <tr key={r.id} className="text-slate-300">
              <td className="py-2">{fmtDate(r.created_at)}</td>
              <td className="py-2 text-slate-400">{r.city || '—'}</td>
              <td className="py-2 text-slate-400 capitalize">{r.business_type || '—'}</td>
              <td className="py-2 text-right">{r.prospects_found ?? 0}</td>
              <td className="py-2 text-right text-green-400">{r.new_leads ?? 0}</td>
              <td className="py-2 text-right text-indigo-400">{r.messages_sent ?? 0}</td>
              <td className="py-2">
                <span className={`px-1.5 py-0.5 rounded text-xs ${
                  r.mode === 'live' ? 'bg-green-900/40 text-green-400' : 'bg-slate-700/60 text-slate-400'
                }`}>{r.mode === 'live' ? 'live' : 'dry'}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AgentDetail() {
  const { agentId } = useParams()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState(false)
  const token = localStorage.getItem('pd_token')

  const agent = AGENTS.find(a => a.id === agentId)

  useEffect(() => {
    if (!agent || agent.status === 'planned') return
    const fetchStats = () => fetchAgentStats(token).then((s) => { setStats(s); setStatsError(false) }).catch(() => setStatsError(true))
    fetchStats()
    const t = setInterval(fetchStats, 10000)
    return () => clearInterval(t)
  }, [token, agent])

  if (!agent) {
    return (
      <div className="p-6">
        <p className="text-sm text-slate-400">Agent not found.</p>
        <button onClick={() => navigate('/agents')} className="mt-3 text-xs text-indigo-400 hover:underline">← Back to Agents</button>
      </div>
    )
  }

  const s = STATUS_STYLE[agent.status]
  const { Icon } = agent
  const isRunning = agent.runningKey && stats?.running?.[agent.runningKey]
  const agentStats = stats && agent.statsKey ? stats[agent.statsKey] : null
  const lastRun = agentStats?.last_run

  const recentRuns = agent.statsKey === 'email_campaign'
    ? stats?.email_campaign?.recent_runs
    : agent.statsKey === 'pipeline'
    ? stats?.pipeline?.recent_runs
    : null

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/agents')}
        className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
      >
        <ArrowLeft size={13} /> Agents
      </button>

      {/* Hero */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-700/60 flex items-center justify-center">
              <Icon size={18} className="text-slate-200" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-white">{agent.name}</h1>
                {isRunning && (
                  <span className="text-xs text-green-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse inline-block" />
                    Running
                  </span>
                )}
                {statsError && <span className="text-xs text-red-400">Stats unavailable — retrying…</span>}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{agent.tech} · {agent.owner}</p>
            </div>
          </div>
          <span className={`shrink-0 text-xs font-medium ${s.text}`}>{s.label}</span>
        </div>

        <p className="mt-4 text-sm text-slate-300 leading-relaxed">{agent.description}</p>

        {lastRun && (
          <p className="mt-3 text-xs text-slate-500 flex items-center gap-1.5">
            <Clock size={11} /> Last run: {timeAgo(lastRun)}
          </p>
        )}
      </div>

      {/* Stats */}
      {agent.status === 'live' && (
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Lifetime Stats</p>
          {(agent.statsKey === 'pipeline') && <PipelineStats stats={stats} />}
          {agent.statsKey === 'email_enrichment' && <EnrichmentStats stats={stats} />}
          {agent.statsKey === 'email_campaign' && <EmailCampaignStats stats={stats} />}
        </div>
      )}

      {/* Technical details */}
      {agent.details && Object.keys(agent.details).length > 0 && (
        <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-5 space-y-3">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Technical Details</p>
          <dl className="space-y-2 text-xs">
            {agent.details.inputs && (
              <div className="flex gap-3">
                <dt className="text-slate-500 w-16 shrink-0">Inputs</dt>
                <dd className="text-slate-300">{agent.details.inputs}</dd>
              </div>
            )}
            {agent.details.outputs && (
              <div className="flex gap-3">
                <dt className="text-slate-500 w-16 shrink-0">Outputs</dt>
                <dd className="text-slate-300">{agent.details.outputs}</dd>
              </div>
            )}
            {agent.details.notes && (
              <div className="flex gap-3">
                <dt className="text-slate-500 w-16 shrink-0">Notes</dt>
                <dd className="text-slate-400">{agent.details.notes}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Planned agents — roadmap card */}
      {agent.status === 'planned' && (
        <div className="bg-slate-800/40 border border-slate-700/30 rounded-lg p-5">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={13} className="text-slate-500" />
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">On Roadmap</p>
          </div>
          <p className="text-sm text-slate-400">
            This agent is planned but not yet built. It will be owned by <strong className="text-slate-300">{agent.owner}</strong>.
          </p>
        </div>
      )}

      {/* Recent runs */}
      {recentRuns && (
        <div className="space-y-3">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Recent Runs</p>
          <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4">
            <RecentRuns
              runs={recentRuns}
              type={agent.statsKey === 'email_campaign' ? 'email' : 'pipeline'}
            />
          </div>
        </div>
      )}

      {/* Action button */}
      {agent.actionPath && agent.status === 'live' && (
        <div>
          <Link
            to={agent.actionPath}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-5 py-2.5 rounded transition-colors"
          >
            <ExternalLink size={13} />
            {agent.actionLabel}
          </Link>
        </div>
      )}
    </div>
  )
}
