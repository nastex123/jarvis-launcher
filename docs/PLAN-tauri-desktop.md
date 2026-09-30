# PLAN — Consolidación Desktop Tauri v2 (Opción 1)

- **Estado:** Acordado / en planificación (D1-D4 cerradas 2026-09-30)
- **Fecha:** 2026-09-30 (America/Bogota)
- **Rama base:** `dev` (`acaf2cc feat(hud): modern Next.js 16 HUD...`)
- **Decisiones cerradas:** D1=A (PLAN vivo + sync) · D2=A (Rust sidecar Python) · D3=A (mantener `page.tsx`) · D4=B (solo plan, ejecuta usuario)
- **Decisión previa:** ADR-015 aceptado (Next.js 16 + PixiJS v8 + Tauri v2)
- **Objetivo:** app de escritorio nativa sin depender del navegador. `npm run dev` solo para desarrollo. El artefacto final es `.exe/.msi` (Windows), `.deb/.AppImage` (Linux), `.dmg` (macOS) vía `tauri build`.

> [!NOTE] Alcance de este plan: consolidar lo que ya existe en `dev`, no reescribir. El HUD ya renderiza a 60 FPS en web; falta cerrar packaging, bridge Tauri nativo, y paridad con PyQt6 (modos, hotkey, tray).

> [!IMPORTANT] Regla inmutable heredada de ADR-015: cero emojis en UI, prompts y logs visibles. Fondo OLED `#000000`.

## 1. Inventario real (verificado en `dev`)

| Capa | Archivo | Estado |
|------|---------|--------|
| Frontend exportable | `src-web/next.config.ts:4` (`output: export`, `images.unoptimized:true`) | OK para `frontendDist: ../out` |
| Ventana desktop | `src-web/src-tauri/tauri.conf.json:6-11` (`frontendDist`, `devUrl`, `beforeDev/Build`, ventana `decorations:false`, `transparent:true`, `alwaysOnTop:true`) | OK parcial, falta `identifier` real + iconos finales |
| Comandos Rust | `src-web/src-tauri/src/lib.rs:4,26,61` (`execute_shell`, `run_opencode`, `invoke_handler`) + `Cargo.toml:24` (`tauri 2.11.6`) | OK parcial, sin validación de política ni tests |
| Cliente dual | `src-web/src/lib/system.ts:12-86` (Tauri `invoke` primero, fallback `http://127.0.0.1:3002`) | OK, pero `triggerSystemMode` solo usa HTTP, no `invoke` |
| Bridge dev | `src-web/scripts/bridge_server.py:15-107` (`/api/shell`, `/api/opencode`, `/api/mode` en `:3002`) | Solo dev, no empaquetar |
| HUD | `src-web/src/app/page.tsx:17-71` + `NeuralCanvas.tsx` + `ChatPanel.tsx` + `JarvisLogo.tsx` | OK visual, falta `hide-to-tray` real y `invoke` de modos |
| Legacy a retirar | `main.py`, `ui/`, `core/launcher.py`, `core/hotkey.py`, `core/tray.py` | Activo en `main`, en `dev` solo referencia para paridad |

> [!WARNING] Gap crítico: `triggerSystemMode()` no tiene ruta Tauri. En el `.exe` final sin bridge `:3002` corriendo, los modos Gaming/Trabajo/Estudio no lanzan nada. Es el P0 del plan.

## 2. Tabla de estrategias (5+ opciones evaluadas)

| # | Estrategia | Peso final | Perf | DX | Riesgo inv. | Coste | Total /50 | Big-O dominante | Veredicto |
|---|------------|------------|------|----|-------------|-------|-----------|-----------------|-----------|
| S1 | Consolidar Tauri actual + cerrar P0-P3 por fases (este plan) | 9 | 9 | 8 | 8 | 9 | **43** | O(n) Pixi + O(1) invoke IPC | **Ganadora (Recommended)** |
| S2 | Migrar a Electron + Next | 4 | 6 | 9 | 6 | 5 | 30 | O(n) + O(m) overhead Chromium bundled | Descartada: 180 MB vs 15 MB mismo HUD |
| S3 | Tauri + Vite React (quitar Next) | 10 | 10 | 9 | 5 | 6 | 40 | O(n), build O(k) más rápido | Reserva si Next export da fricción |
| S4 | Rust puro iced/egui (sin web) | 10 | 10 | 4 | 3 | 3 | 30 | O(n) CPU, sin GPU web | Descartada: reescribir Pixi/GSAP |
| S5 | Quedarse en PyQt6 `main` 2.0.3 | 6 | 7 | 6 | 7 | 8 | 34 | O(n) QPainter, 60 fps difícil | Solo mantenimiento legacy |
| S6 | Neutralino/Wails-Go | 9 | 8 | 5 | 4 | 5 | 31 | O(n) webview ligero | Sin ecosistema Rust ya iniciado |

> [!NOTE] Veredicto: S1 gana por continuidad (ADR-015 + código Tauri ya compilable) y menor coste. S3 queda como plan B documentado.

## 3. Checklist frontend completo (bloquea Build)

### 3.1 Estructura (Next.js 16 + TS)

- [ ] `src-web/src/app/layout.tsx` con `metadata`, `viewport`, `themeColor #000000`.
- [ ] `src-web/src/app/page.tsx` como shell HUD: `NeuralCanvas | ChatPanel | NewsDrawer | BottomDock`.
- [ ] `src-web/src/components/*` con props tipadas, sin `any` salvo `__TAURI__`.
- [ ] `src-web/src/lib/system.ts` con las 3 rutas Tauri (`execute_shell`, `run_opencode`, `launch_mode` nuevo).
- [ ] `output: export` verificado con `npm run build` generando `out/` sin rutas dinámicas.

### 3.2 Animación (PixiJS v8 + GSAP)

- [ ] `NeuralCanvas.tsx`: esfera ASCII 8 meridianos / 7 paralelos, vórtice 14 anillos, morph smoothstep `3t^2-2t^3` ~1.2 s, `ResizeObserver` + `renderer.resize`.
- [ ] Sin reinicio de canvas al alternar `isThinkingRef`.
- [ ] GSAP solo Core, micro-interacción `text-glitch` 0.35 s, sin neón AI-slop.
- [ ] 60 FPS estables en ventana 1280x760 Tauri (medir con overlay dev).

### 3.3 Estilo

- [ ] Tailwind v4 + tokens OLED: `bg #000000`, texto `#f4f4f5`, acento único por tema.
- [ ] `JarvisLogo.tsx` SVG monocromo + telemetría `v2.5`.
- [ ] `react-markdown + remark-gfm` con tablas terminal + botón copiar.
- [ ] Cero emojis (regex 3 capas en `ChatPanel.tsx: stripEmojis`).

### 3.4 Responsive / a11y

- [ ] `flex-1 min-w-0` en canvas, chat 300-850 px redimensionable con mouse + teclado.
- [ ] `page.tsx:56-64` con `startViewTransition` + fallback.
- [ ] Foco visible, `Escape` cierra drawer/reader, `Ctrl+J` abre chat, contraste AA en temas claros.
- [ ] Ventana Tauri `1280x760`, `center:true`, `resizable:true`, `decorations:false` con controles propios (cerrar/minimizar/hide).

## 4. Plan por fases (orden de ejecución)

### P0 — Modo desktop sin bridge (1-2 días)

1. Nuevo comando Rust `launch_mode(mode: String)` en `lib.rs` que reutilice `core/launcher.py` vía sidecar o reimplemente `shutil.which + App Paths + .lnk` en Rust.
2. `system.ts: triggerSystemMode()` primero `invoke("launch_mode")`, fallback HTTP solo si no hay `__TAURI__`.
3. `page.tsx: handleModeSelect` con estado optimistic + telemetría colapsable.
4. DoD: `.exe` sin `:3002` lanza apps reales.

### P1 — Identidad y bundle (0.5 día)

1. `tauri.conf.json`: `identifier: com.gexstudio.jarvis`, `productName: J.A.R.V.I.S.`, `version` sincronizada con tag git (`core/version.py` como referencia).
2. Regenerar `icons/` definitivos, `beforeBuildCommand: npm run build`, verificar `out/`.
3. `npm run tauri build` en Windows verde.

### P2 — Seguridad y política (1 día)

1. `execute_shell` con allowlist + `isDangerousCommand()` espejo Rust, timeout 30 s, cwd confinado.
2. Modal confirmación destructiva ya existente en `ChatPanel.tsx` conectado a `invoke`, no solo a bridge.
3. `capabilities/default.json` mínimo privilegio.

### P3 — Ventana nativa (0.5-1 día)

1. `handleClose` con `hide()` a tray, `alwaysOnTop` configurable, `single-instance` plugin Tauri (reemplaza socket `:47821` de `main.py:40`).
2. Hotkey global `Ctrl+Shift+Espacio` vía plugin `global-shortcut`.
3. Tray nativo con icono `icon.ico` (reemplaza `core/tray.py`).

### P4 — QA y docs sync (0.5 día)

1. `npm run lint + build + tauri build` en CI.
2. Checklist manual 10 puntos (modo, shell, opencode, news, resize, tray, hotkey, offline, temas, performance).
3. Sync `docs/Arquitectura.md §1`, `CHANGELOG.md [Unreleased]`, `TODO.md`, `README.md` (comando run desktop).

> [!TIP] Orden recomendado: P0 > P1 > P2 > P3 > P4. No empieces P3 sin P0 verde, o tendrás ventana bonita que no lanza nada.

## 5. Preguntas abiertas (elegir antes de codificar)

> Decisiones cerradas 2026-09-30: D1=A · D2=A · D3=A · D4=B (solo plan, ejecuta usuario).

- **D1. Doc destino: A (elegida).** Este `PLAN-tauri-desktop.md` vivo + sync a `Arquitectura/CHANGELOG/TODO`.
- **D2. `launch_mode`: A (elegida).** Rust invoca `core/launcher` como sidecar Python.
- **D3. Estructura frontend: A (elegida).** Mantener `page.tsx` shell actual.
- **D4. Modo trabajo: B (elegido).** Solo planificamos, tú ejecutas. No toco `src-web/src/` ni `src-tauri/` en esta tarea.

Frontend pendiente para tu ejecución D4-B: confirma antes de codificar animación (mantener esfera/vórtice actual SÍ/NO), estilo (OLED negro SÍ/NO) y a11y (teclado completo SÍ/NO).

## 6. DoD global

- [ ] `tauri build` genera instalador y corre sin `npm run dev` ni `:3002` ni navegador.
- [ ] Modos, shell y opencode funcionan vía `invoke` con política anti-destructiva.
- [ ] 60 FPS, cero emojis, contraste AA, `lint` + `build` verdes.
- [ ] Docs sincronizadas (este plan + Arquitectura + CHANGELOG + TODO).

## 7. Commits sugeridos (al final de cada fase, no ahora)

```text
feat(tauri): launch_mode nativo via invoke + fallback bridge
fix(tauri): identifier real + icons + frontendDist out verificado
feat(tauri): politica confirmacion destructiva en Rust + capabilities minimas
feat(tauri): single-instance + global-shortcut + tray nativo
docs(plan): sync Arquitectura/CHANGELOG/TODO con desktop Tauri P0-P4
```

---

*Base: `dev acaf2cc`, ADR-015, `src-web/package.json: next 16.3.5 + tauri/cli 2.11.5`, `src-tauri/Cargo.toml: tauri 2.11.6`.*
