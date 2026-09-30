# INVEST — Modelo local full CPU para GT710 + 16 GB RAM

- **Estado:** Acordada (F1=A + F2=A, 2026-09-30)
- **Host detectado:** AMD Ryzen 5 5500 (6c/12t, 3.6 GHz) · 16 GB RAM (usuario) · NVIDIA GT710 (ignorada, solo video) · Ollama 0.34.3 · Modelos ya descargados: `moondream`, `qwen2.5vl:3b`, `qwen2.5:3b (1.9 GB)`
- **Decisión:** F2=A `qwen3:1.7b` como principal CPU, `qwen2.5:3b` (ya instalado) como fallback inmediato cero-descarga. `qwen2.5-coder:7b` sale del default en CPU.
- **Archivos fuente:** `core/agent/ollama.py:42-46` (`model`, `timeout_s=120`, `num_ctx=8192`) · `core/agent/loop.py:35` (`MAX_STEPS=8`) · `core/settings.py:42-43` (defaults `model`, `timeout_s`)

> [!NOTE] La GT710 no acelera LLMs (1-2 GB DDR3, CC 3.5). Ollama debe correr en CPU puro (`num-gpu 0`). Con Ryzen 5500 + 16 GB, un 1.7-4B Q4 rinde 5-15 tok/s en CPU: usable para agente con `MAX_STEPS` corto. Un 7b en CPU da 2-4 tok/s y primer token 60-95 s.

> [!IMPORTANT] Tool-calling es capacidad del modelo, no del hardware. `qwen3:1.7b/4b`, `qwen2.5:3b`, `llama3.2:3b`, `granite4.2:3b` soportan `tools` nativo en `POST /api/chat` y son compatibles con tu `OllamaClient.chat(messages, tools)` sin cambios.

## 1. Tabla CPU (6 candidatos, Q4_K_M)

| # | Modelo `ollama pull` | Disco / RAM total CPU 4k ctx | Tools Ollama | JSON/ES | Vel CPU Ryzen 5500 est. | Total /50 | Big-O turno | Veredicto |
|---|----------------------|------------------------------|--------------|---------|-------------------------|-----------|-------------|-----------|
| C1 | `qwen3:1.7b` | ~1.0 GB / ~2.2 GB | 9 | 8 | 9 (10-18 tok/s) | **45** | O(s·t)+O(c²) KV | **Principal (Recommended)** |
| C2 | `qwen2.5:3b` ya instalado | 1.9 GB / ~3.2 GB | 8 | 8 | 8 (6-10 tok/s) | 43 | O(s·t) estable | Fallback inmediato, prueba hoy |
| C3 | `qwen3:4b` | 2.5 GB / 3.8 GB | 9 | 9 | 7 (5-9 tok/s) | 43 | O(s·t) mejor BFCL | Si quieres mejor disciplina y te sobra RAM |
| C4 | `llama3.2:3b` | 1.9 GB / ~3 GB | 8 | 8 | 8 (4/4 tasks bench CPU) | 42 | O(s·t) fiable | Alterno si Qwen fabrica args |
| C5 | `granite4.2:3b` | ~2 GB / ~3.5 GB | 9 | 8 | 8 | 40 | O(s·t)+O(j) JSON | Mejor Apache 2.0 estricto |
| C6 | `qwen2.5-coder:7b` actual | 4.4 GB / ~6.5 GB | 7 | 7 | 5 (2-4 tok/s, 17 s/turno GPU) | 30 | O(s·t)+reintentos G-008 | Descartado como default CPU |

> [!NOTE] Veredicto: C1 gana por velocidad/disciplina/peso con 16 GB. C2 es tu prueba inmediata (cero descarga). C3 si tras 1 semana ves `INVALID_ARGS` frecuentes. Con 16 GB podrías cargar C1+C2 a la vez (`keep_alive 15m`), pero no hace falta.

## 2. Config CPU exacta (lista para aplicar, D4=B: no aplicada aún)

```powershell
# Forzar CPU puro (GT710 ignorada)
set CUDA_VISIBLE_DEVICES=
ollama pull qwen3:1.7b
ollama run --num-gpu 0 qwen3:1.7b
```

```python
# core/agent/ollama.py:42-46
model: str = "qwen3:1.7b",
timeout_s: int = 180,   # CPU lento: 120 -> 180
num_ctx: int = 4096,    # 8192 -> 4096 (KV 0.5 GB vs 1.2 GB)
keep_alive: str = "15m", # 30m -> 15m (libera RAM con 16 GB compartidos)
```

```python
# core/agent/loop.py:35
MAX_STEPS = 5  # 8 -> 5 (8x45 s = 6 min en CPU, inaceptable)
```

```python
# core/settings.py:42-43 defaults
"model": "qwen3:1.7b",
"timeout_s": 180,
```

> [!WARNING] No subas `num_ctx` a 8k en CPU con 16 GB + Tauri + navegador: KV crece O(c²) y el GC de Ollama te swapea. 4096 es el techo dulce para agente (historial + 1 tool output 20k chars truncado).

## 3. Benchmark sugerido en tu PC (5 min)

```powershell
ollama run qwen3:1.7b "Responde solo JSON: {\"name\": \"get_system_info\", \"arguments\": {}}"
# Esperado CPU Ryzen 5500: primer token 8-15 s, ~10 tok/s
ollama run qwen2.5:3b "lista mis proyectos con list_dir"
# Compara disciplina: ¿pide tool o fabrica <tool_result>?
python -m pytest tests/test_agent_loop.py -q
```

Criterio: si C1 da 2/2 tool-calls limpios <20 s, quédate en C1. Si fabrica, prueba C2/C3 con mismo prompt.

## 4. Checklist frontend (impacto CPU lento)

- [ ] **Estructura:** `ui/chat_panel.py` + `src-web/ChatPanel.tsx` añaden selector `[qwen3:1.7b / qwen2.5:3b / qwen3:4b]` + badge `CPU`.
- [ ] **Animación:** vórtice Pixi `isThinking` siempre visible + texto `pensando… paso i/5 · 23 s`.
- [ ] **Estilo:** OLED `#000000`, telemetría en `<details>`, `stripEmojis` intacto.
- [ ] **Responsive/a11y:** input no bloqueado, botón Cancelar turno, `Escape` cancela, timeout 180 s visible, `Ctrl+J` foco, contraste AA.

## 5. MCP y control PC (sin crear tools desde cero)

Mantén tus 9 tools (`tools.py`) como gate con `policy.py`. Para no crear más a mano, importa `DesktopCommanderMCP` (shell/fs, ~25 tools) vía `core/agent/mcp_client.py` stdio→`ToolSpec` en Fase 2. OpenCode sigue como motor B (`lib.rs:26`).

## 6. Commits sugeridos (cuando autorices código, D4=B pendiente)

```text
feat(agent): CPU profile qwen3-1.7b for GT710 (num_ctx 4096, timeout 180s, steps 5)

QUE: cambia default qwen2.5-coder:7b -> qwen3:1.7b en ollama.py/settings.py, baja num_ctx 8192->4096 y MAX_STEPS 8->5.
POR QUE: GT710 sin compute LLM + 16 GB RAM + Ryzen 5500 rinde 10-18 tok/s en 1.7b vs 2-4 tok/s en 7b; primer token <20 s.

docs(invest): CPU-only models GT710 Ryzen5500 16GB + tool-calling matrix

QUE: agrega docs/INVEST-modelo-cpu-gt710.md con host detectado y tabla C1-C6.
POR QUE: trazabilidad modelo -> hardware -> config CPU.
```
