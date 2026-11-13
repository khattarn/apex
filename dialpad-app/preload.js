'use strict'
// The window cannot touch Node or the SignalWire API token. It can only ask the main process for a short-lived
// login token (see token.js).
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('dialpad', {
  getToken: () => ipcRenderer.invoke('dialpad:token'),
})
