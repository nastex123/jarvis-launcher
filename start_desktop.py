#!/usr/bin/env python3
"""
start_desktop.py - Arranca el HUD Next.js en modo DESKTOP (ventana Tauri, sin navegador).

Solo stdlib. Uso:
    python start_desktop.py            ventana desktop en modo dev (live reload)
    python start_desktop.py --build    compila el .exe/.msi y lo lanza (sin dev server)

Requiere: Node 18+, npm, Rust/Cargo y src-web/ con @tauri-apps/cli.
Ollama (qwen3:1.7b) es opcional pero recomendado para el chat local.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(REPO, "src-web")
TAURI_DIR = os.path.join(WEB_DIR, "src-tauri")


def log_ok(msg: str) -> None:
    print(f"[OK] {msg}")


def log_info(msg: str) -> None:
    print(f"[..] {msg}")


def log_warn(msg: str) -> None:
    print(f"[!!] {msg}")


def log_fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def check_msvc() -> bool:
    """Detecta el linker MSVC que Rust necesita en Windows (VS Code no sirve)."""
    if sys.platform != "win32":
        return True
    if shutil.which("link.exe") is not None:
        log_ok("MSVC linker disponible")
        return True
    vswhere = os.path.join(
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        "Microsoft Visual Studio", "Installer", "vswhere.exe",
    )
    if os.path.exists(vswhere):
        proc = subprocess.run(
            [vswhere, "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools",
             "-property", "installationPath"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.stdout.strip():
            log_ok("Visual Studio C++ Build Tools detectadas")
            return True
    log_fail("Falta el compilador C++ de Visual Studio (Rust MSVC lo exige).")
    print("  Instala SOLO las Build Tools con C++ (~6 GB), una de estas dos:")
    print('  winget install -e --id Microsoft.VisualStudio.2022.BuildTools --override "--quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"')
    print("  o GUI: https://visualstudio.microsoft.com/downloads/ -> Build Tools -> "
          "marcar 'Desarrollo para escritorio con C++'.")
    print("  Nota: VS Code es otro producto y NO trae compilador. Reinicia la terminal tras instalar.")
    return False


def check_env() -> bool:
    ok = True
    # Rust recien instalado no esta en el PATH de terminales viejas: refrescar.
    cargo_bin = os.path.join(os.path.expanduser("~"), ".cargo", "bin")
    if os.path.isdir(cargo_bin) and cargo_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = cargo_bin + os.pathsep + os.environ.get("PATH", "")
    if not os.path.exists(os.path.join(WEB_DIR, "package.json")):
        log_fail("No existe src-web/package.json (usa la rama dev).")
        return False
    if not os.path.exists(os.path.join(TAURI_DIR, "tauri.conf.json")):
        log_fail("No existe src-web/src-tauri/tauri.conf.json.")
        return False
    for bin_name in ("node", "npm"):
        if shutil.which(bin_name) is None:
            log_fail(f"Falta {bin_name} (Node 18+ desde https://nodejs.org).")
            ok = False
        else:
            log_ok(f"{bin_name} disponible")
    if shutil.which("cargo") is None:
        log_fail("Falta Rust/Cargo (https://rustup.rs). Tauri no puede abrir ventana desktop sin el.")
        ok = False
    else:
        log_ok("cargo disponible")
    if shutil.which("ollama") is None:
        log_warn("Ollama no instalado: el chat quedara offline (https://ollama.com).")
    else:
        log_ok("ollama disponible")
    if not check_msvc():
        ok = False
    return ok


def run_node(cmd: list[str], **kwargs) -> "subprocess.CompletedProcess":
    """Ejecuta npm/npx en Windows (npm.cmd) y Unix sin romper subprocess."""
    if sys.platform == "win32":
        return subprocess.run(["cmd", "/c", *cmd], **kwargs)
    return subprocess.run(cmd, **kwargs)


def ensure_web_deps() -> bool:
    if os.path.exists(os.path.join(WEB_DIR, "node_modules")):
        log_ok("node_modules presente")
        return True
    log_info("Instalando dependencias web (npm install) ...")
    proc = run_node(["npm", "install"], cwd=WEB_DIR, timeout=600)
    if proc.returncode != 0:
        log_fail("npm install fallo. Revisa tu red o Node 18+.")
        return False
    log_ok("Dependencias web instaladas")
    return True


def do_dev() -> int:
    log_info("Abriendo HUD en ventana DESKTOP (Tauri dev, sin navegador) ...")
    log_info("Cierra con Ctrl+C en esta terminal.")
    # npx usa el @tauri-apps/cli local sin necesitar script 'tauri' en package.json.
    proc = run_node(["npx", "tauri", "dev"], cwd=WEB_DIR)
    return proc.returncode


def find_bundle() -> str:
    """Localiza el ejecutable/instalador generado por `tauri build`."""
    patterns = []
    if sys.platform == "win32":
        patterns = [
            os.path.join(TAURI_DIR, "target", "release", "bundle", "nsis", "*.exe"),
            os.path.join(TAURI_DIR, "target", "release", "bundle", "msi", "*.msi"),
            os.path.join(TAURI_DIR, "target", "release", "*.exe"),
        ]
    else:
        patterns = [
            os.path.join(TAURI_DIR, "target", "release", "bundle", "appimage", "*.AppImage"),
            os.path.join(TAURI_DIR, "target", "release", "bundle", "deb", "*.deb"),
            os.path.join(TAURI_DIR, "target", "release", "jarvis-launcher"),
        ]
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return ""


def do_build() -> int:
    log_info("Compilando desktop nativo (tauri build, genera .exe/.msi) ...")
    proc = run_node(["npx", "tauri", "build"], cwd=WEB_DIR)
    if proc.returncode != 0:
        log_fail("tauri build fallo. Revisa el log de Rust/Node de arriba.")
        return proc.returncode
    bundle = find_bundle()
    if not bundle:
        log_warn("Build OK pero no localice el bundle en target/release/bundle. Abrelo a mano.")
        return 0
    log_ok(f"Bundle generado: {bundle}")
    log_info("Lanzando el ejecutable desktop ...")
    if sys.platform == "win32" and bundle.endswith(".msi"):
        log_warn("Es un .msi instalador: ejecútalo para instalar y luego abre J.A.R.V.I.S.")
        return 0
    proc = subprocess.run([bundle] if not bundle.endswith(".AppImage") else [bundle])
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Arranca el HUD Next.js en modo DESKTOP (Tauri, sin navegador)."
    )
    parser.add_argument("--build", action="store_true",
                        help="compila el instalador nativo y lo lanza en vez del modo dev")
    args = parser.parse_args()
    if not check_env():
        return 2
    if not ensure_web_deps():
        return 2
    return do_build() if args.build else do_dev()


if __name__ == "__main__":
    sys.exit(main())
