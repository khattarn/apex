# PracticeDesk Dialpad

Desktop dialpad for sales calls to the USA and Canada. Calls go from this app straight to SignalWire; there is no
server in between (the old Railway server is gone).

## Run it

Double-click `Launch Dialpad.bat`, or run `npm start` from this folder. The status line should read
`Ready · +1 208-688-4760`. Pick a quick-dial or type a number, then press Call.

## Credentials

On each call the app creates a one-hour login token with SignalWire. It needs three values, from either:

1. Windows environment variables `SIGNALWIRE_SPACE`, `SIGNALWIRE_PROJECT_ID`, `SIGNALWIRE_API_TOKEN`, or
2. a file `config.json` in the app's data folder:

   ```json
   { "space": "your-space.signalwire.com", "projectId": "...", "apiToken": "..." }
   ```

   If the app cannot find credentials it shows the exact path of that file on screen.

Use a **dedicated API token for this app** (SignalWire dashboard, API tab), with only the **Voice** scope (SignalWire
needs one of Voice, Messaging, Fax or Video on the token that creates login tokens). Do not reuse a broad token. The token never reaches the dialpad window: `token.js` runs in the app's main process and the window only
receives the one-hour login token.

## How it works

`main.js` opens the window and answers `dialpad:token` using `token.js`. `preload.js` exposes `window.dialpad.getToken()`.
`renderer/renderer.js` asks for a token, then dials the number with SignalWire's browser SDK as the subscriber
`practicedesk-dialpad@practicedesk.live`. SignalWire chooses the caller ID.

## If it breaks

- **Crashes on launch with "Cannot read properties of undefined (reading 'handle')":** the environment variable
  `ELECTRON_RUN_AS_NODE` is set (VS Code sets it). `Launch Dialpad.bat` clears it; if you start the app another way, clear it first.
- **"SignalWire would not give a login token":** the API token is wrong or lacks the Voice scope.
- **"Could not reach SignalWire":** no internet connection.
