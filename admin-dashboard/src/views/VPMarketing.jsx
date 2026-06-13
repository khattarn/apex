import { useState } from 'react'
import { TrendingUp, Play, ChevronRight, Copy, Check, AlertTriangle, Loader2, RefreshCw, Zap } from 'lucide-react'

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
