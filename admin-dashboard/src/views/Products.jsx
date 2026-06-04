import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, ChevronRight } from 'lucide-react'
import { fetchProductStats } from '../api'

export const PRODUCTS = [
  {
    id: 'practicedesk',
    name: 'PracticeDesk',
    slug: 'PD',
    color: 'indigo',
    market: 'Australia · USA · Global',
    verticals: 'Dentists · Salons · Accountants · Physiotherapists',
    pricing: '$49 · $99 · $180 / month',
    url: 'https://practicedesk.netlify.app',
    status: 'live',
    stack: 'Netlify · Supabase · Claude · Vapi · Meta WA',
    description: 'AI-powered booking, voice, and outreach platform for service-based small businesses.',
    statsSource: 'supabase',
  },
  {
    id: 'legalaidai-citizen',
    name: 'LegalAidAI — Citizen',
    slug: 'LA',
    color: 'orange',
    market: 'India',
    verticals: '1.4B citizens',
    pricing: 'Freemium',
    url: 'https://www.legalaidai.in/citizen',
    status: 'live',
    stack: 'Netlify · Firebase · Claude · Razorpay · Indian Kanoon',
    description: 'AI legal guidance in plain language for Indian citizens. Accessible, affordable, multilingual.',
    statsSource: 'firebase',
  },
  {
    id: 'legalaidai-advocate',
    name: 'LegalAidAI — Advocate',
    slug: 'LA',
    color: 'orange',
    market: 'India',
    verticals: '1.7M advocates',
    pricing: '₹2,500 first · ₹5,000 renewal',
    url: 'https://www.legalaidai.in/advocate',
    status: 'live',
    stack: 'Netlify · Firebase · Claude · Razorpay',
    description: 'AI research assistant, case tracking, and client management for Indian advocates.',
    statsSource: 'firebase',
  },
  {
    id: 'legalaidai-corporate',
    name: 'LegalAidAI — Corporate',
    slug: 'LA',
    color: 'orange',
    market: 'India',
    verticals: 'Corporate legal teams',
    pricing: 'Custom',
    url: 'https://www.legalaidai.in/corporate',
    status: 'live',
    stack: 'Netlify · Firebase · Claude · Razorpay',
    description: 'Contract review, compliance checks, and legal research for corporate legal departments.',
    statsSource: 'firebase',
  },
]

const COLOR = {
  indigo: {
    bg: 'bg-indigo-600',
    ring: 'ring-indigo-500/30',
    border: 'hover:border-indigo-500/50',
  },
  orange: {
    bg: 'bg-orange-600',
    ring: 'ring-orange-500/30',
    border: 'hover:border-orange-500/40',
  },
}

export default function Products() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const token = localStorage.getItem('pd_token')

  useEffect(() => {
    fetchProductStats(token).then(setStats).catch(() => {})
  }, [token])

  const pd = stats?.practicedesk

  function getFooterStats(product) {
    if (product.statsSource === 'firebase') {
      return <span className="text-slate-600 text-xs">Firebase metrics — connect to enable</span>
    }
    if (!pd) return <span className="text-slate-600 text-xs">Loading…</span>
    return (
      <span className="text-xs text-slate-400">
        <span className="text-white font-medium">{pd.total_leads?.toLocaleString()}</span> leads
        {' · '}
        <span className="text-indigo-400 font-medium">{pd.emailed?.toLocaleString()}</span> emailed
        {' · '}
        <span className="text-green-400 font-medium">{pd.converted?.toLocaleString()}</span> converted
      </span>
    )
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Products</h2>
        <p className="text-xs text-slate-500">{PRODUCTS.length} products · all live</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PRODUCTS.map((product) => {
          const c = COLOR[product.color]

          return (
            <div
              key={product.id}
              onClick={() => navigate(`/products/${product.id}`)}
              className={`bg-[#1e293b] border border-slate-700/40 rounded-lg p-5 flex flex-col gap-4 cursor-pointer transition-all ${c.border} hover:bg-slate-800/40`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-10 h-10 shrink-0 rounded-lg ${c.bg} flex items-center justify-center ring-1 ${c.ring}`}>
                    <span className="text-xs font-bold text-white">{product.slug}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white leading-tight">{product.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{product.pricing}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
                  <span className="text-xs text-green-400">Live</span>
                </div>
              </div>

              {/* Market + description */}
              <div className="space-y-1">
                <p className="text-xs text-slate-500">{product.market} · {product.verticals}</p>
                <p className="text-xs text-slate-400 leading-relaxed">{product.description}</p>
              </div>

              {/* Stack */}
              <p className="text-xs text-slate-600 truncate">{product.stack}</p>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-700/40">
                {getFooterStats(product)}
                <div className="flex items-center gap-3">
                  <a
                    href={product.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="text-slate-600 hover:text-slate-300 transition-colors"
                  >
                    <ExternalLink size={13} />
                  </a>
                  <ChevronRight size={13} className="text-slate-600" />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
