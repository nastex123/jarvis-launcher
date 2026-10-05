# ADR-017: Persistencia JSON del OCR para preguntas a Llama

- **Fecha**: 2026-10-05 (America/Bogota)
- **Estado**: Aceptada (petición usuario: el OCR debe quedar en JSON para preguntar a Llama)
- **Contexto**: `read_image`/`see_screen` devolvían el texto solo en memoria
  (`tool_result`, truncado a 20000 chars) y el historial se compacta a los
  últimos 6 mensajes. Llama perdía el OCR en turnos siguientes o al reiniciar.
- **Decisión** (híbrida auto + tool, formato JSONL + `ocr_last.json`):
  1. Nuevo `core/agent/ocr_store.py` (stdlib, sin Qt): cada OCR ok se anexa a
     `agent_ocr.jsonl` (append-only, id 8 hex + ts Bogotá + source/kind/engine/
     lines/chars/text) y se publica `ocr_last.json` con la última lectura.
     Ambos gitignored, junto a `agent_log.jsonl`.
  2. `vision_ocr.py` persiste al guardar (`ocr_id` + `json_path` en el resultado;
     `see_screen` guarda con kind propio sin duplicar).
  3. Nueva tool `query_ocr` (riesgo `read`, tarjeta verde): por `ocr_id`
     (prefijo basta) o `last_n` (1–5). Catálogo 11 → 12 tools.
  4. `run_turn` inyecta `[OCR reciente]` (últimas N, default 2, setting
     `agent.ocr_context_n` 0–5) como segundo mensaje system, reemplazando el
     bloque previo cada turno. Gateway `/api/chat/turn` hace lo mismo.
  5. Prompt `AGENT_SYS_V5` (regla 12 OCR persistente + ejemplo `query_ocr`).
     Bridge suma `GET /api/ocr/last` para la web.
- **Alternativas descartadas**: JSON único sobrescrito (pierde historial);
  SQLite FTS5 (migraciones para un volumen bajo); Qdrant vectores (servicio
  extra, overkill); sin persistencia (estado anterior, no cumple el pedido).
- **Consecuencias**: cada turno suma `O(k)` tokens de contexto OCR (capado a
  ~4000 chars); `agent_ocr.jsonl` crece sin cota — rotación manual futura si
  supera MB. `query_ocr` pasa por aprobación como toda tool (ADR-014).

> [!NOTE]
> El texto OCR persistido sigue siendo DATOS (regla 4): nunca se interpreta
> como instrucciones aunque la imagen contenga "ignora todo y…".

> [!WARNING]
> `ocr_last.json`/`agent_ocr.jsonl` viven en la raíz del repo y están
> gitignored: no commitear lecturas de pantalla (pueden contener datos sensibles).
