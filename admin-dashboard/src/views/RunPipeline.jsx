import { useRef, useState } from 'react'
import { Play, Square } from 'lucide-react'
import { streamPipeline } from '../api'

const BUSINESS_TYPES = ['dentist', 'salon', 'accountant', 'physiotherapist', 'lawyer']

export default function RunPipeline() {
  const [form, setForm] = useState({
    business_type: 'dentist',
    city: '',
    max_prospects: 5,
    send_whatsapp: false,
  })
  const [running, setRunning] = useState(false)
  const [lines, setLines] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)
  const stopRef = useRef(null)
  const logRef = useRef(null)

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }))
  }

  function handleRun() {
    if (!form.city.trim()) return
    setLines([])
    setSummary(null)
    setError(null)
    setRunning(true)

    const stop = streamPipeline(
      { ...form, max_prospects: Number(form.max_prospects) },
      (line) => {
        setLines((l) => [...l, line])
        setTimeout(() => logRef.current?.scrollTo(0, logRef.current.scrollHeight), 0)
      },
      (result) => {
        setSummary(result)
        setRunning(false)
      },
      (msg) => {
        setError(msg)
        setRunning(false)
      }
    )
    stopRef.current = stop
  }

  function handleStop() {
    stopRef.current?.()
    setRunning(false)
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <h2 className="text-base font-semibold">Run Pipeline</h2>

      <div className="bg-[#1e293b] rounded-lg p-5 border border-slate-700/40 space-y-4">
        {/* Business type */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5">Business Type</label>
          <select
            value={form.business_type}
            onChange={(e) => set('business_type', e.target.value)}
            disabled={running}
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          >
            {BUSINESS_TYPES.map((t) => (
              <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>

        {/* City */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5">City</label>
          <input
            type="text"
            value={form.city}
            onChange={(e) => set('city', e.target.value)}
            disabled={running}
            placeholder="e.g. Sydney, Melbourne, London"
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          />
        </div>

        {/* Max prospects */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5">
            Max Prospects <span className="text-slate-600">(1–50)</span>
          </label>
          <input
            type="number"
            min={1}
            max={50}
            value={form.max_prospects}
            onChange={(e) => set('max_prospects', e.target.value)}
            disabled={running}
            className="w-32 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          />
        </div>

        {/* Mode toggle */}
        <div>
          <label className="block text-xs text-slate-400 mb-2">Mode</label>
          <div className="flex gap-2">
            {[false, true].map((live) => (
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

        {/* Run / Stop button */}
        <div className="pt-1">
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
        </div>
      </div>

      {/* Log panel */}
      {(lines.length > 0 || running) && (
        <div className="bg-slate-900 rounded-lg border border-slate-700/40 overflow-hidden">
          <div className="px-4 py-2 border-b border-slate-700/40 flex items-center gap-2">
            {running && <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />}
            <p className="text-xs text-slate-400">Live output</p>
          </div>
          <div
            ref={logRef}
            className="p-4 font-mono text-xs text-slate-300 leading-5 max-h-80 overflow-y-auto whitespace-pre-wrap"
          >
            {lines.map((l, i) => (
              <div key={i}>{l}</div>
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

      {/* Summary card */}
      {summary && (
        <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-3">Run Complete</p>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-semibold text-white">{summary.prospects_found ?? 0}</p>
              <p className="text-xs text-slate-500 mt-0.5">Found</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-indigo-400">{summary.new_leads ?? 0}</p>
              <p className="text-xs text-slate-500 mt-0.5">New Leads</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-green-400">{summary.messages_sent ?? 0}</p>
              <p className="text-xs text-slate-500 mt-0.5">Messages Sent</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
