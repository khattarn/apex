import { useState, useEffect, useRef } from 'react'
import { Phone, PhoneOff, Delete } from 'lucide-react'
import { Device } from '@twilio/voice-sdk'
import { fetchTwilioToken, startBridgeCall, getBridgeStatus } from '../api'

const KEYS = [
  ['1', ''], ['2', 'ABC'], ['3', 'DEF'],
  ['4', 'GHI'], ['5', 'JKL'], ['6', 'MNO'],
  ['7', 'PQRS'], ['8', 'TUV'], ['9', 'WXYZ'],
  ['*', ''], ['0', '+'], ['#', ''],
]

// ── India Bridge Dialpad ───────────────────────────────────────────────────────

const BRIDGE_STATES = {
  idle:             { ring: 'bg-slate-500',                bar: 'bg-slate-700/40 text-slate-400',    label: 'Ready · +91 9262171423' },
  connecting:       { ring: 'bg-slate-400 animate-pulse',  bar: 'bg-slate-700/40 text-slate-400',    label: 'Connecting to Vobiz…' },
  registering:      { ring: 'bg-slate-400 animate-pulse',  bar: 'bg-slate-700/40 text-slate-400',    label: 'Registering SIP…' },
  calling_founder:  { ring: 'bg-amber-400 animate-pulse',  bar: 'bg-amber-900/30 text-amber-400',    label: 'Calling your mobile…' },
  ringing:          { ring: 'bg-amber-400 animate-pulse',  bar: 'bg-amber-900/30 text-amber-400',    label: 'Ringing your mobile…' },
  answered:         { ring: 'bg-blue-400 animate-pulse',   bar: 'bg-blue-900/30 text-blue-300',      label: 'Connected to your mobile…' },
  transferring:     { ring: 'bg-indigo-400 animate-pulse', bar: 'bg-indigo-900/30 text-indigo-300',  label: 'Transferring to lead…' },
  connected:        { ring: 'bg-green-400 animate-pulse',  bar: 'bg-green-900/30 text-green-400',    label: 'Bridge live — you\'re connected!' },
  no_answer:        { ring: 'bg-orange-400',               bar: 'bg-orange-900/30 text-orange-400',  label: 'Your mobile didn\'t answer' },
  transfer_failed:  { ring: 'bg-red-400',                  bar: 'bg-red-900/30 text-red-400',        label: 'Transfer failed' },
  error:            { ring: 'bg-red-400',                  bar: 'bg-red-900/30 text-red-400',        label: 'Error' },
  not_found:        { ring: 'bg-slate-500',                bar: 'bg-slate-700/40 text-slate-400',    label: 'Ready · +91 9262171423' },
}

function IndiaBridge() {
  const [number, setNumber] = useState('')
  const [bridgeState, setBridgeState] = useState('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [bridgeId, setBridgeId] = useState(null)
  const pollRef = useRef(null)

  const isBusy = ['connecting', 'registering', 'calling_founder', 'ringing',
                   'answered', 'transferring', 'connected'].includes(bridgeState)

  function stopPoll() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => () => stopPoll(), [])

  function press(digit) {
    if (!isBusy) setNumber(n => n + digit)
  }

  function backspace() {
    if (!isBusy) setNumber(n => n.slice(0, -1))
  }

  async function callBridge() {
    if (!number || isBusy) return
    setErrorMsg('')
    setBridgeState('connecting')
    try {
      const { bridge_id } = await startBridgeCall(number)
      setBridgeId(bridge_id)
      pollRef.current = setInterval(async () => {
        try {
          const status = await getBridgeStatus(bridge_id)
          const s = status.state || 'idle'
          setBridgeState(s)
          if (status.error) setErrorMsg(status.error)
          if (['connected', 'no_answer', 'transfer_failed', 'error', 'timeout'].includes(s)) {
            stopPoll()
          }
        } catch {
          // keep polling
        }
      }, 1500)
    } catch (err) {
      setBridgeState('error')
      setErrorMsg(err.message || 'Failed to start bridge')
    }
  }

  function reset() {
    stopPoll()
    setBridgeState('idle')
    setBridgeId(null)
    setErrorMsg('')
  }

  const stateInfo = BRIDGE_STATES[bridgeState] || BRIDGE_STATES.idle
  const isDone = ['connected', 'no_answer', 'transfer_failed', 'error', 'timeout'].includes(bridgeState)

  return (
    <div>
      {/* Status bar */}
      <div className={`mb-4 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-2 ${stateInfo.bar}`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${stateInfo.ring}`} />
        <span className="truncate">
          {bridgeState === 'error' ? `Error: ${errorMsg}` : stateInfo.label}
        </span>
      </div>

      {/* Number display */}
      <div className="flex items-center bg-[#1e293b] border border-slate-700/50 rounded-lg px-4 py-3 mb-4 min-h-[56px]">
        <span className="flex-1 text-xl font-mono tracking-widest text-white">
          {number || <span className="text-slate-600 text-base font-sans">Enter lead number</span>}
        </span>
        {number && !isBusy && (
          <button onClick={backspace} className="text-slate-500 hover:text-slate-200 ml-2 transition-colors">
            <Delete size={18} />
          </button>
        )}
      </div>

      {/* Keypad */}
      <div className="grid grid-cols-3 gap-2 mb-5">
        {KEYS.map(([digit, sub]) => (
          <button
            key={digit}
            onClick={() => press(digit)}
            disabled={isBusy}
            className="flex flex-col items-center justify-center bg-[#1e293b] hover:bg-slate-700/60 border border-slate-700/40 rounded-lg py-3 transition-colors disabled:opacity-40 select-none"
          >
            <span className="text-lg font-semibold text-white leading-none">{digit}</span>
            {sub && <span className="text-[9px] text-slate-500 mt-0.5 tracking-widest">{sub}</span>}
          </button>
        ))}
      </div>

      {/* Call / Reset */}
      <div className="flex justify-center gap-4">
        {!isBusy && !isDone && (
          <button
            onClick={callBridge}
            disabled={!number}
            className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow-lg"
            title="Bridge call via +91 9262171423"
          >
            <Phone size={26} fill="white" stroke="white" />
          </button>
        )}
        {isBusy && (
          <button
            onClick={reset}
            className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 flex items-center justify-center transition-colors shadow-lg"
            title="Cancel"
          >
            <PhoneOff size={26} stroke="white" />
          </button>
        )}
        {isDone && (
          <button
            onClick={reset}
            className="px-6 h-12 rounded-full bg-slate-700 hover:bg-slate-600 text-sm text-white transition-colors"
          >
            New call
          </button>
        )}
      </div>

      <p className="mt-4 text-center text-[11px] text-slate-600">
        Your mobile rings first · then connected to lead · caller ID: +91 9262171423
      </p>
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

      {/* Tab switcher */}
      <div className="flex gap-1 bg-slate-800/60 rounded-lg p-1 mb-6">
        <button
          onClick={() => setTab('india')}
          className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium ${
            tab === 'india'
              ? 'bg-slate-700 text-white'
              : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          🇮🇳 India Bridge
        </button>
        <button
          onClick={() => setTab('intl')}
          className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium ${
            tab === 'intl'
              ? 'bg-slate-700 text-white'
              : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          🌐 International
        </button>
      </div>

      {tab === 'india' ? <IndiaBridge /> : <InternationalDialpad />}
    </div>
  )
}
