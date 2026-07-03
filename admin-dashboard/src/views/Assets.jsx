import { useState, useEffect, useCallback } from 'react'
import {
  Phone, Globe, Server, CreditCard, MessageSquare, Mic,
  Mail, Database, Map, Calendar, Zap, Copy, Check,
  AlertTriangle, ExternalLink, RefreshCw,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Badge({ status }) {
  const map = {
    live:     { label: 'Live',     cls: 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50' },
    active:   { label: 'Active',   cls: 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50' },
    blocked:  { label: 'Blocked',  cls: 'bg-red-900/60 text-red-300 border border-red-700/50' },
    pending:  { label: 'Pending',  cls: 'bg-yellow-900/60 text-yellow-300 border border-yellow-700/50' },
    stubbed:  { label: 'Stubbed',  cls: 'bg-slate-700/60 text-slate-400 border border-slate-600/50' },
    free:     { label: 'Free',     cls: 'bg-blue-900/60 text-blue-300 border border-blue-700/50' },
    'pay-per-use': { label: 'Pay/use', cls: 'bg-indigo-900/60 text-indigo-300 border border-indigo-700/50' },
  }
  const { label, cls } = map[status] || map.active
  return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${cls}`}>{label}</span>
}

function CopyBtn({ value }) {
  const [copied, setCopied] = useState(false)
  function handleCopy() {
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button
      onClick={handleCopy}
      className="ml-1.5 p-0.5 rounded text-slate-600 hover:text-slate-300 transition-colors"
      title="Copy"
    >
      {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
    </button>
  )
}

function Section({ title, icon: Icon, children }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={15} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-widest">{title}</h2>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {children}
      </div>
    </div>
  )
}

function AnthropicBalance() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const token = localStorage.getItem('pd_token')

  const load = useCallback(() => {
    setLoading(true)
    fetch(`${API_BASE}/api/anthropic/spend`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [token])

  useEffect(() => { load() }, [load])

  const colour = data?.total_usd == null ? 'text-slate-500'
    : data.total_usd > 20 ? 'text-red-400'
    : data.total_usd > 8  ? 'text-yellow-400'
    : 'text-emerald-400'

  return (
    <Row label="This month">
      <span className={`font-mono font-semibold ${colour}`}>
        {loading ? '…' : data?.total_usd != null ? `$${data.total_usd.toFixed(2)} spent` : 'unavailable'}
      </span>
      {!loading && (
        <button onClick={load} className="ml-1 text-slate-600 hover:text-slate-400 transition-colors">
          <RefreshCw size={10} />
        </button>
      )}
    </Row>
  )
}

function Card({ name, status, cost, provider, accountId, usedFor, products, notes, warning, consoleUrl, extra }) {
  return (
    <div className="bg-[#1e293b] border border-slate-700/50 rounded-lg p-4 flex flex-col gap-2.5">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-white leading-tight">{name}</p>
        <div className="flex items-center gap-1.5 shrink-0">
          {consoleUrl && (
            <a
              href={consoleUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300 border border-indigo-700/50 rounded px-1.5 py-0.5 transition-colors"
            >
              Console <ExternalLink size={9} />
            </a>
          )}
          <Badge status={status} />
        </div>
      </div>

      {warning && (
        <div className="flex items-start gap-1.5 bg-red-900/30 border border-red-700/40 rounded px-2 py-1.5">
          <AlertTriangle size={11} className="text-red-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-red-300">{warning}</p>
        </div>
      )}

      <div className="space-y-1.5 text-xs">
        {provider && <Row label="Provider">{provider}</Row>}
        {cost && <Row label="Cost">{cost}</Row>}
        {extra}
        {accountId && (
          <Row label="ID / Account">
            <span className="font-mono text-[10px] text-slate-300">{accountId}</span>
            <CopyBtn value={accountId} />
          </Row>
        )}
        {usedFor && <Row label="Used for">{usedFor}</Row>}
        {products && <Row label="Products">{products}</Row>}
        {notes && <Row label="Notes"><span className="text-slate-400">{notes}</span></Row>}
      </div>
    </div>
  )
}

function Row({ label, children }) {
  return (
    <div className="flex gap-2">
      <span className="text-slate-500 w-24 shrink-0">{label}</span>
      <span className="text-slate-300 flex items-center flex-wrap gap-1 min-w-0">{children}</span>
    </div>
  )
}

// ─── Data ────────────────────────────────────────────────────────────────────

const PHONE_NUMBERS = [
  {
    name: '+1 (385) 363-3720',
    status: 'active',
    provider: 'Twilio (Meta-verified)',
    cost: '~$1.15/mo + usage',
    accountId: 'ACecbb29b92a84ef1ddb8e68841fcc6fa4',
    usedFor: 'WA outreach (AU/US/CA), browser dialpad',
    products: 'Apex, PracticeDesk',
    notes: 'Meta Phone Number ID: 1131796990021193 · US number verified 2026-06-05',
  },
  {
    name: '+1 (312) 940-8233',
    status: 'active',
    provider: 'Vapi (free number)',
    cost: 'Free',
    accountId: '50d7061b-ac77-4a4f-b2d5-7430df39b9d5',
    usedFor: 'Henry inbound voice + Sophie outbound (AU/CA/US)',
    products: 'PracticeDesk',
    notes: 'Shared phone number ID for both Henry and Sophie agents',
  },
  {
    name: '+91 9262171423',
    status: 'active',
    provider: 'Vobiz BYOT via Vapi',
    cost: 'Vobiz plan',
    accountId: '55328e0f-b12b-4108-a3b2-ee282aa7bed9',
    usedFor: 'Sophie outbound — India calls only',
    products: 'PracticeDesk India',
    notes: 'SIP trunk: edcf4901.sip.vobiz.ai · Vapi credential ID: e60bddc2',
  },
  {
    name: '+1 (318) 770-6725',
    status: 'blocked',
    provider: 'Twilio',
    cost: '~$1.15/mo',
    accountId: 'PNbfc289130a36ccdfe0b100cf06af8ba0',
    usedFor: 'Henry inbound (confirmed working) + Sophie outbound (blocked)',
    products: 'PracticeDesk',
    warning: 'Outbound error 21216 — Twilio compliance "In Review". Contact support@twilio.com (Acct ACecbb29b).',
    notes: 'Inbound calls connect fine — outbound resumes automatically once Twilio approves the compliance review',
  },
  {
    name: '+1 (289) 514-1951',
    status: 'active',
    provider: 'SignalWire (Vapi BYO)',
    cost: 'SignalWire plan + usage',
    accountId: '13ccacf7-961d-42fb-a2df-b5440ca8af9e',
    usedFor: 'Claire inbound receptionist + Emma outbound patient care',
    products: 'Bright Smile Dental (demo client)',
    notes: 'Ontario, CA · SIP domain uniqe-corporation-vapi-dental.dapp.signalwire.com · inbound credential bfbf497d',
  },
  {
    name: '+1 (587) 209-0343',
    status: 'blocked',
    provider: 'SignalWire (Vapi BYO)',
    cost: 'SignalWire plan + usage',
    accountId: 'a513803a-5229-4ac1-881d-6c89ae708738',
    usedFor: 'Intended: Sophie outbound to Canadian leads',
    products: 'PracticeDesk',
    warning: 'Persistent SIP 407 (proxy auth required) on every outbound attempt, all destinations. Open SignalWire ticket — credential mismatch between Vapi trunk and SignalWire SIP Endpoint.',
    notes: 'Alberta, CA · SIP Endpoint resource 47c76cc5 · send_as correctly set to this number, auth still failing',
  },
  {
    name: '+1 (428) 308-6751',
    status: 'stubbed',
    provider: 'Twilio',
    cost: '~$1.15/mo',
    accountId: 'PNf8620a66e3b6ba54f5aabf7420694616',
    usedFor: 'Unused — purchased but never wired to any app or assistant',
    products: '—',
    notes: 'New Brunswick, CA · still on Twilio default demo voice_url · zero calls ever placed since 2026-06-11 · candidate for reassignment',
  },
  {
    name: '+1 (208) 688-4760',
    status: 'active',
    provider: 'SignalWire',
    cost: 'SignalWire plan + usage',
    accountId: 'a241b24b-7f48-4e13-b3c4-45c37c3c2193',
    usedFor: 'Browser dialpad test number (International tab)',
    products: 'Apex, PracticeDesk',
    notes: 'SIGNALWIRE_TEST_NUMBER / SIGNALWIRE_CALLER_ID env vars',
  },
  {
    name: '+1 (208) 441-4485',
    status: 'pending',
    provider: 'SignalWire',
    cost: 'SignalWire plan + usage',
    accountId: '074110c9-aab7-4c51-9bcc-b731815185a6',
    usedFor: 'Dograh dental inbound proxy (legacy path)',
    products: 'PracticeDesk (legacy)',
    notes: 'Routes to Dograh telephony — superseded by the Vapi+SignalWire Claire/Emma setup on 2026-06-26',
  },
]

const WA_NUMBERS = [
  {
    name: 'Outreach WA — US',
    status: 'active',
    provider: 'Meta WhatsApp Cloud API',
    cost: 'Free (1K service msgs/mo)',
    accountId: '1131796990021193',
    usedFor: 'Outreach to dentists, salons, physios (AU/US/CA)',
    products: 'Apex',
    notes: 'Number: +1 (385) 363-3720 · OUTREACH_WA_PHONE_NUMBER_ID',
  },
  {
    name: 'Outreach WA — India',
    status: 'active',
    provider: 'Meta WhatsApp Cloud API',
    cost: 'Free tier',
    accountId: '1122821020915109',
    usedFor: 'Outreach to Indian prospects (+91 numbers)',
    products: 'Apex',
    notes: 'INDIA_WA_PHONE_NUMBER_ID · Auto-routed from outreach.py',
  },
  {
    name: 'Founder Personal WA',
    status: 'active',
    provider: 'Personal number',
    cost: 'N/A',
    accountId: '+919810982019',
    usedFor: 'Sophie callback alerts, Observatory digest',
    products: 'Apex',
    notes: 'FOUNDER_WHATSAPP_NUMBER env var',
  },
]

const APIS = [
  {
    name: 'Anthropic Claude',
    status: 'active',
    provider: 'Anthropic',
    cost: 'Pay-per-use (token-based)',
    consoleUrl: 'https://console.anthropic.com/settings/billing',
    extra: <AnthropicBalance />,
    accountId: 'ANTHROPIC_API_KEY',
    usedFor: 'AI: Sonnet (complex), Haiku (personalizer, reply classifier)',
    products: 'All 3 products',
    notes: 'Haiku ~$1/1M tokens · Sonnet ~$15/1M tokens',
  },
  {
    name: 'Supabase',
    status: 'active',
    provider: 'Supabase',
    cost: 'Free tier (currently)',
    accountId: 'SUPABASE_URL + SUPABASE_KEY',
    usedFor: 'PostgreSQL DB: leads, campaign_runs, professionals, bookings',
    products: 'PracticeDesk + Apex',
    notes: 'Shared DB — Apex tables: leads, campaign_runs, settings',
  },
  {
    name: 'Firebase Firestore',
    status: 'active',
    provider: 'Google Firebase',
    cost: 'Blaze (pay-per-use)',
    accountId: 'firebase-config.js',
    usedFor: 'DB + Auth for LegalAidAI',
    products: 'LegalAidAI',
    notes: 'Already on Blaze plan — needed for Cloud Functions',
  },
  {
    name: 'Google Maps Places API',
    status: 'active',
    provider: 'Google Cloud',
    cost: 'Pay-per-use (~$32/1K calls)',
    accountId: 'GOOGLE_MAPS_API_KEY',
    usedFor: 'Prospector agent — finds businesses by type + city',
    products: 'Apex',
    notes: 'Also powers email enrichment scraper fallback',
  },
  {
    name: 'Meta WhatsApp API',
    status: 'active',
    provider: 'Meta (Graph API)',
    cost: 'Free (1K msgs/mo) then per-msg',
    accountId: 'App ID: 1325858332273520',
    usedFor: 'WA outreach, reply handling, inbound messages',
    products: 'All 3 products',
    notes: 'WHATSAPP_TOKEN env var · 24h edit window on approved templates',
  },
  {
    name: 'Vapi.ai',
    status: 'active',
    provider: 'Vapi',
    cost: 'Usage-based (~$0.05–0.10/min)',
    accountId: 'VAPI_API_KEY + VAPI_ACCOUNT_ID',
    usedFor: 'Henry inbound agent, Sophie outbound agent, voice calls',
    products: 'PracticeDesk + LegalAidAI',
    notes: '9 agent slots remaining · Agents: Henry (897ca5ec), Sophie outbound',
  },
  {
    name: 'Vobiz (SIP Trunk)',
    status: 'active',
    provider: 'Vobiz',
    cost: 'Vobiz plan',
    accountId: 'edcf4901-9062-44ac-8872-b3d3d36969c8',
    usedFor: 'India BYOT SIP trunk for Sophie → Vapi',
    products: 'PracticeDesk India',
    notes: 'SIP user: practicedesk-priya · Regenerate Auth Token if needed',
  },
  {
    name: 'Twilio',
    status: 'pending',
    provider: 'Twilio',
    cost: '~$1.15/mo per number + usage',
    accountId: 'ACecbb29b92a84ef1ddb8e68841fcc6fa4',
    usedFor: 'Browser dialpad (TwiML App), WA number hosting',
    products: 'PracticeDesk',
    warning: 'Compliance error 21216 blocks all outbound calls. Awaiting Twilio review.',
    notes: 'Balance: $18.82 · TwiML App: AP7da5d1c71ce83e765059f685592c811d',
  },
  {
    name: 'Deepgram',
    status: 'active',
    provider: 'Deepgram',
    cost: 'Pay-per-use',
    accountId: 'DEEPGRAM_API_KEY',
    usedFor: 'Speech-to-text transcription',
    products: 'PracticeDesk',
  },
  {
    name: 'Resend',
    status: 'active',
    provider: 'Resend',
    cost: 'Free tier (3K/mo)',
    accountId: 'RESEND_API_KEY',
    usedFor: 'Transactional email — 8 templates, open/click tracking',
    products: 'PracticeDesk + LegalAidAI',
    notes: 'Sending domain: practicedesk.live · email_sends table in Supabase',
  },
  {
    name: 'Cal.com',
    status: 'active',
    provider: 'Cal.com',
    cost: 'Free',
    accountId: 'CAL_EVENT_ID: 5901537',
    usedFor: 'Demo booking — Sophie sends link when prospect is interested',
    products: 'PracticeDesk',
    notes: '15-min Zoom event · CAL_API_KEY + CAL_USERNAME env vars on Railway',
  },
  {
    name: 'Razorpay',
    status: 'active',
    provider: 'Razorpay',
    cost: '2% transaction fee',
    accountId: 'RAZORPAY_KEY_ID',
    usedFor: 'Payments: ₹2,500 first mo · ₹5,000 renewal (advocate)',
    products: 'LegalAidAI',
    notes: 'Already wired in production',
  },
  {
    name: 'Stripe',
    status: 'stubbed',
    provider: 'Stripe',
    cost: '2.9% + 30¢ per transaction',
    accountId: 'STRIPE_SECRET_KEY',
    usedFor: '$49/$99/$180 monthly plans',
    products: 'PracticeDesk',
    notes: 'Keys present but billing not yet wired',
  },
  {
    name: 'Indian Kanoon API',
    status: 'active',
    provider: 'Indian Kanoon',
    cost: 'API subscription',
    accountId: 'IK_API_KEY',
    usedFor: 'Indian legal database search',
    products: 'LegalAidAI',
  },
]

const DEPLOYMENTS = [
  {
    name: 'Apex Backend (FastAPI)',
    status: 'active',
    provider: 'Railway',
    cost: '~$5/mo',
    accountId: 'serene-passion-production-cd82.up.railway.app',
    usedFor: 'Outreach pipeline, all API endpoints, cron jobs, SSE streaming',
    products: 'Apex',
    notes: 'Project: apex-outreach · Deploy: railway up --service apex --detach',
  },
  {
    name: 'Apex Admin Dashboard',
    status: 'active',
    provider: 'Netlify',
    cost: 'Free tier',
    accountId: 'mpex.netlify.app',
    usedFor: 'Admin UI for all Apex operations',
    products: 'Apex',
    notes: 'Site ID: ffd278b7 · VITE_API_URL → Railway backend',
  },
  {
    name: 'PracticeDesk App',
    status: 'active',
    provider: 'Netlify',
    cost: 'Free tier',
    accountId: 'practicedesk.live',
    usedFor: 'Customer-facing SaaS: dentists, salons, accountants, physios',
    products: 'PracticeDesk',
    notes: 'Also hosts Netlify functions (outreach webhook)',
  },
  {
    name: 'LegalAidAI',
    status: 'active',
    provider: 'Netlify',
    cost: 'Free tier',
    accountId: 'www.legalaidai.in',
    usedFor: 'Citizen + Advocate + Corporate legal AI (India)',
    products: 'LegalAidAI',
    notes: 'Static + Netlify functions · Firebase Firestore backend',
  },
]

// ─── View ────────────────────────────────────────────────────────────────────

const TABS = ['All', 'Phone Numbers', 'WhatsApp', 'APIs & Services', 'Deployments']

export default function Assets() {
  const [tab, setTab] = useState('All')

  const showPhone   = tab === 'All' || tab === 'Phone Numbers'
  const showWA      = tab === 'All' || tab === 'WhatsApp'
  const showAPIs    = tab === 'All' || tab === 'APIs & Services'
  const showDeploys = tab === 'All' || tab === 'Deployments'

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Asset Registry</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            All external subscriptions, phone numbers, APIs, and deployments
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
          {[...PHONE_NUMBERS, ...WA_NUMBERS, ...APIS, ...DEPLOYMENTS].filter(a => a.status === 'active' || a.status === 'live' || a.status === 'free').length} active
          <span className="ml-2 w-2 h-2 rounded-full bg-red-500 inline-block"></span>
          {[...PHONE_NUMBERS, ...WA_NUMBERS, ...APIS, ...DEPLOYMENTS].filter(a => a.status === 'blocked').length} blocked
          <span className="ml-2 w-2 h-2 rounded-full bg-yellow-500 inline-block"></span>
          {[...PHONE_NUMBERS, ...WA_NUMBERS, ...APIS, ...DEPLOYMENTS].filter(a => a.status === 'pending' || a.status === 'stubbed').length} pending
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#0f172a] rounded-lg p-1 w-fit">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              tab === t
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Sections */}
      {showPhone && (
        <Section title="Phone Numbers" icon={Phone}>
          {PHONE_NUMBERS.map(a => <Card key={a.name} {...a} />)}
        </Section>
      )}

      {showWA && (
        <Section title="WhatsApp Numbers" icon={MessageSquare}>
          {WA_NUMBERS.map(a => <Card key={a.name} {...a} />)}
        </Section>
      )}

      {showAPIs && (
        <Section title="APIs & Services" icon={Zap}>
          {APIS.map(a => <Card key={a.name} {...a} />)}
        </Section>
      )}

      {showDeploys && (
        <Section title="Deployments & Hosting" icon={Server}>
          {DEPLOYMENTS.map(a => <Card key={a.name} {...a} />)}
        </Section>
      )}
    </div>
  )
}
