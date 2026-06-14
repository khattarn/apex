import { useState } from 'react'
import { TrendingUp, Play, ChevronRight, Copy, Check, AlertTriangle, Loader2, RefreshCw, Zap, BookOpen } from 'lucide-react'

const PRIORITY_STYLE = {
  urgent:   'bg-red-900/60 text-red-300 border border-red-700/50',
  standard: 'bg-slate-800 text-slate-300 border border-slate-600/50',
  low:      'bg-slate-900 text-slate-500 border border-slate-700/40',
}

const PRIORITY_DOT = {
  urgent:   'bg-red-400',
  standard: 'bg-indigo-400',
  low:      'bg-slate-500',
}

// ── Reference data ────────────────────────────────────────────────────────────

const PD_VERTICALS = [
  {
    name: 'Dentist / GP / Doctor',
    hook: 'Patients search for appointments at 10pm. Your phone doesn\'t answer. They book with whoever responds first.',
    stat: '30% no-show reduction in first month. 25% fewer missed enquiries.',
    wa:    '✅ Live — after-hours booking angle',
    waBroadcast: 'v6 in queue — pending Meta approval',
    email: '✅ Live — 6-step drip, henry@practicedesk.live',
    voice: '✅ Live — opener: "Do you ever get patients trying to book after your reception closes?"',
    markets: 'AU primary (WA 12% reply) · US/CA email + voice only',
    tone: 'Pain-first for WA/Voice · Outcome-first for email (lead with 30% stat)',
  },
  {
    name: 'Physiotherapist',
    hook: 'Patients complete one session and disappear — nobody followed up within 48 hours.',
    stat: '$2,000/month recovered in lost rebookings within 30 days.',
    wa:    '✅ Live — 48-hour follow-up angle',
    waBroadcast: 'v6 in queue',
    email: '✅ Live',
    voice: '✅ Live — opener: "Do you find most patients complete one session and then just don\'t rebook?"',
    markets: 'AU primary · US/CA email + voice',
    tone: 'Pain-first. $2K/mo stat is the strongest email subject line hook.',
  },
  {
    name: 'Salon',
    hook: 'Clients don\'t call to cancel — they just don\'t show. No-show rate 15%. WA reminders → under 5%.',
    stat: 'No-show 15% → under 5% in first month.',
    wa:    '✅ Live — no-show + auto-fill waitlist angle',
    waBroadcast: 'v6 in queue',
    email: '✅ Live',
    voice: '✅ Live — opener: "How many no-shows does your salon deal with each week?"',
    markets: 'AU primary · US/CA email + voice',
    tone: 'Conversational — salon owners respond to friendly, direct language, not corporate.',
  },
  {
    name: 'Accountant',
    hook: 'Clients reply to WhatsApp in minutes. They take days on email. 3–5 hrs/week wasted chasing documents.',
    stat: 'Firms reclaim a full day per week.',
    wa:    '✅ Live — document chasing + WA response angle',
    waBroadcast: 'v6 in queue',
    email: '✅ Live',
    voice: '✅ Live — opener: "Is your team spending more than a few hours a week chasing clients for documents?"',
    markets: 'AU primary · CA strong (South Asian diaspora, high WA adoption) · US email only',
    tone: 'Outcome-first for email (reclaim a full day). Pain-first for WA/Voice.',
  },
  {
    name: 'Lawyer / Law Firm',
    hook: '70% of potential clients abandon if there\'s no instant response. Most enquiries come after hours.',
    stat: '20–30% fewer missed enquiries in first month.',
    wa:    '✅ Live — speed of response angle',
    waBroadcast: 'v6 in queue',
    email: '✅ Live',
    voice: '✅ Live — opener: "How many potential clients do you think you lose because they couldn\'t reach anyone quickly?"',
    markets: 'AU primary · US strong (competitive legal market, after-hours response is differentiator)',
    tone: 'Pain-first. 70% abandonment stat is alarming enough to lead with.',
  },
]

const LAI_MODULES = [
  {
    name: 'Advocate (primary revenue)',
    hook: 'Paying ₹25,000–60,000/year for SCC Online? Nyaya Saathi = real Indian Kanoon, no hallucinated citations, ₹2,500/month.',
    stat: '10× research speed. ~5–20% of SCC Online annual cost.',
    wa:    '🔨 Needs commissioning — bar association framing, peer-to-peer, no cold pitch',
    waHi:  '🔨 Needs commissioning — natural Hinglish, legal terms in English ok',
    email: '🔨 Needs commissioning — hallucination risk angle (ChatGPT danger for court submissions)',
    voice: '✅ Live (inbound) — opener: "Are you still paying SCC Online rates for case law?"',
    coldCall: '🔨 Needs setup — outbound cold calling to advocates. Target: individual advocates & small law firms in IN. Script angle: SCC Online cost + hallucination risk. Priya (IN voice agent via Vobiz) to place calls. NOT Aria.',
    affiliate: 'Agent 11 planned — ₹500/₹500 · target Instagram advocates 10K–100K followers',
    markets: 'IN',
    tone: 'Peer-to-peer professional. NOT "ChatGPT for lawyers." NOT "democratisation" language.',
    close: 'Self-serve.',
  },
  {
    name: 'Corporate / In-house Legal',
    hook: 'In-house teams of 1–3 lawyers covering entire companies. External retainers expensive for routine queries.',
    stat: null,
    wa:    '❌ Not this module — B2B decision-makers don\'t respond to WA cold outreach',
    email: '🔨 Needs commissioning — formal English, ROI + risk framing, target GC/CLO/CFO',
    voice: '🔨 Needs commissioning — formal opener, scoped pilot offer, not a demo',
    coldCall: '🔨 Needs setup — outbound cold calling to corporate legal heads (GC/CLO/Head of Legal). Target: mid-size Indian companies with in-house counsel. Script angle: reduce retainer cost for routine queries, scoped pilot. Human close — founder joins after call qualifies interest.',
    markets: 'IN',
    tone: 'Formal English, ROI-driven, risk-aware. Lead with compliance cost and risk reduction.',
    close: 'Human close — founder joins a call. NOT self-serve.',
  },
  {
    name: 'Citizen',
    hook: 'Ordinary citizens can\'t afford a lawyer. Legal notices, FIRs, tenant disputes — in Hindi and English, free.',
    stat: null,
    wa:    '🔨 Needs commissioning — short bilingual, specific situation (cheque bounce, tenant, FIR) · Hindi CTA: "मुफ्त में जानें अपने अधिकार"',
    social: '🔨 Needs commissioning — Know Your Rights cards, Hindi + English',
    email: '❌ Not primary channel',
    voice: '✅ Live — inbound, empathy-first, bilingual, escalate to human if needed',
    markets: 'IN',
    tone: 'Empowering, plain language, Hinglish natural. "You don\'t need a lawyer for this."',
    close: 'Freemium → Premium self-serve.',
  },
]

const PRIORITY_ORDER = [
  { rank: 1,  vertical: 'Dentist AU',              reason: 'Highest WA reply 12%, 30% no-show stat is conversion-ready' },
  { rank: 2,  vertical: 'Salon AU',                reason: 'Simplest pain, fastest close, 15%→5% stat visceral' },
  { rank: 3,  vertical: 'LegalAidAI Advocate EN',  reason: 'Primary revenue, self-serve, ₹5K/mo renewal' },
  { rank: 4,  vertical: 'Physiotherapist AU',      reason: '$2K/mo stat, physio owners responsive to WA' },
  { rank: 5,  vertical: 'Accountant AU + CA',      reason: 'CA strong for this vertical' },
  { rank: 6,  vertical: 'Lawyer AU',               reason: 'Strong stat, longer sales cycle' },
  { rank: 7,  vertical: 'Advocate HI (Hinglish)',  reason: 'Same audience, extends reach' },
  { rank: 8,  vertical: 'Citizen (social)',         reason: 'Volume play, no WA number cost' },
  { rank: 9,  vertical: 'US/CA dentist/physio/salon', reason: 'Email + voice only' },
  { rank: 10, vertical: 'Corporate Legal',          reason: 'Human close — not scalable yet' },
]

const DECISIONS_NEEDED = [
  { item: 'Corporate close process', detail: 'Who runs the call with GC/CLO? Founder or hired closer?' },
  { item: 'Citizen Premium pricing', detail: 'Tier is TBD — needed before launching social ads' },
  { item: 'PracticeDesk India WA number', detail: 'TRAI DND scrub required, separate number needed before IN campaign' },
  { item: 'Twilio outbound compliance', detail: 'Error 21216 blocking all outbound calls — file support ticket or wait for review' },
  { item: 'v6 WA templates Meta approval', detail: '4 tone variants (A/B/C/D) need submission + approval before cron can switch' },
]

// ── Accordion ─────────────────────────────────────────────────────────────────

function AccordionPanel({ title, subtitle, tag, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-slate-700/50 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-slate-800/60 hover:bg-slate-800 transition-colors text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-medium text-slate-200">{title}</p>
              {tag && <span className="text-[10px] bg-slate-700/80 text-slate-400 border border-slate-600/50 rounded px-1.5 py-0.5 font-medium">{tag}</span>}
            </div>
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>
        <ChevronRight size={14} className={`text-slate-500 transition-transform shrink-0 ${open ? 'rotate-90' : ''}`} />
      </button>
      {open && (
        <div className="border-t border-slate-700/40">
          {children}
        </div>
      )}
    </div>
  )
}

// ── Vertical card (inside reference panels) ───────────────────────────────────

function VerticalCard({ v, isModule = false }) {
  return (
    <div className="bg-slate-800/40 border border-slate-700/30 rounded-lg p-4 space-y-3">
      <p className="text-sm font-semibold text-slate-200">{v.name}</p>

      {v.hook && (
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold mb-1">Hook</p>
          <p className="text-xs text-slate-300 italic leading-relaxed">"{v.hook}"</p>
        </div>
      )}

      {v.stat && (
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold mb-1">Key Stat</p>
          <p className="text-xs text-green-400 font-medium">{v.stat}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-1.5">
        {v.wa && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">WA free-form</span>{v.wa}</p>
        )}
        {v.waBroadcast && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">WA broadcast</span>{v.waBroadcast}</p>
        )}
        {v.waHi && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">WA Hinglish</span>{v.waHi}</p>
        )}
        {v.email && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">Email</span>{v.email}</p>
        )}
        {v.voice && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">Voice (Aria)</span>{v.voice}</p>
        )}
        {v.social && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">Social</span>{v.social}</p>
        )}
        {v.coldCall && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block shrink-0">Cold calling</span>{v.coldCall}</p>
        )}
        {v.affiliate && (
          <p className="text-xs text-slate-400"><span className="text-slate-500 w-28 inline-block">Affiliate</span>{v.affiliate}</p>
        )}
      </div>

      <div className="flex flex-wrap gap-3 pt-1 border-t border-slate-700/30 text-[10px]">
        <span className="text-slate-500"><span className="text-slate-400 font-medium">Markets: </span>{v.markets}</span>
        {v.tone && <span className="text-slate-500"><span className="text-slate-400 font-medium">Tone: </span>{v.tone}</span>}
        {v.close && <span className="text-slate-500"><span className="text-slate-400 font-medium">Close: </span>{v.close}</span>}
      </div>
    </div>
  )
}

function PriorityBadge({ p }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${PRIORITY_STYLE[p] || PRIORITY_STYLE.standard}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${PRIORITY_DOT[p] || PRIORITY_DOT.standard}`}/>
      {p}
    </span>
  )
}

function QueueItem({ item, idx, onCommission, commissioning }) {
  const [result, setResult] = useState(null)
  const [copied, setCopied] = useState(false)
  const isLoading = commissioning === idx

  async function handleCommission() {
    const res = await onCommission(item, idx)
    if (res) setResult(res)
  }

  function handleCopy() {
    if (!result) return
    navigator.clipboard.writeText(result.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="border border-slate-700/60 rounded-lg bg-slate-800/40 overflow-hidden">
      {/* Header row */}
      <div className="flex items-start gap-3 px-4 py-3">
        <span className="text-slate-500 text-xs font-mono mt-0.5 w-5 shrink-0">{idx + 1}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <PriorityBadge p={item.priority} />
            <span className="text-slate-200 text-sm font-semibold">
              {item.product === 'practicedesk' ? 'PracticeDesk' : 'LegalAidAI'}
              {' · '}{item.module}
            </span>
            <ChevronRight size={12} className="text-slate-600"/>
            <span className="text-slate-400 text-xs">{item.content_type}</span>
            <span className="text-slate-600 text-xs">·</span>
            <span className="text-slate-400 text-xs">{item.tone}</span>
            <span className="text-slate-600 text-xs">·</span>
            <span className="text-slate-400 text-xs">{item.market}</span>
            {item.language === 'hi' && (
              <span className="bg-amber-900/50 text-amber-300 text-[10px] px-1.5 py-0.5 rounded border border-amber-700/40 font-medium">HI</span>
            )}
          </div>
          <p className="text-slate-500 text-xs italic">{item.reason}</p>
        </div>
        <button
          onClick={handleCommission}
          disabled={isLoading || !!result}
          className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
            result
              ? 'bg-green-900/40 text-green-400 border border-green-700/40 cursor-default'
              : isLoading
              ? 'bg-slate-700 text-slate-400 cursor-wait'
              : 'bg-violet-700 hover:bg-violet-600 text-white cursor-pointer'
          }`}
        >
          {isLoading ? <Loader2 size={12} className="animate-spin"/> : result ? <Check size={12}/> : <Zap size={12}/>}
          {result ? 'Generated' : isLoading ? 'Generating…' : 'Commission'}
        </button>
      </div>

      {/* Result panel */}
      {result && (
        <div className="border-t border-slate-700/60 bg-slate-900/60">
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/40">
            <span className="text-xs text-slate-400">Generated content</span>
            <div className="flex items-center gap-3">
              <span className="text-slate-600 text-[10px]">
                {result.usage?.input_tokens}↑ {result.usage?.output_tokens}↓ tokens
              </span>
              <button onClick={handleCopy} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors">
                {copied ? <Check size={11} className="text-green-400"/> : <Copy size={11}/>}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
          <pre className="px-4 py-3 text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
            {result.content}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function VPMarketing() {
  const [loading, setLoading]         = useState(false)
  const [plan, setPlan]               = useState(null)
  const [error, setError]             = useState(null)
  const [additionalBrief, setAdditionalBrief] = useState('')
  const [includeSignal, setIncludeSignal]     = useState(true)
  const [commissioning, setCommissioning]     = useState(null)  // queue index being commissioned
  const [filter, setFilter]           = useState('all')  // 'all' | 'urgent' | 'standard' | 'low'

  const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const token = localStorage.getItem('pd_token')
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }

  async function generatePlan() {
    setLoading(true)
    setError(null)
    setPlan(null)
    try {
      const res = await fetch(`${BASE}/api/vp-marketing/plan`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ additional_brief: additionalBrief, include_signal: includeSignal }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setPlan(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function commissionItem(item, idx) {
    setCommissioning(idx)
    try {
      const res = await fetch(`${BASE}/api/vp-marketing/commission`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ commission: item, signal_context: plan?.signal_context || '' }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Commission failed')
      return await res.json()
    } catch (e) {
      setError(e.message)
      return null
    } finally {
      setCommissioning(null)
    }
  }

  const visibleQueue = plan?.content_queue?.filter(
    item => filter === 'all' || item.priority === filter
  ) || []

  const urgentCount   = plan?.content_queue?.filter(i => i.priority === 'urgent').length || 0
  const standardCount = plan?.content_queue?.filter(i => i.priority === 'standard').length || 0
  const lowCount      = plan?.content_queue?.filter(i => i.priority === 'low').length || 0

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={18} className="text-violet-400"/>
            <h1 className="text-lg font-semibold text-slate-100">VP Marketing</h1>
            <span className="bg-green-900/50 text-green-400 text-[10px] px-2 py-0.5 rounded-full border border-green-700/40 font-semibold">Agent 12 · live</span>
          </div>
          <p className="text-slate-500 text-sm">
            Generates campaign plans + content queue for Agent 8 (Content). Reads Signal performance data.
          </p>
        </div>
      </div>

      {/* Generate panel */}
      <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Generate Campaign Plan</h2>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <div
              onClick={() => setIncludeSignal(v => !v)}
              className={`w-9 h-5 rounded-full relative transition-colors ${includeSignal ? 'bg-violet-600' : 'bg-slate-600'}`}
            >
              <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${includeSignal ? 'translate-x-4' : 'translate-x-0.5'}`}/>
            </div>
            <span className="text-sm text-slate-300">Pull live Signal data first</span>
          </label>
          <span className="text-slate-600 text-xs">· reads template scores, dead ends, underperformers</span>
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1.5">Additional brief from CEO (optional)</label>
          <textarea
            value={additionalBrief}
            onChange={e => setAdditionalBrief(e.target.value)}
            rows={2}
            placeholder="e.g. Focus on AU dentists this month. Deprioritise US until Twilio compliance is resolved."
            className="w-full bg-slate-900/60 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500 resize-none"
          />
        </div>

        <button
          onClick={generatePlan}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-violet-700 hover:bg-violet-600 disabled:opacity-50 disabled:cursor-wait text-white text-sm font-semibold rounded-lg transition-colors"
        >
          {loading ? <Loader2 size={15} className="animate-spin"/> : <Play size={15}/>}
          {loading ? 'VP Marketing is thinking…' : 'Generate Plan'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-sm text-red-300">
          <AlertTriangle size={15} className="shrink-0 mt-0.5"/>
          {error}
        </div>
      )}

      {/* Plan output */}
      {plan && (
        <>
          {/* Strategic brief */}
          <div className="bg-slate-800/40 border border-violet-700/30 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-violet-300">Strategic Brief</h2>
              <div className="flex items-center gap-3 text-[10px] text-slate-500">
                <span>{plan.usage?.input_tokens?.toLocaleString()}↑ {plan.usage?.output_tokens?.toLocaleString()}↓ tokens</span>
                <span>Queue: {plan.queue_length} items</span>
              </div>
            </div>
            <pre className="text-slate-300 text-xs leading-relaxed whitespace-pre-wrap font-sans">
              {plan.strategic_brief}
            </pre>
          </div>

          {/* Signal context */}
          {plan.signal_context && plan.signal_context !== 'No Signal data — using benchmark strategy.' && (
            <details className="group">
              <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-300 transition-colors list-none flex items-center gap-1.5">
                <ChevronRight size={12} className="group-open:rotate-90 transition-transform"/>
                Signal data used
              </summary>
              <pre className="mt-2 bg-slate-900/60 border border-slate-700/40 rounded-lg px-4 py-3 text-[11px] text-teal-300/80 font-mono whitespace-pre-wrap leading-relaxed">
                {plan.signal_context}
              </pre>
            </details>
          )}

          {/* Content queue */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-300">
                Content Queue
                <span className="ml-2 text-slate-500 font-normal">({plan.queue_length} items)</span>
              </h2>
              <div className="flex items-center gap-1">
                {[
                  { v: 'all',      label: `All ${plan.queue_length}` },
                  { v: 'urgent',   label: `Urgent ${urgentCount}`,   hide: !urgentCount },
                  { v: 'standard', label: `Standard ${standardCount}` },
                  { v: 'low',      label: `Low ${lowCount}` },
                ].filter(f => !f.hide).map(f => (
                  <button
                    key={f.v}
                    onClick={() => setFilter(f.v)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                      filter === f.v ? 'bg-slate-600 text-slate-100' : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              {visibleQueue.map((item, i) => {
                const globalIdx = plan.content_queue.indexOf(item)
                return (
                  <QueueItem
                    key={globalIdx}
                    item={item}
                    idx={globalIdx}
                    onCommission={commissionItem}
                    commissioning={commissioning}
                  />
                )
              })}
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {!plan && !loading && !error && (
        <div className="text-center py-16 text-slate-600">
          <TrendingUp size={32} className="mx-auto mb-3 opacity-30"/>
          <p className="text-sm">Generate a plan to see the content queue.</p>
          <p className="text-xs mt-1">VP Marketing reads Signal data, then commissions Agent 8 for each vertical.</p>
        </div>
      )}

      {/* ── Reference Playbooks ───────────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pt-2">
          <BookOpen size={14} className="text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-400">Reference Playbooks</h2>
          <span className="text-xs text-slate-600">— use as briefing context when commissioning content</span>
        </div>

        {/* PracticeDesk verticals */}
        <AccordionPanel
          title="PracticeDesk — Vertical Playbooks"
          subtitle="5 verticals · AU primary · US/CA email + voice only"
          tag="5 verticals"
        >
          <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
            {PD_VERTICALS.map(v => <VerticalCard key={v.name} v={v} />)}
          </div>
        </AccordionPanel>

        {/* LegalAidAI modules */}
        <AccordionPanel
          title="LegalAidAI — Module Playbooks"
          subtitle="Advocate · Corporate · Citizen · IN market"
          tag="3 modules"
        >
          <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
            {LAI_MODULES.map(v => <VerticalCard key={v.name} v={v} isModule />)}
          </div>
        </AccordionPanel>

        {/* Execution priority */}
        <AccordionPanel
          title="Execution Priority Order"
          subtitle="Agreed 2026-06-13 · Dentist AU = #1, Corporate Legal = #10"
          tag="10 items"
        >
          <div className="p-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-slate-500 border-b border-slate-700/40">
                  <th className="text-left pb-2 font-medium w-8">#</th>
                  <th className="text-left pb-2 font-medium">Vertical / Market</th>
                  <th className="text-left pb-2 font-medium">Why first</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/20">
                {PRIORITY_ORDER.map(r => (
                  <tr key={r.rank} className="text-slate-300">
                    <td className="py-2 text-slate-500 font-mono">{r.rank}</td>
                    <td className="py-2 font-medium text-slate-200">{r.vertical}</td>
                    <td className="py-2 text-slate-400">{r.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </AccordionPanel>

        {/* Decisions needed */}
        <AccordionPanel
          title="Decisions Needed Before Running"
          subtitle="Human input required — these block certain verticals"
          tag={`${DECISIONS_NEEDED.length} items`}
        >
          <div className="p-4 space-y-2">
            {DECISIONS_NEEDED.map(d => (
              <div key={d.item} className="flex gap-3 text-xs">
                <span className="text-amber-400 shrink-0 mt-0.5">⚠</span>
                <div>
                  <p className="text-slate-200 font-medium">{d.item}</p>
                  <p className="text-slate-500 mt-0.5">{d.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </AccordionPanel>
      </div>

      {/* Chain footer */}
      <div className="border-t border-slate-700/40 pt-4 text-xs text-slate-600 flex items-center gap-1.5 flex-wrap">
        <span className="text-indigo-400 font-medium">CEO</span>
        <ChevronRight size={11}/>
        <span className="text-violet-400 font-medium">VP Marketing (you are here)</span>
        <ChevronRight size={11}/>
        <span className="text-teal-400">Signal</span>
        <span className="text-slate-700 mx-1">·</span>
        <span className="text-green-400">Content Agent</span>
        <ChevronRight size={11}/>
        <span className="text-slate-500">Agents 2, 3, 6, 7</span>
      </div>
    </div>
  )
}
