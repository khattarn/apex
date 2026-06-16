import { useState, useEffect, useRef } from 'react'
import {
  Instagram, Send, UserCheck, DollarSign, RefreshCw,
  ChevronDown, Copy, Check, AlertCircle, Play, Sparkles
} from 'lucide-react'
import {
  getAffiliates, getAffiliateStats, getCommissions,
  scrapeAffiliates, inviteAffiliate, onboardAffiliate, payCommission,
  generateContent,
} from '../api'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const STATUS_STYLES = {
  prospect: 'bg-slate-700 text-slate-300',
  invited:  'bg-amber-900/60 text-amber-300',
  active:   'bg-green-900/60 text-green-300',
  inactive: 'bg-red-900/60 text-red-400',
}

function StatusBadge({ status }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_STYLES[status] || STATUS_STYLES.prospect}`}>
      {status}
    </span>
  )
}

function fmt(n) {
  if (!n) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toLocaleString()
}

function fmtDate(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

// ── Onboard modal ─────────────────────────────────────────────────────────────

function OnboardModal({ affiliate, onClose, onDone }) {
  const [upi, setUpi] = useState('')
  const [bar, setBar] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (!upi.trim()) { setError('UPI ID is required'); return }
    setLoading(true)
    try {
      await onboardAffiliate(affiliate.id, upi.trim(), bar.trim())
      onDone()
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] border border-slate-700 rounded-lg w-full max-w-md p-6 space-y-4">
        <h3 className="font-semibold text-base">Onboard @{affiliate.instagram_handle}</h3>
        <p className="text-xs text-slate-400">This generates a referral code and activates the affiliate.</p>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400 block mb-1">UPI ID *</label>
            <input
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              placeholder="name@upi or 9876543210@paytm"
              value={upi}
              onChange={e => setUpi(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Bar Enrollment No. (optional)</label>
            <input
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              placeholder="MH/1234/2018"
              value={bar}
              onChange={e => setBar(e.target.value)}
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded bg-slate-700 hover:bg-slate-600 transition-colors">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={loading}
            className="text-sm px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Activating...' : 'Activate Affiliate'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Scrape panel ──────────────────────────────────────────────────────────────

function ScrapePanel({ onDone }) {
  const [running, setRunning] = useState(false)
  const [log, setLog] = useState([])
  const [maxPer, setMaxPer] = useState(30)
  const logRef = useRef(null)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  function startScrape() {
    setLog([])
    setRunning(true)
    const token = localStorage.getItem('pd_token')
    const es = new EventSource(
      `${BASE}/api/affiliates/scrape?max_per_hashtag=${maxPer}&_auth=${token}`
    )

    // EventSource doesn't support custom headers; use query param token approach via proxy
    // Instead we use the fetch-based SSE approach
    es.close()

    // Use fetch SSE (POST — endpoint requires auth header)
    const ctrl = new AbortController()
    fetch(`${BASE}/api/affiliates/scrape?max_per_hashtag=${maxPer}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      signal: ctrl.signal,
    }).then(async res => {
      const reader = res.body.getReader()
      const dec = new TextDecoder()
      let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop()
        for (const part of parts) {
          const dataLine = part.split('\n').find(l => l.startsWith('data:'))
          if (!dataLine) continue
          try {
            const obj = JSON.parse(dataLine.slice(5).trim())
            if (obj.type === 'log') setLog(l => [...l, obj.line])
            if (obj.type === 'done') { setRunning(false); onDone(); }
            if (obj.type === 'error') { setLog(l => [...l, `Error: ${obj.message}`]); setRunning(false); }
          } catch {}
        }
      }
      setRunning(false)
    }).catch(e => {
      if (e.name !== 'AbortError') setLog(l => [...l, `Connection error: ${e.message}`])
      setRunning(false)
    })
  }

  return (
    <div className="bg-[#1e293b] border border-slate-700 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <Instagram size={16} className="text-pink-400" />
          <span className="text-sm font-medium">Instagram Scraper</span>
          <span className="text-xs text-slate-500">@leaglebeagle account · 14 legal hashtags</span>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Posts per hashtag:</label>
          <select
            value={maxPer}
            onChange={e => setMaxPer(Number(e.target.value))}
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white"
            disabled={running}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
          <button
            onClick={startScrape}
            disabled={running}
            className="flex items-center gap-2 bg-pink-600 hover:bg-pink-500 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded transition-colors"
          >
            <Play size={13} />
            {running ? 'Scraping...' : 'Run Scrape'}
          </button>
        </div>
      </div>

      {log.length > 0 && (
        <div
          ref={logRef}
          className="bg-[#0f172a] rounded p-3 h-48 overflow-y-auto font-mono text-xs space-y-0.5"
        >
          {log.map((line, i) => (
            <div key={i} className={
              line.startsWith('+') ? 'text-green-400' :
              line.startsWith('#') ? 'text-pink-400 font-semibold mt-1' :
              line.startsWith('Error') ? 'text-red-400' :
              'text-slate-400'
            }>{line || ' '}</div>
          ))}
          {running && <div className="text-slate-500 animate-pulse">▌</div>}
        </div>
      )}
    </div>
  )
}

// ── DM Templates panel ───────────────────────────────────────────────────────

function parseDmVariations(text) {
  // Try --- dividers first
  let parts = text.split(/\n-{3,}\n/)
  if (parts.length >= 3) return parts.map(p => p.trim()).filter(Boolean)
  // Try **A / **B / **C headers
  parts = text.split(/(?=\n\*\*[A-C][\s—\-])/)
  if (parts.length >= 3) return parts.map(p => p.trim()).filter(Boolean)
  // Try bare A: / B: / C: at line start
  parts = text.split(/\n(?=[A-C]\s*[:\-—])/)
  if (parts.length >= 3) return parts.map(p => p.trim()).filter(Boolean)
  return null
}

function DmTemplatesPanel() {
  const [brief, setBrief]     = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState('')
  const [error, setError]     = useState('')
  const [copied, setCopied]   = useState(null)

  async function generate() {
    setLoading(true); setError(''); setResult('')
    try {
      const res = await generateContent({
        product: 'legalaidai',
        module: 'advocate',
        content_type: 'affiliate_dm',
        tone: 'conversational',
        market: 'IN',
        language: 'en',
        brief: brief.trim() ||
          'Instagram DM outreach to Indian advocate influencers (10K–100K followers). Goal: recruit them as Nyaya Saathi affiliates. Draw on specific product features — real Indian Kanoon citations, 44 document templates, WhatsApp access, BNSS mapping — to make the pitch credible and concrete.',
      })
      setResult(res.content)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function copy(text, key) {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  const variations = result ? parseDmVariations(result) : null

  const LABELS = ['Variation A', 'Variation B', 'Variation C']

  return (
    <div className="space-y-4">
      <div className="bg-[#1e293b] border border-slate-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles size={15} className="text-indigo-400" />
          <span className="text-sm font-medium">Generate DM Templates</span>
          <span className="text-xs text-slate-500">Content Agent · legalaidai:advocate · affiliate_dm</span>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Additional brief (optional)</label>
          <textarea
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none placeholder-slate-600"
            rows={2}
            placeholder="e.g. Focus on the 2-minute bail draft angle. Emphasise BNSS migration pain for criminal lawyers."
            value={brief}
            onChange={e => setBrief(e.target.value)}
          />
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded transition-colors"
        >
          <Sparkles size={13} />
          {loading ? 'Generating...' : 'Generate 3 DM Variations'}
        </button>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>

      {result && (
        <div className="space-y-3">
          {variations ? variations.map((v, i) => (
            <div key={i} className="bg-[#1e293b] border border-slate-700 rounded-lg p-4">
              <div className="flex items-start justify-between gap-2 mb-3">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wide">
                  {LABELS[i] || `Variation ${i + 1}`}
                </span>
                <button
                  onClick={() => copy(v.replace(/^\*\*[A-C][^\n]*\n?/, '').trim(), i)}
                  className="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors shrink-0"
                >
                  {copied === i ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
                  {copied === i ? 'Copied' : 'Copy'}
                </button>
              </div>
              <pre className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
                {v.replace(/^\*\*[A-C][^\n]*\n?/, '').trim()}
              </pre>
            </div>
          )) : (
            <div className="bg-[#1e293b] border border-slate-700 rounded-lg p-4">
              <div className="flex items-start justify-between gap-2 mb-3">
                <span className="text-xs font-semibold text-indigo-400">Generated DM Templates</span>
                <button
                  onClick={() => copy(result, 'all')}
                  className="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
                >
                  {copied === 'all' ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
                  {copied === 'all' ? 'Copied' : 'Copy all'}
                </button>
              </div>
              <pre className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">{result}</pre>
            </div>
          )}
          <p className="text-xs text-slate-500 px-1">
            Replace [Name] and [specific detail] before sending. Personalise the opening line per account.
          </p>
        </div>
      )}
    </div>
  )
}

// ── Referral link copy ────────────────────────────────────────────────────────

function ReferralLink({ code }) {
  const [copied, setCopied] = useState(false)
  const url = `https://legalaidai.in/advocate?ref=${code}`
  function copy() {
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={copy} className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 text-xs transition-colors">
      {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
      <span className="font-mono">{code}</span>
    </button>
  )
}

// ── Main view ─────────────────────────────────────────────────────────────────

export default function Affiliates() {
  const [tab, setTab] = useState('prospects')
  const [affiliates, setAffiliates] = useState([])
  const [commissions, setCommissions] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inviting, setInviting] = useState(null)
  const [onboarding, setOnboarding] = useState(null)
  const [paying, setPaying] = useState(null)

  function load() {
    setLoading(true)
    Promise.all([
      getAffiliates(),
      getAffiliateStats(),
      getCommissions(),
    ]).then(([affs, st, comms]) => {
      setAffiliates(affs.data || [])
      setStats(st)
      setCommissions(comms.data || [])
    }).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const prospects = affiliates.filter(a => a.status === 'prospect')
  const invited   = affiliates.filter(a => a.status === 'invited')
  const active    = affiliates.filter(a => a.status === 'active')
  const pendingComms = commissions.filter(c => c.status === 'pending')
  const paidComms    = commissions.filter(c => c.status === 'paid')

  async function handleInvite(aff) {
    setInviting(aff.id)
    try {
      await inviteAffiliate(aff.id)
      load()
    } catch (e) {
      alert(`Invite failed: ${e.message}`)
    } finally {
      setInviting(null)
    }
  }

  async function handlePay(comm) {
    setPaying(comm.id)
    try {
      await payCommission(comm.id)
      load()
    } catch (e) {
      alert(`Failed: ${e.message}`)
    } finally {
      setPaying(null)
    }
  }

  const TABS = [
    { key: 'prospects',    label: 'Prospects',       count: prospects.length + invited.length },
    { key: 'active',       label: 'Active Affiliates', count: active.length },
    { key: 'commissions',  label: 'Commissions',     count: pendingComms.length },
    { key: 'dm_templates', label: 'DM Templates',    count: 0 },
  ]

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-base font-semibold">Affiliate Programme</h2>
          <p className="text-xs text-slate-500 mt-0.5">LegalAidAI · ₹500/conversion · ₹500/renewal</p>
        </div>
        <button onClick={load} className="p-2 rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Stat cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Prospects', value: stats.prospect, color: 'text-slate-300' },
            { label: 'Invited',   value: stats.invited,  color: 'text-amber-400' },
            { label: 'Active',    value: stats.active,   color: 'text-green-400' },
            { label: 'Pending Payouts', value: `₹${pendingComms.reduce((s,c) => s + (c.amount||0), 0).toLocaleString()}`, color: 'text-indigo-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-[#1e293b] border border-slate-700 rounded-lg p-3">
              <p className="text-xs text-slate-500">{label}</p>
              <p className={`text-xl font-semibold mt-1 ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Scrape panel — always visible */}
      <ScrapePanel onDone={load} />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-700">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className="ml-2 text-xs bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded-full">{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Prospects tab */}
      {tab === 'prospects' && (
        <div className="space-y-2">
          {loading && <p className="text-sm text-slate-500">Loading...</p>}
          {!loading && prospects.length === 0 && invited.length === 0 && (
            <p className="text-sm text-slate-500">No prospects yet — run the scraper above.</p>
          )}
          {[...invited, ...prospects].map(aff => (
            <div key={aff.id} className="bg-[#1e293b] border border-slate-700 rounded-lg px-4 py-3 flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Instagram size={14} className="text-pink-400 shrink-0" />
                <a
                  href={`https://instagram.com/${aff.instagram_handle}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-indigo-400 hover:text-indigo-300 truncate"
                >
                  @{aff.instagram_handle}
                </a>
                {aff.name && aff.name !== aff.instagram_handle && (
                  <span className="text-xs text-slate-500 truncate">{aff.name}</span>
                )}
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-400 shrink-0">
                {aff.follower_count > 0 && <span>{fmt(aff.follower_count)} followers</span>}
                {aff.phone && <span className="text-green-400">{aff.phone}</span>}
                {!aff.phone && <span className="text-red-400 flex items-center gap-1"><AlertCircle size={11} /> no phone</span>}
                <StatusBadge status={aff.status} />
                <span className="text-slate-600">{fmtDate(aff.scraped_at)}</span>
              </div>

              <div className="flex gap-2 shrink-0">
                {aff.status === 'prospect' && (
                  <button
                    onClick={() => handleInvite(aff)}
                    disabled={!aff.phone || inviting === aff.id}
                    title={!aff.phone ? 'No phone number extracted from bio' : 'Send WhatsApp invite'}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-green-900/50 text-green-300 hover:bg-green-800/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send size={11} />
                    {inviting === aff.id ? 'Sending...' : 'Invite'}
                  </button>
                )}
                {(aff.status === 'invited' || aff.status === 'prospect') && (
                  <button
                    onClick={() => setOnboarding(aff)}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-indigo-900/50 text-indigo-300 hover:bg-indigo-800/60 transition-colors"
                  >
                    <UserCheck size={11} />
                    Onboard
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Active Affiliates tab */}
      {tab === 'active' && (
        <div className="space-y-2">
          {loading && <p className="text-sm text-slate-500">Loading...</p>}
          {!loading && active.length === 0 && (
            <p className="text-sm text-slate-500">No active affiliates yet. Onboard a prospect to get started.</p>
          )}
          {active.map(aff => (
            <div key={aff.id} className="bg-[#1e293b] border border-slate-700 rounded-lg px-4 py-3 space-y-2">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Instagram size={14} className="text-pink-400 shrink-0" />
                  <a
                    href={`https://instagram.com/${aff.instagram_handle}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-indigo-400 hover:text-indigo-300"
                  >
                    @{aff.instagram_handle}
                  </a>
                  {aff.name && <span className="text-xs text-slate-500">{aff.name}</span>}
                  <StatusBadge status="active" />
                </div>
                <div className="text-xs text-slate-400 shrink-0">Active since {fmtDate(aff.onboarded_at)}</div>
              </div>

              <div className="flex items-center gap-6 text-xs flex-wrap">
                {aff.referral_code && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Referral link:</span>
                    <ReferralLink code={aff.referral_code} />
                  </div>
                )}
                {aff.upi_id && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">UPI:</span>
                    <span className="text-slate-300 font-mono">{aff.upi_id}</span>
                  </div>
                )}
                {aff.phone && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Phone:</span>
                    <span className="text-slate-300">{aff.phone}</span>
                  </div>
                )}
                {aff.bar_enrollment && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Bar no.:</span>
                    <span className="text-slate-300">{aff.bar_enrollment}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Commissions tab */}
      {tab === 'commissions' && (
        <div className="space-y-4">
          {pendingComms.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-amber-400 mb-2 uppercase tracking-wide">
                Pending Payouts — ₹{pendingComms.reduce((s,c) => s + (c.amount||0), 0).toLocaleString()} total
              </h3>
              <div className="space-y-2">
                {pendingComms.map(c => (
                  <div key={c.id} className="bg-[#1e293b] border border-amber-900/40 rounded-lg px-4 py-3 flex items-center gap-3 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">
                        @{c.affiliates?.instagram_handle || '—'}
                        <span className="text-slate-500 font-normal ml-2">{c.affiliates?.name}</span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {c.type === 'conversion' ? 'New subscriber' : 'Renewal'} ·{' '}
                        {c.referrals?.user_email || 'unknown subscriber'} ·{' '}
                        {fmtDate(c.created_at)}
                      </div>
                      {c.affiliates?.upi_id && (
                        <div className="text-xs text-slate-500 mt-0.5 font-mono">UPI: {c.affiliates.upi_id}</div>
                      )}
                    </div>
                    <div className="text-green-400 font-semibold text-sm shrink-0">₹{c.amount}</div>
                    <button
                      onClick={() => handlePay(c)}
                      disabled={paying === c.id}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-green-900/50 text-green-300 hover:bg-green-800/60 disabled:opacity-50 transition-colors shrink-0"
                    >
                      <DollarSign size={11} />
                      {paying === c.id ? 'Marking...' : 'Mark Paid'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {paidComms.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wide">Paid</h3>
              <div className="space-y-2">
                {paidComms.map(c => (
                  <div key={c.id} className="bg-[#1e293b] border border-slate-700/50 rounded-lg px-4 py-3 flex items-center gap-3 flex-wrap opacity-60">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm">@{c.affiliates?.instagram_handle || '—'}</div>
                      <div className="text-xs text-slate-500">
                        {c.type} · paid {fmtDate(c.paid_date)}
                      </div>
                    </div>
                    <div className="text-slate-400 text-sm">₹{c.amount}</div>
                    <span className="text-xs text-green-600">Paid</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading && <p className="text-sm text-slate-500">Loading...</p>}
          {!loading && commissions.length === 0 && (
            <p className="text-sm text-slate-500">No commissions yet. They appear here when referred advocates subscribe on LegalAidAI.</p>
          )}
        </div>
      )}

      {/* DM Templates tab */}
      {tab === 'dm_templates' && <DmTemplatesPanel />}

      {/* Onboard modal */}
      {onboarding && (
        <OnboardModal
          affiliate={onboarding}
          onClose={() => setOnboarding(null)}
          onDone={load}
        />
      )}
    </div>
  )
}
