"""
core/config.py - Gestor de configuracion del Jarvis Launcher.

Lee y escribe config.json. Provee acceso tipado a los modos
y sus respectivas listas de aplicaciones.
"""

import json
import os
import sys
from typing import Any


class ConfigManager:
    """Lee, valida y gestiona la configuracion del launcher."""

    DEFAULT_CONFIG = {
        "app_name": "J.A.R.V.I.S. Launcher",
        "version": "2.0.3",
        "greeting": "Buenos dias, senpai. Selecciona tu modo de operacion:",
        "modes": {
            "gaming": {
                "name": "Gaming",
                "icon": "\U0001f3ae",
                "color": "#FF2D55",
                "description": "Listo para la accion",
                "apps": [],
            },
            "work": {
                "name": "Trabajo",
                "icon": "\U0001f4bc",
                "color": "#007AFF",
                "description": "Modo productividad activado",
                "apps": [],
            },
            "study": {
                "name": "Estudio",
                "icon": "\U0001f4da",
                "color": "#30D158",
                "description": "Modo aprendizaje activado",
                "apps": [],
            },
        },
    }

    def __init__(self, config_path: str | None = None) -> None:
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # En Linux se prefiere config.linux.json si existe (no rompe
            # el config.json de Windows). Fallback a config.json.
            linux_path = os.path.join(base_dir, "config.linux.json")
            default_path = os.path.join(base_dir, "config.json")
            if sys.platform.startswith("linux") and os.path.exists(linux_path):
                config_path = linux_path
            else:
                config_path = default_path
        self.config_path = config_path
        self._config: dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    # Lectura / escritura
    # ------------------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """Carga el archivo JSON. Si no existe, crea uno por defecto."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as fh:
                self._config = json.load(fh)
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
        return self._config

    def save(self) -> None:
        """Persiste la configuracion actual en disco."""
        with open(self.config_path, "w", encoding="utf-8") as fh:
            json.dump(self._config, fh, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Accessors tipados
    # ------------------------------------------------------------------

    @property
    def app_name(self) -> str:
        return self._config.get("app_name", "J.A.R.V.I.S.")

    @property
    def greeting(self) -> str:
        return self._config.get("greeting", "Selecciona tu modo:")

    @property
    def modes(self) -> dict[str, dict[str, Any]]:
        return self._config.get("modes", {})

    def get_mode(self, mode_id: str) -> dict[str, Any] | None:
        """Devuelve la configuracion de un modo o None si no existe."""
        return self.modes.get(mode_id)

    def get_mode_ids(self) -> list[str]:
        """Devuelve la lista ordenada de IDs de modos disponibles."""
        return list(self.modes.keys())

    def get_mode_apps(self, mode_id: str) -> list[dict[str, str]]:
        """Devuelve la lista de apps de un modo."""
        mode = self.get_mode(mode_id)
        if mode is None:
            return []
        return mode.get("apps", [])

    def get_mode_color(self, mode_id: str) -> str:
        """Devuelve el color hex de un modo (fallback: cyan)."""
        mode = self.get_mode(mode_id)
        if mode is None:
            return "#00FFFF"
        return mode.get("color", "#00FFFF")

    def update_mode_apps(self, mode_id: str, apps: list[dict[str, str]]) -> None:
        """Actualiza la lista de apps de un modo y persiste."""
        mode = self.get_mode(mode_id)
        if mode is not None:
            mode["apps"] = apps
            self.save()
