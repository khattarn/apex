import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { getCampaigns } from '../api'

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getCampaigns()
      .then(setCampaigns)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
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
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
              {['Date', 'Business Type', 'City', 'Mode', 'Prospects', 'New Leads', 'Sent'].map((h) => (
                <th key={h} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">Loading…</td></tr>
            )}
            {!loading && campaigns.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">
                  No campaigns yet — run the pipeline to see results here
                </td>
              </tr>
            )}
            {campaigns.map((c) => (
              <tr key={c.id} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-2.5 text-xs text-slate-400 whitespace-nowrap">{fmt(c.created_at)}</td>
                <td className="px-4 py-2.5 capitalize">{c.business_type}</td>
                <td className="px-4 py-2.5 text-slate-400">{c.city}</td>
                <td className="px-4 py-2.5">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    c.mode === 'live'
                      ? 'bg-green-900/50 text-green-300'
                      : 'bg-slate-700 text-slate-300'
                  }`}>
                    {c.mode === 'live' ? 'Live' : 'Dry Run'}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-center">{c.prospects_found ?? 0}</td>
                <td className="px-4 py-2.5 text-center text-indigo-400">{c.new_leads ?? 0}</td>
                <td className="px-4 py-2.5 text-center text-green-400">{c.messages_sent ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
