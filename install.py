#!/usr/bin/env python3
"""
install.py - Instalador e inicializador de J.A.R.V.I.S. Launcher (Windows + Linux).

Todo-en-uno, solo stdlib. Idempotente: se puede re-ejecutar sin romper nada.

Uso:
    python install.py                  instala deps (venv + requirements + modelo CPU)
    python install.py --run            instala (si falta) y lanza el launcher clasico
    python install.py --run-web        instala (si falta) y lanza HUD web (bridge + Next dev)
    python install.py --check-only     solo diagnostico del entorno, no instala
    python install.py --uninstall      revierte bin/.desktop/autostart (Linux)

Opciones:
    --no-autostart   no crea autostart (solo Linux)
    --no-shortcut    no crea acceso del menu (solo Linux)
    --venv PATH      ruta del venv (defecto: <repo>/.venv)
    --yes            no pedir confirmacion en --purge
    --run            lanzar el launcher clasico al terminar (usa el python del venv)
    --run-web        lanzar el HUD web al terminar (bridge :3002 + npm run dev)
    --pull-model     descarga el modelo Ollama CPU con `ollama pull`
    --with-rust      instala Rust/Cargo con rustup si falta (desktop Tauri)
    --model NAME     modelo Ollama (defecto: qwen3:0.6b, perfil CPU GT710)
    --check-only     solo diagnostico

Lo que hace, por etapas:
    1. check_env: Python>=3.10, pip, venv (+ Ollama)
    2. ensure_venv + pip install -r requirements.txt (Windows: .venv\\Scripts)
    3. check_ollama: verifica demonio + modelo CPU (con --pull-model lo descarga)
    4. smoke_test: compileall + valida config.json
    5. do_run / do_run_web: arranca el programa
"""

from __future__ import annotations

import argparse
import compileall
import json
import os
import shutil
import stat
import subprocess
import sys

MIN_PYTHON = (3, 10)
REPO = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(REPO, "assets", "jarvis-launcher.desktop.template")
REQUIREMENTS = os.path.join(REPO, "requirements.txt")
EXAMPLE_CONFIG = os.path.join(REPO, "config.linux.example.json")
LINUX_CONFIG = os.path.join(REPO, "config.linux.json")

HOME = os.path.expanduser("~")
BIN_PATH = os.path.join(HOME, ".local", "bin", "jarvis")
DESKTOP_PATH = os.path.join(HOME, ".local", "share", "applications", "jarvis-launcher.desktop")
AUTOSTART_PATH = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")),
    "autostart",
    "jarvis-launcher.desktop",
)

# Paquetes sistema tipicos para PyQt6 + WebEngine por familia de distro.
SYS_DEPS = {
    "apt": "sudo apt install -y python3-venv python3-pip libgl1 libxkbcommon-x11-0 "
           "libxcb-cursor0 libnss3 libasound2t64 libnotify-bin",
    "dnf": "sudo dnf install -y python3-devel libglvnd-glx libxkbcommon-x11 "
           "nss alsa-lib libnotify",
    "pacman": "sudo pacman -S --needed python-virtualenv libgl libxkbcommon-x11 "
              "nss alsa-lib libnotify",
    "zypper": "sudo zypper install -y python3-venv libgl1 libxkbcommon-x11-0 "
              "mozilla-nss alsa-lib libnotify-tools",
}


def log_ok(msg: str) -> None:
    print(f"[OK] {msg}")


def log_info(msg: str) -> None:
    print(f"[..] {msg}")


def log_warn(msg: str) -> None:
    print(f"[!!] {msg}")


def log_fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


# ----------------------------------------------------------------------
# Diagnostico
# ----------------------------------------------------------------------

def detect_pkg_manager() -> str:
    distro = ""
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("ID="):
                    distro = line.strip().split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    if distro in ("ubuntu", "debian", "linuxmint", "pop", "elementary", "zorin"):
        return "apt"
    if distro in ("fedora", "rhel", "centos", "rocky", "almalinux"):
        return "dnf"
    if distro in ("arch", "manjaro", "endeavouros", "cachyos"):
        return "pacman"
    if distro in ("opensuse-tumbleweed", "opensuse-leap", "sles"):
        return "zypper"
    for mgr in ("apt", "dnf", "pacman", "zypper"):
        if shutil.which(mgr):
            return mgr
    return ""


def check_env() -> bool:
    ok = True
    log_info(f"Repo: {REPO}")
    log_info(f"Python: {sys.version.split()[0]}")
    if sys.version_info < MIN_PYTHON:
        log_fail(f"Se requiere Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}")
        ok = False
    else:
        log_ok("Version de Python compatible")
    for mod, pkg in (("venv", "python3-venv"), ("pip", "python3-pip")):
        try:
            __import__(mod)
            log_ok(f"Modulo stdlib '{mod}' disponible")
        except ImportError:
            log_fail(f"Falta '{mod}' (paquete {pkg})")
            ok = False
    mgr = detect_pkg_manager()
    session = os.environ.get("XDG_SESSION_TYPE", "?")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "?")
    log_info(f"Distro/gestor: {mgr or 'desconocido'} | sesion: {session} | escritorio: {desktop}")
    if session.lower() == "wayland":
        log_info("Wayland detectado: el atajo Ctrl+Shift+Espacio sera interno "
                 "(con foco). Para global: Ajustes > Teclado > comando 'jarvis'.")
    if sys.platform != "win32" and shutil.which("notify-send") is None:
        log_warn("Falta 'notify-send' (libnotify): las notificaciones usaran la bandeja. "
                 f"Instala con tu gestor ({mgr or 'apt/dnf/pacman'}).")
    else:
        log_ok("notify-send disponible")
    tray_hint = shutil.which("gnome-shell") is not None or "gnome" in desktop.lower()
    if tray_hint:
        log_info("GNOME: la bandeja puede estar oculta sin la extension AppIndicator "
                 "(el launcher sigue funcional).")
    return ok


def check_system_libs(venv_py: str) -> bool:
    """Intenta importar PyQt6 con el venv; si falla por .so, sugiere paquetes."""
    if not os.path.exists(venv_py):
        log_warn("Venv aun no creado: se omitira el chequeo de libs Qt hasta instalar deps.")
        return True
    proc = subprocess.run(
        [venv_py, "-c", "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode == 0:
        log_ok(f"PyQt6 importable (Qt {proc.stdout.strip()})")
        return True
    err = (proc.stderr or "")[-1500:]
    log_fail("PyQt6 no se pudo importar con el venv.")
    if err.strip():
        print("----- stderr (recorte) -----")
        print(err.strip())
        print("----------------------------")
    mgr = detect_pkg_manager()
    hint = SYS_DEPS.get(mgr, SYS_DEPS["apt"])
    log_warn(f"Posibles libs del sistema faltantes. Prueba:\n  {hint}")
    return False


# ----------------------------------------------------------------------
# Instalacion
# ----------------------------------------------------------------------

def venv_python(venv_dir: str) -> str:
    """Ruta del python del venv segun SO."""
    if sys.platform == "win32":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def ensure_venv(venv_dir: str) -> str:
    venv_py = venv_python(venv_dir)
    if os.path.exists(venv_py):
        log_ok(f"Venv existente: {venv_dir}")
        return venv_py
    log_info(f"Creando venv en {venv_dir} ...")
    proc = subprocess.run([sys.executable, "-m", "venv", venv_dir])
    if proc.returncode != 0 or not os.path.exists(venv_py):
        log_fail("No se pudo crear el venv (en Windows: reinstala Python con 'Add to PATH' + pip).")
        sys.exit(2)
    log_ok("Venv creado")
    return venv_py


def pip_install(venv_py: str) -> None:
    if not os.path.exists(REQUIREMENTS):
        log_warn("Sin requirements.txt: se omite pip install.")
        return
    log_info("Instalando dependencias (pip install -r requirements.txt) ...")
    proc = subprocess.run(
        [venv_py, "-m", "pip", "install", "--upgrade", "pip"],
        timeout=300,
    )
    if proc.returncode != 0:
        log_warn("pip upgrade fallo; se continua con el pip existente.")
    proc = subprocess.run(
        [venv_py, "-m", "pip", "install", "-r", REQUIREMENTS],
        timeout=900,
    )
    if proc.returncode != 0:
        log_fail("pip install fallo. Revisa tu red o el requirements.txt.")
        sys.exit(2)
    log_ok("Dependencias instaladas")


def ensure_linux_config() -> None:
    if os.path.exists(LINUX_CONFIG):
        log_ok("config.linux.json ya existe (no se toca)")
        return
    if not os.path.exists(EXAMPLE_CONFIG):
        log_warn("No hay config.linux.example.json: se omite config Linux.")
        return
    shutil.copy(EXAMPLE_CONFIG, LINUX_CONFIG)
    log_ok("config.linux.json creado desde el ejemplo (personalizalo a gusto)")
    # Avisar de binarios no encontrados en PATH (informativo, no bloquea)
    try:
        with open(LINUX_CONFIG, encoding="utf-8") as fh:
            cfg = json.load(fh)
        missing: list[str] = []
        for mode in cfg.get("modes", {}).values():
            for app in mode.get("apps", []):
                cmd = (app.get("command") or "").strip()
                if not cmd or cmd.startswith("http"):
                    continue
                if os.path.exists(cmd) or shutil.which(cmd.split()[0]):
                    continue
                missing.append(f"{app.get('name', '?')} ({cmd})")
        if missing:
            log_warn("Estos comandos no estan en tu PATH (el launcher los "
                     "resolvera via .desktop o fallara con aviso): "
                     + ", ".join(sorted(set(missing))))
    except (OSError, json.JSONDecodeError):
        pass


def render_desktop(venv_py: str) -> str:
    if os.path.exists(TEMPLATE):
        with open(TEMPLATE, encoding="utf-8") as fh:
            content = fh.read()
        content = content.replace("@@VENV_PY@@", venv_py).replace("@@REPO@@", REPO)
    else:
        content = (
            "[Desktop Entry]\nType=Application\nName=J.A.R.V.I.S. Launcher\n"
            f"Exec={venv_py} {REPO}/main.py\nPath={REPO}\nTerminal=false\n"
            "Categories=Utility;\nStartupNotify=true\n"
        )
    return content


def install_bin(venv_py: str) -> None:
    os.makedirs(os.path.dirname(BIN_PATH), exist_ok=True)
    wrapper = (
        "#!/usr/bin/env bash\n"
        "# Generado por install.py - comando global `jarvis`.\n"
        f'VENV_PY="{venv_py}"\n'
        f'REPO="{REPO}"\n'
        'if [ ! -x "$VENV_PY" ]; then\n'
        '  echo "[jarvis] venv no encontrado en $VENV_PY. Ejecuta: python3 install.py" >&2\n'
        "  exit 1\n"
        "fi\n"
        'cd "$REPO" || exit 1\n'
        'exec "$VENV_PY" "$REPO/main.py" "$@"\n'
    )
    with open(BIN_PATH, "w", encoding="utf-8") as fh:
        fh.write(wrapper)
    os.chmod(BIN_PATH, os.stat(BIN_PATH).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    log_ok(f"Comando instalado: {BIN_PATH}")
    local_bin = os.path.join(HOME, ".local", "bin")
    if local_bin not in os.environ.get("PATH", ""):
        log_warn(f"{local_bin} no esta en tu PATH. Agrega:\n"
                 f"  export PATH=\"$HOME/.local/bin:$PATH\"  (en ~/.bashrc)")


def install_desktop_file(venv_py: str, dest: str, autostart: bool = False) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    content = render_desktop(venv_py)
    if autostart and "X-GNOME-Autostart-enabled" not in content:
        content += "X-GNOME-Autostart-enabled=true\n"
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(content)
    log_ok(f"{'Autostart' if autostart else 'Acceso'} creado: {dest}")
    if shutil.which("update-desktop-database"):
        subprocess.run(
            ["update-desktop-database", os.path.dirname(dest)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def check_ollama(model: str = "qwen3:0.6b", pull: bool = False) -> None:
    """Verifica Ollama para el asistente (aviso, no bloquea la instalación)."""
    import json as _json
    import urllib.request as _url

    if shutil.which("ollama") is None:
        log_warn("Ollama no instalado: el asistente IA quedará offline. "
                 "Instálalo desde https://ollama.com y ejecuta: ollama pull " + model)
        return
    log_ok("Binario ollama disponible")
    try:
        with _url.urlopen("http://localhost:11434/", timeout=5) as resp:
            if resp.status != 200:
                raise OSError(f"HTTP {resp.status}")
    except OSError:
        log_warn("El demonio Ollama no responde. Arráncalo con: ollama serve")
        return
    log_ok("Demonio Ollama en línea")
    try:
        with _url.urlopen("http://localhost:11434/api/tags", timeout=10) as resp:
            models = [m.get("name", "") for m in _json.loads(resp.read().decode()).get("models", [])]
    except OSError:
        log_warn("No se pudo listar modelos de Ollama.")
        return
    if any(m.split(":")[0] == model.split(":")[0] for m in models):
        log_ok(f"Modelo {model} descargado")
    elif pull:
        log_info(f"Descargando modelo CPU {model} (ollama pull, ~1.4 GB) ...")
        proc = subprocess.run(["ollama", "pull", model], timeout=900)
        if proc.returncode == 0:
            log_ok(f"Modelo {model} descargado")
        else:
            log_fail(f"No se pudo descargar {model}. Ejecuta manual: ollama pull {model}")
    else:
        log_warn(f"Modelo {model} ausente. Descárgalo con: ollama pull {model} "
                 f"(o re-ejecuta con --pull-model)")


def check_msvc(install: bool = False) -> bool:
    """Detecta el linker MSVC que Rust exige en Windows (VS Code no sirve)."""
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
    if install and shutil.which("winget") is not None:
        log_info("Instalando VS 2022 Build Tools con C++ (~6 GB, tarda 15-30 min) ...")
        proc = subprocess.run(
            ["winget", "install", "-e", "--id", "Microsoft.VisualStudio.2022.BuildTools",
             "--override", "--quiet --wait --norestart --nocache "
                           "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended",
             "--accept-source-agreements", "--accept-package-agreements"],
            timeout=3600,
        )
        if proc.returncode == 0:
            log_ok("VS Build Tools instaladas (reinicia la terminal)")
            return True
        log_fail("winget falló con Build Tools. Instálalas a mano: "
                 "https://visualstudio.microsoft.com/downloads/ -> Build Tools -> "
                 "'Desarrollo para escritorio con C++'. (VS Code NO trae compilador.)")
        return False
    log_warn("Falta el compilador C++ de Visual Studio (Rust MSVC lo exige para Tauri). "
             "Re-ejecuta con --with-rust para instalarlo, o a mano desde "
             "https://visualstudio.microsoft.com/downloads/ (VS Code NO sirve).")
    return False


def check_rust(install: bool = False) -> bool:
    """Detecta Rust/Cargo para el desktop Tauri; con install=True lo instala."""
    if shutil.which("cargo") is not None and shutil.which("rustc") is not None:
        try:
            proc = subprocess.run(["cargo", "--version"], capture_output=True, text=True, timeout=30)
            log_ok(f"Rust disponible ({(proc.stdout or '').strip() or 'cargo'})")
        except OSError:
            log_ok("Rust disponible (cargo en PATH)")
        check_msvc(install=install)
        return True
    if not install:
        log_warn("Falta Rust/Cargo: el desktop Tauri no puede compilar. "
                 "Re-ejecuta con --with-rust para instalarlo solo (rustup).")
        return False
    log_info("Instalando Rust (rustup, ~300 MB) ...")
    if sys.platform == "win32":
        if install_rust_windows() and refresh_cargo_path():
            check_msvc(install=True)
            return True
        return False
    if install_rust_unix():
        check_msvc(install=True)
        return True
    return False


def install_rust_windows() -> bool:
    """Instala rustup en Windows via winget, con fallback a rustup-init.exe."""
    if shutil.which("winget") is not None:
        log_info("Instalando con winget (Rustlang.Rustup) ...")
        proc = subprocess.run(
            ["winget", "install", "-e", "--id", "Rustlang.Rustup",
             "--accept-source-agreements", "--accept-package-agreements"],
            timeout=900,
        )
        if proc.returncode == 0:
            log_ok("rustup instalado via winget")
            return True
        log_warn("winget falló; se intenta con rustup-init.exe directo.")
    import tempfile
    import urllib.request as _url
    url = "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe"
    tmp = os.path.join(tempfile.gettempdir(), "rustup-init.exe")
    try:
        log_info(f"Descargando rustup-init.exe ({url}) ...")
        _url.urlretrieve(url, tmp)
    except OSError as exc:
        log_fail(f"No se pudo descargar rustup: {exc}")
        return False
    proc = subprocess.run([tmp, "-y", "--no-modify-path"], timeout=900)
    if proc.returncode != 0:
        log_fail("rustup-init.exe falló. Instálalo manual desde https://rustup.rs")
        return False
    log_ok("rustup instalado (perfil minimal, sin modificar PATH del sistema)")
    return True


def install_rust_unix() -> bool:
    """Instala rustup en Linux/macOS via el script oficial."""
    if shutil.which("curl") is None:
        log_fail("Falta curl para instalar rustup. Instala curl y re-ejecuta con --with-rust.")
        return False
    proc = subprocess.run(
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal",
        shell=True, timeout=900,
    )
    if proc.returncode != 0:
        log_fail("El instalador de rustup falló. Ver https://rustup.rs")
        return False
    log_ok("rustup instalado (perfil minimal)")
    return refresh_cargo_path()


def refresh_cargo_path() -> bool:
    """Agrega ~/.cargo/bin al PATH del proceso y verifica cargo."""
    cargo_bin = os.path.join(HOME, ".cargo", "bin")
    if os.path.isdir(cargo_bin) and cargo_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = cargo_bin + os.pathsep + os.environ.get("PATH", "")
    if shutil.which("cargo") is None:
        log_warn("Rust instalado pero cargo aún no está en el PATH de esta terminal. "
                 "Cierra y abre una terminal nueva (o usa start_desktop.py desde una nueva).")
        return False
    log_ok("Cargo verificado en PATH")
    return True


def smoke_test(venv_py: str) -> bool:
    ok = True
    log_info("Smoke test: compileall ...")
    if not compileall.compile_dir(REPO, quiet=1):
        log_fail("compileall encontro errores de sintaxis.")
        ok = False
    else:
        log_ok("compileall sin errores")
    for cfg_path in (LINUX_CONFIG, os.path.join(REPO, "config.json")):
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as fh:
                    json.load(fh)
                log_ok(f"JSON valido: {os.path.basename(cfg_path)}")
            except json.JSONDecodeError as exc:
                log_fail(f"JSON invalido en {cfg_path}: {exc}")
                ok = False
    proc = subprocess.run(
        [venv_py, "-c",
         "import core.platform, core.launcher, core.notifier, core.version;"
         "print(core.version.get_app_version())"],
        cwd=REPO, capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        log_fail("Import del core fallo con el venv.")
        print((proc.stderr or "")[-1000:])
        ok = False
    else:
        log_ok(f"Core importable (version {proc.stdout.strip()})")
    return ok


def do_install(args) -> int:
    if not check_env():
        log_fail("Corrige el entorno y re-ejecuta.")
        return 2
    venv_py = ensure_venv(args.venv)
    pip_install(venv_py)
    if sys.platform != "win32":
        check_system_libs(venv_py)  # informativo, no bloquea
        ensure_linux_config()
    check_ollama(model=args.model, pull=args.pull_model)
    check_rust(install=args.with_rust)
    if sys.platform != "win32":
        install_bin(venv_py)
        if not args.no_shortcut:
            install_desktop_file(venv_py, DESKTOP_PATH)
        else:
            log_info("--no-shortcut: se omite el .desktop del menu.")
        if not args.no_autostart:
            install_desktop_file(venv_py, AUTOSTART_PATH, autostart=True)
        else:
            log_info("--no-autostart: se omite el autostart.")
    else:
        log_info("Windows: se omite bin/.desktop/autostart Linux "
                 "(usa install_jarvis_cmd.bat / install_startup.bat si los quieres).")
    ok = smoke_test(venv_py)
    print()
    if ok:
        if sys.platform == "win32":
            log_ok("Instalacion completa. Lanza con:  python install.py --run  (clasico) "
                   "o  python install.py --run-web  (HUD web)")
        else:
            log_ok("Instalacion completa. Abre una terminal nueva y ejecuta:  jarvis")
        log_info("Agente CPU: qwen3:0.6b (num_ctx 4096, timeout 180s, steps 5). "
                 "Forzar CPU con GT710:  set CUDA_VISIBLE_DEVICES=  + ollama serve")
    else:
        log_warn("Instalacion con advertencias: revisa los [FAIL] de arriba.")
    if args.run_web:
        return do_run_web(args)
    if args.run:
        return do_run(args)
    return 0 if ok else 1


def do_run(args) -> int:
    venv_py = venv_python(args.venv)
    if not os.path.exists(venv_py):
        log_fail(f"No hay venv en {args.venv}. Ejecuta primero: python install.py")
        return 2
    log_info("Iniciando J.A.R.V.I.S. Launcher (clasico PyQt6) ...")
    if sys.platform == "win32":
        proc = subprocess.run([venv_py, os.path.join(REPO, "main.py")])
        return proc.returncode
    os.execv(venv_py, [venv_py, os.path.join(REPO, "main.py")])


def run_node(cmd: list[str], **kwargs):
    """Ejecuta npm/npx en Windows (npm.cmd) y Unix sin romper subprocess."""
    import subprocess as _sp
    if sys.platform == "win32":
        return _sp.run(["cmd", "/c", *cmd], **kwargs)
    return _sp.run(cmd, **kwargs)


def do_run_web(args) -> int:
    """Arranca el HUD web: bridge :3002 + npm run dev (requiere Node 18+)."""
    if shutil.which("npm") is None:
        log_fail("Falta Node/npm (Node 18+). Instálalo desde https://nodejs.org y re-ejecuta.")
        return 2
    web_dir = os.path.join(REPO, "src-web")
    if not os.path.exists(os.path.join(web_dir, "package.json")):
        log_fail("No se encontró src-web/package.json (rama dev requerida).")
        return 2
    if not os.path.exists(os.path.join(web_dir, "node_modules")):
        log_info("Instalando dependencias web (npm install) ...")
        proc = run_node(["npm", "install"], cwd=web_dir, timeout=600)
        if proc.returncode != 0:
            log_fail("npm install falló. Revisa tu red o Node 18+.")
            return 2
    bridge = os.path.join(web_dir, "scripts", "bridge_server.py")
    venv_py = venv_python(args.venv)
    bridge_py = venv_py if os.path.exists(venv_py) else sys.executable
    log_info("Puente local en http://127.0.0.1:3002 + Next dev en http://localhost:3000 ...")
    log_info("Cierra con Ctrl+C en esta terminal.")
    bridge_proc = subprocess.Popen([bridge_py, bridge], cwd=REPO)
    try:
        proc = run_node(["npm", "run", "dev"], cwd=web_dir)
        return proc.returncode
    finally:
        bridge_proc.terminate()


def do_uninstall(args) -> int:
    removed = []
    for path in (BIN_PATH, DESKTOP_PATH, AUTOSTART_PATH):
        if os.path.exists(path) or os.path.islink(path):
            try:
                os.remove(path)
                removed.append(path)
            except OSError as exc:
                log_fail(f"No se pudo borrar {path}: {exc}")
    if removed:
        for p in removed:
            log_ok(f"Eliminado: {p}")
    else:
        log_info("Nada que desinstalar (bin/.desktop ya ausentes).")
    if args.purge:
        if not args.yes:
            ans = input("Esto borrara settings.json y state.json generados. [s/N] ").strip().lower()
            if ans not in ("s", "si", "y", "yes"):
                log_info("Purge cancelado.")
                return 0
        for name in ("settings.json", "state.json"):
            p = os.path.join(REPO, name)
            if os.path.exists(p):
                os.remove(p)
                log_ok(f"Purgado: {p}")
    log_ok("Desinstalacion completa. (El venv y config.linux.json se conservan.)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instalador e inicializador de J.A.R.V.I.S. Launcher (Windows + Linux)."
    )
    parser.add_argument("--run", action="store_true", help="lanzar el launcher clasico al terminar")
    parser.add_argument("--run-web", action="store_true", help="lanzar el HUD web (bridge + Next dev)")
    parser.add_argument("--pull-model", action="store_true", help="descargar el modelo Ollama CPU")
    parser.add_argument("--with-rust", action="store_true", help="instalar Rust/Cargo si falta (desktop Tauri)")
    parser.add_argument("--model", default="qwen3:0.6b", help="modelo Ollama (defecto: qwen3:0.6b)")
    parser.add_argument("--uninstall", action="store_true", help="desinstalar bin/.desktop/autostart")
    parser.add_argument("--purge", action="store_true", help="con --uninstall, borra settings/state")
    parser.add_argument("--no-autostart", action="store_true", help="no crear autostart")
    parser.add_argument("--no-shortcut", action="store_true", help="no crear acceso del menu")
    parser.add_argument("--venv", default=os.path.join(REPO, ".venv"), help="ruta del venv")
    parser.add_argument("--yes", action="store_true", help="no pedir confirmacion")
    parser.add_argument("--check-only", action="store_true", help="solo diagnostico")
    args = parser.parse_args()

    if args.check_only:
        ok = check_env()
        check_ollama(model=args.model, pull=False)
        check_rust(install=False)
        return 0 if ok else 2
    if args.uninstall:
        if sys.platform == "win32":
            log_fail("En Windows --uninstall aun no gestiona .bat: borra el venv a mano si quieres.")
            return 2
        return do_uninstall(args)
    return do_install(args)


if __name__ == "__main__":
    sys.exit(main())
