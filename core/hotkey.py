"""
core/hotkey.py - Atajo Ctrl+Shift+Espacio (dual Windows + Linux).

Windows: implementacion nativa con RegisterHotKey (ctypes) +
  QAbstractNativeEventFilter. Sin dependencias nuevas.

Linux (X11/Wayland): no existe RegisterHotKey a nivel de SO accesible
  sin portal/permisos. Se usa un QShortcut interno sobre la ventana
  (funciona cuando el launcher tiene el foco). Degradacion elegante y
  logueada; la API register()/unregister()/nativeEventFilter se conserva
  para que ui/jarvis_ui.py no cambie de firma.

En GNOME/Wayland, para un atajo realmente global, el usuario puede
asignar el comando `jarvis` en Ajustes > Teclado > Atajos (el
instalador install.py genera el .desktop y el bin necesarios).
"""

from __future__ import annotations

import logging
import sys

from PyQt6.QtCore import QAbstractNativeEventFilter

logger = logging.getLogger("jarvis.hotkey")

# Constantes de la API de Windows
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_SPACE = 0x20
WM_HOTKEY = 0x0312

HOTKEY_ID = 0x4A41  # 'J A' -> identificador unico para nuestra ventana

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:  # pragma: no cover - solo Windows
    import ctypes
    from ctypes import wintypes

    class Msg(ctypes.Structure):
        """Estructura MSG de Win32 (solo los campos que usamos)."""

        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", wintypes.POINT),
        ]

    _user32 = ctypes.windll.user32

    # Firmas explicitas para evitar truncado de punteros de 64 bits
    _user32.RegisterHotKey.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.UINT,
    ]
    _user32.RegisterHotKey.restype = wintypes.BOOL
    _user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.UnregisterHotKey.restype = wintypes.BOOL
else:
    ctypes = None  # type: ignore[assignment]
    Msg = None  # type: ignore[assignment]
    _user32 = None


class GlobalHotkey(QAbstractNativeEventFilter):
    """Registra Ctrl+Shift+Espacio y emite el callback al pulsarlo."""

    def __init__(self, on_triggered, parent_widget=None) -> None:
        super().__init__()
        self._on_triggered = on_triggered
        self._registered = False
        self._parent_widget = parent_widget
        self._qt_shortcut = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def register(self) -> bool:
        """
        Registra la combinacion.

        Windows: hotkey global real. Linux: QShortcut interno sobre la
        ventana padre (requiere foco). Retorna True si quedo activo.

        Returns
        -------
        True si quedo registrado; False si otro proceso la tiene ocupada
        o la plataforma no soporta hotkey global.
        """
        if _IS_WINDOWS:  # pragma: no cover - solo Windows
            ok = bool(
                _user32.RegisterHotKey(
                    None,  # hwnd = None -> el mensaje llega al hilo de la app
                    HOTKEY_ID,
                    MOD_CONTROL | MOD_SHIFT,
                    VK_SPACE,
                )
            )
            self._registered = ok
            if ok:
                logger.info("Atajo global Ctrl+Shift+Espacio registrado.")
            else:
                logger.warning(
                    "No se pudo registrar Ctrl+Shift+Espacio "
                    "(posiblemente ya esta en uso por otra app)."
                )
            return ok

        # ---- Linux: atajo interno Qt (sin foco global en Wayland) ----
        try:
            from PyQt6.QtGui import QKeySequence, QShortcut

            parent = self._parent_widget
            if parent is None:
                # Sin ventana padre no hay donde anclar el QShortcut:
                # degradacion silenciosa (el launcher sigue usable).
                logger.warning(
                    "Atajo Ctrl+Shift+Espacio sin ventana padre en Linux: "
                    "solo disponible via Ajustes > Teclado > comando 'jarvis'."
                )
                self._registered = False
                return False
            self._qt_shortcut = QShortcut(
                QKeySequence("Ctrl+Shift+Space"), parent
            )
            self._qt_shortcut.setContext(
                __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.ShortcutContext.WindowShortcut
            )
            self._qt_shortcut.activated.connect(self._on_triggered)
            self._registered = True
            logger.info(
                "Atajo interno Ctrl+Shift+Espacio registrado (Linux: "
                "requiere foco del launcher; para global usa Ajustes > Teclado)."
            )
            return True
        except Exception as exc:
            logger.warning(f"No se pudo registrar el atajo interno Qt: {exc}")
            self._registered = False
            return False

    def unregister(self) -> None:
        if _IS_WINDOWS:  # pragma: no cover - solo Windows
            if self._registered:
                _user32.UnregisterHotKey(None, HOTKEY_ID)
                self._registered = False
                logger.info("Atajo global desregistrado.")
            return
        try:
            if self._qt_shortcut is not None:
                self._qt_shortcut.setEnabled(False)
                self._qt_shortcut.deleteLater()
        except Exception:
            pass
        finally:
            self._qt_shortcut = None
            self._registered = False

    # ------------------------------------------------------------------
    # Filtro de eventos nativos (solo Windows)
    # ------------------------------------------------------------------

    def nativeEventFilter(self, eventType, message):
        """Captura WM_HOTKEY del hilo y dispara el callback (Windows)."""
        if not _IS_WINDOWS:
            return False, 0
        if eventType == b"windows_generic_MSG":
            try:
                import ctypes as _ct

                msg = _ct.cast(int(message), _ct.POINTER(Msg)).contents
            except (TypeError, ValueError):  # pragma: no cover
                return False, 0
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                logger.debug("WM_HOTKEY recibido.")
                self._on_triggered()
                return True, 0
        return False, 0
