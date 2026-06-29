import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MapPin, MessageSquare, Send, Search, Mail,
  Reply, Calendar, RefreshCw, Phone, FileText,
  Activity, Share2, ChevronRight, TrendingUp, Brain,
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
    status: 'live',
    runningKey: null,
    Icon: Reply,
    description: 'Classifies inbound WhatsApp replies with Claude Haiku. Auto-responds to questions, routes interested leads to Demo Booking.',
    tech: 'Claude Haiku + Meta Webhooks',
    owner: 'GM Care',
    statsKey: null,
    details: {
      inputs: 'Inbound WA message + sender phone',
      outputs: 'Intent classification, auto-reply, lead status update',
      notes: 'Webhook: POST /api/webhooks/wa-outreach. Intents: interested | not_interested | question | out_of_office.',
    },
  },
  {
    id: 'demo-booking',
    name: 'Demo Booking',
    status: 'live',
    runningKey: null,
    Icon: Calendar,
    description: 'Sends a Cal.com booking link to leads classified as interested by Reply Handler or Sophie. Tracks confirmations.',
    tech: 'Cal.com API',
    owner: 'GM Care',
    statsKey: null,
    details: {
      inputs: 'Lead marked interested by Reply Handler or Sophie call',
      outputs: 'Cal.com demo link sent via WhatsApp, activity logged',
      notes: 'Integrated into reply_handler.py. Event: PracticeDesk Demo 15min Zoom (ID 5901537).',
    },
  },
  {
    id: 'follow-up',
    name: 'Follow-up',
    status: 'live',
    runningKey: null,
    Icon: RefreshCw,
    description: 'Sends a follow-up WhatsApp message 3 days after initial outreach with no reply.',
    tech: 'APScheduler + Meta WA',
    owner: 'VP Marketing',
    statsKey: null,
    details: {
      inputs: 'Leads contacted 3+ days ago with no reply',
      outputs: 'Follow-up WA message, activity logged',
      notes: 'Runs daily at 9am UTC via APScheduler. agents/followup.py.',
    },
  },
  {
    id: 'voice-followup',
    name: 'Voice Follow-up',
    status: 'live',
    runningKey: null,
    Icon: Phone,
    description: 'Places an outbound Sophie call after 5 days of silence. Routes AU/CA/US via Vapi free number, India via Vobiz SIP.',
    tech: 'Vapi.ai + Vobiz SIP',
    owner: 'VP Marketing',
    statsKey: null,
    details: {
      inputs: 'Leads with no reply after 5 days, within 10am–5pm local time Mon–Fri',
      outputs: 'Outbound call placed via Sophie, activity logged',
      notes: 'agents/voice_outreach.py. Also runs click-to-call (Sophie) hourly on email-clicked leads.',
    },
  },
  {
    id: 'signal',
    name: 'Signal',
    status: 'live',
    runningKey: null,
    Icon: TrendingUp,
    description: 'Marketing Head. Scores templates, detects dead channels, runs A/B tests autonomously, sets quarterly targets, and generates revenue projections.',
    tech: 'Claude Haiku + Supabase',
    owner: 'VP Marketing',
    statsKey: null,
    details: {
      inputs: 'leads, email_sends, lead_activities, template_scores tables',
      outputs: 'Template scores, funnel metrics, projections (base/optimistic/pessimistic), quarterly targets, weekly Marketing Head brief',
      notes: 'Auto-promotes variants with 2× lift. Auto-kills zero-rate templates at 30 sends. Runs Monday 6am UTC.',
    },
  },
  {
    id: 'ceo',
    name: 'CEO',
    status: 'building',
    runningKey: null,
    Icon: Brain,
    description: 'System orchestrator. Issues directives to other agents, monitors health, receives WhatsApp commands from the founder.',
    tech: 'Claude Haiku + APScheduler',
    owner: 'Neeraj',
    statsKey: null,
    details: {
      inputs: 'Agent health, system_journal, founder WhatsApp messages',
      outputs: 'Directives to agents, architecture reviews, WA replies to founder',
      notes: 'Structure built in agents/ceo.py. Activation deferred.',
    },
  },
  {
    id: 'content',
    name: 'Content',
    status: 'live',
    runningKey: null,
    Icon: FileText,
    description: 'Generates WA broadcast templates, cold emails, Sophie voice guidance, and social posts per vertical. Reads Signal performance data to improve on underperformers.',
    tech: 'Claude Sonnet + flat-file RAG',
    owner: 'VP Marketing',
    statsKey: null,
    actionLabel: 'Open Content',
    actionPath: '/content',
    details: {
      inputs: 'Product, module, content type, tone, market, language, optional brief + Signal feedback',
      outputs: 'WA template body · Email HTML + subject · Sophie opener/insight/pain question · LinkedIn/Instagram post',
      notes: 'RAG: knowledge/brand/ + knowledge/practicedesk/ + knowledge/legalaidai/ loaded per request. Accepts signal_feedback to improve on underperforming templates.',
    },
  },
  {
    id: 'vp-marketing',
    name: 'VP Marketing',
    status: 'live',
    runningKey: null,
    Icon: TrendingUp,
    description: 'Orchestrator. Reads Signal performance data, generates campaign plans, and commissions Content Agent (Agent 8) with a prioritised queue. Supervises Agents 1–3, 6, 8, 9, 11.',
    tech: 'Claude Sonnet',
    owner: 'CEO (Neeraj)',
    statsKey: null,
    actionLabel: 'Open VP Marketing',
    actionPath: '/vp-marketing',
    details: {
      inputs: 'Signal performance brief (winning templates, underperformers, dead ends) + optional CEO directive',
      outputs: 'Strategic brief · Ordered content queue (urgent/standard/low) · Commissioned content via Agent 8',
      notes: 'Agent 12. Queue: urgent Signal-flagged underperformers first, then standard plan. POST /api/vp-marketing/plan · /api/vp-marketing/commission.',
    },
  },
  {
    id: 'observatory',
    name: 'Observatory',
    status: 'live',
    runningKey: null,
    Icon: Activity,
    description: 'Daily 7am IST digest: Anthropic costs, lead counts, conversion rates, voice minutes → your WhatsApp.',
    tech: 'APScheduler + Anthropic API',
    owner: 'Observatory (AI)',
    statsKey: null,
    details: {
      inputs: 'Anthropic usage API, Supabase lead stats, Vapi voice minutes',
      outputs: 'WhatsApp digest to founder personal number',
      notes: 'Runs at 1:30am UTC (7am IST) via APScheduler. agents/observatory.py.',
    },
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
