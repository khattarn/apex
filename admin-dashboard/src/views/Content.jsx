import { useState, useCallback } from 'react'
import { Wand2, Copy, Check, RefreshCw, ChevronRight, Info } from 'lucide-react'
import { generateContent, getContentModules } from '../api'

// ── Static config (mirrors content_agent.py) ──────────────────────────────────

const PRODUCTS = {
  practicedesk: {
    label: 'PracticeDesk',
    color: 'indigo',
    modules: [
      { value: 'dentist',         label: 'Dentist' },
      { value: 'doctor',          label: 'Doctor / GP' },
      { value: 'physiotherapist', label: 'Physiotherapist' },
      { value: 'salon',           label: 'Salon' },
      { value: 'accountant',      label: 'Accountant' },
      { value: 'lawyer',          label: 'Lawyer' },
    ],
    defaultMarket: 'AU',
  },
  legalaidai: {
    label: 'LegalAidAI',
    color: 'emerald',
    modules: [
      { value: 'advocate',  label: 'Advocate' },
      { value: 'corporate', label: 'Corporate / In-house' },
      { value: 'citizen',   label: 'Citizen' },
    ],
    defaultMarket: 'IN',
  },
}

const CONTENT_TYPES = [
  { value: 'wa_template',    label: 'WA Broadcast Template', hint: '→ template_manager.py · Agent 3' },
  { value: 'email',          label: 'Email (subject + HTML)', hint: '→ email_templates.py' },
  { value: 'voice_guidance', label: 'Voice Guidance (Aria)', hint: '→ copy.yaml · Agent 7' },
  { value: 'social_post',    label: 'Social Post', hint: '→ manual publish' },
]

const TONES = [
  { value: 'structured',     label: 'Structured', desc: 'Soft open + bullets + CTA (current standard)' },
  { value: 'pain_first',     label: 'Pain-first', desc: 'Opens with a sharp rhetorical question' },
  { value: 'outcome_first',  label: 'Outcome-first', desc: 'Leads with a result stat, punchier' },
  { value: 'conversational', label: 'Conversational', desc: 'No bullets — reads like a personal message' },
]

const MARKETS = ['AU', 'US', 'CA', 'IN']

// ── Routing indicator ─────────────────────────────────────────────────────────

const ROUTING = {
  wa_template:    { label: 'Route: Agents 2 + 3', detail: 'Submit to Meta → template_manager.py → wa_broadcast cron', color: 'text-indigo-400' },
  email:          { label: 'Route: Email pipeline', detail: 'Update email_templates.py → email_personalizer → Resend', color: 'text-blue-400' },
  voice_guidance: { label: 'Route: Agent 7 (Aria)', detail: 'Update copy.yaml → click_caller picks up on next run', color: 'text-purple-400' },
  social_post:    { label: 'Route: Manual publish', detail: 'Copy-paste to LinkedIn / Instagram', color: 'text-slate-400' },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function Select({ label, value, onChange, options, disabled }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1.5">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        className="w-full bg-slate-800 border border-slate-600/60 text-slate-200 text-sm rounded-md px-3 py-2
                   focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {options.map(o => (
          <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>
            {typeof o === 'string' ? o : o.label}
          </option>
        ))}
      </select>
    </div>
  )
}

function RadioGroup({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-2">{label}</label>
      <div className="space-y-1.5">
        {options.map(o => (
          <label
            key={o.value}
            className={`flex items-start gap-3 p-2.5 rounded-md border cursor-pointer transition-colors ${
              value === o.value
                ? 'border-indigo-500/60 bg-indigo-950/40'
                : 'border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <input
              type="radio"
              name={label}
              value={o.value}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
              className="mt-0.5 accent-indigo-500"
            />
            <div className="min-w-0">
              <p className="text-sm text-slate-200">{o.label}</p>
              {o.desc && <p className="text-xs text-slate-500 mt-0.5">{o.desc}</p>}
              {o.hint && <p className="text-xs text-slate-500 font-mono mt-0.5">{o.hint}</p>}
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md
                 bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
    >
      {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

// ── Main view ─────────────────────────────────────────────────────────────────

export default function Content() {
  const [product, setProduct]           = useState('practicedesk')
  const [module, setModule]             = useState('dentist')
  const [contentType, setContentType]   = useState('wa_template')
  const [tone, setTone]                 = useState('structured')
  const [market, setMarket]             = useState('AU')
  const [language, setLanguage]         = useState('en')
  const [platform, setPlatform]         = useState('linkedin')
  const [brief, setBrief]               = useState('')

  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)

  // When product changes, reset module + market to that product's defaults
  function handleProductChange(p) {
    setProduct(p)
    setModule(PRODUCTS[p].modules[0].value)
    setMarket(PRODUCTS[p].defaultMarket)
    setLanguage('en')
  }

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await generateContent({
        product,
        module,
        content_type: contentType,
        tone,
        market,
        language,
        platform: contentType === 'social_post' ? platform : '',
        brief,
      })
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const prod         = PRODUCTS[product]
  const routing      = ROUTING[contentType]
  const showLang     = product === 'legalaidai' || market === 'IN'
  const showPlatform = contentType === 'social_post'

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            <Wand2 size={20} className="text-indigo-400" />
            Content Agent
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Agent 8 · Reports to VP Marketing · Generates copy for Agents 2, 3, 6, 7
          </p>
        </div>
        <div className="hidden md:flex items-center gap-2 text-xs text-slate-500 bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2">
          <Info size={13} className="text-indigo-400 shrink-0" />
          <span>Content is generated for review — approve before deploying to any agent.</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[380px,1fr] gap-6 items-start">

        {/* ── LEFT: Form ──────────────────────────────────────────────────────── */}
        <div className="bg-[#1e293b] rounded-xl border border-slate-700/50 p-5 space-y-5">

          {/* Product */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Product</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(PRODUCTS).map(([key, p]) => (
                <button
                  key={key}
                  onClick={() => handleProductChange(key)}
                  className={`px-3 py-2.5 rounded-md text-sm font-medium border transition-colors text-left ${
                    product === key
                      ? 'border-indigo-500 bg-indigo-950/50 text-indigo-300'
                      : 'border-slate-700/50 text-slate-400 hover:border-slate-600 hover:text-slate-200'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Module */}
          <Select
            label="Vertical / Module"
            value={module}
            onChange={setModule}
            options={prod.modules}
          />

          {/* Content type */}
          <RadioGroup
            label="Content Type"
            value={contentType}
            onChange={setContentType}
            options={CONTENT_TYPES}
          />

          {/* Tone */}
          <RadioGroup
            label="Tone"
            value={tone}
            onChange={setTone}
            options={TONES}
          />

          {/* Market + Language row */}
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Market"
              value={market}
              onChange={setMarket}
              options={MARKETS}
            />
            {showLang ? (
              <Select
                label="Language"
                value={language}
                onChange={setLanguage}
                options={[{ value: 'en', label: 'English' }, { value: 'hi', label: 'Hindi' }]}
              />
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Language</label>
                <div className="px-3 py-2 bg-slate-800/50 border border-slate-700/30 rounded-md text-sm text-slate-500">
                  English
                </div>
              </div>
            )}
          </div>

          {/* Platform (social only) */}
          {showPlatform && (
            <Select
              label="Platform"
              value={platform}
              onChange={setPlatform}
              options={[{ value: 'linkedin', label: 'LinkedIn' }, { value: 'instagram', label: 'Instagram' }]}
            />
          )}

          {/* Brief */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Additional Brief <span className="text-slate-600">(optional)</span>
            </label>
            <textarea
              value={brief}
              onChange={e => setBrief(e.target.value)}
              rows={3}
              placeholder="e.g. Focus on the after-hours missed call angle. Mention the 30% no-show stat."
              className="w-full bg-slate-800 border border-slate-600/60 text-slate-200 text-sm rounded-md px-3 py-2
                         placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1
                         focus:ring-indigo-500/30 resize-none"
            />
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-semibold
                       bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed
                       text-white transition-colors"
          >
            {loading
              ? <><RefreshCw size={15} className="animate-spin" /> Generating…</>
              : <><Wand2 size={15} /> Generate</>
            }
          </button>
        </div>

        {/* ── RIGHT: Output ────────────────────────────────────────────────────── */}
        <div className="space-y-4">

          {/* Routing badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-medium ${routing.color}`}>{routing.label}</span>
            <ChevronRight size={12} className="text-slate-600" />
            <span className="text-xs text-slate-500">{routing.detail}</span>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-950/40 border border-red-700/50 rounded-xl p-4 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Placeholder */}
          {!result && !error && !loading && (
            <div className="bg-[#1e293b] rounded-xl border border-slate-700/50 border-dashed p-12
                            flex flex-col items-center justify-center gap-3 text-center min-h-[320px]">
              <Wand2 size={28} className="text-slate-600" />
              <p className="text-slate-500 text-sm">Configure the brief on the left and click Generate.</p>
              <p className="text-slate-600 text-xs">
                Content is loaded with full knowledge base context<br />
                from your source docs + brand brief.
              </p>
            </div>
          )}

          {/* Loading skeleton */}
          {loading && (
            <div className="bg-[#1e293b] rounded-xl border border-slate-700/50 p-6 min-h-[320px]
                            flex flex-col gap-3 animate-pulse">
              {[80, 60, 90, 50, 70, 40, 80].map((w, i) => (
                <div key={i} className="h-3 bg-slate-700/60 rounded" style={{ width: `${w}%` }} />
              ))}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="bg-[#1e293b] rounded-xl border border-slate-700/50 overflow-hidden">

              {/* Result header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-800/40">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-slate-300">
                    {prod.label} · {prod.modules.find(m => m.value === result.module)?.label} · {
                      CONTENT_TYPES.find(c => c.value === result.content_type)?.label
                    }
                  </span>
                  <span className="text-[10px] text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">
                    {result.tone}
                  </span>
                  <span className="text-[10px] text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">
                    {result.market} · {result.language.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-600">
                    {result.usage?.input_tokens?.toLocaleString()} in · {result.usage?.output_tokens?.toLocaleString()} out
                  </span>
                  <CopyButton text={result.content} />
                  <button
                    onClick={handleGenerate}
                    className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-md
                               bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
                  >
                    <RefreshCw size={12} />
                    Regen
                  </button>
                </div>
              </div>

              {/* Content body */}
              <pre className="p-5 text-sm text-slate-200 font-mono whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-[640px] overflow-y-auto">
                {result.content}
              </pre>

              {/* Footer: what to do next */}
              <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-800/20">
                <p className="text-xs text-slate-500">
                  <span className="text-slate-400 font-medium">Next step: </span>
                  {contentType === 'wa_template' && 'Review copy → update template_manager.py → run submit_v6_templates.py → wait for Meta approval → enable in wa_broadcast.py'}
                  {contentType === 'email' && 'Review → update email_templates.py → redeploy Railway → test with previewEmail()'}
                  {contentType === 'voice_guidance' && 'Review → update outreach-agent/assets/copy.yaml under the relevant vertical → no redeploy needed'}
                  {contentType === 'social_post' && 'Copy text → paste into LinkedIn / Instagram → post manually'}
                </p>
              </div>
            </div>
          )}

          {/* Mandate summary */}
          <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 p-4 space-y-2">
            <p className="text-xs font-medium text-slate-400">Agent 8 — Operating chain</p>
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
              <span>CEO (Neeraj)</span>
              <span className="text-slate-700">→</span>
              <span>VP Marketing</span>
              <span className="text-slate-700">→</span>
              <span className="text-indigo-400 font-medium">Content Agent</span>
              <span className="text-slate-700">→</span>
              <span>Agents 2, 3, 6, 7, 9, 11</span>
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              {[
                { label: 'WA broadcast', agent: 'Agent 3', color: 'text-indigo-400' },
                { label: 'WA personalised', agent: 'Agent 2', color: 'text-indigo-400' },
                { label: 'Email', agent: 'email pipeline', color: 'text-blue-400' },
                { label: 'Voice', agent: 'Agent 7 · Aria', color: 'text-purple-400' },
                { label: 'Follow-up copy', agent: 'Agent 6', color: 'text-teal-400' },
                { label: 'Social', agent: 'manual', color: 'text-slate-400' },
              ].map(({ label, agent, color }) => (
                <span key={label} className="text-[10px] bg-slate-800 border border-slate-700/50 rounded px-2 py-1">
                  <span className="text-slate-400">{label} </span>
                  <span className={color}>→ {agent}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
