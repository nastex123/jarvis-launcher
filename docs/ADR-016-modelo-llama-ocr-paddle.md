# ADR-016: Modelo local `llama3.2:1b` + lectura de imágenes con PaddleOCR local

- **Fecha**: 2026-10-05 (America/Bogota)
- **Estado**: Aceptada (petición usuario: usar llama instalado + PaddleOCR)
- **Contexto**: default previo `qwen3:0.6b`/`qwen3:1.7b`. Instalado verificado
  `ollama list`: `llama3.2:1b` Q8_0 1.3 GB (tools), `glm-ocr:latest` 2.2 GB
  (vision+tools), `NaviDC-OCR-GGUF:F16` 2.8 GB. En este PC ya existe
  `rapidocr-onnxruntime 1.2.3` + Pillow (PaddleOCR vía ONNX, sin `paddlepaddle`).
- **Decisión**:
  1. Default local -> `llama3.2:1b` en `core/agent/ollama.py`, `core/settings.py`,
     `install.py --model`, `apps/gateway` (`JARVIS_OLLAMA_MODEL`), `ChatPanel.tsx`.
  2. OCR local con ecosistema PaddleOCR vía `rapidocr-onnxruntime` (PP-OCR ONNX,
     ~100 MB) + alterno clásico `paddleocr` si se instala. Nuevo módulo
     `core/agent/vision_ocr.py` (lazy, degradado `OCR_UNAVAILABLE`, captura
     QScreen/ImageGrab downscale 1600 px).
  3. Nuevas tools `read_image(path)` + `see_screen()` (riesgo `read`, tarjeta
     verde) + prompt `AGENT_SYS_V4` (11 tools, regla 11 imágenes).
  4. UI: Qt `Adjuntar` + `Pantalla` en `ui/chat_panel.py`; bridge `POST /api/ocr`
     (`path` o `filename+data_b64`, `screen:true`); HUD web botón clip con FileReader.
- **Alternativas descartadas**:
  - `paddlepaddle` clásico como único motor: ~1 GB, ruedas Windows/Python 3.14
    frágiles; se deja como alterno opcional, no requerido.
  - Visión LLM (`glm-ocr`, `NaviDC`, `qwen2.5vl:7b` ~5 GB): más RAM/GPU y
    alucinación UI; el usuario eligió OCR determinista. Se documenta como
    fallback futuro, no implementado en este cambio.
  - Tesseract/EasyOCR: ES débil (Tesseract) o torch pesado (EasyOCR) frente a
    PP-OCR español ya disponible vía ONNX.
- **Consecuencias**:
  - `llama3.2:1b` emite `tool_calls` nativo pero con args débiles (verificado en
    vivo: `arguments: {"type":"object"...}`); el fallback JSON §3.4.1/§3.4.3 +
    validación tolerante lo cubre. Esperar más reintentos que con qwen en CPU.
  - `settings.json` es gitignored: el default nuevo aplica a instalaciones
    frescas; en este PC actualizar el archivo local a mano o desde Ajustes.
  - `requirements.txt` añade `rapidocr-onnxruntime + Pillow` como opcional con
    degradado; `install.py --check-only` avisa sin bloquear.

> [!NOTE]
> `llama3.2:1b` declara `context 131072` pero se mantiene `num_ctx 4096`
> (techo CPU/RAM con 16 GB + Tauri + navegador). No subir sin medir swap.

> [!WARNING]
> PaddleOCR lee texto, no intenciones. El texto OCR entra como DATOS (regla 4)
> y jamás dispara tools encadenadas sin tarjeta de aprobación.
