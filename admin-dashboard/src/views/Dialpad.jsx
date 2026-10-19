import { useState, useRef, useEffect } from 'react'
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
  idle:    { color: 'bg-green-900/30 text-green-400',  dot: 'bg-green-400',               label: 'Ready · +1 208-688-4760' },
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

// Pasted numbers like "1 (888) 207-3363" must reach SignalWire as E.164 ("+18882073363");
// it rejects URIs containing spaces/brackets/dashes with uri_does_not_resolve_to_address.
function toE164(raw) {
  const s = raw.trim()
  const digits = s.replace(/\D/g, '')
  return s.startsWith('+') ? `+${digits}` : `+${digits.replace(/^00/, '')}`
}

function InternationalDialpad() {
  const [number, setNumber]       = useState('')
  const [status, setStatus]       = useState('idle')
  const [errorMsg, setErrMsg]     = useState('')
  const [muted, setMuted]         = useState(false)
  const [audioOutputs, setOutputs] = useState([])
  const [sinkId, setSinkId]       = useState('')

  const clientRef    = useRef(null)
  const callRef      = useRef(null)
  const subRef       = useRef(null)
  const streamSubRef = useRef(null)
  const audioRef     = useRef(null)
  const sinkIdRef    = useRef('')   // stable ref for use inside stream closure

  // Enumerate audio output devices — labels only appear after mic permission is granted
  useEffect(() => {
    async function loadOutputs() {
      if (!navigator.mediaDevices?.enumerateDevices) return
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const outputs = devices.filter(d => d.kind === 'audiooutput')
        setOutputs(outputs)
      } catch {}
    }
    loadOutputs()
    // Re-enumerate after mic permission fires (labels become available)
    navigator.mediaDevices?.addEventListener?.('devicechange', loadOutputs)
    return () => navigator.mediaDevices?.removeEventListener?.('devicechange', loadOutputs)
  }, [])

  function selectSink(id) {
    sinkIdRef.current = id
    setSinkId(id)
    const el = audioRef.current
    if (el?.setSinkId) el.setSinkId(id).catch(() => {})
  }

  const longPressRef = useRef(null)

  function press(digit)  { setNumber(n => n + digit) }
  function backspace()   { setNumber(n => n.slice(0, -1)) }

  // Long-press 0 → inserts '+' (standard phone behaviour)
  function onZeroDown() {
    longPressRef.current = setTimeout(() => {
      longPressRef.current = null
      setNumber(n => n + '+')
    }, 500)
  }
  function onZeroUp() {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current)
      longPressRef.current = null
      press('0')
    }
  }
  function onZeroCancel() {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current)
      longPressRef.current = null
    }
  }

  function attachAudio(stream) {
    const el = audioRef.current
    if (!el || !stream) return
    el.srcObject = stream
    // Route to the selected headset / output device if setSinkId is supported (Chrome/Edge)
    if (sinkIdRef.current && el.setSinkId) el.setSinkId(sinkIdRef.current).catch(() => {})
    el.play().catch(err => console.warn('[Dialpad] audio.play() blocked:', err))
  }

  function cleanupCall() {
    subRef.current?.unsubscribe()
    streamSubRef.current?.unsubscribe()
    subRef.current = null
    streamSubRef.current = null
    callRef.current = null
    if (audioRef.current) { audioRef.current.srcObject = null }
  }

  async function startCall() {
    if (!number || ['init', 'ringing', 'active'].includes(status)) return
    setStatus('init')
    setErrMsg('')
    setMuted(false)

    // Unlock the audio element NOW while the user gesture is still active —
    // Chrome revokes autoplay permission once the call stack goes async.
    if (audioRef.current) {
      audioRef.current.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='
      audioRef.current.play().catch(() => {})
      audioRef.current.removeAttribute('src')
    }

    try {
      const dest = toE164(number)

      // Fetch a fresh Subscriber Access Token (SAT) from backend
      const { token } = await request('/api/signalwire/token')

      // Authenticate as the practicedesk-dialpad subscriber
      const { SignalWire, StaticCredentialProvider } = await import('@signalwire/js')
      const client = new SignalWire(new StaticCredentialProvider({ token }))
      clientRef.current = client

      // Dial the PSTN number directly
      let call
      try {
        call = await client.dial(dest, { audio: true, video: false })
      } catch (e) {
        console.error('[Dialpad] dial() error:', e)
        throw new Error(e.message || 'Call creation failed')
      }
      callRef.current = call
      setStatus('ringing')

      // Subscribe to remote stream — fires when the far-end audio track arrives
      streamSubRef.current = call.remoteStream$.subscribe((stream) => {
        console.log('[Dialpad] remoteStream$ emitted', stream)
        attachAudio(stream)
      })

      subRef.current = call.status$.subscribe((s) => {
        console.log('[Dialpad] status$:', s)
        if (s === 'connected') {
          setStatus('active')
          // Fallback: if remoteStream$ already emitted before we subscribed,
          // the sync getter will have the value.
          const existing = call.remoteStream
          if (existing) attachAudio(existing)
          // Fire-and-forget: start server-side recording now that the call is live.
          request('/api/signalwire/start-recording', {
            method: 'POST',
            body: JSON.stringify({ call_id: call.id, to: dest }),
          }).catch(err => console.warn('[Dialpad] start-recording failed:', err))
        } else if (['disconnected', 'failed', 'destroyed'].includes(s)) {
          if (s === 'failed') { setStatus('error'); setErrMsg('Call failed') }
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
      <div className={`mb-3 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-2 ${sm.color}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${sm.dot}`} />
        <span className="truncate">{sm.label}</span>
      </div>

      {/* Audio output device selector — shown when browser supports setSinkId */}
      {audioOutputs.length > 1 && typeof HTMLMediaElement !== 'undefined' && 'setSinkId' in HTMLMediaElement.prototype && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[10px] text-slate-500 shrink-0">🎧 Output</span>
          <select
            value={sinkId}
            onChange={e => selectSink(e.target.value)}
            className="flex-1 text-[11px] bg-[#1e293b] border border-slate-700/50 rounded px-2 py-1 text-slate-300 outline-none"
          >
            {audioOutputs.map(d => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Output ${d.deviceId.slice(0, 8)}`}
              </option>
            ))}
          </select>
        </div>
      )}

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
        <input
          type="tel"
          value={number}
          onChange={e => !inCall && setNumber(e.target.value)}
          placeholder="Enter number or paste"
          readOnly={inCall}
          className="flex-1 bg-transparent text-xl font-mono tracking-widest text-white placeholder-slate-600 outline-none"
        />
        {number && !inCall && (
          <button onClick={backspace} className="text-slate-500 hover:text-slate-200 ml-2 transition-colors">
            <Delete size={18} />
          </button>
        )}
      </div>

      {/* Keypad (hidden during call) */}
      {!inCall && (
        <div className="grid grid-cols-3 gap-2 mb-5">
          {KEYS.map(([digit, sub]) => {
            const isZero = digit === '0'
            return (
              <button
                key={digit}
                onPointerDown={isZero ? onZeroDown : undefined}
                onPointerUp={isZero ? onZeroUp : undefined}
                onPointerLeave={isZero ? onZeroCancel : undefined}
                onContextMenu={isZero ? e => e.preventDefault() : undefined}
                onClick={isZero ? undefined : () => press(digit)}
                className="flex flex-col items-center justify-center bg-[#1e293b] hover:bg-slate-700/60 border border-slate-700/40 rounded-lg py-3 transition-colors select-none"
              >
                <span className="text-lg font-semibold text-white leading-none">{digit}</span>
                {isZero
                  ? <span className="text-[9px] text-indigo-400 mt-0.5">hold for +</span>
                  : sub && <span className="text-[9px] text-slate-500 mt-0.5 tracking-widest">{sub}</span>
                }
              </button>
            )
          })}
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

      {/* Hidden audio element — receives the remote stream */}
      <audio ref={audioRef} autoPlay />
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
