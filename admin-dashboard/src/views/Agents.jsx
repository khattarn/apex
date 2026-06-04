import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MapPin, MessageSquare, Send, Search, Mail,
  Reply, Calendar, RefreshCw, Phone, FileText,
  Activity, Share2, ChevronRight,
} from 'lucide-react'
import { fetchAgentStats } from '../api'

export const AGENTS = [
  {
    id: 'prospector',
    name: 'Prospector',
    status: 'live',
    runningKey: 'pipeline',
    Icon: MapPin,
    description: 'Finds businesses on Google Maps by type and city. Fetches name, address, phone, and website.',
    tech: 'Google Maps Places API',
    owner: 'VP Marketing',
    statsKey: 'pipeline',
    metricLabel: 'Prospects found',
    metricKey: 'prospects_found',
    actionLabel: 'Run Pipeline',
    actionPath: '/pipeline',
    details: {
      inputs: 'Business type, city, max results',
      outputs: 'Name, address, phone, website, place_id',
      notes: 'Max ~60 per query. Use sub-areas (North York, Scarborough) to expand Toronto coverage.',
    },
  },
  {
    id: 'personalizer',
    name: 'Personalizer',
    status: 'live',
    runningKey: 'pipeline',
    Icon: MessageSquare,
    description: 'Writes personalized WhatsApp messages per business type using Claude Haiku.',
    tech: 'Claude Haiku',
    owner: 'VP Marketing',
    statsKey: 'pipeline',
    metricLabel: 'Messages generated',
    metricKey: 'new_leads',
    actionLabel: 'Run Pipeline',
    actionPath: '/pipeline',
    details: {
      inputs: 'Business name, type, city',
      outputs: 'Personalized WhatsApp message',
      notes: 'Profession-specific pain points for: dentist, salon, accountant, physiotherapist, lawyer.',
    },
  },
  {
    id: 'outreach',
    name: 'WA Outreach',
    status: 'live',
    runningKey: 'pipeline',
    Icon: Send,
    description: 'Sends personalized WhatsApp messages to prospects via Meta Cloud API.',
    tech: 'Meta WhatsApp Cloud API',
    owner: 'VP Marketing',
    statsKey: 'pipeline',
    metricLabel: 'Messages sent',
    metricKey: 'messages_sent',
    actionLabel: 'Run Pipeline',
    actionPath: '/pipeline',
    details: {
      inputs: 'Phone number + personalized message',
      outputs: 'Delivery status, lead marked contacted',
      notes: 'From +91 120 427 9928. Rate-limited to 1 send per 2 seconds.',
    },
  },
  {
    id: 'email-scraper',
    name: 'Email Scraper',
    status: 'live',
    runningKey: 'email_scraper',
    Icon: Search,
    description: 'Scrapes contact email addresses from business websites. Finds mailto links, contact pages, structured data.',
    tech: 'Python requests + regex',
    owner: 'VP Marketing',
    statsKey: 'email_enrichment',
    metricLabel: 'Emails found',
    metricKey: 'with_email',
    actionLabel: 'Run Enrichment',
    actionPath: '/leads',
    details: {
      inputs: 'Business website URL',
      outputs: 'Contact email address',
      notes: 'Achieves ~37% coverage. JavaScript-rendered contact pages are not scraped.',
    },
  },
  {
    id: 'email-campaign',
    name: 'Email Campaign',
    status: 'live',
    runningKey: 'email_campaign',
    Icon: Mail,
    description: 'Generates personalised cold emails and sends via Resend. Tracks opens and clicks with a Railway-hosted pixel.',
    tech: 'Claude Haiku + Resend',
    owner: 'VP Marketing',
    statsKey: 'email_campaign',
    metricLabel: 'Emails sent',
    metricKey: 'emails_sent',
    actionLabel: 'Go to Leads',
    actionPath: '/leads',
    details: {
      inputs: 'Lead with email address, business_type, city',
      outputs: 'HTML email from henry@practicedesk.live with open/click tracking',
      notes: 'Skips leads with email_sent=true. A/B subject line testing (2 variants).',
    },
  },
  {
    id: 'reply-handler',
    name: 'Reply Handler',
    status: 'building',
    runningKey: null,
    Icon: Reply,
    description: 'Classifies inbound WhatsApp replies with Claude Haiku. Auto-responds to questions, routes interested leads to Demo Booking.',
    tech: 'Claude Haiku + Meta Webhooks',
    owner: 'GM Care',
    statsKey: null,
    details: {
      inputs: 'Inbound WA message + sender phone',
      outputs: 'Intent classification, auto-reply, lead status update',
      notes: 'Webhook: .netlify/functions/outreach-webhook on PracticeDesk site.',
    },
  },
  {
    id: 'demo-booking',
    name: 'Demo Booking',
    status: 'planned',
    runningKey: null,
    Icon: Calendar,
    description: 'Sends a Cal.com booking link to leads classified as interested by Reply Handler. Tracks confirmations.',
    tech: 'Cal.com API',
    owner: 'GM Care',
    statsKey: null,
    details: {},
  },
  {
    id: 'follow-up',
    name: 'Follow-up',
    status: 'planned',
    runningKey: null,
    Icon: RefreshCw,
    description: 'Sends a follow-up WhatsApp message 3 days after initial outreach with no reply.',
    tech: 'Railway Cron + Meta WA',
    owner: 'VP Marketing',
    statsKey: null,
    details: {},
  },
  {
    id: 'voice-followup',
    name: 'Voice Follow-up',
    status: 'planned',
    runningKey: null,
    Icon: Phone,
    description: 'Places an outbound Vapi call after 5 days of silence using the Aria agent.',
    tech: 'Vapi.ai outbound',
    owner: 'VP Marketing',
    statsKey: null,
    details: {},
  },
  {
    id: 'content',
    name: 'Content',
    status: 'planned',
    runningKey: null,
    Icon: FileText,
    description: 'Generates and schedules weekly LinkedIn and Instagram posts per vertical.',
    tech: 'Claude + Meta Graph API',
    owner: 'VP Marketing',
    statsKey: null,
    details: {},
  },
  {
    id: 'observatory',
    name: 'Observatory',
    status: 'planned',
    runningKey: null,
    Icon: Activity,
    description: 'Daily 7am IST digest: Anthropic costs, lead counts, conversion rates → your WhatsApp.',
    tech: 'Railway Cron + Anthropic API',
    owner: 'Observatory (AI)',
    statsKey: null,
    details: {},
  },
  {
    id: 'affiliate',
    name: 'Affiliate Tracker',
    status: 'planned',
    runningKey: null,
    Icon: Share2,
    description: 'Tracks referral links for LegalAidAI advocates. ₹500 on first subscription + ₹500 on renewal.',
    tech: 'Supabase + Razorpay',
    owner: 'VP Marketing',
    statsKey: null,
    details: {},
  },
]

const STATUS_STYLE = {
  live:     { dot: 'bg-green-400',               badge: 'bg-green-900/40 text-green-400 border-green-800/60',   label: 'Live' },
  building: { dot: 'bg-amber-400 animate-pulse', badge: 'bg-amber-900/40 text-amber-400 border-amber-800/60',   label: 'Building' },
  planned:  { dot: 'bg-slate-600',               badge: 'bg-slate-800/60 text-slate-500 border-slate-700/60',   label: 'Planned' },
}

function timeAgo(iso) {
  if (!iso) return null
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function Agents() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const token = localStorage.getItem('pd_token')

  useEffect(() => {
    fetchAgentStats(token).then(setStats).catch(() => {})
    const t = setInterval(() => fetchAgentStats(token).then(setStats).catch(() => {}), 10000)
    return () => clearInterval(t)
  }, [token])

  const liveCount = AGENTS.filter(a => a.status === 'live').length
  const buildingCount = AGENTS.filter(a => a.status === 'building').length
  const plannedCount = AGENTS.filter(a => a.status === 'planned').length

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Agents</h2>
        <p className="text-xs text-slate-500">
          <span className="text-green-400">{liveCount} live</span>
          <span className="mx-1.5 text-slate-700">·</span>
          <span className="text-amber-400">{buildingCount} building</span>
          <span className="mx-1.5 text-slate-700">·</span>
          {plannedCount} planned
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {AGENTS.map((agent) => {
          const s = STATUS_STYLE[agent.status]
          const agentStats = stats && agent.statsKey ? stats[agent.statsKey] : null
          const metric = agentStats && agent.metricKey ? agentStats[agent.metricKey] : null
          const isRunning = agent.runningKey && stats?.running?.[agent.runningKey]
          const lastRun = agentStats?.last_run ? timeAgo(agentStats.last_run) : null
          const { Icon } = agent
          const clickable = agent.status !== 'planned'

          return (
            <div
              key={agent.id}
              onClick={() => clickable && navigate(`/agents/${agent.id}`)}
              className={`bg-[#1e293b] border border-slate-700/40 rounded-lg p-4 flex flex-col gap-3 transition-all ${
                clickable
                  ? 'cursor-pointer hover:border-indigo-500/50 hover:bg-slate-800/40'
                  : 'opacity-55 cursor-default'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 shrink-0 rounded-md bg-slate-700/60 flex items-center justify-center">
                    <Icon size={14} className="text-slate-300" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white leading-tight">{agent.name}</p>
                    <p className="text-xs text-slate-500 truncate">{agent.tech}</p>
                  </div>
                </div>
                <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${s.badge}`}>
                  {s.label}
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-slate-400 leading-relaxed flex-1">{agent.description}</p>

              {/* Footer row */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-700/40">
                {agent.status === 'live' && (
                  isRunning ? (
                    <span className="text-xs text-green-400 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse inline-block" />
                      Running…
                    </span>
                  ) : metric != null ? (
                    <span className="text-xs text-slate-400">
                      <span className="text-white font-medium">{metric.toLocaleString()}</span>
                      {' '}{agent.metricLabel?.toLowerCase()}
                      {lastRun && <span className="text-slate-600 ml-1.5">· {lastRun}</span>}
                    </span>
                  ) : (
                    <span className="text-xs text-slate-600">No runs yet</span>
                  )
                )}
                {agent.status === 'building' && (
                  <span className="text-xs text-amber-500/80">In development</span>
                )}
                {agent.status === 'planned' && (
                  <span className="text-xs text-slate-600">On roadmap</span>
                )}
                {clickable && <ChevronRight size={13} className="text-slate-600 shrink-0" />}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
