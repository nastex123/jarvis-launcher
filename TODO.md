# TODO - J.A.R.V.I.S. Launcher

## Completado

- [x] Estructura base del proyecto
- [x] ConfigManager para leer/write `config.json`
- [x] AppLauncher con lanzamiento en hilo separado
- [x] UI principal con anillos HUD, particulas, scan line, vignette
- [x] Tarjetas de modo animadas (glassmorphism, hover glow)
- [x] Auto-inicio Windows (VBS + boton toggle)
- [x] Deteccion de instancia unica
- [x] Documentacion (README, CHANGELOG, TODO)
- [x] `requirements.txt`
- [x] `.gitignore`
- [x] Repo publico GitHub (GexStudio-Team/jarvis-launcher)
- [x] Fix PyQt6: QDesktopWidget -> QApplication.primaryScreen()
- [x] Fix singleton: retencion global del socket (lock estable)
- [x] Sonidos de feedback (click, exito, error)
- [x] Efecto de typewriter en el greeting
- [x] Pantalla de carga animada al iniciar
- [x] Historial de modos recientes
- [x] Animacion de seleccion con flash de color del modo
- [x] Notificaciones Windows al completar lanzamiento
- [x] soporte multi-monitor
- [x] Fix v1.2.0: eliminar QGraphicsEffect (spam QPainter + cards negras en hover)
- [x] Fix v1.2.0: sonidos con winsound.Beep (ya no dependen del esquema de Windows)
- [x] Fix v1.2.0: resolucion robusta de rutas de apps (PATH, menu inicio, App Paths)
- [x] v1.2.0: beam de energia a la card seleccionada
- [x] v1.2.0: corner brackets HUD en tarjetas + halo de hover manual
- [x] v1.2.0: boot rediseñado con barra de progreso
- [x] v1.3.0: comando global `jarvis` en CMD/PowerShell (install_jarvis_cmd.bat)
- [x] v1.4.0: `core/settings.py` — SettingsManager con `settings.json` (preferencias UI, gitignored)
- [x] v1.4.0: `core/themes.py` — ThemeManager + 8 temas (obsidiana, nocturno, crimson, esmeralda, matriz, violeta, ambar, luz, nieve)
- [x] v1.4.0: `core/news.py` — NewsService RSS/Atom solo stdlib + 10 presets + URL propia
- [x] v1.4.0: `ui/news_panel.py` — panel lateral redimensionable, refresh 10 min, entrada animada, click abre noticia, estado desconectado con CONECTAR
- [x] v1.4.0: `ui/settings_dialog.py` — rueda ⚙ con temas/swatches y ConnectDialog con validacion en hilo (señal Qt)
- [x] v1.4.0: `ui/mode_card.py` — paint 100% custom, icono flotante, zoom hover, sweep, entrada escalonada
- [x] v1.4.0: `ui/jarvis_ui.py` — layout compacto sin huecos, panel noticias lateral izq/der, temas en caliente
- [x] v1.4.0: fix crash `QColor("#hex", n)` (constructores invalidos Qt6) en overwlays/paintEvent
- [x] v1.4.0: fix `ConnectDialog`: reemplazado `QMetaObject.invokeMethod` con kwargs por señal `validationDone`
- [x] v1.4.0: render test offscreen completo (boot, hover, click, panel, 8 temas) 0 errores QPainter
- [x] v1.4.0: prueba en vivo de noticias (18 items reales de 4 fuentes)
- [x] v1.4.0: docs ADR-004 (temas) y ADR-005 (panel noticias); Arquitectura/README/CHANGELOG actualizados
- [x] v1.4.0: release GitHub v1.4.0 publicada (tag v1.4.0, main == origin/main == a6e57a8)
- [x] v2: `core/hotkey.py` — atajo global Ctrl+Shift+Espacio (RegisterHotKey ctypes + QAbstractNativeEventFilter, cero deps)
- [x] v2: `core/tray.py` — bandeja del sistema (icono generado por codigo, menu Mostrar/Salir, doble click)
- [x] v2: `core/greeting.py` — saludo dinamico por franja horaria + adjetivo rotativo por arranque
- [x] v2: `core/github_link.py` — vinculacion real de GitHub (deteccion `gh` autenticado + verificacion API publica, sin secretos)
- [x] v2: `core/settings.py` — claves tray/github/greeting con migracion suave
- [x] v2: `ui/mode_card.py` — cards modo workspace: monograma tipografico en vez de emoji, barra IDE, paleta sobria (modos conservados)
- [x] v2: `ui/news_panel.py` — cabecera "¿Que esta pasando en el mundo ahora?", items con jerarquia limpia (fuente/hora/titulo/preview), estado vacio sin emoji
- [x] v2: `ui/settings_dialog.py` — lista estructurada (1 Apariencia, 2 Comportamiento, 3 Noticias, 4 GitHub, 5 Proximamente) + GithubDialog
- [x] v2: `ui/jarvis_ui.py` — z-order siempra al frente, ocultar al elegir modo, ✕ oculta a bandeja, saludo dinamico, refresh_greeting/toggle_startup publicos
- [x] v2: `main.py` — show_and_raise al arrancar + deteccion automatica de GitHub en hilo
- [x] v2: pruebas offscreen (render UI, tarjetas, noticias, dialogo ajustes, boot completo) 0 errores
- [x] v2: push main -> origin/main (cce3112)
- [x] v2: docs actualizadas — CHANGELOG [2.0.0], README (caracteristicas/atajos/estructura), Arquitectura.md (modulos v2, flujo), ADR-006 (atajo global + bandeja), config.json -> 2.0.0
- [x] v2: `ui/news_reader.py` — NewsReaderView lector fullscreen split-pane (lista izq + lectura larga der, QSplitter) + MiniNewsItem
- [x] v2: tipografia lectura larga — columna centrada, titulo Georgia, lead con capitular, pull-quote cursiva, divisores; HTML del tema activo
- [x] v2: click en noticia del panel emite `readerRequested` y abre el lector; boton "Abrir original" en navegador cuando el feed no trae cuerpo
- [x] v2: atajos del lector (Escape cierra, flechas navegan) priorizados en JarvisUI; fade windowOpacity (ADR-001)
- [x] v2: tests offscreen lector (render, splitter, navegacion, temas, respaldo sin summary) + integracion con JarvisUI 0 errores
- [x] v2: docs ADR-007 (lector), Arquitectura (news_reader + flujo), CHANGELOG [Unreleased], README
- [x] v2: **mini navegador embebido** — `PyQt6-WebEngine` instalado (6.11); `MiniBrowser` con `QWebEngineView` carga la URL real del articulo (imagenes y todo); fallback a QTextBrowser si no esta instalado; `AA_ShareOpenGLContexts` en main
- [x] v2: **panel de noticias des saturado** — sin preview apilado (fuente+hora+titulo), altura 88px, spacing 10, 12 items; lo completo se lee en el lector
- [x] v2: docs ADR-008 (webengine), Arquitectura y README actualizados (requisitos + lector)
- [x] v2.0.0: PR #2 mergeado a main (6d80316) y release publicada (tag v2.0.0)
- [x] v2.0.1: pre-warm Chromium + caché disco + bloqueo rastreadores + fade 110 ms (ADR-009); `JARVIS_DISABLE_WEBENGINE` para CI headless
- [x] v2.0.1: feedback sonoro eliminado — `core/feedback.py` + 15 llamadas (ADR-010)
- [x] v2.0.1: 5 suites offscreen 0 errores; PR #3 mergeado (e5735e4) y release v2.0.1 (tag v2.0.1)
- [x] v2.0.2: **Bug G-001** — método público `apply_news_panel()` (antes `AttributeError` cerraba la app al cambiar fuente)
- [x] v2.0.2: **Bug G-002** — `_center_on_screen()` ahora tapa toda la pantalla (modo foco total, ADR-011) y mínimo relativo al monitor
- [x] v2.0.2: **Bug G-003** — Ajustes -> Aplicar re-aplica panel y refresca noticias en vivo (`refresh_news()`)
- [x] v2.0.2: smoke test offscreen 3/3 (G-001, G-002, G-003) + compileall OK
- [x] v2.0.2: docs — CHANGELOG [2.0.2] + mensaje GexStudio Team a la comunidad, ADR-011, Arquitectura, TODO
- [x] v2.0.2: **Perf G-004** — descarga de fuentes en paralelo (`ThreadPoolExecutor`, máx 6 workers); 12 fuentes ≈ 2.1 s (antes ~suma)
- [x] v2.0.2: **Perf G-005** — cambio de artículo instantáneo en el lector (resumen local ~1 ms + página real en segundo plano con guard por secuencia)
- [x] v2.0.2: perf tests offscreen OK (G-004, G-005, regresión lector) + smoke 3/3 + reader 11/11 + engine warm 5/5
- [x] v2.0.3: **Bug G-006** — embebido vuelve a cargar siempre (resumen + web con red de seguridad `QTimer 2.5s` + `_on_web_finished` muestra aunque falle)
- [x] v2.0.3: **Bug G-007** — versión automática en la barra de estado: `core/version.py` (`get_app_version` lee tag git al arrancar); UI, main y config sincronizados a 2.0.2
- [x] v2.0.3: **docs/RELEASE.md** — metodología de release: branding (GexStudio Team → Comunidad GexClub), saludo por franja horaria de Bogotá (`greeting_for_bogota`), versión por tag
- [x] v2.0.3: branding corregido en notas del release v2.0.2 de GitHub (`gh release edit`)
- [x] v2.0.3: releases v2.0.0/v2.0.1/v2.0.2 con notas **UTF-8 sin BOM** (mojibake reparado en GitHub) + regla en `docs/RELEASE.md`
- [x] v2.0.3: release publicada (Latest) + `git fetch --tags` → versión automática muestra **2.0.3**
- [x] Linux: `core/platform.py` — helpers dual (autostart, .desktop, distro/sesion)
- [x] Linux: `core/launcher.py` dual (webbrowser, start_new_session, .desktop + alias)
- [x] Linux: `core/hotkey.py` dual (QShortcut interno), `notifier.py` (notify-send),
      `version.py` (creationflags solo Windows), `config.py` (config.linux.json)
- [x] Linux: `ui/jarvis_ui.py` autostart dual + `main.py` fuentes Linux
- [x] Linux: `install.py` todo-en-uno (venv, jarvis, .desktop, autostart, smoke) —
      verificado punta a punta + `config.linux.example.json` + template .desktop
- [x] Linux: docs ADR-012, README, CHANGELOG [Unreleased], `.gitignore` (config.linux.json)
- [x] Linux: fix stylesheet f-string en `main.py` (`%s`, bug NameError background)
- [x] Agente G-008: modelo fabricaba `<tool_result>` como texto (sin tarjeta,
      datos inventados) — `looks_fabricated` + re-pregunta acotada (máx 2) +
      `AGENT_SYS_V2` (reglas 8–9); ESPEC §3.4.2; tests C10–C11; verificado en
      vivo (tarjeta → dato real 2728 MB → respuesta natural)
- [x] Agente G-009: modelo en bucle de disculpas sin actuar (regla 8 de V2 lo
      bloqueaba) — `AGENT_SYS_V3` (JSON-único + few-shot + lista de tools),
      extracción en 3 niveles, corrección con ejemplo; ESPEC §3.4.3; tests
      C12–C13; verificado en vivo (tarjeta → 2586 MB reales)

## En progreso

- [x] Perfil CPU GT710: default `qwen3:1.7b` (`num_ctx 4096`, `timeout 180s`, `MAX_STEPS 5`) + `ollama pull qwen3:1.7b` verificado (1.4 GB, tools OK) — docs/INVEST-modelo-cpu-gt710.md

- [x] Documentación del asistente IA local: ADR-013, ADR-014, ESPEC (incl.
      §3.4.1 fallback JSON), PLAN-fases, TEST-agente, Arquitectura §8,
      README índice, CHANGELOG, TODO
- [ ] Checklist manual M1–M10 del agente en GUI real (TEST-agente.md)

## Pendiente

- [ ] Editor grafico de modos (GUI para agregar/quitar apps desde la rueda ⚙)
- [ ] Soporte JSON Feed en noticias
- [ ] Cache offline de items de noticias
- [ ] Filtro de noticias por categoria/idioma
- [ ] Verificar contraste de temas claros en todo el paint custom
- [ ] Editor visual de paletas de temas
- [x] ~~Sonido en hover de tarjetas~~ — **descartado**: feedback 100 % visual
      (ADR-010); reabrir solo si la comunidad pide feedback sonoro
      configurable explícitamente
- [ ] Variar velocidad del typewriter
- [ ] Probar en la maquina real: instalar Discord y Spotify para validar resolucion por nombre
- [ ] Verificacion de toasts de Windows 10/11
- [ ] Prueba de pantalla completa real y posicion en monitores multiples
- [ ] Revisar uso de CPU del core/beam en pantallas grandes

## Asistente IA local — Fase 1 (Chat + Sistema)

Contrato: `docs/ESPEC-agente-fase1.md`. Decisiones: ADR-013/ADR-014.
Roadmap: `docs/PLAN-fases.md`. Pruebas: `docs/TEST-agente.md`.

### Motor (`core/agent/`) — implementado 2026-09-22, 26/26 tests OK
- [x] `core/agent/ollama.py` — cliente `/api/chat` con tools (urllib stdlib,
      timeouts, reintentos x3 con backoff, `num_ctx`, `temperature`, modo degradado)
- [x] `core/agent/tools.py` — `read_file`, `list_dir`, `search` (lectura)
- [x] `core/agent/tools.py` — `write_file` (con `.bak`), `edit_file` (old/new exacto)
- [x] `core/agent/tools.py` — `run_shell` (timeout 120 s, cwd confinado, lista negra dura)
- [x] `core/agent/tools.py` — `open_app`/`list_apps` (reusa `core/launcher.py`),
      `get_system_info`, JSON-schemas + errores tipados de `ESPEC §3.3`
- [x] `core/agent/loop.py` — bucle agéntico (MAX_STEPS=8, append `role:tool`,
      truncado de outputs, `AGENT_SYS_V1` de `ESPEC §3.5`) en `QThread` +
      fallback JSON §3.4.1 + `run_turn` funcional para tests
- [x] `core/agent/policy.py` — máquina `PROPUESTA→APROBADA|RECHAZADA|EDITADA`,
      nada ejecuta sin señal del usuario (ADR-014) + `rm_home` y fork-bomb
      corregidas tras la suite B
- [x] `agent_log.jsonl` append-only con el schema de `ESPEC §3.8` (gitignored)

### Interfaz (`ui/chat_panel.py` + integración) — implementada 2026-09-22
- [x] `ui/chat_panel.py` — burbujas terminal-HUD, input, tarjetas de aprobación
      (tool, args, diff colapsable, Aprobar/Rechazar/Editar), estados
      pensando/ejecutando/error/offline, 8 temas via `ThemeManager`
- [x] `ui/jarvis_ui.py` — botón 💬 + `Ctrl+J`, pestañas Noticias|Asistente,
      worker con señales (sin tocar widgets desde hilos), log append-only
- [x] `ui/settings_dialog.py` — sección "6 · Asistente" (url, modelo + probar
      conexión, límites, ver log, vaciar chat)
- [x] `core/settings.py` — claves `agent.*` con migración suave

### Instalador, pruebas y docs de Fase 1 — hechos 2026-09-22
- [x] `install.py` — verifica `ollama` + modelo `qwen2.5-coder:7b` (`ollama list`),
      aviso si el demonio no corre (incl. `--check-only`)
- [x] `tests/test_agent_{tools,policy,loop,ui}.py` — suites A–D en verde (26/26) +
      caso C9 (fallback JSON); turno real contra Ollama verificado (17 s)
- [x] Tests offscreen Qt — render panel + tarjetas + clics, 0 errores `QPainter`
- [x] Docs Fase 1 — resultados anexados a `TEST-agente.md`; CHANGELOG actualizado;
      pendiente solo el checklist manual M1–M10 en GUI real

## Roadmap Fases 2–4 (fuera de Fase 1, solo plan en `docs/PLAN-fases.md`)

- [ ] Fase 2 — Visión: captura (`grab`/gnome-screenshot) + modelo visión
      (`qwen2.5vl:7b`, ~5 GB) para "qué ves en pantalla"
- [ ] Fase 3 — Web: fetch→markdown (base `core/news.py`) + control del MiniBrowser
- [ ] Fase 4 — Voz: STT/TTS local (Piper + Whisper.cpp, evaluar costo CPU)

## Validación en máquina real (ADR-009 / ADR-011)

- [ ] **Primer clic en noticia**: abrir el lector y confirmar que carga el
      artículo casi al instante (sin el "arranque" de Chromium del clic)
- [ ] Segunda visita al mismo artículo: confirmar salida de caché de disco
      (assets cargan más rápido)
- [ ] Página con rastreadores (p. ej. un portal de noticias): red abierta del
      sistema → comprobar líderes de red menos saturados (los dominios de
      ads/analytics quedan bloqueados)
- [ ] Confirmar que la UI no emite ningún sonido al hacer clic (feedback
      visual únicamente)
- [ ] **Cambiar de fuente de noticias (⚙ → Noticias → CONECTAR)**: la app NO
      debe cerrarse y el panel debe mostrar la nueva fuente en el momento
- [ ] **Ajustes → Aplicar**: cambiar posición/tema y confirmar que el panel
      y la interfaz cambian al instante (sin reiniciar)
- [ ] **Modo foco total**: al abrir J.A.R.V.I.S. debe tapar toda la vista
      (sin "nueva ventana flotante"); probar también en monitor de
      resolución baja si se tiene acceso
- [ ] **Rendimiento del panel**: con varias fuentes conectadas, la primera
      carga debe llegar en ~1–3 s (descarga en paralelo, no en fila)
- [ ] **Cambio de artículo rápido (G-005)**: abrir una noticia, navegar con
      ←/→ y confirmar que el resumen aparece al instante y la página web
      salta sola al cargar (sin pantalla en blanco)
- [ ] **Embebido siempre visible (G-006)**: abrir una noticia, esperar ~3 s y
      confirmar que el navegador embebido SÍ aparece (resumen + web; el motor
      no se queda dormido oculto); también con sitios lentos o que fallan
- [ ] **Versión al iniciar (G-007)**: la barra inferior debe mostrar
      **v2.0.3** (o la release vigente) sin editar nada a mano
- [ ] **Agente (Fase 1)**: "lista mis proyectos" → tarjeta 🟢 → Aprobar →
      listado real; "abre VS Code" → Aprobar → se abre; "borra X" → Rechazar →
      intacto; `rm -rf /` dictado → tarjeta "Bloqueada por política";
      Ollama apagado → offline + Reintentar; `agent_log.jsonl` registra
      propuesta+decisión+resultado

---
_Historial de release: v2.0.0 (modo foco + lector), v1.4.0 (temas/noticias/settings),
v1.3.0 (comando global jarvis), v1.2.0 (fix renderizado/sonidos/resolución de apps),
v3.0.0 (asistente IA local Fase 1 implementado 2026-09-22: core/agent, chat,
26/26 tests, turno real OK; pendiente checklist manual M1–M10)._