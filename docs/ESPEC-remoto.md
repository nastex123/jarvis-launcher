# ESPEC Remoto v1 — Gateway movil + RustDesk propio

> [!NOTE] Contrato aprobado opcion 1: FastAPI + WS + JWT + QR. Reutiliza `core/` sin copiar.

## 1. Base

* Base URL LAN: `http://<pc-lan>:8000`. Solo LAN o Tailscale.
* Auth: `Authorization: Bearer <JWT 15min>`. Pairing inicial por QR LAN.
* Idempotencia: `POST /api/modes/run` exige `idempotency_key` 8-128 chars. Reintentos seguros `O(1)`.
* Errores: `401` auth, `403 DENIED_BY_POLICY`, `404` modo, `502` ollama offline.

## 2. Endpoints

| Metodo | Ruta | Auth | Body | Respuesta |
|--------|------|------|------|-----------|
| GET | `/health` | no | - | `{ok, app, modes}` |
| GET | `/api/pairing` | LAN | - | `{pairing_url, token, expires_in_s:300}` |
| POST | `/api/pairing/exchange` | token 1 uso | `{token}` | `{jwt, expires_in_s:900}` |
| GET | `/api/modes` | JWT | - | `{modes: [{id,name,color,description,apps}]}` |
| POST | `/api/modes/run` | JWT | `{mode_id, idempotency_key}` | `{mode_id,mode_name,launched[],failed[]}` |
| POST | `/api/chat/turn` | JWT | `{text,history[]}` | `{reply, proposals[]}` |
| POST | `/api/decide` | JWT | `{proposal_id,decision,new_args:{_tool,...}}` | `{status,result}` o `403 DENIED_BY_POLICY` |
| GET | `/api/rustdesk` | JWT | - | `{hbbs,hbbr,device_id}` |
| WS | `/ws/chat/stream` | JWT primer frame | `{jwt}` luego `{text}` | `{type:status|reply|error}` |

## 3. Politica remota

* Toda `run_shell` pasa por `check_shell` + tarjeta Aprobar/Rechazar/Editar en movil.
* Rechazo auto a los 60s. `DENIED_BY_POLICY` nunca es aprobable.
* `redact()` antes de devolver outputs al modelo. Log append-only `agent_log.jsonl`.
* Kill-switch movil cierra WS + sesion RustDesk.

> [!WARNING] Nunca exponer `8000` a internet directo. Usar Tailscale o reverse-proxy + TLS.

> [!IMPORTANT] Secreto `JARVIS_GATEWAY_SECRET` 32+ chars solo en `.env`, jamas en repo.
