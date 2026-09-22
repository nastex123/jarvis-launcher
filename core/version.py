"""
core/version.py - Version de la aplicacion (fuente unica + franja de saludo).

El launcher muestra su version en la barra de estado ("vX.Y.Z"). Para que la
version salte SOLA al publicar una release (sin editar config.json a mano):

1. Si el proyecto vive en un repo git con tags, al arrancar se lee
   `git describe --tags --abbrev=0` (v2.0.2 -> "2.0.2").
2. Si git no esta disponible (instalacion entregada), se usa la constante
   `__version__`, que se sincroniza en cada release.

Tambien expone `greeting_for_bogota()`: la franja horaria real de
America/Bogota para que los mensajes de GexStudio Team a la comunidad
(seccion "GexStudio Team -> Comunidad GexClub" del CHANGELOG / release notes)
saluden con coherencia horaria:
- Buenos dias:   05:00-11:59
- Buenas tardes: 12:00-18:59
- Buenas noches: 19:00-04:59
"""

import os
import subprocess
import sys

__version__ = "2.0.3"

# Windows: evita abrir una ventana de consola al invocar git.
# En POSIX creationflags no existe: solo se pasa en Windows.
_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_version() -> str:
    """Version efectiva: tag git mas reciente si esta disponible, si no la
    constante `__version__` (VERIFICADO en cada arranque)."""
    try:
        cmd = ["git", "-C", _GIT_ROOT, "describe", "--tags", "--abbrev=0"]
        if sys.platform == "win32":
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=_CREATE_NO_WINDOW,
            )
        else:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
            )
        tag = proc.stdout.strip() if proc.returncode == 0 else ""
        if tag:
            return tag.lstrip("v")
    except Exception:  # noqa: BLE001 - git ausente, timeout o entorno raro
        pass
    return __version__


def greeting_for_bogota() -> str:
    """Saludo de comunidad segun la franja horaria de America/Bogota
    (fallback a la hora local del equipo si no hay datos de zona IANA)."""
    import datetime as _dt

    try:
        import zoneinfo as _zi

        now = _dt.datetime.now(_zi.ZoneInfo("America/Bogota"))
    except Exception:  # noqa: BLE001 - sin tzdata/zoneinfo en Windows
        now = _dt.datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        return "Buenos dias"
    if 12 <= hour < 19:
        return "Buenas tardes"
    return "Buenas noches"