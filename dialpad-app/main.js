const { app, BrowserWindow, session } = require('electron')
const path = require('path')

function createWindow() {
  // Auto-grant microphone permission (needed for WebRTC audio)
  session.defaultSession.setPermissionRequestHandler((_wc, permission, callback) => {
    callback(permission === 'media')
  })

  const win = new BrowserWindow({
    width: 380,
    height: 700,
    resizable: false,
    maximizable: false,
    title: 'PracticeDesk Dialpad',
    backgroundColor: '#0a0f1e',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      // Bypass CORS — this is a private internal tool, no untrusted content
      webSecurity: false,
    },
  })

  win.setMenuBarVisibility(false)
  win.loadFile('renderer/index.html')
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => app.quit())
