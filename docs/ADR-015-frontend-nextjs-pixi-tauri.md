# ADR-015: Arquitectura Frontend Next.js 16, PixiJS v8, Esfera/Vórtice ASCII 3D, Doble Motor (Ollama + OpenCode) y Tauri v2

- **Estado**: Aceptado y Actualizado
- **Fecha**: 2026-09-22T12:13:00-05:00
- **Autores**: Brandon Carranza & Dual Dev Squad (🌸 Chibi-chan & 🦇 Kuro-chan)
- **Contexto**: J.A.R.V.I.S. Launcher evoluciona de una interfaz clásica de escritorio a un HUD terminal minimalista de grado industrial, acelerado por GPU y empaquetado nativamente con Tauri v2, con control total de PC, búsqueda web en tiempo real y política estricta anti-emojis.

---

## 1. Contexto y Problema

La interfaz previa en PyQt6 presentaba limitaciones para animaciones web modernas, visualización matemática continua de alto refresco (60+ FPS) y personalización fluida de layouts reactivos sin sobrecargar la CPU. Asimismo, se requería una estética anti-"AI slop":
- Cero gradientes de neón o brillos difusos artificiales.
- Fondo OLED negro absoluto (`#000000`).
- Geometría 3D generada puramente en caracteres ASCII con proyección tridimensional real y corrección de aspecto tipográfico.
- Chatbot redimensionable y conectado en streaming con el motor local Ollama (`qwen2.5-coder:7b`) y conmutación hacia agente autónomo OpenCode (`~/.opencode/bin/opencode`).
- Requerimiento inmutable: **Cero emojis bajo ningún contexto ni motor**.
- Control total de PC (apertura de apps, ejecución de comandos en shell) con modal interactivo de confirmación destructiva.

---

## 2. Decisión

Se adopta una arquitectura desacoplada moderna:

1. **Frontend (`src-web/`)**:
   - **Framework**: Next.js 16 (React 19, TypeScript) con exportación estática (`output: "export"`).
   - **Motor Gráfico**: PixiJS v8 (`pixi.js@8.21.0`) para renderizado acelerado WebGL/WebGPU en un canvas dinámico 100% responsivo con `ResizeObserver`.
   - **Cinemática**: GSAP Core (`gsap@3.15.0`) y micro-interacciones CSS nativas (`text-glitch` de 0.35s).
   - **Markdown HUD**: `react-markdown` y `remark-gfm` para renderizado de tablas Paper/Terminal con botón de copiado al portapapeles y estilo tipográfico estructurado.

2. **Empaquetado de Escritorio (`src-web/src-tauri/`) y Puente de Sistema (`scripts/bridge_server.py`)**:
   - **Tauri v2 (Rust)**: Contenedor de escritorio ultraligero (<30 MB RAM) con comandos `execute_shell` y `run_opencode`.
   - **Bridge Server HTTP (`http://127.0.0.1:3002`)**: Servidor local en Python para soporte web/desarrollo de ejecución de shell, OpenCode y lanzamiento de modos de aplicaciones (`core.launcher.AppLauncher`).

3. **Renderizado de la Esfera ASCII 3D y Morphing a Vórtice (`NeuralCanvas.tsx`)**:
   - **Modo Zen**: 8 meridianos y 7 paralelos calculados matemáticamente en coordenadas esféricas 3D, inclinación axial fija de 15° y rotación pausada sobre el eje Y (`delta * 0.003`).
   - **Modo Razonamiento**: Vórtice concéntrico 3D de 14 anillos de partículas ASCII con rotación diferencial calibrada (`delta * 0.007`).
   - **Transición Continua (Morphing)**: Desacoplamiento del ciclo de vida de PixiJS mediante `isThinkingRef`. Curva smoothstep cúbica ($3t^2 - 2t^3$) a lo largo de ~1.2 segundos en ida y retorno, sin reinicios del canvas.
   - **Responsividad Total**: `ResizeObserver` vinculado a `app.renderer.resize(newW, newH)` sobre contenedor `flex-1 min-w-0`, recentrando matemáticamente la esfera al redimensionar el chat.

4. **Logo SVG J.A.R.V.I.S. (`JarvisLogo.tsx`)**:
   - Reactor Arc vectorial minimalista monocromático en esquina superior derecha con rotación sincronizada al estado de inferencia.
   - Marca técnica `J.A.R.V.I.S. v2.5` y telemetría de estado.

5. **Inferencia Dual y Control de PC (`ChatPanel.tsx`)**:
   - **Doble Motor**: Toggle `[motor: ollama / opencode]` con fallback automático hacia OpenCode si Ollama no está disponible.
   - **Búsqueda Web en Vivo**: Detección de intención (`busca:`, `noticias`, etc.) con inyección de snippets web al contexto.
   - **Historial de Sesiones**: Drawer desplegable con persistencia en `localStorage`.
   - **Seguridad**: Detección estricta de comandos destructivos (`rm`, `kill`, etc.) con modal interactivo de confirmación.
   - **Blindaje Cero Emojis**: Filtrado en 3 capas (prompting estricto, regex en stream y purificación en renderizado con `stripEmojis`).
   - **Estructuración HUD y Acordeón**: Telemetría de consola y logs de búsqueda encapsulados en `<details><summary>[+] Telemetría...</summary>` y viñetas formateadas con guiones largos.

---

## 3. Consecuencias

### Positivas:
- Rendimiento a 60 FPS estables sin bloqueos ni cortes en la animación.
- Respuestas limpias, estructuradas y profesionales sin emojis ni ruido de telemetría de consola.
- Control seguro del sistema operativo con confirmación explícita para evitar pérdida de datos.
- Resiliencia agéntica: si el modelo local falla, OpenCode asume automáticamente la tarea.

### Consideraciones:
- Requiere tener Ollama activo en el puerto 11434 o el binario OpenCode instalado en `~/.opencode/bin/opencode`.
- En modo navegador, el servidor puente en el puerto 3002 debe estar en ejecución para comandos de terminal.
