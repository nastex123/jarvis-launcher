#!/usr/bin/env python3
"""
install.py - Instalador e inicializador de J.A.R.V.I.S. Launcher para Linux.

Todo-en-uno, solo stdlib. Idempotente: se puede re-ejecutar sin romper nada.

Uso:
    python3 install.py                  instala todo (venv + deps + bin + .desktop)
    python3 install.py --run            instala (si falta) y lanza el launcher
    python3 install.py --uninstall      revierte bin/.desktop/autostart
    python3 install.py --uninstall --purge  ademas borra settings/state generados

Opciones:
    --no-autostart   no crea ~/.config/autostart/jarvis-launcher.desktop
    --no-shortcut    no crea ~/.local/share/applications/jarvis-launcher.desktop
    --venv PATH      ruta del venv (defecto: <repo>/.venv)
    --yes            no pedir confirmacion en --purge
    --run            lanzar al terminar (usa el python del venv)
    --check-only     solo diagnostico del entorno, no instala

Lo que hace, por etapas:
    1. check_env: Python>=3.10, pip, venv, distro/sesion (apt/dnf/pacman/zypper)
    2. ensure_venv + pip install -r requirements.txt
    3. check_system_libs: sugiere paquetes Qt6/X11/Wayland/WebEngine si faltan
    4. ensure_linux_config: crea config.linux.json desde config.linux.example.json
    5. install_bin: ~/.local/bin/jarvis (wrapper al venv + main.py)
    6. install_desktop: ~/.local/share/applications/jarvis-launcher.desktop
    7. install_autostart: ~/.config/autostart/jarvis-launcher.desktop
    8. smoke_test: compileall + import PyQt6 + valida config.linux.json

En Windows este script no instala: usa install_jarvis_cmd.bat / install_startup.bat.
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
    if shutil.which("notify-send") is None:
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

def ensure_venv(venv_dir: str) -> str:
    venv_py = os.path.join(venv_dir, "bin", "python")
    if os.path.exists(venv_py):
        log_ok(f"Venv existente: {venv_dir}")
        return venv_py
    log_info(f"Creando venv en {venv_dir} ...")
    proc = subprocess.run([sys.executable, "-m", "venv", venv_dir])
    if proc.returncode != 0 or not os.path.exists(venv_py):
        log_fail("No se pudo crear el venv (instala python3-venv).")
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


def check_ollama() -> None:
    """Verifica Ollama para el asistente (aviso, no bloquea la instalación)."""
    import json as _json
    import urllib.request as _url

    model = "qwen2.5-coder:7b"
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
            models = [m.get("name", "") for m in _json.loads(resp.read().decode()) .get("models", [])]
    except OSError:
        log_warn("No se pudo listar modelos de Ollama.")
        return
    if any(m.split(":")[0] == model.split(":")[0] for m in models):
        log_ok(f"Modelo {model} descargado")
    else:
        log_warn(f"Modelo {model} ausente. Descárgalo con: ollama pull {model}")


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
    check_system_libs(venv_py)  # informativo, no bloquea
    ensure_linux_config()
    check_ollama()
    install_bin(venv_py)
    if not args.no_shortcut:
        install_desktop_file(venv_py, DESKTOP_PATH)
    else:
        log_info("--no-shortcut: se omite el .desktop del menu.")
    if not args.no_autostart:
        install_desktop_file(venv_py, AUTOSTART_PATH, autostart=True)
    else:
        log_info("--no-autostart: se omite el autostart.")
    ok = smoke_test(venv_py)
    print()
    if ok:
        log_ok("Instalacion completa. Abre una terminal nueva y ejecuta:  jarvis")
        log_info("Atajo con foco: Ctrl+Shift+Espacio. Global en GNOME: "
                 "Ajustes > Teclado > Anadir atajo -> comando 'jarvis'.")
        log_info("Auto-inicio: rueda de ajustes del launcher o re-ejecuta install.py.")
    else:
        log_warn("Instalacion con advertencias: revisa los [FAIL] de arriba.")
    if args.run:
        return do_run(args)
    return 0 if ok else 1


def do_run(args) -> int:
    venv_py = os.path.join(args.venv, "bin", "python")
    if not os.path.exists(venv_py):
        log_fail(f"No hay venv en {args.venv}. Ejecuta primero: python3 install.py")
        return 2
    log_info("Iniciando J.A.R.V.I.S. Launcher ...")
    os.execv(venv_py, [venv_py, os.path.join(REPO, "main.py")])


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
        description="Instalador e inicializador de J.A.R.V.I.S. Launcher para Linux."
    )
    parser.add_argument("--run", action="store_true", help="lanzar el launcher al terminar")
    parser.add_argument("--uninstall", action="store_true", help="desinstalar bin/.desktop/autostart")
    parser.add_argument("--purge", action="store_true", help="con --uninstall, borra settings/state")
    parser.add_argument("--no-autostart", action="store_true", help="no crear autostart")
    parser.add_argument("--no-shortcut", action="store_true", help="no crear acceso del menu")
    parser.add_argument("--venv", default=os.path.join(REPO, ".venv"), help="ruta del venv")
    parser.add_argument("--yes", action="store_true", help="no pedir confirmacion")
    parser.add_argument("--check-only", action="store_true", help="solo diagnostico")
    args = parser.parse_args()

    if sys.platform == "win32":
        log_fail("install.py es para Linux. En Windows usa install_jarvis_cmd.bat.")
        return 2
    if args.check_only:
        ok = check_env()
        check_ollama()
        return 0 if ok else 2
    if args.uninstall:
        return do_uninstall(args)
    return do_install(args)


if __name__ == "__main__":
    sys.exit(main())
