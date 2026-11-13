'use strict'
// Creates the short-lived SignalWire login token (a "SAT") that lets the dialpad window place calls.
//
// This used to be done by a Railway server (/api/signalwire/token). That server is gone, and this was the
// only thing the dialpad needed from it: the call itself goes straight from this app to SignalWire.
//
// Runs in the app's main process, never in the window. The long-lived SignalWire API token stays here; the
// window only ever receives the one-hour login token.
//
// Credentials are read from, in this order:
//   1. environment variables SIGNALWIRE_SPACE, SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN
//   2. <userData>/config.json  ->  { "space": "...signalwire.com", "projectId": "...", "apiToken": "..." }
//      (on Windows: %APPDATA%\practicedesk-dialpad\config.json)
// Use a dedicated API token for this app, with only the "Voice" scope (SignalWire requires one of Voice, Messaging,
// Fax or Video on the token that creates subscriber tokens; Voice is the narrowest sensible choice).

const fs = require('fs')
const path = require('path')

const REFERENCE = 'practicedesk-dialpad@practicedesk.live'   // the SignalWire subscriber this dialpad logs in as
const CALLER_ID = '+12086884760'                               // shown in the UI only; SignalWire picks the real caller ID
const TTL_SECONDS = 3600

function readConfig(userDataDir) {
  let file = {}
  try { file = JSON.parse(fs.readFileSync(path.join(userDataDir || '.', 'config.json'), 'utf8')) } catch { /* no file is fine */ }
  let host = String(process.env.SIGNALWIRE_SPACE || file.space || '').trim().replace(/^https?:\/\//, '').replace(/\/.*$/, '')
  if (host && !/\.signalwire\.com$/.test(host)) host += '.signalwire.com'
  return {
    host,
    projectId: String(process.env.SIGNALWIRE_PROJECT_ID || file.projectId || '').trim(),
    apiToken: String(process.env.SIGNALWIRE_API_TOKEN || process.env.SIGNALWIRE_TOKEN || file.apiToken || '').trim(),
  }
}

async function mintToken(userDataDir, fetchImpl = fetch) {
  const { host, projectId, apiToken } = readConfig(userDataDir)
  if (!host || !projectId || !apiToken) {
    throw new Error(
      'SignalWire credentials not found. Set SIGNALWIRE_SPACE, SIGNALWIRE_PROJECT_ID and SIGNALWIRE_API_TOKEN, or create ' +
      path.join(userDataDir || '.', 'config.json') + ' with {"space","projectId","apiToken"}.'
    )
  }
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
      signal: AbortSignal.timeout(10000),
    })
    data = await res.json().catch(() => ({}))
  } catch (e) {
    throw new Error(`Could not reach SignalWire (${e.message}). Check your internet connection.`)
  }
  if (!res.ok || !data.token) {
    const why = res.status === 401 || res.status === 403
      ? 'the API token was rejected: check it is correct and has the Voice scope'
      : String((data.errors && data.errors[0] && data.errors[0].detail) || data.error || data.message || '').slice(0, 160)
    throw new Error(`SignalWire would not give a login token (HTTP ${res.status}${why ? ': ' + why : ''}).`)
  }
  return { token: data.token, caller_id: CALLER_ID }
}

module.exports = { mintToken, readConfig, REFERENCE }
