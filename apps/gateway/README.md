# Jarvis Gateway (MVP Fase 2)

Backend FastAPI que expone el core local al telefono en LAN.

## Endpoints

* `GET /health` publico
* `GET /api/pairing` publico LAN, retorna QR JSON de un solo uso
* `POST /api/pairing/exchange` canjea token por JWT 15 min
* `GET /api/modes`, `POST /api/modes/run` con `Idempotency-Key` via `idempotency_key`
* `POST /api/chat/turn` 1 turno Ollama + tarjetas sin ejecutar
* `POST /api/decide` ejecuta tras `approve/edit`, respeta `DENIED_BY_POLICY`
* `GET /api/rustdesk` handoff hbbs/hbbr propio
* `WS /ws/chat/stream` primer mensaje `{"jwt": "..."}`

## Arranque

```bash
pip install -r apps/gateway/requirements.txt
set JARVIS_GATEWAY_SECRET=64-hex-aleatorios
uvicorn apps.gateway.main:app --host 0.0.0.0 --port 8000
```

> [!WARNING] Solo LAN o Tailscale. Nunca exponer 8000 a internet sin reverse-proxy + TLS.
