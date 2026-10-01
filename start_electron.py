#!/usr/bin/env python3
"""
start_electron.py - Arranca el HUD Next.js en modo DESKTOP con Electron (sin navegador).

Solo stdlib. Sin Rust, sin MSVC, solo Node. Uso:
    python start_electron.py            ventana desktop en modo dev (live reload)
    python start_electron.py --build    genera el instalador .exe (NSIS) y lo lanza

Requiere: Node 18+, npm. Ollama (qwen3:1.7b) opcional para el chat local.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(REPO, "src-web")


def log_ok(msg: str) -> None:
    print(f"[OK] {msg}")


def log_info(msg: str) -> None:
    print(f"[..] {msg}")


def log_warn(msg: str) -> None:
    print(f"[!!] {msg}")


def log_fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def run_node(cmd: list[str], **kwargs):
    """Ejecuta npm/npx en Windows (npm.cmd) y Unix sin romper subprocess."""
    if sys.platform == "win32":
        return subprocess.run(["cmd", "/c", *cmd], **kwargs)
    return subprocess.run(cmd, **kwargs)


def check_env() -> bool:
    ok = True
    if not os.path.exists(os.path.join(WEB_DIR, "electron", "main.js")):
        log_fail("No existe src-web/electron/main.js (usa la rama dev).")
        return False
    for bin_name in ("node", "npm"):
        if shutil.which(bin_name) is None:
            log_fail(f"Falta {bin_name} (Node 18+ desde https://nodejs.org).")
            ok = False
        else:
            log_ok(f"{bin_name} disponible")
    if shutil.which("ollama") is None:
        log_warn("Ollama no instalado: el chat quedara offline (https://ollama.com).")
    else:
        log_ok("ollama disponible")
    return ok


def ensure_web_deps() -> bool:
    need = ("electron", "electron-builder")
    missing = [p for p in need if not os.path.exists(os.path.join(WEB_DIR, "node_modules", p))]
    if not os.path.exists(os.path.join(WEB_DIR, "node_modules")) or missing:
        log_info("Instalando dependencias web+desktop (npm install, ~200 MB) ...")
        proc = run_node(["npm", "install"], cwd=WEB_DIR, timeout=900)
        if proc.returncode != 0:
            log_fail("npm install fallo. Revisa tu red o Node 18+.")
            return False
    log_ok("node_modules presente (incl. electron)")
    return True


def wait_http(url: str, timeout_s: int = 120) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except OSError:
            time.sleep(1)
    return False


def do_dev() -> int:
    log_info("Levantando Next dev en http://localhost:3000 ...")
    next_proc = subprocess.Popen(
        ["cmd", "/c", "npm", "run", "dev"] if sys.platform == "win32" else ["npm", "run", "dev"],
        cwd=WEB_DIR,
    )
    try:
        if not wait_http("http://localhost:3000", timeout_s=180):
            log_fail("Next dev no respondio en 180 s. Revisa el log de arriba.")
            return 1
        log_info("Abriendo ventana DESKTOP Electron (sin navegador) ...")
        log_info("Cierra con Ctrl+C en esta terminal.")
        proc = run_node(["npx", "electron", "./electron/main.js", "--dev"], cwd=WEB_DIR)
        return proc.returncode
    finally:
        next_proc.terminate()


def do_build() -> int:
    log_info("Generando instalador .exe (next build + electron-builder NSIS) ...")
    proc = run_node(["npm", "run", "dist"], cwd=WEB_DIR, timeout=1800)
    if proc.returncode != 0:
        log_fail("electron-builder fallo. Revisa el log de arriba.")
        return proc.returncode
    hits = sorted(glob.glob(os.path.join(WEB_DIR, "dist", "*.exe")))
    # El NSIS web installer pesa menos; preferirlo si existe.
    exe = next((h for h in hits if "Setup" in os.path.basename(h)), hits[0] if hits else "")
    if not exe:
        log_warn("Build OK pero no localice .exe en src-web/dist. Abrelo a mano.")
        return 0
    log_ok(f"Instalador generado: {exe}")
    log_info("Lanzando el instalador desktop ...")
    proc = subprocess.run([exe])
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Arranca el HUD Next.js en modo DESKTOP con Electron (sin navegador)."
    )
    parser.add_argument("--build", action="store_true",
                        help="genera el instalador .exe y lo lanza en vez del modo dev")
    args = parser.parse_args()
    if not check_env():
        return 2
    if not ensure_web_deps():
        return 2
    return do_build() if args.build else do_dev()


if __name__ == "__main__":
    sys.exit(main())
