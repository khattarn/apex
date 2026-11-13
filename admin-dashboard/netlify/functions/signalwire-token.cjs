'use strict'
// Creates a one-hour SignalWire login token (a "SAT") for the dashboard's Dialpad.
// Replaces the Railway backend's GET /api/signalwire/token, which no longer exists.
//
// Netlify environment variables (Site configuration -> Environment variables):
//   SIGNALWIRE_SPACE        e.g. uniqe-corporation.signalwire.com
//   SIGNALWIRE_PROJECT_ID
//   SIGNALWIRE_API_TOKEN    a DEDICATED token with only the "Fabric" scope
//   DIALPAD_KEY             a long random string; the Dialpad asks for it once and remembers it in the browser
//
// Anyone who can call this URL and knows DIALPAD_KEY can place calls on your SignalWire account, so keep the key
// secret and long. It is deliberately NOT the old dashboard admin password, which is in this repo's git history.

const crypto = require('crypto')

const REFERENCE = 'practicedesk-dialpad@practicedesk.live'   // the SignalWire subscriber the dialpad logs in as
const TTL_SECONDS = 3600
const MIN_KEY_LENGTH = 16

const json = (code, body) => ({
  statusCode: code,
  headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  body: JSON.stringify(body),
})

const safeEqual = (a, b) => {
  const x = Buffer.from(String(a)), y = Buffer.from(String(b))
  return x.length === y.length && crypto.timingSafeEqual(x, y)
}

exports.handler = async (event, _context, fetchImpl = fetch) => {
  if (event.httpMethod !== 'GET' && event.httpMethod !== 'POST') return json(405, { detail: 'Method not allowed' })

  const key = process.env.DIALPAD_KEY || ''
  if (key.length < MIN_KEY_LENGTH) return json(500, { detail: `DIALPAD_KEY is not set (or shorter than ${MIN_KEY_LENGTH} characters) on the server` })

  // 403, not 401: the dashboard logs you out and reloads on any 401 from its own API.
  const given = (event.headers && (event.headers['x-dialpad-key'] || event.headers['X-Dialpad-Key'])) || ''
  if (!safeEqual(given, key)) return json(403, { detail: 'Wrong dialpad key' })

  let host = String(process.env.SIGNALWIRE_SPACE || '').trim().replace(/^https?:\/\//, '').replace(/\/.*$/, '')
  if (host && !/\.signalwire\.com$/.test(host)) host += '.signalwire.com'
  const projectId = String(process.env.SIGNALWIRE_PROJECT_ID || '').trim()
  const apiToken = String(process.env.SIGNALWIRE_API_TOKEN || '').trim()
  if (!host || !projectId || !apiToken) return json(500, { detail: 'SIGNALWIRE_SPACE, SIGNALWIRE_PROJECT_ID or SIGNALWIRE_API_TOKEN is not set on the server' })

  let res, data
  try {
    res = await fetchImpl(`https://${host}/api/fabric/subscribers/tokens`, {
      method: 'POST',
      headers: {
        Authorization: 'Basic ' + Buffer.from(`${projectId}:${apiToken}`).toString('base64'),
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ reference: REFERENCE, expires_in: TTL_SECONDS }),
      signal: AbortSignal.timeout(8000),
    })
    data = await res.json().catch(() => ({}))
  } catch (e) {
    return json(502, { detail: `Could not reach SignalWire (${e.message})` })
  }
  if (!res.ok || !data.token) {
    const why = res.status === 401 || res.status === 403
      ? 'the SignalWire API token was rejected: check it is correct and has the Fabric scope'
      : String((data.errors && data.errors[0] && data.errors[0].detail) || data.error || data.message || '').slice(0, 160)
    return json(502, { detail: `SignalWire would not give a login token (HTTP ${res.status}${why ? ': ' + why : ''})` })
  }
  return json(200, { token: data.token })
}
