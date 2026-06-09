import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, MessageSquare, Mail } from 'lucide-react'
import { getCampaigns } from '../api'

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function TypeBadge({ type }) {
  if (type === 'email') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded font-medium bg-indigo-900/50 text-indigo-300">
        <Mail size={10} /> Email
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded font-medium bg-green-900/50 text-green-300">
      <MessageSquare size={10} /> WA
    </span>
  )
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getCampaigns()
      .then(data => setCampaigns(Array.isArray(data) ? data : data?.data || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-base font-semibold">Campaigns</h2>
        <button
          onClick={() => navigate('/pipeline')}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          <Plus size={14} />
          New Campaign
        </button>
      </div>

      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[700px]">
          <thead>
            <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
              {['Date', 'Channel', 'Business Type', 'City', 'Mode', 'Prospects', 'New Leads', 'Sent', 'Opened', 'Clicked'].map((h) => (
                <th key={h} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-slate-500 text-xs">Loading…</td></tr>
            )}
            {!loading && campaigns.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-slate-500 text-xs">
                  No campaigns yet — run the pipeline to see results here
                </td>
              </tr>
            )}
            {campaigns.map((c) => {
              const isEmail = c.type === 'email'
              const sent    = isEmail ? (c.emails_sent ?? 0) : (c.messages_sent ?? 0)
              const opened  = c.emails_opened ?? 0
              const clicked = c.emails_clicked ?? 0
              const openRate   = sent > 0 ? Math.round((opened  / sent) * 100) : null
              const clickRate  = sent > 0 ? Math.round((clicked / sent) * 100) : null
              return (
                <tr key={c.id} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-2.5 text-xs text-slate-400 whitespace-nowrap">{fmt(c.created_at)}</td>
                  <td className="px-4 py-2.5"><TypeBadge type={c.type} /></td>
                  <td className="px-4 py-2.5 capitalize text-xs" title={c.business_type}>
                    {c.business_type && c.business_type.length > 20 ? c.business_type.slice(0, 18) + '…' : c.business_type}
                  </td>
                  <td className="px-4 py-2.5 text-slate-400 text-xs" title={c.city}>
                    {c.city && c.city.length > 22 ? c.city.slice(0, 20) + '…' : c.city}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-slate-700 text-slate-300">
                      {c.mode === 'live' ? 'Live' : 'Dry Run'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-center">{c.prospects_found ?? 0}</td>
                  <td className="px-4 py-2.5 text-center text-indigo-400">{isEmail ? '—' : (c.new_leads ?? 0)}</td>
                  <td className="px-4 py-2.5 text-center text-green-400">{sent}</td>
                  <td className="px-4 py-2.5 text-center">
                    {isEmail ? (
                      <span className={opened > 0 ? 'text-amber-400' : 'text-slate-600'}>
                        {opened}{openRate !== null ? <span className="text-slate-500 text-[10px] ml-1">{openRate}%</span> : null}
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    {isEmail ? (
                      <span className={clicked > 0 ? 'text-indigo-400' : 'text-slate-600'}>
                        {clicked}{clickRate !== null ? <span className="text-slate-500 text-[10px] ml-1">{clickRate}%</span> : null}
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  )
}
