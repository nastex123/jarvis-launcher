"""QA LAN gateway (solo localhost, sin lanzar apps reales)."""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
ENV = dict(os.environ, JARVIS_GATEWAY_SECRET="qa-secreto-32-caracteres-minimo-xxxx",
           JARVIS_OLLAMA_TIMEOUT="20", JARVIS_HBBS="127.0.0.1:21116",
           JARVIS_HBBR="127.0.0.1:21117", JARVIS_DEVICE_ID="jarvis-pc")


def call(method, path, body=None, jwt=""):
    req = urllib.request.Request(BASE + path, method=method,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": f"Bearer {jwt}"} if jwt else {})},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


results = []
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.gateway.main:app",
                         "--host", "127.0.0.1", "--port", "8000"], env=ENV,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(100):
        try:
            s, b = call("GET", "/health")
            if s == 200 and b.get("ok"):
                break
        except OSError:
            time.sleep(0.2)
    else:
        print("QA FAIL: gateway no arranco"); sys.exit(1)
    results.append(("health", s == 200 and len(b.get("modes", [])) == 3))

    s, _ = call("GET", "/api/modes")
    results.append(("modes-sin-auth-401", s == 401))

    s, p = call("GET", "/api/pairing")
    results.append(("pairing-token", s == 200 and len(p.get("token", "")) >= 32))

    s, e = call("POST", "/api/pairing/exchange", {"token": p["token"]})
    jwt = e.get("jwt", "")
    results.append(("exchange-jwt", s == 200 and len(jwt.split(".")) == 3))

    s, m = call("GET", "/api/modes", jwt=jwt)
    results.append(("modes-con-jwt", s == 200 and len(m.get("modes", [])) == 3))

    s, _ = call("POST", "/api/modes/run", {"mode_id": "no-existe", "idempotency_key": "qa-key-12345678"}, jwt)
    results.append(("run-modo-404-sin-lanzar", s == 404))

    s, r = call("GET", "/api/rustdesk", jwt=jwt)
    results.append(("rustdesk-handoff", s == 200 and "21116" in r.get("hbbs", "")))

    s, d = call("POST", "/api/decide", {"proposal_id": "qa1", "decision": "reject"}, jwt)
    results.append(("decide-reject", s == 200 and d.get("status") == "denied_by_user"))

    s, d = call("POST", "/api/decide",
                {"proposal_id": "qa2", "decision": "approve",
                 "new_args": {"_tool": "run_shell", "cmd": "rm -rf /"}}, jwt)
    results.append(("politica-bloquea-rm-rf", s == 403 and d.get("error_code") == "DENIED_BY_POLICY"))

    try:
        s, c = call("POST", "/api/chat/turn", {"text": "hola", "history": []}, jwt)
        results.append(("chat-turn", s in (200, 502)))
        print(f"chat-turn: HTTP {s} (200=ollama vivo, 502=offline aceptado)")
    except Exception as ex:
        results.append(("chat-turn", False))
        print(f"chat-turn error: {ex}")
finally:
    proc.terminate()

fails = [n for n, ok in results if not ok]
for n, ok in results:
    print(f"[{'OK' if ok else 'FAIL'}] {n}")
print("QA PASS 10/10" if not fails else f"QA FAIL: {fails}")
sys.exit(0 if not fails else 1)
