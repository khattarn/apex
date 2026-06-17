import { useState, useEffect, useRef } from 'react'
import { Phone, PhoneOff, Delete } from 'lucide-react'
import { Device } from '@twilio/voice-sdk'
import { fetchTwilioToken } from '../api'

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

// ── International Dialpad (Twilio) ─────────────────────────────────────────────

function InternationalDialpad() {
  const [number, setNumber] = useState('')
  const [status, setStatus] = useState('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [duration, setDuration] = useState(0)
  const [callerID, setCallerID] = useState('')
  const deviceRef = useRef(null)
  const callRef = useRef(null)
  const timerRef = useRef(null)

  useEffect(() => {
    initDevice()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (deviceRef.current) deviceRef.current.destroy()
    }
  }, [])

  async function initDevice() {
    setStatus('initializing')
    setErrorMsg('')
    try {
      const { token, caller_id } = await fetchTwilioToken()
      setCallerID(caller_id)
      const device = new Device(token, { logLevel: 'warn' })
      device.on('registered', () => setStatus('ready'))
      device.on('error', (err) => { setStatus('error'); setErrorMsg(err.message || 'Device error') })
      await device.register()
      deviceRef.current = device
    } catch (err) {
      setStatus('error')
      setErrorMsg(err.message || 'Failed to initialise dialer')
    }
  }

  function press(digit) { setNumber(n => n + digit) }
  function backspace() { setNumber(n => n.slice(0, -1)) }

  async function startCall() {
    if (!deviceRef.current || !number || status !== 'ready') return
    setStatus('connecting')
    setDuration(0)
    try {
      const call = await deviceRef.current.connect({ params: { To: number } })
      callRef.current = call
      call.on('accept', () => {
        setStatus('on-call')
        timerRef.current = setInterval(() => setDuration(d => d + 1), 1000)
      })
      call.on('disconnect', endCall)
      call.on('cancel', endCall)
      call.on('error', (err) => {
        setStatus('error')
        setErrorMsg(err.message || 'Call error')
        clearInterval(timerRef.current)
        callRef.current = null
      })
    } catch (err) {
      setStatus('error')
      setErrorMsg(err.message || 'Call failed')
    }
  }

  function endCall() {
    clearInterval(timerRef.current)
    setDuration(0)
    setStatus('ready')
    callRef.current = null
  }

  function hangUp() {
    if (callRef.current) callRef.current.disconnect()
    endCall()
  }

  function fmt(s) {
    return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`
  }

  const inCall = status === 'on-call' || status === 'connecting'

  const statusBar = {
    idle:         { ring: 'bg-slate-500',               bar: 'bg-slate-700/40 text-slate-400',   label: 'Initialising…' },
    initializing: { ring: 'bg-slate-400 animate-pulse', bar: 'bg-slate-700/40 text-slate-400',   label: 'Connecting to Twilio…' },
    ready:        { ring: 'bg-green-400',               bar: 'bg-green-900/30 text-green-400',    label: `Ready · ${callerID}` },
    connecting:   { ring: 'bg-amber-400 animate-pulse', bar: 'bg-amber-900/30 text-amber-400',   label: `Calling ${number}…` },
    'on-call':    { ring: 'bg-indigo-400 animate-pulse',bar: 'bg-indigo-900/30 text-indigo-300', label: `On call · ${fmt(duration)}` },
    error:        { ring: 'bg-red-400',                 bar: 'bg-red-900/30 text-red-400',       label: `Error: ${errorMsg}` },
  }[status]

  return (
    <div>
      <div className={`mb-4 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-2 ${statusBar.bar}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${statusBar.ring}`} />
        <span className="truncate">{statusBar.label}</span>
      </div>

      <div className="mb-3 px-3 py-2 rounded-md text-xs bg-orange-950/40 text-orange-400 border border-orange-800/30">
        Twilio compliance pending — outbound calls blocked until approved.
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
            disabled={inCall}
            className="flex flex-col items-center justify-center bg-[#1e293b] hover:bg-slate-700/60 border border-slate-700/40 rounded-lg py-3 transition-colors disabled:opacity-40 select-none"
          >
            <span className="text-lg font-semibold text-white leading-none">{digit}</span>
            {sub && <span className="text-[9px] text-slate-500 mt-0.5 tracking-widest">{sub}</span>}
          </button>
        ))}
      </div>

      <div className="flex justify-center">
        {!inCall ? (
          <button
            onClick={startCall}
            disabled={status !== 'ready' || !number}
            className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow-lg"
          >
            <Phone size={26} fill="white" stroke="white" />
          </button>
        ) : (
          <button
            onClick={hangUp}
            className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 flex items-center justify-center transition-colors shadow-lg"
          >
            <PhoneOff size={26} stroke="white" />
          </button>
        )}
      </div>

      {status === 'error' && (
        <div className="mt-5 text-center">
          <button onClick={initDevice} className="text-xs text-indigo-400 hover:text-indigo-300 underline">
            Retry connection
          </button>
        </div>
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
