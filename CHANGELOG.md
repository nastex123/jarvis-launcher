# Changelog

Todos los cambios notables en el J.A.R.V.I.S. Launcher.

Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- **Modelo ultraliviano `qwen3:0.6b` + `think:false` por defecto (CPU) (`core/agent/ollama.py`, `core/settings.py`, `ui/jarvis_ui.py`, `ChatPanel.tsx`, `install.py`)**: `hola` 44.5 s -> 5.4 s y tool-call 9.6 s limpio sin `<tool_result>` fabricado en Ryzen 5500 CPU (`2026-10-01`). Nueva clave `agent.think` (defecto False) cableada al payload `/api/chat`.

### Added
- **Perfil CPU GT710 `qwen3:1.7b` (Ryzen 5500 + 16 GB) (`core/agent/ollama.py`, `core/settings.py`, `install.py`, `docs/INVEST-modelo-cpu-gt710.md`)**: default `qwen2.5-coder:7b` -> `qwen3:1.7b` Q4_K_M (2.0B, tools+thinking, Apache 2.0) verificado con `ollama show` (`2026-09-30`). `qwen3:1.7b` descargado (1.4 GB) junto a `qwen2.5:3b` existente como fallback inmediato.

### Fixed
- **Resolución de Endpoint de Modos en Servidor Puente (`src-web/scripts/bridge_server.py`)**: Corrección de la importación y llamada en el endpoint `/api/mode`, pasando de `Config`/`launch_mode` a `ConfigManager` y `AppLauncher().launch_mode(apps)`, permitiendo el lanzamiento nativo de aplicaciones por modo (`trabajo`, `gaming`, `estudio`) sin errores HTTP 500 (`2026-09-22T12:06:00-05:00`).

### Added
- **Blindaje Estricto de Cero Emojis Multi-Motor (Ollama + OpenCode) (`src-web/src/components/ChatPanel.tsx`)**: Implementación de una política de tres capas contra glifos y emojis (`2026-09-22T12:06:00-05:00`): (1) Prompting reforzado tanto en Ollama como en las directivas enviadas a OpenCode (`(Nota estricta: No uses emojis bajo ninguna circunstancia)`). (2) Función de sanitización Unicode `stripEmojis` aplicada a nivel de stream, post-procesamiento de OpenCode y de contingencia. (3) Filtro directo en la capa de renderizado React (`ReactMarkdown {stripEmojis(msg.content)}`), garantizando matemáticamente que ningún emoji o glifo no técnico sea digitado o visualizado en el chat.
- **Estructuración HUD Avanzada de Respuestas y Separador de Telemetría OpenCode (`src-web/src/components/ChatPanel.tsx`, `src/app/globals.css`)**: Optimización estética e informativa de las respuestas del asistente (`2026-09-22T11:59:00-05:00`). (1) **Separación de Telemetría en Acordeón Técnico**: Los códigos de escape ANSI de consola (`\x1b[...m`, `[0m`) y los registros de telemetría de búsqueda web generados por OpenCode se aíslan y encapsulan automáticamente dentro de un desplegable técnico colapsable (`<details><summary>[+] Telemetría y registros de ejecución</summary>...`), manteniendo limpia y legible la respuesta principal. (2) **Tipografía y Estructura HUD**: Nueva jerarquía visual en `globals.css` para elementos Markdown: títulos `h1`-`h4` en blanco brillante con líneas divisorias sobrias, listas con guiones estilizados monoespaciados (`—`), espaciado vertical ergonómico entre conceptos (`- **Concepto**: Detalle`), bloques de código con fondo `#09090b` y citas delimitadas por bordes zinc. (3) **Instrucciones Estructurales en Inferencia**: El system prompt de Ollama refuerza la presentación obligatoria de información mediante secciones estructuradas, viñetas individuales espaciadas y tablas comparativas.
- **Logo J.A.R.V.I.S. SVG Superior Derecho, Fondo Canvas Totalmente Responsivo y Eliminación Estricta de Emojis (`src-web/`)**: Implementación de directivas estéticas y de comportamiento (`2026-09-22T11:55:00-05:00`). (1) **Logo SVG J.A.R.V.I.S. (`src-web/src/components/JarvisLogo.tsx`, `page.tsx`)**: Reactor Arc vectorial monocromático de precisión con triple anillo segmentado, radiadores triangulares y núcleo central rotatorio reactivo a la inferencia (`isThinking`), acompañado de la marca tipográfica técnica monoespaciada `J.A.R.V.I.S. v2.5` y telemetría de estado HUD en la esquina superior derecha del área principal. (2) **Fondo Canvas PixiJS Dinámico y Responsivo (`src-web/src/components/NeuralCanvas.tsx`)**: Integración de `ResizeObserver` vinculado al renderizador de PixiJS v8 (`renderer.resize(newW, newH)`) sobre un contenedor flexible (`flex-1 min-w-0`), de modo que al ensanchar o reducir el panel de chat arrastrando con el cursor, el lienzo recalcula inmediatamente sus dimensiones físicas y recentra con exactitud matemática la esfera/vórtice ASCII en el área visual visible restante. (3) **Política Absoluta de Cero Emojis (`src-web/src/components/ChatPanel.tsx`)**: Refuerzo inmutable en el system prompt de Ollama prohibiendo terminantemente el uso de emojis; sustitución de iconos en respuestas de sistema y terminal por etiquetas HUD sobrias (`[OK]`, `[FAIL]`, `[CANCELADO]`, `[ERROR]`); y aplicación de un filtro purificador de expresiones regulares en streaming (`u{1F600}-u{1FAFF}`) que neutraliza y purga en tiempo real cualquier glifo o emoji transmitido.
- **Animación Continua de Pensamiento y Retorno Suave al Estado Zen (`src-web/src/components/NeuralCanvas.tsx`)**: Desacoplamiento total del ciclo de vida de PixiJS v8 respecto al estado reactivo `isThinking` mediante referencias mutables sincronizadas (`isThinkingRef`). El ticker de WebGL ejecuta la animación del vórtice de datos de forma constante e ininterrumpida mientras dura el razonamiento del LLM o agente OpenCode; al concluir, el lerp y la curva smoothstep cúbica se ejecutan suavemente en reversa hasta el estado base $0$, garantizando una transición fluida y completa sin cortes ni reinicios bruscos del lienzo (`2026-09-22T11:47:00-05:00`).
- **Asistente Red Neuronal 2.D ASCII central (`ui/ascii_neural_net.py`)**: Reemplazo de las 3 tarjetas de modo centrales por un asistente visual dinámico en arte ASCII interactivo. Muestra la topología neuronal en 2D (5 capas: Input, Hidden, Dense, Attention, Output), pesos y sinapsis con pulsos senoidales, tensores de inferencia activos y telemetría de estado reactiva sincronizada con el motor agéntico y los temas del sistema (`2026-09-22T09:58:00-05:00`).
- **Renderizador de Markdown completo con tablas comparativas (`ui/chat_panel.py`)**: Soporte integral de Markdown en las burbujas de chat del asistente, permitiendo formatear tablas comparativas con bordes estilizados, encabezados coloreados según el tema activo y bloques de código/listas con tipografía y legibilidad de grado HUD (`2026-09-22T09:58:00-05:00`).
- **Prompting reforzado para respuestas en Markdown y tablas comparativas (`core/agent/loop.py`)**: Actualizadas las reglas del sistema `AGENT_SYS_V2` y `AGENT_SYS_V3` instruyendo explícitamente al asistente a responder con tablas comparativas Markdown formateadas cuando se comparen tecnologías o datos (`2026-09-22T09:58:00-05:00`).
- **Nueva UI Next.js 15 + PixiJS v8 + GSAP + Tauri v2 (`src-web/`)**: Arquitectura frontend moderna de alto rendimiento con renderizado estático (`output: export`), aceleración WebGL/WebGPU para la Red Neuronal 2D interactiva (`src-web/src/components/NeuralCanvas.tsx`), animaciones cinemáticas y transiciones HUD con GSAP Core (`src-web/src/components/AsciiOverlay.tsx`), panel de conversación agéntico con soporte de tablas comparativas Markdown GFM (`react-markdown` + `remark-gfm`) y configuración base de empaquetado ultraligero Tauri v2 en Rust (`2026-09-22T10:08:00-05:00`).
- **Red Neuronal Holográfica 2.5D, Dock Lateral GSAP y Copiado de Tablas (`src-web/`)**: Evolución a estética Sci-Fi Industrial titanio/ámbar (#F59E0B) y fósforo verde (#10B981), renderizado esférico con perspectiva 2.5D en PixiJS v8 reactivo al cursor, dock lateral de chat colapsable con cinemática GSAP, telemetría de CPU/RAM en la barra superior y botón de copiado rápido para tablas comparativas en Markdown (`2026-09-22T10:17:00-05:00`).
- **Control Total de PC, Agente OpenCode Autónomo y Modal de Confirmación Destructiva (`src-web/src/components/ChatPanel.tsx`, `src/lib/system.ts`, `src-tauri/src/lib.rs`, `scripts/bridge_server.py`)**: Implementación integral del control de sistema y conmutación de motor (`2026-09-22T11:37:00-05:00`). (1) **Control de Sistema y Terminal**: Soporte para ejecutar comandos de terminal (`ejecuta: <cmd>`, `terminal: <cmd>`, `run: <cmd>`) y apertura de aplicaciones (`abre <app>`) con captura de código de salida, stdout y stderr. Lanzamiento nativo de aplicaciones por modo al hacer clic en el dock inferior (`[1] GAMING`, `[2] TRABAJO`, `[3] ESTUDIO`) conectado al launcher del sistema. (2) **Política de Seguridad con Confirmación Destructiva**: Detección estricta de comandos peligrosos (`rm`, `kill`, `pkill`, `del`, `format`, etc.) mediante un modal interactivo con botones `[CONFIRMAR Y EJECUTAR]` y `[CANCELAR]`, impidiendo ejecuciones destructivas sin permiso explícito. (3) **Integración Autónoma con OpenCode**: Soporte para `/home/cohorte5/.opencode/bin/opencode` con toggle `[motor: ollama / opencode]` en la cabecera del chat y fallback automático hacia OpenCode si el LLM local Ollama no se encuentra disponible.
- **Auto-Scroll Instantáneo en Chatbot (`src-web/src/components/ChatPanel.tsx`)**: Implementación de desplazamiento automático instantáneo hacia el último mensaje (`2026-09-22T11:22:00-05:00`). Utiliza referencias directas al contenedor (`messagesContainerRef`) con asignación directa de `scrollTop = scrollHeight` (sin retrasos de smooth-scroll) disparado reactivamente al enviar mensajes por el usuario, al recibir tokens por streaming de Ollama y al conmutar de sesión en el historial.
- **Transición Morfológica Continua (Morphing 1.2s) Esfera ↔ Vórtice (`src-web/src/components/NeuralCanvas.tsx`)**: Implementación de cinemática de transición gradual entre reposo y razonamiento (`2026-09-22T11:20:00-05:00`). Interpola un factor de morphing continuo $t \in [0, 1]$ con curva cúbica smoothstep a lo largo de ~1.2 segundos (72 frames a 60 FPS); la esfera expande su radio y dispersa sus meridianos/paralelos en una torsión helicoidal de micropuntos (`effLon = lon + morphAngle`, `lat * 2.0`), mientras emergen sincrónicamente los 14 anillos del vórtice de datos concéntrico, interpolando suavemente la paleta de gris zinc (`#52525b`) a blanco zinc (`#f4f4f5`) y viceversa al finalizar la inferencia.
- **Vórtice ASCII de Tensores, Historial de Conversaciones y Búsqueda Web en Tiempo Real (`src-web/src/components/NeuralCanvas.tsx`, `ChatPanel.tsx`, `lib/search.ts`)**: Implementación integral de las tres capacidades acordadas en la sesión `/grill-me` (`2026-09-22T11:17:00-05:00`). (1) **Vórtice de Aceleración de Tensores en Razonamiento**: La esfera en reposo conmuta de forma dinámica durante el estado `pensando...` a un vórtice concéntrico 3D de 14 anillos de partículas ASCII (`*`, `+`, `%`, `#`, `=`, `·`) calibrado a un ritmo pausado y sereno (`delta * 0.007`, frecuencia amortiguada) con dispersión radial y rotación diferencial, retornando suavemente a la esfera zen al finalizar. (2) **Historial y Gestión de Sesiones**: Drawer lateral desplegable en el chat con persistencia en `localStorage`, lista cronológica de charlas anteriores, contador de mensajes y creación de nuevas sesiones (`[+ NUEVA SESIÓN]`). (3) **Navegación Web en Tiempo Real**: Módulo de búsqueda web cliente abierto sin dependencias de pago, detección automática de intención de búsqueda (`busca:`, `noticias`, `hoy`, etc.), inyección contextual del contenido al prompt de `qwen2.5-coder:7b` en Ollama y toggle `[web: on/off]` en la barra superior del panel.
- **Documentación Técnica Integral y Guía de Puesta en Marcha (`README.md`, `docs/ADR-015-frontend-nextjs-pixi-tauri.md`, `docs/README.md`)**: Publicación del estándar arquitectónico ADR-015 y actualización completa de las instrucciones de instalación y despliegue del proyecto (`2026-09-22T11:03:30-05:00`). Detalla la guía paso a paso para ejecutar el nuevo frontend HUD Next.js 16 + PixiJS v8 (`npm run dev` / `npm run build`), empaquetado nativo con Tauri v2 (`npm run tauri dev`), inicialización del motor Ollama con `qwen2.5-coder:7b`, y convivencia con la versión de escritorio clásica en PyQt6.
- **Conexión Directa en Vivo con Modelo Local Ollama (`src-web/src/components/ChatPanel.tsx`)**: Integración del motor de inferencia local (`2026-09-22T11:00:30-05:00`). Conexión streaming token-a-token directa con la API de Ollama (`http://localhost:11434/api/chat`) utilizando el modelo `qwen2.5-coder:7b`. Incluye context prompt técnico de sistema que refuerza el uso de tablas comparativas formateadas en Markdown estándar, persistencia del historial de conversación en memoria durante la sesión, cálculo en vivo del cronómetro de inferencia `· pensando... (Xs)` y sincronización en tiempo real con la aceleración e iluminación de la esfera ASCII 3D en el fondo.
- **Efecto Glitch en Cambio de Modo y Chatbot Redimensionable (`src-web/src/app/page.tsx`, `globals.css`)**: Implementación de micro-interacciones solicitadas (`2026-09-22T10:58:30-05:00`). (1) Efecto cinemático `text-glitch` sutil de terminal en la etiqueta `[modo activo: X]` activado instantáneamente al cambiar de modo en el dock. (2) Panel lateral de chat y noticias redimensionable libremente arrastrando con el mouse mediante una barra/manija táctil minimalista vertical (`cursor-col-resize`) con 3 puntos de agarre táctil, permitiendo ajustar dinámicamente el ancho entre 300px y 850px según la preferencia del usuario.
- **Esfera Geodésica ASCII Uniforme Minimalista (`src-web/src/components/NeuralCanvas.tsx`)**: Reconfiguración de la esfera 3D para una apariencia homogénea, limpia y ligera en toda la superficie (`2026-09-22T10:55:00-05:00`). Se eliminó el cúmulo y apiñamiento asimétrico de líneas en los polos mediante una rotación axial fija inclinada ($15^\circ$) sobre el eje Y; reducción a 8 meridianos y 7 paralelos bien espaciados; y oclusión estricta de la cara posterior (`pZ > 0`), logrando una cuadrícula de alambre uniforme, aireada y perfectamente equilibrada en ambos hemisferios.
- **Rediseño Minimalista Puro OLED sin Clichés de IA (`src-web/`)**: Transformación total del frontend siguiendo los principios de 'frontend-design' y las respuestas de la sesión /grill-me: eliminación de gradientes y brillos difusos ('AI slop'), paleta monocromática OLED (#000000 puro y texto gris/blanco), gráfica vectorial de 1px en PixiJS v8 con ruta crítica que se ilumina durante el cálculo, indicador textual monoespaciado 'pensando... (Xs)' con cronómetro de inferencia, tablas estilo Paper/Terminal limpias, Zero-Header despejado y dock inferior de texto plano con controles directos por clic (`2026-09-22T10:40:00-05:00`).

### Changed
- `ui/jarvis_ui.py`: El área central ahora hospeda exclusivamente el visualizador `AsciiNeuralNet`, eliminando el renderizado de las 3 cards tradicionales de modo, conservando la arquitectura de fondo limpia y conectando los eventos de estado del agente hacia el núcleo ASCII.
- **Port a Linux (dual Windows + Linux)**: `core/platform.py` (deteccion
  SO/distro/sesion, rutas autostart y `.desktop`), `config.linux.example.json`
  y `assets/jarvis-launcher.desktop.template`. Detalle en
  `docs/ADR-012-linux-port.md`.
- **Instalador e inicializador `install.py` (todo-en-uno, stdlib)**:
  crea venv + `pip install -r requirements.txt`, genera
  `config.linux.json`, instala `~/.local/bin/jarvis`, el `.desktop` del menu
  y el autostart `~/.config/autostart/`. Flags `--run/--uninstall/--purge/
  --no-autostart/--no-shortcut/--venv/--check-only`. Ver README (seccion Linux).
- Resolucion de apps en Linux via `PATH` + archivos `.desktop`
  freedesktop (incl. Flatpak/snap) en `core/launcher.py`.
- Notificaciones Linux via `notify-send` (`core/notifier.py`).
- Auto-inicio Linux via `~/.config/autostart/` desde la rueda de ajustes
  (`ui/jarvis_ui.py`).
- **Documentación del asistente IA local (Fase 1, sin código aún)**:
  `docs/ADR-013-motor-agentico-local.md` (Ollama `qwen2.5-coder:7b`),
  `docs/ADR-014-politica-confirmacion.md` (confirmar-todo + lista negra),
  `docs/ESPEC-agente-fase1.md` (contrato: 9 tools, loop, `AGENT_SYS_V1`, UX,
  settings, log, casos borde), `docs/PLAN-fases.md` (roadmap 1–4),
  `docs/TEST-agente.md` (suites A–D + checklist manual) y §8 en
  `docs/Arquitectura.md`.
- **Fix agente G-008 — el modelo fabricaba `<tool_result>` como texto**
  (datos inventados, sin tarjeta de aprobación): `loop.py` detecta el bloque
  (`looks_fabricated`), re-pregunta acotado (máx 2) y jamás lo muestra;
  `AGENT_SYS_V2` añade reglas 8–9; ESPEC §3.4.2; tests C10–C11. Verificado en
  vivo: tarjeta `get_system_info` → dato real (2728 MB) → respuesta natural.
- **Fix agente G-009 — el modelo pedía disculpas en bucle sin actuar**
  (la regla 8 de V2 prohibía el JSON como texto, su único mecanismo efectivo):
  `AGENT_SYS_V3` con regla 8 reescrita (JSON-único para actuar) + few-shot +
  lista de tools; extracción en 3 niveles (completo, fence, embebido con
  `raw_decode`, solo tools reales); `_CORRECTION_MSG` con ejemplo exacto;
  ESPEC §3.4.3; tests C12–C13. Verificado en vivo: tarjeta → 2586 MB reales.
- **Asistente IA local Fase 1 implementado**: `core/agent/` (`ollama.py`,
  `tools.py` con 9 tools, `policy.py` con lista negra + redact + backups,
  `loop.py` con `AGENT_SYS_V1`, bucle 8 pasos y `AgentWorker` en `QThread`),
  `ui/chat_panel.py` (burbujas + tarjetas Aprobar/Rechazar/Editar +diff),
  pestañas Noticias|Asistente, botón 💬 + `Ctrl+J`, sección "6 · Asistente"
  en ajustes, settings `agent.*`, `agent_log.jsonl` (gitignored) y chequeo
  Ollama en `install.py`. Fallback JSON si el modelo no emite `tool_calls`
  (ESPEC §3.4.1). Verificado: 26 tests OK + turno real contra
  `qwen2.5-coder:7b` (propuesta→aprobación→ejecución→respuesta, 17 s).

### Changed
- `core/hotkey.py`: en Linux usa `QShortcut` interno `Ctrl+Shift+Espacio`
  (requiere foco; en Wayland no hay hotkey global sin portal). Windows intacto.
- `core/version.py`: `creationflags` solo en Windows (rompia en POSIX).
- `core/config.py`: en Linux prefiere `config.linux.json` si existe.
- `main.py`: pila de fuentes Linux (`Inter/Ubuntu/DejaVu Sans`).

---

## [2.0.3] - 2026-09-11 (America/Bogota)

### Fixed
- **Bug G-006 — el navegador embebido dejó de cargar el artículo**: el cambio
  instantáneo (G-005) escondía el `QWebEngineView` tras el resumen del feed
  para cargar "en segundo plano"; en varios entornos Chromium **no completa la
  carga de un widget oculto**, así que el `loadFinished` nunca llegaba y el
  lector se quedaba solo con el resumen. Ahora:
  - `_on_web_finished` muestra la web **siempre** que termina su carga (aunque
    `ok=False`: el motor dibuja su página de error y el embebido nunca
    "desaparece"), y
  - una red de seguridad (`QTimer.singleShot(2500, _force_show_web)`) muestra
    el mini navegador si la página tarda (Chromium reanuda la navegación al
    volverse visible). El resumen instantáneo se conserva mientras tanto.
- **Bug G-007 — la barra de estado seguía mostrando v2.0.0**: la versión se
  leía de `config.json`, que quedó sin sincronizar tras las releases. Nuevo
  `core/version.py` como fuente única: al arrancar lee `git describe --tags`
  (la versión salta **sola** con cada release) y, si no hay git (instalación
  entregada), usa la constante `__version__` sincronizada al liberar. La UI,
  `main.py` y el `DEFAULT_CONFIG` de `config.py` usan `get_app_version()`.

### Added
- **Metodología de release documentada** (`docs/RELEASE.md`): identidad de
  marca (GexStudio Team = desarrolladores; **GexClub** = comunidad; J.A.R.V.I.S.
  = proyecto de GexClub desarrollado por GexStudio Team), saludo por franja
  horaria de América/Bogotá (`core/version.greeting_for_bogota`) y flujo
  completo tag → CHANGELOG → PR → release. El mensaje de comunidad saluda a la
  **comunidad GexClub** (corrección de branding).
- **Encoding UTF-8 sin BOM en release notes**: re-subidas las notas de
  v2.0.0/v2.0.1 y reconstruidas las de v2.0.2 (alcanzada por mojibake al
  reescribir con PowerShell 5.1: emojis y acentos no se renderizaban en
  GitHub). `docs/RELEASE.md` fija la regla: notas siempre con herramienta de
  archivo UTF-8 sin BOM.

---

## 🎙️ GexStudio Team → Comunidad GexClub

¡Buenas noches, comunidad GexClub! 🌙

Hoy vinimos a contarles algo que quizá ya sospechaban y que nos duele
admitir: **ibas a leer una noticia y el navegador embebido ya no aparecía**.
Resulta que, en la versión anterior, dejamos el motor escondido mientras la
página terminaba de cargar "por detrás"… y Chromium, en varios equipos, se
queda dormido cuando no lo puedes ver. El embebido ya no se nos vuelve a
perder: ahora la página salta siempre, con una red de seguridad que la
muestra si se demora (y de paso, el resumen instantáneo que tanto les gustó
se queda de cortesía mientras llega).

Y la segunda: **la barrita de abajo seguía diciendo v2.0.0** cuando ustedes
ya estaban en v2.0.2. No es que fuéramos lentos publicando — es que la
versión se leía de un archivo que olvidamos actualizar. Ahora J.A.R.V.I.S.
**se pregunta a sí mismo la versión desde el tag de la release**: cada vez
que publicamos una nueva, el launcher la muestra sola. Prometido.

De paso, afinamos nuestra casa: el mensaje de cada release ahora se escribe
según la **hora real de Bogotá** y saluda a nuestra gente: la **comunidad
GexClub**. Porque GexClub es el hogar, GexStudio Team es la familia que
desarrolla, y J.A.R.V.I.S. es el hijo de esa casa.

Con cariño, su equipo GexStudio Team. Que J.A.R.V.I.S. te acompañe en el
modo foco, comunidad. 🖤

---

## [2.0.2] - 2026-09-11 (America/Bogota)

### Fixed
- **Bug G-001 — la app se cerraba al cambiar la fuente de noticias**:
  `JarvisUI` no tenía el método público `apply_news_panel()` que invocaban el
  flujo de conexión (`jarvis_ui._open_connect_dialog`) y el diálogo de Ajustes
  (`settings_dialog._apply_and_close`); el `AttributeError` resultante cerraba
  el launcher al aceptar "CONECTAR" o "Aplicar". Ahora `apply_news_panel()` es
  API pública y delega en `_apply_news_panel_position()`.
- **Bug G-002 — el launcher se veía como "ventana flotante"**:
  `_center_on_screen()` limitaba la geometría a 1480×920 centrada; ahora la
  ventana (frameless y siempre al frente) se expande a la geometría completa
  del monitor activo y **tapa toda la vista** (modo foco total). El tamaño
  mínimo se calcula relativo a la pantalla (no falla en monitores pequeños).
- **Bug G-003 — las noticias no se actualizaban en la UI hasta reiniciar**:
  al guardar ajustes, el panel no se re-aplicaba ni re-descargaba. `Aplicar`
  ahora ejecuta `apply_news_panel()` (posición/visibilidad) y `refresh_news()`
  (descarga en vivo) sobre el padre `JarvisUI`.

### Added
- **Mensaje de la comunidad (ADR-011)** — a partir de esta versión cada
  release incluye un apartado de **GexStudio Team** dirigido a la comunidad
  (véase abajo), como parte de la metodología de documentación de releases.

### Changed (rendimiento de noticias)
- **G-004 — descarga de fuentes en paralelo**: `NewsService.fetch_sources`
  ahora descarga las fuentes de forma **concurrente** (`ThreadPoolExecutor`,
  máx. 6 workers) en vez de en serie. El tiempo total pasa de la *suma* de
  latencias a ~el *máximo*: 12 fuentes que antes tardaban ~4–8 s cargan en
  ~2 s (medido en offscreen). Las fuentes duplicadas por URL solo se
  descargan una vez; el caché de 600 s se conserva.
- **G-005 — cambio de artículo instantáneo en el lector**: al pasar de una
  noticia a otra, el lector muestra **al instante (≈1 ms)** el resumen del
  feed con la tipografía del tema y carga la página real (**web completa**)
  en segundo plano; salta a ella cuando termina de cargar. Antes cada cambio
  esperaba la descarga de red completa sin mostrar nada (varios segundos).

---

## 🎙️ GexStudio Team → Comunidad GexClub

¡Buenas noches, comunidad GexClub! 🌙

Esta semana estuvimos de guardia con el launcher y, como siempre, ustedes
fueron los primeros en avisar. Detectamos tres cosas que no nos dejaban
dormir tranquilos:

1. **Al cambiar el motor de noticias, J.A.R.V.I.S. se cerraba.** Malísimo:
   justo cuando ibas a conectar tu fuente favorita, adiós. Un método que el
   diálogo de Ajustes y el flujo de conexión esperaban no existía; el error
   tumbaba todo el launcher.
2. **La ventana se veía como una ventanita flotante.** J.A.R.V.I.S. nació
   para ser un HUD: ahora **tapa toda la vista**, pantalla completa, siempre
   al frente, como debe ser.
3. **Las noticias no se actualizaban solas.** Cambiabas la fuente o la
   posición del panel, cerrabas, y hasta volver a entrar no se veía nada.
   Ahora al aplicar ajustes el panel reacciona **al instante**.

Y, para no irnos con las manos vacías, aprovechamos la misma ronda para
hablar del otro tema que nos contaron por ahí: **"las noticias cargan muy
lento"**. Dos cirugías:

4. **El panel descarga las fuentes en paralelo.** Antes cada fuente se pedía
   una detrás de otra; si una se dormía, las demás hacían fila. Ahora todas
   se descargan al mismo tiempo y solo se espera a la más lenta: la primera
   carga del panel bajó de la *suma* de tiempos a **~el doble de la fuente
   más lenta** (12 fuentes: ~2 s en pruebas).
5. **El lector te enseña sin esperar.** Al cambiar de artículo ya no aparece
   la pantalla en blanco hasta que baja la página: ves **al momento** el
   resumen con la tipografía del launcher y, mientras tanto, la web completa
   se carga por detrás y salta sola. Cambiar de noticia ahora es **instantáneo**.

Todo corregido, probado y documentado: cada uno de estos arreglos quedó
registrado en el changelog con su identificador (G-001…G-005) y la decisión
técnica del modo foco total quedó sellada en el ADR-011.

Que J.A.R.V.I.S. te acompañe en el modo foco, comunidad. Hasta la próxima
entrega. 🖤

---

## [2.0.1] - 2026-09-11 (America/Bogota)

### Added
- **Optimización del lector de noticias (ADR-009)** — se elimina el *cold
  start* de Chromium que hacía lento el primer clic:
  - **Pre-warm del motor**: `NewsReaderView` se instancia oculto a los ~900 ms
    del boot (`QTimer.singleShot`); el primer clic solo navega a la URL real
    del artículo en lugar de arrancar Chrome embebido.
  - **Perfil persistente con caché HTTP en disco** (100 MB) en
    `%APPDATA%\JarvisLauncher\WebEngine`: re-visitas y assets repetidos cargan
    desde caché.
  - **Bloqueo de rastreadores/publicidad** (`_TrackerBlocker`, 17 dominios de
    ads/analytics): menos peticiones y bytes por página; no toca imágenes/CSS
    del sitio.
  - Settings de red: `DnsPrefetchEnabled` habilitado y
    `PlaybackRequiresUserGesture` (sin autoplay de video → menos datos).
  - Fade de apertura del lector reducido de 220 ms a **110 ms** (respuesta
    visual casi instantánea).
  - `JARVIS_DISABLE_WEBENGINE=1`: modo para CI headless que prueba el lector
    completo por el fallback de texto (el renderer de Chromium no navega sin
    GPU).

### Removed
- **`core/feedback.py` y sus 15 llamadas (ADR-010)**: se eliminan los sonidos
  `winsound.Beep` (click/éxito/error) de cards, panel, lector y Ajustes. El
  feedback pasa a ser **100 % visual** (hover, resaltado, sweep, barra de
  estado y notificaciones del sistema); cada clic ya no crea un hilo daemon de
  audio y la UI responde sin ruido.

---

## [2.0.0] - 2026-09-11 (America/Bogota)

### Added
- `core/hotkey.py` (`GlobalHotkey`): atajo global `Ctrl+Shift+Espacio` para
  convocar/ocultar el launcher desde cualquier aplicación, implementado con
  `RegisterHotKey` (API nativa de Windows vía ctypes) y
  `QAbstractNativeEventFilter`; degradación silenciosa si el atajo está en uso
- `core/tray.py` (`Tray`): bandeja del sistema con icono generado por código
  (`QPainter`, sin assets externos), menú contextual Mostrar/Salir y doble
  clic para invocar el launcher
- `core/greeting.py`: saludo dinámico según franja horaria (Buenos días /
  Buenas tardes / Buenas noches) + adjetivo profesional rotativo por arranque
  (Desarrollador, Ingeniero, Arquitecto, Creador, Hacker, Explorador, Maestro,
  Visionario, Estratega, Artesano)
- `core/github_link.py`: vinculación real de la cuenta de GitHub para que el
  launcher salude por el nombre real — detección automática con `gh` autenticado
  (`gh api user`) y verificación manual contra la API pública
  `GET https://api.github.com/users/{username}`; sin tokens ni secretos
- `core/settings.py`: nuevas claves de ajuste con migración suave —
  `tray.enabled`, `github.{username,name}` y `greeting.adjective_index`
- `ui/settings_dialog.py` (`GithubDialog`): modal de vinculación de cuenta
  GitHub con detección automática en hilo y verificación manual por username
- Opción 5 “Próximamente” en el panel de control: editor visual de modos,
  editor de paletas y lector de noticias a pantalla completa (estado borrador)

### Changed
- **Comportamiento de ventana (decisión C del diseño v2)**: el launcher queda
  SIEMPRE al frente (`show_and_raise` + `activateWindow`), se oculta
  automáticamente al elegir un modo (deja al frente las aplicaciones lanzadas)
  y se reinvoca con el atajo global o la bandeja; el botón ✕ ahora oculta a la
  bandeja en lugar de cerrar la aplicación
- `ui/mode_card.py`: rediseño "modo workspace" — el icono emoji flotante se
  sustituye por un monograma tipográfico (inicial del modo) en contenedor
  sobrio, barra de acento superior estilo IDE, paleta del tema, jerarquía clara
  (nombre / descripción / contador de aplicaciones en Consolas); se CONSERVAN
  los modos Gaming/Trabajo/Estudio tal como pidió el usuario
- `ui/news_panel.py`: cabecera nueva "¿QUÉ ESTÁ PASANDO EN EL MUNDO AHORA?",
  items con jerarquía tipográfica limpia (fuente + hora en dim, título
  destacado de 2 líneas, preview del resumen del feed), estado vacío sobrio sin
  emoji grande y botón CONFIG de fuentes
- `ui/settings_dialog.py`: el panel de control pasa a ser una LISTA
  ESTRUCTURADA con filas etiqueta-izquierda/control-derecha y separadores
  (1 · Apariencia, 2 · Comportamiento, 3 · Noticias, 4 · Cuenta de GitHub,
  5 · Próximamente); añadidos controles de bandeja y auto-inicio funcionales
- `ui/jarvis_ui.py`: integración de bandeja + atajo global + saludo dinámico;
  `refresh_greeting()` y `toggle_startup()` públicos para el diálogo de ajustes;
  el icono de bandeja se recolorea al cambiar de tema
- `main.py`: usa `show_and_raise()` al arrancar y detecta automáticamente la
  cuenta GitHub en un hilo si aún no está vinculada

### Fixed
- El launcher podía quedar detrás de otras ventanas al arrancar: ahora fuerza
  z-order y foco con `raise_()` + `activateWindow()`

### Lector de noticias (spec v2 puntos 3 y 4)
- `ui/news_reader.py` (`NewsReaderView` + `MiniBrowser` + `MiniNewsItem`):
  **lector de noticias a pantalla completa** que se abre al hacer clic en una
  noticia del panel:
  - **Mini navegador embebido (Chromium)**: `QWebEngineView` carga la **URL
    real del artículo** dentro del launcher, mostrando imágenes, CSS y el
    contenido completo del sitio; botones **⟳** (recargar) y
    **ABRIR ORIGINAL ↗** (navegador externo) en el encabezado
  - **Split-pane redimensionable** (`QSplitter`) con lista compacta a la
    izquierda (título + fuente/hora, artículo actual resaltado) y el mini
    navegador a la derecha
  - **Fallback elegante sin la dependencia**: si `PyQt6-WebEngine` no está
    instalado, el lector muestra el resumen del feed con la tipografía de
    lectura larga de la v2 (lead con capitular, pull-quote en cursiva) en un
    `QTextBrowser`; la app nunca deja de funcionar
  - Navegación por teclado: `←`/`→` cambian de artículo y `Escape` vuelve al
    launcher; feedback de carga en el encabezado ("Cargando artículo…")
- `main.py`: `QApplication.setAttribute(AA_ShareOpenGLContexts, True)` antes
  de crear la app (requisito del WebEngine)
- Panel des saturado: `ui/news_panel.py` elimina el preview apilado (cada
  noticia queda con fuente + hora + título, sin texto encima de otro), altura
  de tarjeta reducida a 88 px, más respiro entre items (spacing 10) y lista
  limitada a 12 noticias; el clic emite `readerRequested(items, index)` y
  abre el lector (el enlace original queda dentro del lector)
- `ui/jarvis_ui.py`: integra `NewsReaderView` bajo demanda
  (`_open_reader` / `_close_reader`), conecta `readerRequested`, prioriza los
  atajos del lector en `keyPressEvent` y aplica el tema vivo al abrir
- `requirements.txt`: añadido `PyQt6-WebEngine>=6.7` como dependencia
  **opcional** (mini navegador del lector; el fallback de texto no la exige).
  Instalada en el entorno: `PyQt6-WebEngine 6.11.0`
- Docs: `docs/ADR-007-lector-noticias.md` actualizado y
  `docs/ADR-008-webengine.md` (decisión del mini navegador: justificación de
  la dependencia y fallback); `docs/Arquitectura.md`, `README.md` y
  `TODO.md` actualizados

---

## [1.4.0] - 2026-09-10 (America/Bogota)

### Added
- `core/settings.py` (`SettingsManager`): preferencias de interfaz del usuario
  en `settings.json` separado de `config.json` (tema, estado/posición/ancho del
  panel de noticias y fuentes RSS); `settings.json` excluido de git
- `core/themes.py` (`Theme` + `ThemeManager`): sistema de temas de color con 8
  paletas (obsidiana, nocturno, crimson, esmeralda, matriz, violeta, ambar,
  luz, nieve) y helper `rgba()` para construir `QColor` con alpha
- `core/news.py` (`NewsService`): descarga/parseo de feeds RSS 2.0 y Atom con
  solo la biblioteca estándar (sin dependencias nuevas); 10 fuentes
  predefinidas + URL RSS/Atom personalizada; fechas normalizadas a UTC aware
- `ui/news_panel.py` (`NewsPanel`): panel lateral de noticias con posición
  izquierda/derecha, ancho redimensionable por el borde (280–560 px), refresh
  automático cada 10 min, descarga en hilo separado (señal a la UI),
  animación de entrada por tarjeta y apertura de la noticia en el navegador al
  hacer clic; estado desconectado con botón CONECTAR
- `ui/settings_dialog.py` (`SettingsDialog`): rueda ⚙ con selector de tema
  (swatches), activación y posición del panel de noticias; `ConnectDialog`
  modal con presets y URL personalizada con validación en hilo
- `ui/mode_card.py`: tarjeta con pintura 100% custom, icono flotante animado,
  zoom en hover, sweep de selección, brackets de esquina y entrada escalonada
- `ui/jarvis_ui.py`: layout compacto sin huecos grandes (barra superior,
  título, tarjetas, estado y panel lateral), temas en caliente en todos los
  fondos HUD, rueda de ajustes integrada
- Docs: `docs/ADR-004-temas-thememanager.md` y
  `docs/ADR-005-panel-noticias-rss.md`; `docs/Arquitectura.md` actualizada con
  los nuevos módulos y flujos

### Fixed
- Crash nativo al iniciar en Qt6 por constructores inválidos
  `QColor("#hex", alpha)` en overlays y grid (reemplazados por
  `ThemeManager.rgba`)
- `ConnectDialog`: la validación de URL usaba `QMetaObject.invokeMethod` con
  kwargs (API inválida en PyQt6); se reemplazó por la señal Qt propia
  `validationDone(bool, str)` con entrega segura al hilo principal

### Changed
- `ui/mode_card.py` dejó de usar sub-widgets para el contenido: todo el estado
  visual se pinta en `paintEvent` (más liviano y sin conflictos de painter)
- `main.py` ahora inyecta `SettingsManager` a `JarvisUI`
- `.gitignore` excluye `settings.json` (preferencias locales del usuario)

---

## [1.3.0] - 2026-09-10 (America/Bogota)

### Added
- Comando global `jarvis`: `assets/jarvis.cmd` + instalador `install_jarvis_cmd.bat`
  que copia el script a `%USERPROFILE%\bin` y lo agrega al PATH de usuario
- Se abre cualquier ventana nueva de CMD o PowerShell y se escribe `jarvis`
  para lanzar el launcher (usa `pythonw.exe`, sin consola y devuelve el prompt)

### Fixed
- El comando resuelve correctamente desde PowerShell y CMD (verificado con
  reconstruccion del PATH desde el registro y lanzamiento real del proceso)

### Docs (histórico absorbido)
- Carpeta `docs/` creada como fuente principal de documentación técnica
  (`Arquitectura.md` + ADR-001/002/003) y enlace desde el README raíz
- README se declara explícitamente como documentación de usuario final

---

## [1.2.0] - 2026-09-10 (America/Bogota)

### Fixed
- Conflictos de QPainter (`paint device can only be painted by one painter`): se eliminaron todos los `QGraphicsEffect` (opacity en la ventana, drop shadow en las tarjetas) que, combinados con `paintEvent` custom, generaban spam de errores y tarjetas pintadas en negro al hacer hover en Qt6
- Fade-in de la ventana ahora usa la propiedad nativa `windowOpacity` en lugar de `QGraphicsOpacityEffect`
- Overlays (boot y flash) ahora animan su opacidad con propiedades propias (`fade`/`alpha`) y repintado manual
- Sonidos de feedback: reemplazado `PlaySound(SND_ALIAS)` (dependia del esquema de sonido de Windows) por `winsound.Beep` con frecuencias reales en hilos daemon
- `core/launcher.py`: resolucion robusta de rutas de apps (PATH, menu de inicio `.lnk` via COM y registro App Paths); mensaje claro cuando la app no esta instalada
- `config.json`: las apps Discord y Spotify ahora usan nombre corto (`"Discord"`, `"Spotify"`) en lugar de rutas fijas que cambiaban con cada instalacion

### Added
- Beam de energia desde el nucleo central hacia la tarjeta seleccionada (efecto HUD animado)
- Corner brackets estilo mira/arqueria en las tarjetas (se acentuan en hover)
- Halo exterior de hover dibujado manualmente (reemplaza al `QGraphicsDropShadowEffect`)
- Pantalla de boot rediseñada: barra de progreso animada, titulo con glow medido por font metrics y posiciones dinamicas

### Changed
- `ui/mode_card.py`: sin `QGraphicsDropShadowEffect`, todo el glow se dibuja en `paintEvent`
- Boot overlay centrado dinamicamente segun el ancho real del texto

---

## [1.1.0] - 2026-09-09 (America/Bogota)

### Fixed
- Error `ImportError: QDesktopWidget` en PyQt6: reemplazado por `QApplication.primaryScreen().availableGeometry()`
- Fuga del lock de instancia unica: el socket ahora se retiene globalmente y no usa SO_REUSEADDR
- Limpieza del handler de seleccion de modo en `main.py` (sin ui=None provisional)

### Added
- `core/state.py`: historial de modos recientes persistente (`state.json`)
- `core/feedback.py`: sonidos de feedback con winsound (click, exito, error)
- `core/notifier.py`: notificaciones toast nativas de Windows via PowerShell
- Pantalla de boot animada tipo arranque de sistema
- Efecto typewriter en el greeting
- Flash de color del modo al seleccionar + pulse de tarjeta al click
- Barra de estado muestra el ultimo modo usado y hace cuanto
- Soporte multi-monitor (centrado en monitor primario)

---

## [1.0.1] - 2026-09-09 (America/Bogota)

### Added
- `.gitignore` para excluir `__pycache__`, entornos virtuales y archivos de IDE
- Repositorio publico: https://github.com/GexStudio-Team/jarvis-launcher
- Proyecto movido a `Documents/Proyectos/GexClub/proyectos/jarvis-launcher`

---

## [1.0.0] - 2026-09-09 (America/Bogota)

### Added
- Interfaz principal tipo JARVIS con efectos HUD completos (anillos rotantes, particulas, scan line, vignette)
- 3 modos de operacion: Gaming, Trabajo, Estudio
- Tarjetas animadas con efecto glassmorphism, hover glow y elevacion
- Motor de lanzamiento de aplicaciones con soporte para ejecutables, argumentos y URLs
- Configuracion via `config.json` (JSON editable)
- Auto-inicio en Windows con script VBS (oculta consola)
- Boton de toggle auto-inicio desde la interfaz
- Deteccion de instancia unica (puerto local)
- Lanzamiento de apps en hilo separado para no bloquear la UI
- Atajos de teclado: Escape (cerrar), F11 (fullscreen)
- Documentacion completa: README, CHANGELOG, TODO
