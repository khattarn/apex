import { SignalWire, StaticCredentialProvider } from '@signalwire/js'

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE  = 'https://serene-passion-production-cd82.up.railway.app'
const API_TOKEN = 'Ne63ni71me01ja04!'
const CALLER_ID = '+1 208-688-4760'

const QUICK_DIALS = [
  { label: 'Claire — Bright Smile Dental', number: '+12084414485', note: 'Inbound demo agent' },
  { label: 'Test Line',                    number: '+12086884760', note: 'Echo / loopback'    },
]

const KEYS = [
  ['1',''], ['2','ABC'], ['3','DEF'],
  ['4','GHI'], ['5','JKL'], ['6','MNO'],
  ['7','PQRS'], ['8','TUV'], ['9','WXYZ'],
  ['*',''], ['0','+'], ['#',''],
]

// ── State ─────────────────────────────────────────────────────────────────────
let swClient   = null
let activeCall = null
let statusSub  = null
let streamSub  = null
let audioEl    = new Audio()
let timerID    = null
let seconds    = 0
let muted      = false

// ── DOM refs (populated after DOMContentLoaded) ───────────────────────────────
let $status, $statusDot, $number, $timer
let $keypad, $quickDials, $btnCall, $btnHangup, $btnMute, $callControls

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(n) { return String(n).padStart(2, '0') }

function startTimer() {
  seconds = 0
  timerID = setInterval(() => {
    seconds++
    if ($timer) $timer.textContent = `${fmt(Math.floor(seconds / 60))}:${fmt(seconds % 60)}`
  }, 1000)
}

function stopTimer() {
  clearInterval(timerID)
  timerID = null
  if ($timer) $timer.textContent = '00:00'
}

function setStatus(state, msg) {
  const cfg = {
    idle:    { dot: 'dot-green',  text: `Ready · ${CALLER_ID}` },
    init:    { dot: 'dot-amber',  text: 'Connecting…' },
    ringing: { dot: 'dot-amber',  text: msg || 'Ringing…' },
    active:  { dot: 'dot-green',  text: '● Live call' },
    ended:   { dot: 'dot-grey',   text: 'Call ended' },
    error:   { dot: 'dot-red',    text: msg || 'Error' },
  }
  const c = cfg[state] || cfg.idle
  $statusDot.className = `dot ${c.dot}`
  $status.textContent  = c.text

  const inCall = ['init', 'ringing', 'active'].includes(state)
  $keypad.style.display      = inCall ? 'none' : 'grid'
  $quickDials.style.display  = inCall ? 'none' : 'flex'
  $btnCall.style.display     = inCall ? 'none' : 'flex'
  $btnHangup.style.display   = inCall ? 'flex'  : 'none'
  $callControls.style.display = state === 'active' ? 'flex' : 'none'

  if (state !== 'active') stopTimer()
  if (state === 'active') startTimer()
}

function dialDigit(d) {
  $number.textContent = ($number.dataset.value || '') + d
  $number.dataset.value = $number.textContent
}

function backspace() {
  const v = ($number.dataset.value || '').slice(0, -1)
  $number.dataset.value = v
  $number.textContent   = v || ''
}

function attachAudio(stream) {
  if (!stream) return
  audioEl.srcObject = stream
  audioEl.play().catch(e => console.warn('[Dialpad] audio.play():', e))
}

function cleanupCall() {
  statusSub?.unsubscribe(); statusSub = null
  streamSub?.unsubscribe(); streamSub = null
  activeCall = null
  audioEl.srcObject = null
  stopTimer()
}

// ── Fetch SAT from Railway ────────────────────────────────────────────────────
async function fetchToken() {
  const res = await fetch(`${API_BASE}/api/signalwire/token`, {
    headers: { Authorization: `Bearer ${API_TOKEN}` },
  })
  if (!res.ok) throw new Error(`Token fetch failed: ${res.status}`)
  const data = await res.json()
  if (!data.token) throw new Error('No SAT token in response')
  return data.token
}

// ── Place call ────────────────────────────────────────────────────────────────
async function startCall() {
  const raw = ($number.dataset.value || '').trim()
  if (!raw) return

  const dest = raw.startsWith('+') ? raw : `+${raw.replace(/^00/, '')}`
  setStatus('init')

  try {
    const token = await fetchToken()

    // Electron has no autoplay restrictions — no unlock needed
    swClient = new SignalWire(new StaticCredentialProvider({ token }))

    let call
    try {
      call = await swClient.dial(dest, { audio: true, video: false })
    } catch (e) {
      throw new Error(e.message || 'Dial failed')
    }

    activeCall = call
    setStatus('ringing', `Calling ${dest}…`)

    streamSub = call.remoteStream$.subscribe(stream => {
      console.log('[Dialpad] remoteStream$:', stream)
      attachAudio(stream)
    })

    statusSub = call.status$.subscribe(s => {
      console.log('[Dialpad] status$:', s)
      if (s === 'connected') {
        setStatus('active')
        // Fallback: check sync getter if observable already emitted
        if (call.remoteStream) attachAudio(call.remoteStream)
      } else if (['disconnected', 'failed', 'destroyed'].includes(s)) {
        setStatus(s === 'failed' ? 'error' : 'ended', s === 'failed' ? 'Call failed' : null)
        cleanupCall()
      }
    })

  } catch (err) {
    console.error('[Dialpad] startCall error:', err)
    setStatus('error', err.message)
    swClient = null
  }
}

// ── Hang up ───────────────────────────────────────────────────────────────────
async function endCall() {
  try { await activeCall?.hangup() } catch {}
  cleanupCall()
  setStatus('idle')
}

// ── Mute ─────────────────────────────────────────────────────────────────────
async function toggleMute() {
  if (!activeCall) return
  try {
    if (muted) { await activeCall.unmute(); muted = false }
    else        { await activeCall.mute();   muted = true  }
    $btnMute.classList.toggle('muted', muted)
    $btnMute.title = muted ? 'Unmute' : 'Mute'
  } catch {}
}

// ── Build DOM ─────────────────────────────────────────────────────────────────
function buildUI() {
  document.body.innerHTML = `
    <div class="app">
      <div class="header">
        <span class="logo">PracticeDesk</span>
        <span class="sub">Sales Dialpad</span>
      </div>

      <div class="status-bar">
        <span class="dot dot-green" id="dot"></span>
        <span id="status">Ready · ${CALLER_ID}</span>
      </div>

      <div class="number-row">
        <div class="number-display" id="number"></div>
        <button class="btn-back" id="btnBack">⌫</button>
      </div>

      <div class="quick-dials" id="quickDials">
        ${QUICK_DIALS.map(q => `
          <button class="quick-btn" data-num="${q.number}">
            <span class="ql">${q.label}</span>
            <span class="qn">${q.number}</span>
          </button>`).join('')}
      </div>

      <div class="keypad" id="keypad">
        ${KEYS.map(([d, s]) => `
          <button class="key" data-digit="${d}">
            <span class="kd">${d}</span>
            ${s ? `<span class="ks">${s}</span>` : ''}
          </button>`).join('')}
      </div>

      <div class="call-controls" id="callControls" style="display:none">
        <button class="btn-mute" id="btnMute" title="Mute">
          🎙 Mute
        </button>
        <div class="timer" id="timer">00:00</div>
      </div>

      <div class="dial-row">
        <button class="btn-call" id="btnCall">📞 Call</button>
        <button class="btn-hangup" id="btnHangup" style="display:none">⬛ End</button>
      </div>
    </div>
  `

  // Grab refs
  $status      = document.getElementById('status')
  $statusDot   = document.getElementById('dot')
  $number      = document.getElementById('number')
  $timer       = document.getElementById('timer')
  $keypad      = document.getElementById('keypad')
  $quickDials  = document.getElementById('quickDials')
  $btnCall     = document.getElementById('btnCall')
  $btnHangup   = document.getElementById('btnHangup')
  $btnMute     = document.getElementById('btnMute')
  $callControls = document.getElementById('callControls')

  // Wire events
  document.getElementById('btnBack').addEventListener('click', backspace)
  document.getElementById('btnCall').addEventListener('click', startCall)
  document.getElementById('btnHangup').addEventListener('click', endCall)
  document.getElementById('btnMute').addEventListener('click', toggleMute)

  document.getElementById('keypad').addEventListener('click', e => {
    const btn = e.target.closest('[data-digit]')
    if (btn) dialDigit(btn.dataset.digit)
  })

  document.getElementById('quickDials').addEventListener('click', e => {
    const btn = e.target.closest('[data-num]')
    if (btn) {
      $number.dataset.value = btn.dataset.num
      $number.textContent   = btn.dataset.num
    }
  })

  // Keyboard support
  document.addEventListener('keydown', e => {
    if ('0123456789*#'.includes(e.key)) dialDigit(e.key)
    else if (e.key === 'Backspace') backspace()
    else if (e.key === 'Enter') {
      if (activeCall) endCall()
      else startCall()
    }
    else if (e.key === '+') dialDigit('+')
    else if (e.key === 'Escape') endCall()
  })
}

document.addEventListener('DOMContentLoaded', buildUI)
