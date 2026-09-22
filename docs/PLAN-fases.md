# PLAN — Roadmap del asistente: Fases 1–4

- **Fecha**: 2026-09-22 (America/Bogota)
- **Estado**: Plan vigente. Fase 1 en especificación; Fases 2–4 solo
  dimensionadas (sin ESPEC hasta terminar la anterior).

## Fase 1 — Chat + Sistema (actual)

- **Objetivo**: conversar con el PC (archivos, shell, apps) con confirmación
  total. Contrato: [ESPEC-agente-fase1.md](./ESPEC-agente-fase1.md).
- **Entregables**: `core/agent/` (ollama, tools, loop, policy),
  `ui/chat_panel.py`, settings `agent.*`, `agent_log.jsonl`, tests
  (`TEST-agente.md`), verificación Ollama en `install.py`.
- **Aceptación**: checklist manual 10/10 + suites unitarias/offscreen en verde
  + `compileall` OK + latencia de primer token < 30 s en la CPU de referencia.
- **Riesgos**: tool-calling indisciplinado del 7b (mitigado con schemas
  estrictos + reintento `INVALID_ARGS`); context 8k (mitigado con compactado
  B6); aprobar-sin-leer (aviso de primer uso).

## Fase 2 — Visión de pantalla

- **Objetivo**: "¿qué ves en mi pantalla?" y asistencia contextual
  (leer un error visible, guiar un clic).
- **Entregables previstos**: tool `see_screen()` (captura vía `QScreen.grab`
  o `gnome-screenshot`, downscale máx 1280 px + JPEG q70 para caber en
  contexto); modelo visión `qwen2.5vl:7b` (~5 GB, `ollama pull`) conmutable
  desde Ajustes; tarjeta de aprobación 🟢 para capturas (son lectura).
- **Aceptación (borrador)**: describe la ventana enfocada con ≥80 % de
  acierto en checklist de 10 capturas; latencia < 60 s en CPU.
- **Dependencias**: ESPEC Fase 2 (payload multimodal `/api/chat` con
  `images:[base64]`); evaluar RAM (visión 7b ≈ +5 GB residente).
- **Riesgos**: alucinación de elementos UI (mitigar pidiendo coordenadas
  relativas + confirmación antes de actuar sobre lo visto).

## Fase 3 — Web: navegación y extracción

- **Objetivo**: "lee esta página y resúmela / extrae la tabla a CSV".
- **Entregables previstos**: tool `fetch_url(url)` → markdown limpio
  (reusa patrones de `core/news.py`, timeout 20 s, tope 200 KiB, sin JS);
  tool `browser_open(url)` que ordena al `MiniBrowser` existente cargar la
  URL (solo navegación, sin DOM automation en esta fase); guardado a archivo
  vía `write_file` (con su tarjeta 🟡 habitual).
- **Aceptación (borrador)**: 5 sitios reales (noticia, docs, tabla) extraídos
  con contenido verificable; `fetch` malicioso (`file:///etc/passwd`,
  `http://localhost:11434`) bloqueado por allowlist `http(s)` público.
- **Dependencias**: ESPEC Fase 3; regla de seguridad: el contenido web entra
  como DATOS (regla 4 del system prompt) y jamás dispara tools encadenadas
  sin aprobación.
- **Riesgos**: prompt-injection web (mitigado por ADR-014 capas 2–4).

## Fase 4 — Voz (STT/TTS local)

- **Objetivo**: hablar y escuchar al estilo JARVIS, 100 % offline.
- **Candidatos**: STT `Whisper.cpp` (modelo `base`/`small`, ~150–500 MB),
  TTS `Piper` en español (~100 MB/voz). Ambos binarios externos al pip
  (descarga en `install.py --with-voice`, no en el flujo base).
- **Aceptación (borrador)**: latencia pregunta→audio < 2× la del texto;
  botón micrófono + push-to-talk (`Ctrl+M`); transcripción editable antes de
  enviar (cuenta como el texto escrito: el loop exige aprobación igual).
- **Dependencias**: ESPEC Fase 4; evaluar costo CPU concurrente (STT + LLM +
  TTS sin GPU) — posible requisito de modelos más pequeños o turnos más
  cortos; wake-word ("Jarvis") explícitamente fuera (privacidad micrófono
  siempre abierto).
- **Riesgos**: mayor superficie de instalación; se mantiene opcional.

## Reglas entre fases

1. Ninguna fase empieza sin su ESPEC + TEST + criterios de aceptación.
2. La política ADR-014 no se relaja sin ADR nuevo.
3. Cada fase suma tools versionando `AGENT_SYS_Vn` y actualizando CHANGELOG.
