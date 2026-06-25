import { useState } from 'react'
import { Phone, PhoneOff, Delete } from 'lucide-react'
import { request } from '../api'

const KEYS = [
  ['1', ''], ['2', 'ABC'], ['3', 'DEF'],
  ['4', 'GHI'], ['5', 'JKL'], ['6', 'MNO'],
  ['7', 'PQRS'], ['8', 'TUV'], ['9', 'WXYZ'],
  ['*', ''], ['0', '+'], ['#', ''],
]

// ── India — Zoiper instructions ───────────────────────────────────────────────

function IndiaBridge() {
  const fields = [
    { label: 'Domain',    value: 'edcf4901.sip.vobiz.ai' },
    { label: 'Username',  value: 'practicedesk-priya' },
    { label: 'Password',  value: 'Ap#CSPgPc3mf9Jq$' },
    { label: 'Transport', value: 'TCP' },
    { label: 'Caller ID', value: '+91 9262171423' },
  ]
  const [copied, setCopied] = useState('')

  function copy(value, label) {
    navigator.clipboard.writeText(value).catch(() => {})
    setCopied(label)
    setTimeout(() => setCopied(''), 1500)
  }

  return (
    <div>
      <p className="text-xs text-slate-400 mb-4">
        Use <span className="text-white font-medium">Zoiper</span> (free desktop app) to call Indian leads directly from your computer.
      </p>

      <div className="space-y-2 mb-5">
        {fields.map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between bg-[#1e293b] border border-slate-700/50 rounded-lg px-3 py-2">
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
              <p className="text-sm font-mono text-white">{value}</p>
            </div>
            <button
              onClick={() => copy(value, label)}
              className="text-xs text-slate-500 hover:text-indigo-400 transition-colors px-2 py-1 rounded"
            >
              {copied === label ? '✓' : 'Copy'}
            </button>
          </div>
        ))}
      </div>

      <div className="text-[11px] text-slate-500 space-y-1">
        <p>1. Download Zoiper5 (free) → zoiper.com</p>
        <p>2. Add SIP account with the credentials above</p>
        <p>3. Dial any +91 number — caller ID shows +91 9262171423</p>
      </div>
    </div>
  )
}

// ── International Dialpad (SignalWire click-to-call) ──────────────────────────

function InternationalDialpad() {
  const [number, setNumber] = useState('')
  const [status, setStatus] = useState('idle')  // idle | calling | done | error
  const [errorMsg, setErrorMsg] = useState('')
  const [callSid, setCallSid] = useState('')

  function press(digit) { setNumber(n => n + digit) }
  function backspace() { setNumber(n => n.slice(0, -1)) }

  async function startCall() {
    if (!number || status === 'calling') return
    setStatus('calling')
    setErrorMsg('')
    setCallSid('')
    try {
      const data = await request('/api/signalwire/call', {
        method: 'POST',
        body: JSON.stringify({ to: number }),
      })
      setCallSid(data.sid || '')
      setStatus('done')
    } catch (err) {
      setStatus('error')
      setErrorMsg(err.message || 'Call failed')
    }
  }

  function reset() { setStatus('idle'); setCallSid(''); setErrorMsg('') }

  const QUICK_DIALS = [
    { label: 'Claire (Bright Smile)', number: '+12084414485', note: 'Dental inbound agent' },
    { label: 'Test Line 2',           number: '+12086884760', note: 'New inbound test number' },
  ]

  const statusBar = {
    idle:   { ring: 'bg-green-400',               bar: 'bg-green-900/30 text-green-400',    label: 'Ready · +1 208-441-4485 (SignalWire)' },
    calling:{ ring: 'bg-amber-400 animate-pulse', bar: 'bg-amber-900/30 text-amber-400',   label: `Dialling ${number}…` },
    done:   { ring: 'bg-indigo-400',              bar: 'bg-indigo-900/30 text-indigo-300', label: 'Call placed — check your phone' },
    error:  { ring: 'bg-red-400',                 bar: 'bg-red-900/30 text-red-400',       label: `Error: ${errorMsg}` },
  }[status]

  return (
    <div>
      <div className={`mb-4 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-2 ${statusBar.bar}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${statusBar.ring}`} />
        <span className="truncate">{statusBar.label}</span>
      </div>

      <div className="flex flex-col gap-1 mb-4">
        {QUICK_DIALS.map(q => (
          <button
            key={q.number}
            onClick={() => setNumber(q.number)}
            className="flex items-center justify-between bg-[#111e35] hover:bg-[#1e3a5f] border border-slate-700/40 rounded-lg px-3 py-2 text-left transition-colors"
          >
            <div>
              <p className="text-xs font-medium text-white">{q.label}</p>
              <p className="text-[10px] text-slate-500">{q.note}</p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">{q.number}</span>
          </button>
        ))}
      </div>

      <div className="flex items-center bg-[#1e293b] border border-slate-700/50 rounded-lg px-4 py-3 mb-4 min-h-[56px]">
        <span className="flex-1 text-xl font-mono tracking-widest text-white">
          {number || <span className="text-slate-600 text-base font-sans">Enter number</span>}
        </span>
        {number && (
          <button onClick={backspace} className="text-slate-500 hover:text-slate-200 ml-2 transition-colors">
            <Delete size={18} />
          </button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 mb-5">
        {KEYS.map(([digit, sub]) => (
          <button
            key={digit}
            onClick={() => press(digit)}
            disabled={status === 'calling'}
            className="flex flex-col items-center justify-center bg-[#1e293b] hover:bg-slate-700/60 border border-slate-700/40 rounded-lg py-3 transition-colors disabled:opacity-40 select-none"
          >
            <span className="text-lg font-semibold text-white leading-none">{digit}</span>
            {sub && <span className="text-[9px] text-slate-500 mt-0.5 tracking-widest">{sub}</span>}
          </button>
        ))}
      </div>

      <div className="flex justify-center">
        {status !== 'done' ? (
          <button
            onClick={startCall}
            disabled={status === 'calling' || !number}
            className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow-lg"
          >
            {status === 'calling'
              ? <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              : <Phone size={26} fill="white" stroke="white" />}
          </button>
        ) : (
          <button
            onClick={reset}
            className="w-16 h-16 rounded-full bg-slate-600 hover:bg-slate-500 flex items-center justify-center transition-colors shadow-lg"
          >
            <PhoneOff size={26} stroke="white" />
          </button>
        )}
      </div>

      {callSid && (
        <p className="mt-4 text-center text-[10px] text-slate-500 font-mono">{callSid}</p>
      )}
    </div>
  )
}

// ── Root ───────────────────────────────────────────────────────────────────────

export default function Dialpad() {
  const [tab, setTab] = useState('india')

  return (
    <div className="p-6 max-w-xs mx-auto">
      <h2 className="text-base font-semibold mb-4">Dialpad</h2>

      <div className="flex gap-1 bg-slate-800/60 rounded-lg p-1 mb-6">
        <button
          onClick={() => setTab('india')}
          className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium ${
            tab === 'india' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          🇮🇳 India (Zoiper)
        </button>
        <button
          onClick={() => setTab('intl')}
          className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium ${
            tab === 'intl' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          🌐 International
        </button>
      </div>

      {tab === 'india' ? <IndiaBridge /> : <InternationalDialpad />}
    </div>
  )
}
