"""Jarvis Gateway FastAPI — opcion 1 aprobada (REST + WS + JWT + QR).

Reutiliza sin copiar: core.config, core.launcher, core.agent.policy,
core.agent.ollama y core.agent.tools (ninguno exige Qt salvo loop.py,
que aqui NO se importa; el loop remoto es propio y ligero).
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from apps.gateway import auth
from apps.gateway.models import ChatRequest, DecisionRequest, RunModeRequest

from core.agent.ollama import AgentTransportError, OllamaClient
from core.agent.policy import check_shell, redact
from core.agent.tools import execute_tool, ollama_tools
from core.config import ConfigManager
from core.launcher import AppLauncher

app = FastAPI(title="Jarvis Gateway", version="0.1.0")

config = ConfigManager()
launcher = AppLauncher()
_idempotency: dict[str, dict] = {}
_pairing: dict[str, float] = {}


def _ollama() -> OllamaClient:
    return OllamaClient(
        base_url=os.environ.get("JARVIS_OLLAMA_URL", "http://localhost:11434"),
        model=os.environ.get("JARVIS_OLLAMA_MODEL", "qwen3:0.6b"),
        timeout_s=int(os.environ.get("JARVIS_OLLAMA_TIMEOUT", "180")),
        think=False,
    )


def require_auth(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="falta Bearer JWT")
    try:
        return auth.verify_jwt(authorization[7:])
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/health")
def health() -> dict:
    return {"ok": True, "app": config.app_name, "modes": config.get_mode_ids()}


@app.get("/api/pairing")
def pairing() -> dict:
    # Solo LAN: el PC muestra este JSON como QR, el movil lo escanea.
    token, exp = auth.new_pairing_token()
    _pairing[token] = time.time() + exp
    base = os.environ.get("JARVIS_GATEWAY_PUBLIC", "http://pc-lan:8000")
    return {"pairing_url": f"{base}/api/pairing/exchange?t={token}", "token": token, "expires_in_s": exp}


@app.post("/api/pairing/exchange")
def exchange(body: dict) -> dict:
    token = str(body.get("token", ""))
    exp = _pairing.pop(token, 0)
    if not token or exp < time.time():
        raise HTTPException(status_code=401, detail="pairing invalido o expirado")
    return {"jwt": auth.issue_jwt(), "expires_in_s": auth.JWT_EXP_S}


@app.get("/api/modes")
def modes(_: dict = Depends(require_auth)) -> dict:
    out = []
    for mid in config.get_mode_ids():
        mode = config.get_mode(mid) or {}
        out.append({"id": mid, "name": mode.get("name", mid), "color": mode.get("color", "#00FFFF"),
                    "description": mode.get("description", ""), "apps": mode.get("apps", [])})
    return {"modes": out}


@app.post("/api/modes/run")
def run_mode(body: RunModeRequest, _: dict = Depends(require_auth)) -> dict:
    if body.idempotency_key in _idempotency:
        return _idempotency[body.idempotency_key]
    mode = config.get_mode(body.mode_id)
    if mode is None:
        raise HTTPException(status_code=404, detail="modo no encontrado")
    result = launcher.launch_mode(mode.get("apps", []))
    resp = {"mode_id": body.mode_id, "mode_name": mode.get("name", body.mode_id),
            "launched": result["launched"], "failed": result["failed"]}
    _idempotency[body.idempotency_key] = resp
    return resp


@app.post("/api/chat/turn")
def chat_turn(body: ChatRequest, _: dict = Depends(require_auth)) -> dict:
    # Turno ligero sin Qt: 1 llamada Ollama + tarjetas de propuesta sin ejecutar.
    client = _ollama()
    history = list(body.history) + [{"role": "user", "content": body.text}]
    try:
        msg = client.chat(history, ollama_tools())
    except AgentTransportError as exc:
        raise HTTPException(status_code=502, detail=f"ollama offline: {exc}")
    cards = []
    for call in msg.get("tool_calls") or []:
        fn = call.get("function") or {}
        cards.append({"id": call.get("id", ""), "tool": fn.get("name", ""),
                      "args": fn.get("arguments") or {}, "summary": f"Ejecutar {fn.get('name','')}",
                      "risk": "shell" if (fn.get("name") == "run_shell") else "read"})
    return {"reply": redact(msg.get("content", "")), "proposals": cards}


@app.post("/api/decide")
def decide(body: DecisionRequest, _: dict = Depends(require_auth)) -> dict:
    if body.decision == "reject":
        return {"status": "denied_by_user", "proposal_id": body.proposal_id}
    args = body.new_args or {}
    if not args:
        raise HTTPException(status_code=400, detail="new_args requerido para approve/edit")
    tool = str(args.pop("_tool", ""))
    if not tool:
        raise HTTPException(status_code=400, detail="new_args._tool requerido")
    if tool == "run_shell":
        ok, motivo = check_shell(str(args.get("cmd", "")))
        if not ok:
            return JSONResponse(status_code=403, content={"status": "error", "error_code": "DENIED_BY_POLICY",
                                                          "error_detail": motivo})
    ctx = {"repo_root": os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}
    result = execute_tool(tool, args, ctx)
    return {"status": result.get("status"), "proposal_id": body.proposal_id, "result": result}


@app.get("/api/rustdesk")
def rustdesk(_: dict = Depends(require_auth)) -> dict:
    # Handoff al RustDesk Server propio (Fase 4 lo levanta con compose).
    return {"hbbs": os.environ.get("JARVIS_HBBS", "pc-lan:21116"),
            "hbbr": os.environ.get("JARVIS_HBBR", "pc-lan:21117"),
            "device_id": os.environ.get("JARVIS_DEVICE_ID", "jarvis-pc")}


@app.websocket("/ws/chat/stream")
async def ws_chat(ws: WebSocket) -> None:
    # MVP: autentica por primer mensaje {"jwt": "..."} y luego stremea turnos.
    await ws.accept()
    try:
        hello = await ws.receive_json()
        auth.verify_jwt(str(hello.get("jwt", "")))
    except Exception:
        await ws.close(code=4401)
        return
    client = _ollama()
    history: list[dict] = []
    try:
        while True:
            data = await ws.receive_json()
            text = str(data.get("text", ""))[:4000]
            if not text:
                continue
            history.append({"role": "user", "content": text})
            await ws.send_json({"type": "status", "status": "pensando"})
            try:
                msg = client.chat(history, ollama_tools())
            except AgentTransportError as exc:
                await ws.send_json({"type": "error", "error": f"ollama offline: {exc}"})
                continue
            history.append(msg)
            await ws.send_json({"type": "reply", "reply": redact(msg.get("content", "")),
                                "proposals": msg.get("tool_calls") or []})
    except WebSocketDisconnect:
        return
