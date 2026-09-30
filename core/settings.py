"""
core/settings.py - Gestor de ajustes de usuario (settings.json).

Persiste preferencias de la aplicacion:
  - Tema activo (ver core/themes.py)
  - Panel de noticias: conectado/desconectado, posicion (izquierda/derecha),
    ancho en pixeles y fuentes RSS configuradas.

Separa los ajustes de UI de la configuracion de modos (config.json).
"""

import json
import os
from typing import Any


class SettingsManager:
    """Lee, valida y persiste los ajustes de usuario en settings.json."""

    DEFAULT_SETTINGS: dict[str, Any] = {
        "theme": "obsidiana",
        "news": {
            "enabled": False,
            "position": "right",        # "left" | "right"
            "width": 360,                # px del panel
            "sources": [],               # list[{"name": str, "url": str}]
            "custom_url": "",            # URL escrita por el usuario
        },
        "tray": {
            "enabled": True,             # minimizar a bandeja en vez de cerrar
        },
        "github": {
            "username": "",              # cuenta vinculada ("" = no vinculada)
            "name": "",                  # nombre real obtenido de la API
        },
        "greeting": {
            "adjective_index": 0,        # indice del adjetivo rotativo
        },
        "agent": {
            "enabled": True,             # asistente IA local activo
            "url": "http://localhost:11434",
            "model": "qwen3:1.7b",
            "timeout_s": 180,            # timeout por llamada a Ollama (CPU GT710)
            "max_steps": 5,              # pasos maximos del loop por turno (CPU)
            "log_path": "agent_log.jsonl",
        },
    }

    def __init__(self, settings_path: str | None = None) -> None:
        if settings_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            settings_path = os.path.join(base_dir, "settings.json")
        self.settings_path = settings_path
        self._settings: dict[str, Any] = self._load()
        self._migrate()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                return json.loads(json.dumps(self.DEFAULT_SETTINGS))
        return json.loads(json.dumps(self.DEFAULT_SETTINGS))

    def _migrate(self) -> None:
        """Completa claves faltantes con valores por defecto (migracion suave)."""
        changed = False
        for key, value in self.DEFAULT_SETTINGS.items():
            if key not in self._settings:
                self._settings[key] = json.loads(json.dumps(value))
                changed = True
        for group_key, group_value in (
            ("news", self._settings["news"]),
            ("tray", self._settings["tray"]),
            ("github", self._settings["github"]),
            ("greeting", self._settings["greeting"]),
            ("agent", self._settings["agent"]),
        ):
            for key, value in self.DEFAULT_SETTINGS[group_key].items():
                if key not in group_value:
                    group_value[key] = json.loads(json.dumps(value))
                    changed = True
        if changed:
            self.save()

    def save(self) -> None:
        try:
            with open(self.settings_path, "w", encoding="utf-8") as fh:
                json.dump(self._settings, fh, indent=4, ensure_ascii=False)
        except OSError as exc:  # pragma: no cover
            print(f"[settings] No se pudo guardar settings.json: {exc}")

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    @property
    def theme(self) -> str:
        return self._settings.get("theme", "obsidiana")

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings["theme"] = value
        self.save()

    # ------------------------------------------------------------------
    # Panel de noticias
    # ------------------------------------------------------------------

    @property
    def news_enabled(self) -> bool:
        return bool(self._settings.get("news", {}).get("enabled", False))

    @news_enabled.setter
    def news_enabled(self, value: bool) -> None:
        self._settings.setdefault("news", {})["enabled"] = value
        self.save()

    @property
    def news_position(self) -> str:
        pos = self._settings.get("news", {}).get("position", "right")
        return pos if pos in ("left", "right") else "right"

    @news_position.setter
    def news_position(self, value: str) -> None:
        value = value if value in ("left", "right") else "right"
        self._settings.setdefault("news", {})["position"] = value
        self.save()

    @property
    def news_width(self) -> int:
        return int(self._settings.get("news", {}).get("width", 360))

    @news_width.setter
    def news_width(self, value: int) -> None:
        value = max(280, min(560, int(value)))
        self._settings.setdefault("news", {})["width"] = value
        self.save()

    @property
    def news_sources(self) -> list[dict[str, str]]:
        return self._settings.get("news", {}).get("sources", [])

    @news_sources.setter
    def news_sources(self, value: list[dict[str, str]]) -> None:
        self._settings.setdefault("news", {})["sources"] = list(value)
        self.save()

    @property
    def custom_url(self) -> str:
        return self._settings.get("news", {}).get("custom_url", "")

    @custom_url.setter
    def custom_url(self, value: str) -> None:
        self._settings.setdefault("news", {})["custom_url"] = value.strip()
        self.save()

    def set_news_config(
        self,
        enabled: bool | None = None,
        position: str | None = None,
        width: int | None = None,
        sources: list[dict[str, str]] | None = None,
        custom_url: str | None = None,
    ) -> None:
        """Actualiza varios valores del panel de noticias de una sola vez."""
        news = self._settings.setdefault("news", {})
        if enabled is not None:
            news["enabled"] = enabled
        if position is not None:
            news["position"] = position if position in ("left", "right") else "right"
        if width is not None:
            news["width"] = max(280, min(560, int(width)))
        if sources is not None:
            news["sources"] = list(sources)
        if custom_url is not None:
            news["custom_url"] = custom_url.strip()
        self.save()

    # ------------------------------------------------------------------
    # Bandeja del sistema
    # ------------------------------------------------------------------

    @property
    def tray_enabled(self) -> bool:
        return bool(self._settings.get("tray", {}).get("enabled", True))

    @tray_enabled.setter
    def tray_enabled(self, value: bool) -> None:
        self._settings.setdefault("tray", {})["enabled"] = bool(value)
        self.save()

    # ------------------------------------------------------------------
    # Cuenta de GitHub vinculada (para el saludo con nombre real)
    # ------------------------------------------------------------------

    @property
    def github_username(self) -> str:
        return self._settings.get("github", {}).get("username", "").strip()

    @github_username.setter
    def github_username(self, value: str) -> None:
        self._settings.setdefault("github", {})["username"] = value.strip()
        self.save()

    @property
    def github_name(self) -> str:
        return self._settings.get("github", {}).get("name", "").strip()

    @github_name.setter
    def github_name(self, value: str) -> None:
        self._settings.setdefault("github", {})["name"] = value.strip()
        self.save()

    # ------------------------------------------------------------------
    # Saludo (adjetivo rotativo por arranque)
    # ------------------------------------------------------------------

    @property
    def greeting_adjective_index(self) -> int:
        return int(self._settings.get("greeting", {}).get("adjective_index", 0))

    @greeting_adjective_index.setter
    def greeting_adjective_index(self, value: int) -> None:
        self._settings.setdefault("greeting", {})["adjective_index"] = int(value)
        self.save()

    # ------------------------------------------------------------------
    # Asistente IA local (Fase 1: Chat + Sistema)
    # ------------------------------------------------------------------

    def _agent(self, key: str, default: Any) -> Any:
        return self._settings.get("agent", {}).get(key, default)

    def _set_agent(self, key: str, value: Any) -> None:
        self._settings.setdefault("agent", {})[key] = value
        self.save()

    @property
    def agent_enabled(self) -> bool:
        return bool(self._agent("enabled", True))

    @agent_enabled.setter
    def agent_enabled(self, value: bool) -> None:
        self._set_agent("enabled", bool(value))

    @property
    def agent_url(self) -> str:
        return str(self._agent("url", "http://localhost:11434")).rstrip("/")

    @agent_url.setter
    def agent_url(self, value: str) -> None:
        self._set_agent("url", value.strip().rstrip("/") or "http://localhost:11434")

    @property
    def agent_model(self) -> str:
        return str(self._agent("model", "qwen3:1.7b")).strip() or "qwen3:1.7b"

    @agent_model.setter
    def agent_model(self, value: str) -> None:
        self._set_agent("model", value.strip() or "qwen3:1.7b")

    @property
    def agent_timeout_s(self) -> int:
        try:
            return max(10, min(600, int(self._agent("timeout_s", 180))))
        except (TypeError, ValueError):
            return 180

    @agent_timeout_s.setter
    def agent_timeout_s(self, value: int) -> None:
        self._set_agent("timeout_s", max(10, min(600, int(value))))

    @property
    def agent_max_steps(self) -> int:
        try:
            return max(1, min(20, int(self._agent("max_steps", 5))))
        except (TypeError, ValueError):
            return 5

    @agent_max_steps.setter
    def agent_max_steps(self, value: int) -> None:
        self._set_agent("max_steps", max(1, min(20, int(value))))

    @property
    def agent_log_path(self) -> str:
        return str(self._agent("log_path", "agent_log.jsonl"))

    @agent_log_path.setter
    def agent_log_path(self, value: str) -> None:
        self._set_agent("log_path", value.strip() or "agent_log.jsonl")