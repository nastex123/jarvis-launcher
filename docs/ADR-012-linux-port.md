# ADR-012 — Port a Linux + instalador `install.py`

Fecha: 2026-09-22. Estado: aceptado.

## Contexto

El launcher era 100 % Windows: `winreg`, `os.startfile`, `RegisterHotKey`,
toasts PowerShell, auto-inicio en `%APPDATA%\...\Startup` y `config.json`
con rutas `C:\`. Se pide soporte Linux manteniendo compatibilidad Windows,
con un instalador/inicializador en Python.

Entorno de referencia: Ubuntu 24.04 + GNOME + Wayland + Python 3.12.
Objetivo: multi-distro generico (spec freedesktop), sin nuevas dependencias pip.

## Decision

1. **Codigo dual con branches por plataforma**, no fork. Nuevo
   `core/platform.py` como fuente unica (`is_windows/is_linux`,
   `autostart_*`, `linux_desktop_dirs`, `distro_id/session_info`).
2. **`core/launcher.py`**: URLs via `webbrowser.open()`; `Popen` con
   `creationflags` solo en NT y `start_new_session=True` en POSIX;
   resolucion Linux via `shutil.which` + parseo de `*.desktop`
   (`Name/Exec/StartupWMClass`, limpieza de field-codes `%U/%F/...`,
   soporte `flatpak run`/`snap`). `winreg`/`.lnk` con import perezoso
   solo en Windows.
3. **Atajo**: en Wayland no hay hotkey global sin portal/permisos.
   Se usa `QShortcut` interno `Ctrl+Shift+Espacio` anclado a la ventana
   (requiere foco). Misma clase `GlobalHotkey` y misma firma, degradacion
   logueada. Para global real: asignar el comando `jarvis` en
   Ajustes > Teclado (documentado en README e `install.py`).
4. **Notificaciones**: `notify-send` si existe, si no bandeja/tray.
   `notify()` ya no hace early-return en Linux.
5. **Auto-inicio**: Windows intacto (`.vbs` en Startup); Linux escribe
   `~/.config/autostart/jarvis-launcher.desktop` (spec freedesktop,
   valido en GNOME/KDE/X11/Wayland y systemd-less).
6. **Config**: `ConfigManager` prefiere `config.linux.json` en Linux si
   existe (sin romper `config.json` Windows). `install.py` lo genera
   desde `config.linux.example.json` con binarios `steam/code/google-chrome/
   discord/spotify` resolvibles por PATH o `.desktop`.
7. **`install.py` todo-en-uno (stdlib)**: venv + pip + `~/.local/bin/jarvis`
   + `.desktop` de menu + autostart + `compileall`/import smoke. Flags
   `--run/--uninstall/--purge/--no-autostart/--no-shortcut/--venv/--check-only`.
   `--run` actua como inicializador (exec del venv sobre `main.py`).
8. **`core/version.py`**: `creationflags` solo en `win32` (en POSIX el
   kwarg no existe y rompia `git describe`).
9. **Fuentes**: pila `Inter/Ubuntu/DejaVu Sans` en Linux (Segoe UI solo Windows).

## Alternativas descartadas

- A. Fork solo-Linux: mas simple pero duplica mantenimiento; se eligio dual.
- B. Hotkey global via `pynput/evdev`: global real pero exige permisos de
  input, demonios y nuevas deps; se deja como trabajo futuro documentado.
- C. Paquete `.deb`/Flatpak: buen paso siguiente, pero `install.py --user`
  cubre todas las distros sin sudo ni empaquetado por distro.
- D. `systemd --user` service: innecesario para app GUI de sesion; el
  `.desktop` en autostart es el mecanismo estandar de escritorio.

## Consecuencias

- GNOME sin AppIndicator: la bandeja queda oculta; el launcher sigue
  funcional (`install.py` avisa, no bloquea).
- WebEngine en Linux exige libs sistema (`libnss3`, `libasound2`, ...);
  `install.py` las sugiere por gestor (apt/dnf/pacman/zypper).
- `config.linux.json` esta gitignored (dato local); el ejemplo se versiona.
