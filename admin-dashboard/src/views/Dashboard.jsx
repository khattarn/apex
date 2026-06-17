import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { Users, Mail, Eye, CornerDownRight, TrendingUp, MousePointerClick, Phone, Telescope } from 'lucide-react'
import { getStats, getLeads, getObservatoryLatest } from '../api'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'

const CHART_TOOLTIP = {
  contentStyle: { background: '#0f172a', border: '1px solid #334155', borderRadius: 6, fontSize: 12 },
  labelStyle: { color: '#94a3b8' },
  itemStyle: { color: '#fff' },
}

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [observatory, setObservatory] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getStats(), getLeads({ limit: 10 })])
      .then(([s, l]) => {
        setStats(s)
        setRecent(l.data || [])
      })
      .catch((e) => setError(e.message))

    getObservatoryLatest()
      .then(setObservatory)
      .catch(() => {})
  }, [])

  if (error) return <p className="p-8 text-red-400">{error}</p>
  if (!stats) return <p className="p-8 text-slate-400">Loading…</p>

  const byTypeData = Object.entries(stats.by_business_type || {}).map(([name, count]) => ({ name, count }))
  const byCityData = Object.entries(stats.by_city || {}).slice(0, 10).map(([name, count]) => ({ name, count }))

  return (
    <div className="p-4 md:p-6 space-y-6">
      <h2 className="text-base font-semibold">Dashboard</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard label="Total Leads" value={stats.total_leads} icon={Users} />
        <StatCard label="Emailed" value={stats.emailed ?? 0} icon={Mail} color="blue" />
        <StatCard label="Opened" value={stats.email_opened ?? 0} icon={Eye} color="yellow" />
        <StatCard label="Clicked" value={stats.email_clicked ?? 0} icon={MousePointerClick} color="yellow" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard label="Aria Called" value={stats.aria_called ?? 0} icon={Phone} color="blue" />
        <StatCard label="Replied" value={stats.replied ?? 0} icon={CornerDownRight} color="yellow" />
        <StatCard label="Converted" value={stats.converted ?? 0} icon={TrendingUp} color="green" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#1e293b] rounded-lg p-4 border border-slate-700/40">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-4">By Business Type</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={byTypeData} barSize={28}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...CHART_TOOLTIP} />
              <Bar dataKey="count" fill="#6366f1" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-[#1e293b] rounded-lg p-4 border border-slate-700/40">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-4">By City</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={byCityData} barSize={28}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...CHART_TOOLTIP} />
              <Bar dataKey="count" fill="#818cf8" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Observatory digest */}
      {observatory && (
        <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700/40 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Telescope size={14} className="text-amber-400" />
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Apex Daily — Last Report</p>
            </div>
            {observatory.updated_at && (
              <span className="text-[10px] text-slate-500">
                {new Date(observatory.updated_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
          {observatory.digest ? (
            <pre className="px-4 py-3 text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
              {observatory.digest}
            </pre>
          ) : (
            <p className="px-4 py-4 text-xs text-slate-500 italic">
              No digest yet — Observatory runs daily at 7am IST. Check back tomorrow.
            </p>
          )}
        </div>
      )}

      {/* Recent activity */}
      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700/40">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Recent Activity</p>
        </div>
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[480px]">
          <thead>
            <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
              <th className="text-left px-4 py-2 font-medium">Name</th>
              <th className="text-left px-4 py-2 font-medium">City</th>
              <th className="text-left px-4 py-2 font-medium">Type</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
              <th className="text-left px-4 py-2 font-medium">Added</th>
            </tr>
          </thead>
          <tbody>
            {recent.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500 text-xs">
                  No leads yet
                </td>
              </tr>
            )}
            {recent.map((lead) => (
              <tr key={lead.id} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-2.5">{lead.name}</td>
                <td className="px-4 py-2.5 text-slate-400">{lead.city}</td>
                <td className="px-4 py-2.5 text-slate-400 capitalize">{lead.business_type}</td>
                <td className="px-4 py-2.5"><StatusBadge status={lead.status} /></td>
                <td className="px-4 py-2.5 text-slate-500 text-xs">{fmt(lead.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  )
}
