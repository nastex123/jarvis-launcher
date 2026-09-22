# ADR-013: Asistente IA local con Ollama (`qwen2.5-coder:7b`) y herramientas del sistema (Fase 1)

- **Estado**: Aceptado (documentación previa a implementación)
- **Fecha**: 2026-09-22 (America/Bogota)
- **Versión asociada**: v3.0.0 (planificada — Fase 1: Chat + Sistema)
- **Decisores**: Brandon (usuario), Muse Spark (opencode)
- **Tipo**: Feature / nuevo subsistema (`core/agent/` + `ui/chat_panel.py`)

## Contexto

El proyecto evoluciona de *launcher* de modos a *asistente IA local* capaz de
gestionar el PC: leer/editar archivos, ejecutar comandos, abrir aplicaciones y
responder con lenguaje natural, todo con modelos ejecutados en la propia
máquina (privacidad total, cero costo por token, funciona sin internet salvo
noticias/GitHub).

Entorno de referencia verificado el 2026-09-22:

| Recurso | Valor |
|---|---|
| CPU | 12 hilos |
| RAM | 15 GiB (5.6 GiB disponibles en la medición) |
| GPU | Sin GPU NVIDIA (inferencia por CPU) |
| SO / sesión | Ubuntu 24.04, GNOME, Wayland |
| Ollama | Instalado (`/usr/local/bin/ollama`), demonio disponible en `localhost:11434` |

Modelos ya descargados en Ollama:

| Modelo | Tamaño | Tool-calling | Idoneidad como cerebro agéntico |
|---|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Sí (nativo, formato `tools` de Ollama) | ✅ Alta: entrenado para llamadas a función y código |
| `brsilvapimentel/DeepSeek-R1-0528-Qwen3-8B` | 2.0 GB | Parcial (reasoning, tools inestable) | ⚠️ Media: bueno razonando, flojo obedeciendo schemas |
| `huihui_ai/deepseek-r1-abliterated:8b` | 5.0 GB | Parcial (igual que arriba, sin censura) | ⚠️ Media, mismo perfil que el anterior |
| `gemma4:12b` | 7.6 GB | Sí | ❌ Lento en CPU sin GPU para uso interactivo |

Rendimiento esperado en esta CPU con un 7b cuantizado: **~10–20 tok/s**,
suficiente para turnos cortos de comando/respuesta con tool-calling.

Restricciones heredadas del proyecto: **cero dependencias pip nuevas**
(stdlib + PyQt6), dual Windows+Linux donde sea razonable, tono formal en docs,
zona horaria `America/Bogota`.

## Opciones consideradas

| Opción | Implementación | Ventajas | Desventajas | Veredicto |
|---|---|---|---|---|
| A. `qwen2.5-coder:7b` local vía Ollama | Cliente HTTP stdlib (`urllib`) contra `/api/chat` con `tools` | Ya instalado; tool-calling fiable; rápido en CPU; 100 % local | Razonamiento general inferior a modelos grandes | ✅ Elegida (Fase 1) |
| B. Descargar `qwen3:8b` | `ollama pull qwen3:8b` (~5 GB) | Mejor razonamiento + tools que A | Descarga pesada; latencia algo mayor en CPU | ⏳ Reserva si A queda corto (Fase 2+) |
| C. `gemma4:12b` local | Usar el modelo existente | Más capaz en conocimiento general | Lento sin GPU; tool-calling menos disciplinado que A | ❌ No cumple interactividad |
| D. API cloud (Claude/OpenAI) | SDK + API key | Máxima capacidad | Viola "IA local" (privacidad, costo, offline); dependencia nueva | ❌ Descarta el objetivo |

## Decision

1. **Cerebro**: `qwen2.5-coder:7b` vía Ollama local, endpoint configurable
   (default `http://localhost:11434`), chat con `tools` en formato Ollama
   (`{"type":"function","function":{"name","description","parameters"}}`).
2. **Cliente** (`core/agent/ollama.py`): solo stdlib (`urllib.request`,
   `json`); timeouts configurables (default 120 s); **3 reintentos con
   backoff** (1 s, 2 s, 4 s) ante errores de conexión/timeout; `temperature`
   default `0.2` (disciplina en tools); `num_ctx` default `8192`;
   `keep_alive` default `"30m"` para no recargar el modelo entre turnos.
3. **Modo degradado**: si el demonio no responde tras los reintentos, el chat
   muestra estado *offline* con el diagnóstico exacto (conexión rechazada /
   timeout / modelo ausente) y botón **Reintentar**; el resto del launcher
   sigue 100 % funcional (el agente es un subsistema, no el entry point).
4. **Hilo de ejecución**: el bucle agéntico corre en `QThread`
   (`AgentWorker`); la UI solo se toca vía señales Qt (mismo patrón que el
   lector de noticias y el lanzamiento de modos). Prohibido bloquear el hilo
   principal: toda llamada a Ollama y toda tool van al worker.
5. **`install.py`**: nueva verificación (no instalación) — comprueba binario
   `ollama`, demonio alcanzable y modelo presente en `ollama list`; si falta
   algo imprime el comando exacto (`ollama serve`, `ollama pull
   qwen2.5-coder:7b`) y continúa con aviso (el launcher no depende del agente).
6. **Idioma**: system prompt y respuestas en español; los nombres de tools y
   sus parámetros en inglés snake_case (convención de schemas).
7. **Versionado del prompt**: constante `AGENT_SYS_V1` en `core/agent/loop.py`;
   cualquier cambio de system prompt o de catálogo de tools incrementa la
   versión (`V2`…) y se registra en el CHANGELOG.

## Consecuencias

- **Positivas**: asistente totalmente local y privado; sin dependencias pip;
  reutiliza `core/launcher.py` (resolución PATH/`.desktop`/alias) y
  `core/notifier.py`; base extensible a visión/web/voz (Fases 2–4,
  ver `PLAN-fases.md`).
- **Negativas / límites**: latencia de CPU (~10–20 tok/s) — turnos largos se
  sienten; contexto 8k — historiales largos se resumen/truncan (ver ESPEC
  §3.9); `qwen2.5-coder:7b` puede proponer args inválidos — por eso existe la
  política de confirmación (ADR-014) y los errores tipados (ESPEC §3.3).
- **Pruebas**: ver `TEST-agente.md` (unitarias con Ollama mockeado + checklist
  en máquina real con `ollama serve`).

## Referencias

- [ADR-014](./ADR-014-politica-confirmacion.md) (seguridad y confirmación)
- [ESPEC-agente-fase1.md](./ESPEC-agente-fase1.md) (contrato implementable)
- [PLAN-fases.md](./PLAN-fases.md) (roadmap Fases 1–4)
- [TEST-agente.md](./TEST-agente.md) (plan de pruebas)
- Sección 9 de [Arquitectura.md](./Arquitectura.md) (subsistema agente)
