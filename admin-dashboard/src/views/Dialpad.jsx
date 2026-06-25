import { useState, useRef } from 'react'
import { Phone, PhoneOff, Delete, Mic, MicOff } from 'lucide-react'
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

// ── International Dialpad (SignalWire WebRTC browser softphone) ───────────────

const STATUS_META = {
  idle:    { color: 'bg-green-900/30 text-green-400',  dot: 'bg-green-400',               label: 'Ready · +1 208-441-4485' },
  init:    { color: 'bg-amber-900/30 text-amber-400',  dot: 'bg-amber-400 animate-pulse', label: 'Connecting…' },
  ringing: { color: 'bg-amber-900/30 text-amber-400',  dot: 'bg-amber-400 animate-pulse', label: '' },
  active:  { color: 'bg-green-900/30 text-green-400',  dot: 'bg-green-400 animate-pulse', label: '● Live call — speak into headset' },
  ended:   { color: 'bg-slate-800/60 text-slate-400',  dot: 'bg-slate-500',               label: 'Call ended' },
  error:   { color: 'bg-red-900/30 text-red-400',      dot: 'bg-red-400',                 label: '' },
}

const QUICK_DIALS = [
  { label: 'Claire (Bright Smile)', number: '+12084414485', note: 'Dental inbound agent' },
  { label: 'Test Line 2',           number: '+12086884760', note: 'Inbound test number' },
]

function InternationalDialpad() {
  const [number, setNumber]   = useState('')
  const [status, setStatus]   = useState('idle')
  const [errorMsg, setErrMsg] = useState('')
  const [muted, setMuted]     = useState(false)

  const clientRef  = useRef(null)
  const callRef    = useRef(null)
  const subRef     = useRef(null)
  const callSidRef = useRef(null)

  function press(digit)  { setNumber(n => n + digit) }
  function backspace()   { setNumber(n => n.slice(0, -1)) }

  function cleanupCall() {
    subRef.current?.unsubscribe()
    subRef.current     = null
    callRef.current    = null
    callSidRef.current = null
  }

  async function startCall() {
    if (!number || ['init', 'ringing', 'active'].includes(status)) return
    setStatus('init')
    setErrMsg('')
    setMuted(false)
    try {
      const dest = number.startsWith('+') ? number : `+${number.replace(/^00/, '')}`

      // Step 1: get embed token + space, then pre-create room & place PSTN call in parallel
      const [{ embed_token, space }, { SignalWire, EmbedTokenCredentialProvider }] = await Promise.all([
        request('/api/signalwire/token'),
        import('@signalwire/js'),
      ])

      let bridgeData
      try {
        bridgeData = await request('/api/signalwire/bridge', {
          method: 'POST',
          body: JSON.stringify({ to: dest }),
        })
      } catch (e) { throw new Error(`Bridge: ${e.message}`) }

      const { room_name, call_sid } = bridgeData
      callSidRef.current = call_sid

      // Step 2: browser joins the Fabric room using the Click-to-Call embed token
      const client = new SignalWire(new EmbedTokenCredentialProvider(space, embed_token))
      clientRef.current = client

      let call
      try {
        call = await client.dial(`/public/${room_name}`, { audio: true, video: false })
      } catch (e) {
        console.error('[Dialpad] dial() error:', e)
        throw new Error(`Room join: ${e.message}`)
      }
      callRef.current = call
      setStatus('ringing')

      subRef.current = call.status$.subscribe((s) => {
        if (s === 'connected') {
          setStatus('active')
        } else if (['disconnected', 'failed', 'destroyed'].includes(s)) {
          if (s === 'failed') { setStatus('error'); setErrMsg('Room join failed') }
          else setStatus('ended')
          cleanupCall()
        }
      })
    } catch (err) {
      setStatus('error')
      setErrMsg(err.message || 'Failed to start call')
      console.error('[Dialpad] startCall error:', err)
      clientRef.current = null
    }
  }

  async function endCall() {
    // cancel the PSTN outbound leg if still ringing
    if (callSidRef.current) {
      request('/api/signalwire/cancel', {
        method: 'POST',
        body: JSON.stringify({ call_sid: callSidRef.current }),
      }).catch(() => {})
    }
    try { await callRef.current?.hangup() } catch {}
    cleanupCall()
    setStatus('idle')
    setMuted(false)
  }

  async function toggleMute() {
    if (!callRef.current) return
    try {
      if (muted) { await callRef.current.unmute(); setMuted(false) }
      else       { await callRef.current.mute();   setMuted(true) }
    } catch {}
  }

  const inCall = ['init', 'ringing', 'active'].includes(status)
  const sm = {
    ...STATUS_META[status],
    label: status === 'ringing' ? `Calling ${number} — waiting for answer…`
         : status === 'error'   ? `Error: ${errorMsg}`
         : STATUS_META[status].label,
  }

  return (
    <div>
      {/* Status bar */}
      <div className={`mb-4 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-2 ${sm.color}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${sm.dot}`} />
        <span className="truncate">{sm.label}</span>
      </div>

      {/* Quick dials (hidden during call) */}
      {!inCall && (
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
      )}

      {/* Number display */}
      <div className="flex items-center bg-[#1e293b] border border-slate-700/50 rounded-lg px-4 py-3 mb-4 min-h-[56px]">
        <span className="flex-1 text-xl font-mono tracking-widest text-white">
          {number || <span className="text-slate-600 text-base font-sans">Enter number</span>}
        </span>
        {number && !inCall && (
          <button onClick={backspace} className="text-slate-500 hover:text-slate-200 ml-2 transition-colors">
            <Delete size={18} />
          </button>
        )}
      </div>

      {/* Keypad (hidden during call) */}
      {!inCall && (
        <div className="grid grid-cols-3 gap-2 mb-5">
          {KEYS.map(([digit, sub]) => (
            <button
              key={digit}
              onClick={() => press(digit)}
              className="flex flex-col items-center justify-center bg-[#1e293b] hover:bg-slate-700/60 border border-slate-700/40 rounded-lg py-3 transition-colors select-none"
            >
              <span className="text-lg font-semibold text-white leading-none">{digit}</span>
              {sub && <span className="text-[9px] text-slate-500 mt-0.5 tracking-widest">{sub}</span>}
            </button>
          ))}
        </div>
      )}

      {/* Call controls */}
      <div className="flex justify-center gap-4 items-center">
        {status === 'active' && (
          <button
            onClick={toggleMute}
            title={muted ? 'Unmute mic' : 'Mute mic'}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors shadow ${
              muted ? 'bg-red-700 hover:bg-red-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            {muted ? <MicOff size={20} stroke="white" /> : <Mic size={20} stroke="white" />}
          </button>
        )}

        {inCall ? (
          <button
            onClick={endCall}
            className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 flex items-center justify-center transition-colors shadow-lg"
          >
            {status === 'init'
              ? <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              : <PhoneOff size={26} stroke="white" />}
          </button>
        ) : ['ended', 'error'].includes(status) ? (
          <button
            onClick={() => { setStatus('idle'); setErrMsg('') }}
            className="w-16 h-16 rounded-full bg-slate-600 hover:bg-slate-500 flex items-center justify-center transition-colors shadow-lg"
          >
            <PhoneOff size={26} stroke="white" />
          </button>
        ) : (
          <button
            onClick={startCall}
            disabled={!number}
            className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow-lg"
          >
            <Phone size={26} fill="white" stroke="white" />
          </button>
        )}
      </div>

      <p className="mt-4 text-center text-[10px] text-slate-500">WebRTC · SignalWire · headset audio</p>
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
