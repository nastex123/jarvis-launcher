# ADR-016: Frontend desktop con Electron (reemplaza Tauri v2)

- **Estado:** Aceptado (2026-10-01, rama `dev`)
- **Revoca en la práctica:** ADR-015 §2.2 (Tauri v2 + Rust) como ruta desktop
- **Motivo:** Tauri exige toolchain MSVC (~6 GB Build Tools + compilación Rust) que bloqueó el arranque en la máquina de desarrollo (Ryzen 5500 + GT710, sin VS instalado). Electron empaqueta Chromium+Node: `npm install` y listo, sin compiladores.

## Decisión

1. **Ventana desktop (`src-web/electron/`)**: `main.js` (1280x760, frameless, transparente, alwaysOnTop, instancia única) + `preload.js` con `window.electronAPI` (contextIsolation, sin nodeIntegration).
2. **IPC nativo sin bridge ni Rust**: `execute-shell` (timeout 30 s), `run-opencode` (mismo binario `~/.opencode/bin`), `launch-mode` (reusa `core/launcher.py` vía `python -c`). Cierra el P0 que Tauri dejó abierto (`triggerSystemMode` sin `invoke`).
3. **Cliente dual (`src/lib/system.ts`)**: orden `electronAPI` → `__TAURI__` → bridge `:3002`. El HUD funciona igual en Electron, Tauri y navegador.
4. **Empaquetado (`electron-builder`, NSIS)**: `npm run dist` genera instalador `.exe` sin VS ni Rust. Tauri queda como alternativa documentada, no como ruta principal.

## Consecuencias

- Positivas: arranque desktop sin MSVC; `.exe` instalable; misma UI PixiJS/GSAP; política cero emojis y modal destructivo intactos.
- Coste: bundle ~180 MB vs ~15 MB de Tauri; RAM mayor (Chromium completo).
- Seguridad: `execute-shell` corre comandos que el HUD ya filtra con modal de confirmación (`isDangerousCommand`); no exponer el puerto ni deshabilitar `contextIsolation`.

> [!NOTE] Arranque: `python start_electron.py` (dev) o `python start_electron.py --build` (instalador). Requiere solo Node 18+.
