#!/usr/bin/env python3
"""
scripts/bridge_server.py - Servidor puente HTTP local para desarrollo web.
Permite ejecutar comandos de sistema, lanzar apps de modo y consultar OpenCode desde la web.
Escucha en http://127.0.0.1:3002 con CORS habilitado.
"""

import http.server
import json
import os
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

PORT = 3002
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path == "/api/shell":
            cmd = payload.get("cmd", "")
            if not cmd:
                self._send_json({"error": "Comando vacío"}, 400)
                return

            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                self._send_json({
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "ok": proc.returncode == 0
                })
            except Exception as e:
                self._send_json({"error": str(e), "ok": False}, 500)

        elif parsed.path == "/api/opencode":
            prompt = payload.get("prompt", "")
            opencode_bin = os.path.expanduser("~/.opencode/bin/opencode")
            if not os.path.exists(opencode_bin):
                opencode_bin = "opencode"

            try:
                # Ejecutar opencode en modo no interactivo
                proc = subprocess.run(
                    [opencode_bin, "run", prompt],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
                self._send_json({
                    "output": output,
                    "exit_code": proc.returncode,
                    "ok": proc.returncode == 0
                })
            except Exception as e:
                self._send_json({"error": f"Fallo ejecutando OpenCode: {e}", "ok": False}, 500)

        elif parsed.path == "/api/mode":
            mode_id = payload.get("mode", "")
            # Mapear modo (español -> id interno si aplica)
            mode_map = {"gaming": "gaming", "trabajo": "work", "work": "work", "estudio": "study", "study": "study"}
            target_key = mode_map.get(mode_id.lower(), mode_id.lower())

            try:
                sys.path.insert(0, REPO_ROOT)
                from core.config import ConfigManager
                from core.launcher import AppLauncher
                cfg = ConfigManager()
                apps = cfg.get_mode_apps(target_key)
                launcher = AppLauncher()
                res = launcher.launch_mode(apps)
                self._send_json({"ok": True, "message": f"Modo {mode_id} procesado", "result": res})
            except Exception as e:
                self._send_json({"error": str(e), "ok": False}, 500)

        else:
            self._send_json({"error": "Ruta no encontrada"}, 404)

    def _send_json(self, data, code=200):
        self.send_response(code)
        self._set_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def run():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), BridgeHandler)
    print(f"[JARVIS Bridge Server] Activo en http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    run()
