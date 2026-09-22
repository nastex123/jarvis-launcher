"""
core/platform.py - Helpers de plataforma (dual Windows + Linux).

Centraliza la deteccion de SO, rutas de autostart / aplicaciones y
utilidades freedesktop para que el resto del codigo no repita
`sys.platform` por todas partes.

Linux soportado: cualquier distro con spec freedesktop
(~/.config/autostart + ~/.local/share/applications), probado en
Ubuntu 24.04 / GNOME / Wayland y compatible con KDE, X11, etc.
"""

from __future__ import annotations

import os
import sys


def is_windows() -> bool:
    return os.name == "nt" or sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------------
# Autostart
# ------------------------------------------------------------------

def windows_startup_dir() -> str:
    base = os.environ.get("APPDATA", "")
    return os.path.join(base, r"Microsoft\Windows\Start Menu\Programs\Startup")


def linux_autostart_dir() -> str:
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "autostart",
    )


def linux_autostart_file() -> str:
    return os.path.join(linux_autostart_dir(), "jarvis-launcher.desktop")


def autostart_is_configured() -> bool:
    """True si el auto-inicio esta activo en la plataforma actual."""
    if is_windows():
        d = windows_startup_dir()
        return any(
            os.path.exists(os.path.join(d, f))
            for f in ("JarvisLauncher.vbs", "JarvisLauncher.bat")
        )
    if is_linux():
        return os.path.exists(linux_autostart_file())
    return False


# ------------------------------------------------------------------
# Aplicaciones instaladas (Linux .desktop)
# ------------------------------------------------------------------

def linux_desktop_dirs() -> list[str]:
    """Directorios donde buscar *.desktop (spec freedesktop + XDG)."""
    dirs: list[str] = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        os.path.join(
            os.environ.get(
                "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
            ),
            "applications",
        ),
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    ]
    for extra in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":"):
        if extra:
            dirs.append(os.path.join(extra, "applications"))
    # Deduplicar preservando orden, quedarnos con los que existen
    seen: set[str] = set()
    out: list[str] = []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            if os.path.isdir(d):
                out.append(d)
    return out


def linux_config_path() -> str:
    """Ruta sugerida del config de modos para Linux."""
    return os.path.join(repo_root(), "config.linux.json")


def distro_id() -> str:
    """ID de distro (ubuntu, fedora, arch...) o '' si no se detecta."""
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("ID="):
                    return line.strip().split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def session_info() -> dict[str, str]:
    return {
        "session_type": os.environ.get("XDG_SESSION_TYPE", ""),
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
        "distro": distro_id(),
    }
