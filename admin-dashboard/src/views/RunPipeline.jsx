import { useEffect, useRef, useState } from 'react'
import { Play, Square, Search, CheckCircle } from 'lucide-react'
import { streamPipeline, streamEnrich, getStats } from '../api'

const BUSINESS_TYPES = ['dentist', 'salon', 'accountant', 'physiotherapist', 'lawyer']

const CITIES = {
  US: [
    'New York','Los Angeles','Chicago','Houston','Phoenix','Philadelphia',
    'San Antonio','San Diego','Dallas','San Jose','Austin','Jacksonville',
    'Fort Worth','Columbus','Charlotte','Indianapolis','San Francisco',
    'Seattle','Denver','Nashville','Portland','Las Vegas','Memphis',
    'Louisville','Baltimore','Milwaukee','Atlanta','Miami','Minneapolis',
    'Tampa','Raleigh','New Orleans','Cleveland','Sacramento','Tucson',
    'Omaha','Colorado Springs','Virginia Beach','Long Beach','Fresno',
  ],
  CA: [
    'Toronto','Vancouver','Calgary','Edmonton','Montreal','Ottawa',
    'Winnipeg','Quebec City','Hamilton','Kitchener','London','Halifax',
    'Victoria','Windsor','Saskatoon','Regina','Kelowna','Barrie',
    'Abbotsford','Mississauga','Brampton','Markham','Richmond Hill',
  ],
  AU: [
    'Sydney','Melbourne','Brisbane','Perth','Adelaide','Gold Coast',
    'Canberra','Newcastle','Sunshine Coast','Wollongong','Hobart',
    'Darwin','Cairns','Toowoomba','Ballarat','Geelong','Bendigo',
    'Launceston','Mackay','Rockhampton','Townsville','Mandurah',
  ],
  UK: [
    'London','Birmingham','Manchester','Glasgow','Leeds','Liverpool',
    'Sheffield','Edinburgh','Bristol','Leicester','Coventry','Bradford',
    'Nottingham','Cardiff','Belfast','Southampton','Reading','Aberdeen',
    'Newcastle','Oxford','Cambridge','Brighton','Exeter','Norwich',
  ],
}

const FLAG = { US: '🇺🇸', CA: '🇨🇦', AU: '🇦🇺', UK: '🇬🇧' }

// phase: idle | prospecting | enriching | done
export default function RunPipeline() {
  const [form, setForm] = useState({
    business_type: 'dentist',
    city: '',
    max_prospects: 5,
    send_whatsapp: false,
  })
  const [phase, setPhase]       = useState('idle')
  const [lines, setLines]       = useState([])
  const [summary, setSummary]   = useState(null)  // { prospects_found, new_leads, messages_sent, enriched, queued }
  const [error, setError]       = useState(null)
  const [activeTab, setActiveTab]   = useState('CA')
  const [citySearch, setCitySearch] = useState('')
  const [cityStats, setCityStats]   = useState({})
  const stopRef = useRef(null)
  const logRef  = useRef(null)

  useEffect(() => {
    getStats().then(s => setCityStats(s.by_city || {})).catch(() => {})
  }, [])

  function addLine(line) {
    setLines(l => [...l, line])
    setTimeout(() => logRef.current?.scrollTo(0, logRef.current.scrollHeight), 0)
  }

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  function selectedCities() {
    return form.city.split(',').map(c => c.trim().toLowerCase()).filter(Boolean)
  }

  function toggleCity(city) {
    const current = form.city.split(',').map(c => c.trim()).filter(Boolean)
    const idx = current.findIndex(c => c.toLowerCase() === city.toLowerCase())
    if (idx >= 0) current.splice(idx, 1)
    else current.push(city)
    set('city', current.join(', '))
  }

  function startEnrichment(prospectSummary) {
    setPhase('enriching')
    addLine('')
    addLine('── Phase 2: Email Enrichment ─────────────────────')

    const stop = streamEnrich(
      (line) => addLine(line),
      (result) => {
        setPhase('done')
        setSummary({ ...prospectSummary, enriched: result.enriched || 0, queued: result.queued || 0 })
        getStats().then(s => setCityStats(s.by_city || {})).catch(() => {})
        stopRef.current = null
      },
      (msg) => {
        setPhase('done')
        setError(`Enrichment: ${msg}`)
        setSummary({ ...prospectSummary, enriched: 0, queued: 0 })
        stopRef.current = null
      }
    )
    stopRef.current = stop
  }

  function handleRun() {
    if (!form.city.trim()) return
    setLines([])
    setSummary(null)
    setError(null)
    setPhase('prospecting')
    addLine('── Phase 1: Prospecting ──────────────────────────')

    const stop = streamPipeline(
      { ...form, max_prospects: Number(form.max_prospects) },
      (line) => addLine(line),
      (result) => {
        addLine('')
        addLine(`✓ Prospecting complete — ${result.new_leads ?? 0} new leads found`)
        startEnrichment(result)
      },
      (msg) => {
        setError(msg)
        setPhase('idle')
        stopRef.current = null
      }
    )
    stopRef.current = stop
  }

  function handleStop() {
    stopRef.current?.()
    setPhase('idle')
  }

  const running = phase === 'prospecting' || phase === 'enriching'

  const filteredCities = CITIES[activeTab].filter(c =>
    c.toLowerCase().includes(citySearch.toLowerCase())
  )
  const selected = selectedCities()

  const phaseLabel = {
    idle:        null,
    prospecting: { text: 'Phase 1 — Prospecting…',   color: 'text-amber-400', dot: 'bg-amber-400' },
    enriching:   { text: 'Phase 2 — Enriching emails…', color: 'text-indigo-400', dot: 'bg-indigo-400' },
    done:        { text: 'Complete', color: 'text-green-400', dot: 'bg-green-400' },
  }[phase]

  return (
    <div className="p-4 md:p-6 flex flex-col lg:flex-row gap-6 items-start">

      {/* ── LEFT ─────────────────────────────────────────── */}
      <div className="flex-1 min-w-0 w-full space-y-5">
        <h2 className="text-base font-semibold">Run Pipeline</h2>

        <div className="bg-[#1e293b] rounded-lg p-5 border border-slate-700/40 space-y-4">

          {/* Business type */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Business Type</label>
            <select
              value={form.business_type}
              onChange={e => set('business_type', e.target.value)}
              disabled={running}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            >
              {BUSINESS_TYPES.map(t => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>

          {/* City */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">
              City <span className="text-slate-600">(comma-separated · click cities on right)</span>
            </label>
            <input
              type="text"
              value={form.city}
              onChange={e => set('city', e.target.value)}
              disabled={running}
              placeholder="e.g. Toronto, Vancouver, Calgary"
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
            {selected.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {selected.map(c => (
                  <span
                    key={c}
                    onClick={() => !running && toggleCity(c)}
                    className="inline-flex items-center gap-1 bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 text-xs px-2 py-0.5 rounded-full cursor-pointer hover:bg-red-900/30 hover:border-red-500/40 hover:text-red-300 transition-colors"
                    title="Click to remove"
                  >
                    {c} ×
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Max prospects */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">
              Max Prospects <span className="text-slate-600">(1–50 per city)</span>
            </label>
            <input
              type="number" min={1} max={50}
              value={form.max_prospects}
              onChange={e => set('max_prospects', e.target.value)}
              disabled={running}
              className="w-32 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
          </div>

          {/* Mode */}
          <div>
            <label className="block text-xs text-slate-400 mb-2">Mode</label>
            <div className="flex flex-wrap gap-2">
              {[false, true].map(live => (
                <button
                  key={String(live)}
                  onClick={() => set('send_whatsapp', live)}
                  disabled={running}
                  className={`px-4 py-1.5 rounded text-xs font-medium border transition-colors disabled:opacity-50 ${
                    form.send_whatsapp === live
                      ? live
                        ? 'bg-green-700 border-green-600 text-white'
                        : 'bg-indigo-700 border-indigo-600 text-white'
                      : 'bg-transparent border-slate-600 text-slate-400 hover:border-slate-400'
                  }`}
                >
                  {live ? 'Live (send WhatsApp)' : 'Dry Run (preview only)'}
                </button>
              ))}
            </div>
          </div>

          {/* Run / Stop */}
          <div className="pt-1 flex items-center gap-4">
            {!running ? (
              <button
                onClick={handleRun}
                disabled={!form.city.trim()}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2.5 rounded transition-colors"
              >
                <Play size={14} />
                Run Pipeline
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="flex items-center gap-2 bg-red-700 hover:bg-red-600 text-white text-sm font-medium px-5 py-2.5 rounded transition-colors"
              >
                <Square size={14} />
                Stop
              </button>
            )}
            {phaseLabel && (
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full shrink-0 ${phaseLabel.dot} ${running ? 'animate-pulse' : ''}`} />
                <span className={`text-xs font-medium ${phaseLabel.color}`}>{phaseLabel.text}</span>
              </div>
            )}
          </div>
        </div>

        {/* Log */}
        {lines.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-700/40 overflow-hidden">
            <div className="px-4 py-2 border-b border-slate-700/40 flex items-center gap-2">
              {running && <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />}
              <p className="text-xs text-slate-400">Output</p>
            </div>
            <div
              ref={logRef}
              className="p-4 font-mono text-xs text-slate-300 leading-5 max-h-96 overflow-y-auto whitespace-pre-wrap"
            >
              {lines.map((l, i) => (
                <div key={i} className={
                  l.startsWith('── Phase 1') ? 'text-amber-400 font-semibold mt-1' :
                  l.startsWith('── Phase 2') ? 'text-indigo-400 font-semibold mt-1' :
                  l.startsWith('✓') ? 'text-green-400' :
                  l.startsWith('  ✗') ? 'text-red-400' :
                  l.startsWith('  ⏰') ? 'text-slate-500' :
                  ''
                }>{l}</div>
              ))}
              {running && <span className="text-slate-500 animate-pulse">▌</span>}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-700/40 rounded-lg p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Summary */}
        {summary && phase === 'done' && (
          <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5 space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle size={14} className="text-green-400" />
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Run Complete</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Prospecting */}
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-[10px] text-amber-400 font-semibold uppercase tracking-wide mb-2">Phase 1 — Prospecting</p>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div>
                    <p className="text-xl font-semibold text-white">{summary.prospects_found ?? 0}</p>
                    <p className="text-[10px] text-slate-500">Found</p>
                  </div>
                  <div>
                    <p className="text-xl font-semibold text-indigo-400">{summary.new_leads ?? 0}</p>
                    <p className="text-[10px] text-slate-500">New Leads</p>
                  </div>
                </div>
              </div>
              {/* Enrichment */}
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wide mb-2">Phase 2 — Enrichment</p>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div>
                    <p className="text-xl font-semibold text-white">{summary.enriched ?? 0}</p>
                    <p className="text-[10px] text-slate-500">Emails Found</p>
                  </div>
                  <div>
                    <p className="text-xl font-semibold text-green-400">{summary.queued ?? 0}</p>
                    <p className="text-[10px] text-slate-500">Queued Email 1</p>
                  </div>
                </div>
              </div>
            </div>
            {(summary.queued ?? 0) > 0 && (
              <p className="text-xs text-green-400/80">
                {summary.queued} lead{summary.queued !== 1 ? 's' : ''} queued for Email 1 — go to Campaigns to send.
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── RIGHT: city picker ───────────────────────────── */}
      <div className="w-full lg:w-64 lg:shrink-0 bg-[#1e293b] border border-slate-700/40 rounded-lg overflow-hidden lg:sticky lg:top-6">
        <div className="px-4 pt-4 pb-2 border-b border-slate-700/40">
          <p className="text-xs font-semibold text-slate-300 mb-3">Cities</p>
          <div className="flex gap-1">
            {Object.keys(CITIES).map(tab => (
              <button
                key={tab}
                onClick={() => { setActiveTab(tab); setCitySearch('') }}
                className={`flex-1 py-1 text-xs rounded font-medium transition-colors ${
                  activeTab === tab ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {FLAG[tab]}
              </button>
            ))}
          </div>
          <div className="relative mt-2">
            <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={citySearch}
              onChange={e => setCitySearch(e.target.value)}
              placeholder="Search…"
              className="w-full bg-slate-800 border border-slate-600/60 rounded pl-7 pr-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="overflow-y-auto max-h-64 lg:max-h-[calc(100vh-280px)]">
          {filteredCities.map(city => {
            const count = cityStats[city] || cityStats[city.toLowerCase()] || 0
            const isSelected = selected.includes(city.toLowerCase())
            return (
              <button
                key={city}
                onClick={() => toggleCity(city)}
                className={`w-full flex items-center justify-between px-4 py-2 text-xs transition-colors text-left border-b border-slate-700/20 last:border-0 ${
                  isSelected
                    ? 'bg-indigo-600/20 text-indigo-300'
                    : 'text-slate-400 hover:bg-slate-700/40 hover:text-slate-200'
                }`}
              >
                <span>{city}</span>
                {count > 0 && (
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                    isSelected ? 'bg-indigo-500/30 text-indigo-300' : 'bg-slate-700 text-slate-400'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

    </div>
  )
}
