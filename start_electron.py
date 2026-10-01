#!/usr/bin/env python3
"""
start_electron.py - Arranca el HUD Next.js en modo DESKTOP con Electron (sin navegador).

Solo stdlib. Sin Rust, sin MSVC, solo Node. Uso:
    python start_electron.py            ventana desktop en modo dev (live reload)
    python start_electron.py --build    genera el instalador .exe (NSIS) y lo lanza

Servicios que levanta/cierra solo:
    - Ollama serve (:11434, modelo CPU qwen3:1.7b) — solo si no estaba corriendo.
      Al cerrar la ventana, apaga el Ollama que el abrio (el pre-existente se respeta).
    - Next dev (:3000) + ventana Electron.
    - OpenCode es CLI por invocacion (sin demonio): solo verifica el binario.

Requiere: Node 18+, npm.
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
OLLAMA_URL = "http://localhost:11434/"
NEXT_URL = "http://localhost:3000"


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


def ollama_up(timeout_s: int = 5) -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_URL, timeout=timeout_s) as resp:
            return resp.status == 200
    except OSError:
        return False


def ensure_ollama() -> "subprocess.Popen | None":
    """Levanta `ollama serve` solo si no hay demonio. Retorna el proc propio o None."""
    if ollama_up():
        log_ok("Ollama ya estaba corriendo (se respeta, no se apagara al salir)")
        return None
    if shutil.which("ollama") is None:
        log_warn("Ollama no instalado: el chat quedara offline (https://ollama.com).")
        return None
    log_info("Levantando ollama serve en segundo plano ...")
    kwargs: dict = {}
    if sys.platform == "win32":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs = {"startupinfo": startup, "creationflags": subprocess.CREATE_NO_WINDOW}
    proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, **kwargs)
    for _ in range(60):
        if ollama_up(timeout_s=2):
            log_ok("Ollama en linea (se apagara al cerrar el programa)")
            return proc
        if proc.poll() is not None:
            log_fail("ollama serve murio al arrancar. Ejecuta `ollama serve` a mano.")
            return None
        time.sleep(1)
    log_fail("Ollama no respondio en 60 s. El chat quedara offline.")
    stop_proc(proc, "ollama")
    return None


def ensure_opencode() -> str:
    """Verifica el binario OpenCode (CLI por invocacion, sin demonio que levantar)."""
    home = os.path.expanduser("~")
    cands = [os.path.join(home, ".opencode", "bin", "opencode.exe"),
             os.path.join(home, ".opencode", "bin", "opencode")]
    for cand in cands:
        if os.path.exists(cand):
            log_ok(f"OpenCode local: {cand}")
            return cand
    found = shutil.which("opencode")
    if found:
        log_ok(f"OpenCode en PATH: {found}")
        return found
    log_warn("OpenCode no encontrado: el motor B pedira instalarlo "
             "(winget install SST.opencode o https://opencode.ai).")
    return ""


def stop_proc(proc: "subprocess.Popen | None", name: str) -> None:
    if proc is None or proc.poll() is not None:
        return
    log_info(f"Apagando {name} ...")
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_ok(f"{name} apagado")


def wait_http(url: str, timeout_s: int = 180) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except OSError:
            time.sleep(1)
    return False


def electron_env() -> dict:
    """Entorno para Electron: python del venv (puede con core/*) para launch-mode."""
    env = os.environ.copy()
    venv_py = (os.path.join(REPO, ".venv", "Scripts", "python.exe")
               if sys.platform == "win32"
               else os.path.join(REPO, ".venv", "bin", "python"))
    env["JARVIS_PYTHON"] = venv_py if os.path.exists(venv_py) else sys.executable
    return env


def do_dev() -> int:
    ollama_proc = ensure_ollama()
    ensure_opencode()
    log_info("Levantando Next dev en http://localhost:3000 ...")
    next_cmd = (["cmd", "/c", "npm", "run", "dev"] if sys.platform == "win32"
                else ["npm", "run", "dev"])
    next_proc = subprocess.Popen(next_cmd, cwd=WEB_DIR, env=electron_env())
    try:
        if not wait_http(NEXT_URL, timeout_s=180):
            log_fail("Next dev no respondio en 180 s. Revisa el log de arriba.")
            return 1
        log_info("Abriendo ventana DESKTOP Electron (sin navegador) ...")
        log_info("Al cerrar la ventana se apagan Next y el Ollama propio. Ctrl+C tambien cierra todo.")
        proc = run_node(["npx", "electron", "./electron/main.js", "--dev"],
                        cwd=WEB_DIR, env=electron_env())
        return proc.returncode
    except KeyboardInterrupt:
        log_info("Ctrl+C: cerrando todo ...")
        return 130
    finally:
        stop_proc(next_proc, "Next dev")
        stop_proc(ollama_proc, "Ollama (propio)")


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
