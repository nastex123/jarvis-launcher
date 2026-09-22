"""
core/launcher.py - Motor de apertura de aplicaciones (dual Windows + Linux).

Ejecuta la lista de apps asociadas a un modo de forma secuencial,
con un pequeno delay entre cada una para evitar picos de CPU.

Resolucion de comandos (en orden):
  1. Si el comando es una URL -> navegador por defecto.
  2. Si la ruta existe -> se lanza directamente.
  3. Si el comando es un nombre corto (p. ej. "Discord") o la ruta
     no existe -> se busca el ejecutable:
     - Windows: menu de inicio del usuario y del sistema (accesos
       directos .lnk) y registro App Paths.
     - Linux: PATH + archivos .desktop freedesktop
       (/usr/share/applications, ~/.local/share/applications,
       XDG_DATA_DIRS, exports de Flatpak).
  4. Si no se encuentra -> fallo con mensaje descriptivo.
"""

import glob
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
import webbrowser
from typing import Callable

logger = logging.getLogger("jarvis.launcher")

from core.platform import is_linux, is_windows, linux_desktop_dirs

# Directorios del menu de inicio donde buscar accesos directos (Windows)
_START_MENU_DIRS = [
    os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
    os.path.join(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
        r"Microsoft\Windows\Start Menu\Programs",
    ),
]


class AppLauncher:
    """Lanza aplicaciones definidas en la configuracion de un modo."""

    # Delay (segundos) entre cada app para no saturar el disco
    LAUNCH_DELAY = 0.6

    def __init__(self) -> None:
        self._cancelled = False

    # ------------------------------------------------------------------
    # Cancelacion
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Detiene el lanzamiento pendiente."""
        self._cancelled = True

    def reset(self) -> None:
        """Resetea el flag de cancelacion."""
        self._cancelled = False

    # ------------------------------------------------------------------
    # Lanzamiento
    # ------------------------------------------------------------------

    def launch_mode(
        self,
        apps: list[dict[str, str]],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, str]:
        """
        Lanza todas las apps de un modo.

        Parameters
        ----------
        apps : lista de dicts con keys 'name', 'command' y opcionalmente 'args'.
        on_progress : callback(app_name, index, total) para notificar progreso.

        Returns
        -------
        dict con 'launched' y 'failed' como listas de nombres.
        """
        self._cancelled = False
        launched: list[str] = []
        failed: list[str] = []
        total = len(apps)

        for idx, app in enumerate(apps):
            if self._cancelled:
                logger.info("Lanzamiento cancelado por el usuario.")
                break

            name = app.get("name", "Desconocido")
            command = app.get("command", "")
            args = app.get("args", "")

            if on_progress:
                on_progress(name, idx + 1, total)

            success = self._open_app(command, args)
            if success:
                launched.append(name)
            else:
                failed.append(name)

            # Pausa entre apps (excepto la ultima)
            if idx < total - 1:
                time.sleep(self.LAUNCH_DELAY)

        self._cancelled = False
        return {"launched": launched, "failed": failed}

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _open_app(self, command: str, args: str = "") -> bool:
        """Abre una aplicacion individual. Retorna True si fue exitoso."""
        if not command:
            logger.warning("Comando vacio, saltando.")
            return False

        # Si es URL, abrir en navegador por defecto (cross-platform)
        if command.startswith("http://") or command.startswith("https://"):
            try:
                if is_windows():
                    os.startfile(command)  # type: ignore[attr-defined]
                else:
                    webbrowser.open(command)
                logger.info(f"URL abierta: {command}")
                return True
            except OSError as exc:
                logger.error(f"Error abriendo URL {command}: {exc}")
                return False

        # Resolver la ruta real del ejecutable
        resolved = self._resolve_command(command)
        if resolved is None:
            logger.error(
                f"No se encontro la aplicacion '{command}'. "
                "Verifica que este instalada o corrige la ruta en config.json."
            )
            return False

        # Lanzamiento normal
        try:
            cmd_list = self._build_cmd_list(resolved, args)
            popen_kwargs: dict = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if is_windows():
                popen_kwargs["creationflags"] = (
                    subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Equivalente POSIX: detach de la terminal sin creationflags
                popen_kwargs["start_new_session"] = True
            subprocess.Popen(cmd_list, **popen_kwargs)
            logger.info(f"App lanzada: {cmd_list} {args}")
            return True
        except Exception as exc:
            logger.error(f"Error lanzando {resolved}: {exc}")
            # Fallback Windows: os.startfile
            if is_windows():
                try:
                    os.startfile(resolved)  # type: ignore[attr-defined]
                    return True
                except OSError:
                    return False
            return False

    @staticmethod
    def _build_cmd_list(resolved: str, args: str) -> list[str]:
        """Construye argv. Soporta comandos flatpak y args con comillas."""
        # resolved puede ser "flatpak run org.X" (multi-token) si vino de .desktop
        base = shlex.split(resolved) if " " in resolved and not os.path.exists(resolved) else [resolved]
        if args:
            base.extend(shlex.split(args))
        return base

    # ------------------------------------------------------------------
    # Resolucion de comandos
    # ------------------------------------------------------------------

    def _resolve_command(self, command: str) -> str | None:
        """Devuelve la ruta/comando real del ejecutable o None si no existe."""
        # 1. Ruta absoluta existente
        if os.path.exists(command):
            return command

        # 2. Ejecutable en el PATH
        found = shutil.which(command)
        if found:
            return found

        # 3. Plataforma: menu inicio / App Paths (Windows) o .desktop (Linux)
        if is_windows():
            exe_name = os.path.basename(command).split(".exe")[0]
            found = self._find_in_start_menu(exe_name)
            if found:
                return found
            found = self._find_in_app_paths(command)
            if found:
                return found
        elif is_linux():
            found = self._find_in_desktop_files(command)
            if found:
                return found

        return None

    # ------------------------- Windows --------------------------------

    def _find_in_start_menu(self, app_name: str) -> str | None:
        """
        Busca un acceso directo .lnk cuyo nombre coincida con app_name
        (insensible a mayusculas) y extrae el TargetPath del ejecutable.
        Solo Windows.
        """
        if not is_windows():
            return None
        app_lower = app_name.lower()
        for start_dir in _START_MENU_DIRS:
            if not os.path.isdir(start_dir):
                continue
            pattern = os.path.join(start_dir, "**", "*.lnk")
            for lnk in glob.glob(pattern, recursive=True):
                base = os.path.splitext(os.path.basename(lnk))[0].lower()
                if app_lower in base:
                    target = self._read_lnk_target(lnk)
                    if target and os.path.exists(target) and target.lower().endswith(".exe"):
                        logger.info(f"App '{app_name}' resuelta via: {lnk}")
                        return target
        return None

    @staticmethod
    def _read_lnk_target(lnk_path: str) -> str | None:
        """Extrae TargetPath de un .lnk usando WScript.Shell (COM via PowerShell)."""
        import subprocess as sp

        ps_script = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
            f"'{lnk_path}'); $s.TargetPath"
        )
        try:
            out = sp.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=sp.CREATE_NO_WINDOW,
            )
            target = out.stdout.strip()
            return target if target else None
        except Exception as exc:  # pragma: no cover
            logger.warning(f"No se pudo leer el acceso directo {lnk_path}: {exc}")
            return None

    def _find_in_app_paths(self, command: str) -> str | None:
        """Busca el ejecutable en la clave App Paths del registro (Windows)."""
        if not is_windows():
            return None
        import winreg

        exe_name = os.path.basename(command)
        if not exe_name.lower().endswith(".exe"):
            exe_name += ".exe"

        base_key = r"Software\Microsoft\Windows\CurrentVersion\App Paths"
        candidates = [
            (winreg.HKEY_CURRENT_USER, rf"{base_key}\{exe_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"{base_key}\{exe_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\WOW6432Node\{base_key}\{exe_name}"),
        ]

        for hive, key_path in candidates:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    value, _ = winreg.QueryValueEx(key, "")
                    if value and os.path.exists(value):
                        logger.info(f"App '{command}' resuelta via App Paths: {value}")
                        return value
            except OSError:
                continue
        return None

    # ------------------------- Linux ----------------------------------

    # Alias de nombres amigables -> candidatos .desktop/PATH (Linux).
    # Permite usar "VS Code" en config y resolver code.desktop, etc.
    _LINUX_ALIASES: dict[str, list[str]] = {
        "vs code": ["code", "visual studio code"],
        "vscode": ["code"],
        "chrome": ["google-chrome", "chromium", "brave-browser"],
        "discord": ["discord"],
        "spotify": ["spotify"],
        "steam": ["steam"],
        "firefox": ["firefox"],
        "terminal": ["gnome-terminal", "konsole", "xterm"],
        "files": ["nautilus", "dolphin", "thunar"],
    }

    def _find_in_desktop_files(self, command: str) -> str | None:
        """Busca la app en archivos .desktop freedesktop (Linux).

        Matchea por nombre de archivo (discord.desktop), campo Name= o
        StartupWMClass, insensible a mayusculas. Retorna la linea Exec
        limpia de field-codes (%U, %F, ...) o el binario si existe.
        """
        if not is_linux():
            return None
        needle = os.path.splitext(os.path.basename(command))[0].lower()
        # 0. Alias amigables ("VS Code" -> code) via PATH directo primero
        for alias in self._LINUX_ALIASES.get(needle, []):
            direct = shutil.which(alias)
            if direct:
                logger.info(f"App '{command}' resuelta via alias PATH: {alias}")
                return direct
        needles = [needle] + self._LINUX_ALIASES.get(needle, [])
        for app_dir in linux_desktop_dirs():
            try:
                entries = os.listdir(app_dir)
            except OSError:
                continue
            for entry in entries:
                if not entry.lower().endswith(".desktop"):
                    continue
                stem = os.path.splitext(entry)[0].lower()
                desktop_path = os.path.join(app_dir, entry)
                if not any(
                    n and (n in stem or n == stem) for n in needles
                ):
                    # Leer Name=/StartupWMClass antes de descartar
                    # (p. ej. "code.desktop" vs "VS Code")
                    name_field = self._desktop_field(desktop_path, "Name").lower()
                    wm_class = self._desktop_field(desktop_path, "StartupWMClass").lower()
                    if not any(
                        n and (n in name_field or n in wm_class) for n in needles
                    ):
                        continue
                exec_line = self._desktop_field(desktop_path, "Exec")
                if not exec_line:
                    continue
                cleaned = self._clean_exec(exec_line)
                if not cleaned:
                    continue
                first_token = shlex.split(cleaned)[0]
                # Aceptar si el binario existe en PATH o es ruta absoluta
                if os.path.isabs(first_token) and os.path.exists(first_token):
                    logger.info(f"App '{command}' resuelta via desktop: {desktop_path}")
                    return cleaned
                if shutil.which(first_token):
                    logger.info(f"App '{command}' resuelta via desktop: {desktop_path}")
                    return cleaned
                # Flatpak / snap: devolver el comando completo aunque no este en PATH
                if first_token in ("flatpak", "snap"):
                    logger.info(f"App '{command}' resuelta via desktop: {desktop_path}")
                    return cleaned
        return None

    @staticmethod
    def _desktop_field(desktop_path: str, field: str) -> str:
        """Lee un campo X= de la seccion [Desktop Entry] sin dependencias."""
        in_entry = False
        prefix = field + "="
        try:
            with open(desktop_path, encoding="utf-8", errors="ignore") as fh:
                for raw in fh:
                    line = raw.strip()
                    if line.startswith("["):
                        in_entry = line.strip().lower() == "[desktop entry]"
                        continue
                    if not in_entry:
                        continue
                    if line.startswith(prefix):
                        return line[len(prefix):].strip()
                    if line.startswith("["):
                        break
        except OSError:
            return ""
        return ""

    @staticmethod
    def _clean_exec(exec_line: str) -> str:
        """Quita field-codes freedesktop (%U %F %u %f %i %c %k %%) de Exec."""
        tokens: list[str] = []
        for tok in shlex.split(exec_line):
            if tok.startswith("%"):
                continue
            if tok == "%%":
                tokens.append("%")
                continue
            tokens.append(tok)
        return " ".join(tokens)


def _unused_ref() -> None:  # evita warning de import no usado en Windows
    _ = sys.platform
