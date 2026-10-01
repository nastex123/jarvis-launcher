/**
 * electron/preload.js - Puente seguro HUD <-> main (contextIsolation, sin node).
 * Expone window.electronAPI con las 3 operaciones de sistema + plataforma.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  executeShell: (cmd) => ipcRenderer.invoke('execute-shell', cmd),
  runOpencode: (prompt) => ipcRenderer.invoke('run-opencode', prompt),
  launchMode: (mode) => ipcRenderer.invoke('launch-mode', mode),
  platform: process.platform,
});
