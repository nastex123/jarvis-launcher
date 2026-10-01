/**
 * electron/main.js - Ventana desktop J.A.R.V.I.S. con Electron (sin navegador).
 *
 * Dev:  npx electron ./electron/main.js --dev   (carga http://localhost:3000)
 * Prod: npx electron ./electron/main.js          (carga out/index.html exportado)
 *
 * IPC expuesto al HUD via preload (contextBridge, sin nodeIntegration):
 *   electronAPI.executeShell(cmd)   -> { stdout, stderr, exitCode, ok }
 *   electronAPI.runOpencode(prompt) -> string (salida del agente OpenCode)
 *   electronAPI.launchMode(mode)    -> { ok, launched, failed }
 */
const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { exec, execFile } = require('child_process');

const isDev = process.argv.includes('--dev');
// electron/ -> src-web/ -> repo/
const REPO_ROOT = path.join(__dirname, '..', '..');
const IS_WIN = process.platform === 'win32';

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 760,
    title: 'J.A.R.V.I.S.',
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    center: true,
    resizable: true,
    backgroundColor: '#00000000',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (isDev) {
    win.loadURL('http://localhost:3000');
  } else {
    win.loadFile(path.join(__dirname, '..', 'out', 'index.html'));
  }

  // "Abrir original" y links externos van al navegador del sistema.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  return win;
}

// Instancia unica: segundo intento enfoca la ventana existente.
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    const [win] = BrowserWindow.getAllWindows();
    if (win) {
      if (win.isMinimized()) win.restore();
      win.show();
      win.focus();
    }
  });

  app.whenReady().then(createWindow);

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}

// --- IPC: terminal (gobernada por el modal de confirmacion del HUD) ---
ipcMain.handle('execute-shell', async (_event, cmd) => {
  if (typeof cmd !== 'string' || !cmd.trim()) {
    return { stdout: '', stderr: 'Comando vacio', exitCode: 1, ok: false };
  }
  return new Promise((resolve) => {
    exec(cmd, { timeout: 30000, maxBuffer: 1024 * 1024, windowsHide: true }, (err, stdout, stderr) => {
      if (err) {
        resolve({ stdout: String(stdout || ''), stderr: String(stderr || err.message), exitCode: err.code ?? 1, ok: false });
      } else {
        resolve({ stdout: String(stdout || ''), stderr: String(stderr || ''), exitCode: 0, ok: true });
      }
    });
  });
});

// --- IPC: agente OpenCode (motor B, mismo binario que usa Tauri) ---
ipcMain.handle('run-opencode', async (_event, prompt) => {
  const home = process.env.HOME || process.env.USERPROFILE || '.';
  const { join } = path;
  const candidates = IS_WIN
    ? [join(home, '.opencode', 'bin', 'opencode.exe'), join(home, '.opencode', 'bin', 'opencode'), 'opencode']
    : [join(home, '.opencode', 'bin', 'opencode'), 'opencode'];
  const bin = candidates[0];
  return new Promise((resolve) => {
    execFile(bin, ['run', String(prompt || '')], { timeout: 120000, maxBuffer: 4 * 1024 * 1024, windowsHide: true }, (err, stdout, stderr) => {
      const out = String(stdout || '') + (stderr ? `\n${stderr}` : '');
      if (err && !out) resolve(`Error ejecutando OpenCode: ${err.message}`);
      else resolve(out || 'OpenCode completado sin salida.');
    });
  });
});

// --- IPC: modos Gaming/Trabajo/Estudio via core/launcher.py del repo ---
ipcMain.handle('launch-mode', async (_event, mode) => {
  const map = { gaming: 'gaming', trabajo: 'work', work: 'work', estudio: 'study', study: 'study' };
  const target = map[String(mode || '').toLowerCase()] || String(mode || '').toLowerCase();
  const py = IS_WIN ? 'python' : 'python3';
  const code = [
    'import json, sys',
    'sys.path.insert(0, r"""' + REPO_ROOT + '""")',
    'from core.config import ConfigManager',
    'from core.launcher import AppLauncher',
    `apps = ConfigManager().get_mode_apps(${JSON.stringify(target)})`,
    'res = AppLauncher().launch_mode(apps)',
    'print(json.dumps({"ok": True, "launched": res.get("launched", []), "failed": res.get("failed", [])}))',
  ].join('; ');
  return new Promise((resolve) => {
    execFile(py, ['-c', code], { cwd: REPO_ROOT, timeout: 60000, windowsHide: true }, (err, stdout, stderr) => {
      if (err) {
        resolve({ ok: false, launched: [], failed: [String(stderr || err.message).slice(0, 500)] });
        return;
      }
      try {
        const parsed = JSON.parse(String(stdout).slice(String(stdout).indexOf('{')));
        resolve({ ok: true, launched: parsed.launched || [], failed: parsed.failed || [] });
      } catch (e) {
        resolve({ ok: false, launched: [], failed: [`Respuesta no JSON: ${String(e.message)}`] });
      }
    });
  });
});
