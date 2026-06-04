import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, ExternalLink, Database } from 'lucide-react'
import { PRODUCTS } from './Products'
import { fetchProductStats } from '../api'

const COLOR = {
  indigo: { bg: 'bg-indigo-600', ring: 'ring-indigo-500/30', accent: 'text-indigo-400' },
  orange: { bg: 'bg-orange-600', ring: 'ring-orange-500/30', accent: 'text-orange-400' },
}

function StatBox({ label, value, accent, sub }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg p-4 text-center">
      <p className={`text-2xl font-semibold ${accent || 'text-white'}`}>{value ?? '—'}</p>
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

function BarRow({ label, value, total, color }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-slate-400 w-28 shrink-0 capitalize">{label}</span>
      <div className="flex-1 bg-slate-700/40 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-slate-300 w-8 text-right">{value}</span>
    </div>
  )
}

function PracticeDeskDetail({ stats }) {
  const pd = stats?.practicedesk
  if (!pd) {
    return <p className="text-xs text-slate-500">Loading stats…</p>
  }

  const verticalColors = ['bg-indigo-500', 'bg-violet-500', 'bg-blue-500', 'bg-cyan-500', 'bg-teal-500']
  const cityColors = ['bg-indigo-400', 'bg-indigo-500', 'bg-indigo-600', 'bg-indigo-700', 'bg-slate-600']

  const totalVerticals = Object.values(pd.by_vertical || {}).reduce((a, b) => a + b, 0)
  const sortedCities = Object.entries(pd.by_city || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8)

  const openRate = pd.emailed ? Math.round((pd.opened / pd.emailed) * 100) : 0
  const clickRate = pd.emailed ? Math.round((pd.clicked / pd.emailed) * 100) : 0

  return (
    <div className="space-y-6">
      {/* Primary stats */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Outreach Pipeline</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatBox label="Total Leads" value={pd.total_leads?.toLocaleString()} />
          <StatBox label="Emailed" value={pd.emailed?.toLocaleString()} accent="text-indigo-400" />
          <StatBox label="Opened" value={pd.opened?.toLocaleString()} accent="text-yellow-400"
            sub={`${openRate}%`}
          />
          <StatBox label="Converted" value={pd.converted?.toLocaleString()} accent="text-green-400" />
        </div>
      </div>

      {/* Email engagement */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4 space-y-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Email Engagement</p>
        <div className="space-y-2.5">
          <BarRow label="Emailed" value={pd.emailed} total={pd.total_leads} color="bg-indigo-500" />
          <BarRow label="Opened" value={pd.opened} total={pd.emailed || 1} color="bg-yellow-500" />
          <BarRow label="Clicked" value={pd.clicked} total={pd.emailed || 1} color="bg-green-500" />
          <BarRow label="Replied" value={pd.replied} total={pd.total_leads} color="bg-blue-500" />
          <BarRow label="WA Sent" value={pd.wa_sent} total={pd.total_leads} color="bg-emerald-500" />
        </div>
        <div className="flex gap-4 pt-2 text-xs text-slate-500">
          <span>Open rate: <span className="text-white">{openRate}%</span></span>
          <span>Click rate: <span className="text-white">{clickRate}%</span></span>
        </div>
      </div>

      {/* By vertical */}
      {totalVerticals > 0 && (
        <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Leads by Vertical</p>
          <div className="space-y-2.5">
            {Object.entries(pd.by_vertical || {})
              .sort(([, a], [, b]) => b - a)
              .map(([vt, count], i) => (
                <BarRow key={vt} label={vt} value={count} total={totalVerticals} color={verticalColors[i % verticalColors.length]} />
              ))
            }
          </div>
        </div>
      )}

      {/* By city */}
      {sortedCities.length > 0 && (
        <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Top Cities</p>
          <div className="space-y-2.5">
            {sortedCities.map(([city, count], i) => (
              <BarRow key={city} label={city} value={count} total={pd.total_leads} color={cityColors[i % cityColors.length]} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function FirebasePlaceholder({ product }) {
  return (
    <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-6 text-center space-y-3">
      <Database size={24} className="mx-auto text-slate-600" />
      <p className="text-sm text-slate-400">Firebase metrics not connected</p>
      <p className="text-xs text-slate-600 max-w-sm mx-auto">
        {product.name} runs on Firebase Firestore. Connect the Firebase Admin SDK to this API to pull live subscriber, usage, and revenue data.
      </p>
      <a
        href={product.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:underline"
      >
        Open live site <ExternalLink size={11} />
      </a>
    </div>
  )
}

export default function ProductDetail() {
  const { productId } = useParams()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const token = localStorage.getItem('pd_token')

  const product = PRODUCTS.find(p => p.id === productId)

  useEffect(() => {
    if (!product || product.statsSource !== 'supabase') return
    fetchProductStats(token).then(setStats).catch(() => {})
  }, [token, product])

  if (!product) {
    return (
      <div className="p-6">
        <p className="text-sm text-slate-400">Product not found.</p>
        <button onClick={() => navigate('/products')} className="mt-3 text-xs text-indigo-400 hover:underline">← Back to Products</button>
      </div>
    )
  }

  const c = COLOR[product.color]

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/products')}
        className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
      >
        <ArrowLeft size={13} /> Products
      </button>

      {/* Hero */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl ${c.bg} flex items-center justify-center ring-1 ${c.ring}`}>
              <span className="text-sm font-bold text-white">{product.slug}</span>
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">{product.name}</h1>
              <p className="text-xs text-slate-500 mt-0.5">{product.pricing}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
            <span className="text-xs text-green-400">Live</span>
          </div>
        </div>

        <p className="mt-4 text-sm text-slate-300 leading-relaxed">{product.description}</p>

        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-500">
          <span>Market: <span className="text-slate-300">{product.market}</span></span>
          <span>Verticals: <span className="text-slate-300">{product.verticals}</span></span>
        </div>

        <div className="mt-3 flex items-center gap-4">
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:underline"
          >
            <ExternalLink size={11} /> {product.url.replace('https://', '')}
          </a>
        </div>
      </div>

      {/* Stack */}
      <div className="bg-[#1e293b] border border-slate-700/40 rounded-lg p-4">
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Tech Stack</p>
        <div className="flex flex-wrap gap-2">
          {product.stack.split(' · ').map(s => (
            <span key={s} className="text-xs px-2.5 py-1 bg-slate-800 border border-slate-700/40 rounded-full text-slate-300">
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-3">Metrics</p>
        {product.statsSource === 'supabase'
          ? <PracticeDeskDetail stats={stats} />
          : <FirebasePlaceholder product={product} />
        }
      </div>
    </div>
  )
}
