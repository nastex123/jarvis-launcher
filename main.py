"""
main.py - Entry point del J.A.R.V.I.S. Launcher.

Carga la configuracion, construye la interfaz y coordina el lanzamiento
de aplicaciones cuando el usuario selecciona un modo.
"""

import sys
import os
import socket
import logging
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# Asegurar que los modulos del proyecto estan en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager
from core.github_link import detect_gh_identity
from core.launcher import AppLauncher
from core.settings import SettingsManager
from core.version import get_app_version
from ui.jarvis_ui import JarvisUI

# -----------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("jarvis.main")

# -----------------------------------------------------------------------
# Singleton check - evitar dos instancias simultaneas
# -----------------------------------------------------------------------
SOCKET_PORT = 47821

# Referencia global: el socket debe vivir toda la sesion,
# de lo contrario el GC lo cierra y se pierde el lock.
_singleton_socket: socket.socket | None = None


def _acquire_singleton() -> bool:
    """
    Adquiere el lock de instancia unica bindeando un puerto local.

    Returns
    -------
    True si esta instancia tiene el lock; False si ya hay otra.
    """
    global _singleton_socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Sin SO_REUSEADDR en Windows: el segundo bind falla con
        # WSAEADDRINUSE -> deteccion de instancia duplicada.
        sock.bind(("127.0.0.1", SOCKET_PORT))
        sock.listen(1)
        _singleton_socket = sock
        return True
    except OSError:
        return False


# -----------------------------------------------------------------------
# Callback de seleccion de modo
# -----------------------------------------------------------------------

def _handle_mode_selected(launcher: AppLauncher, ui: JarvisUI, config: ConfigManager):
    """Retorna un closure que maneja la seleccion de modo."""

    def handler(mode_id: str) -> None:
        mode = config.get_mode(mode_id)
        if mode is None:
            ui.set_launch_complete(mode_id, "Error", [], ["Modo no encontrado"])
            return

        apps = mode.get("apps", [])
        if not apps:
            ui.set_launch_complete(
                mode_id,
                mode.get("name", mode_id),
                [],
                ["No hay apps configuradas"],
            )
            return

        mode_name = mode.get("name", mode_id)
        logger.info(f"Modo seleccionado: {mode_name} ({len(apps)} apps)")

        # Lanzar en un hilo separado para no bloquear la UI
        def _run_launch():
            result = launcher.launch_mode(apps)
            # Actualizar UI en el hilo principal
            ui.set_launch_complete(
                mode_id, mode_name, result["launched"], result["failed"]
            )
            logger.info(
                f"Resultado: {len(result['launched'])} OK, "
                f"{len(result['failed'])} fallos"
            )

        thread = threading.Thread(target=_run_launch, daemon=True)
        thread.start()

    return handler


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> int:
    # Verificar instancia unica
    if not _acquire_singleton():
        logger.warning("Ya hay una instancia ejecutandose. Cerrando.")
        return 0

    # Cargar configuracion
    config = ConfigManager()
    logger.info(f"Configuracion cargada: {config.app_name}")

    # Crear app Qt.
    # AA_ShareOpenGLContexts DEBE activarse antes de crear la app: lo exige
    # el mini navegador embebido (PyQt6-WebEngine / QWebEngineView).
    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
    )
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S. Launcher")
    app.setApplicationVersion(get_app_version())

    # Estilo global (pila de fuentes por plataforma: Segoe UI solo en Windows)
    font_stack = (
        "'Segoe UI', 'Consolas', monospace"
        if sys.platform == "win32"
        else "'Inter', 'Ubuntu', 'DejaVu Sans', monospace"
    )
    app.setStyleSheet(
        """
        * {
            font-family: %s;
        }
        QWidget {
            background: #080A12;
            color: white;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 6px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 255, 255, 40);
            border-radius: 3px;
            min-height: 30px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        % font_stack
    )

    # Crear launcher y ventana principal
    launcher = AppLauncher()
    settings = SettingsManager()
    ui = JarvisUI(config._config, settings=settings)
    ui._on_mode_selected = _handle_mode_selected(launcher, ui, config)

    # Deteccion automatica de la cuenta de GitHub (si aun no esta vinculada).
    # Corre en un hilo para no bloquear el arranque; el saludo se actualiza
    # en el hilo principal cuando se detecta la identidad.
    if not settings.github_username:
        def _detect_github():
            ident = detect_gh_identity()
            if ident:
                login, name = ident
                settings.github_username = login
                settings.github_name = name or login
                logger.info("Cuenta GitHub detectada automaticamente: %s", login)
                ui.refresh_greeting()

        threading.Thread(target=_detect_github, daemon=True).start()

    # Z-order: garantiza que la ventana quede al frente y con foco
    ui.show_and_raise()

    logger.info("J.A.R.V.I.S. Launcher iniciado.")
    exit_code = app.exec()

    logger.info("Cerrando J.A.R.V.I.S. Launcher.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
