"""
core/agent/ollama.py - Cliente HTTP de Ollama (solo stdlib).

Habla con POST /api/chat (formato `tools` de Ollama) y GET /api/tags.
Reintentos con backoff ante fallos de transporte; errores tipados para que
el loop distinga "demonio caído" de "modelo ausente" (ESPEC §3.9 B1/B2).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

logger = logging.getLogger("jarvis.agent.ollama")


class AgentTransportError(Exception):
    """Base de errores de transporte hacia Ollama."""


class OllamaOffline(AgentTransportError):
    """El demonio no responde tras los reintentos (ESPEC B1)."""


class OllamaTimeout(AgentTransportError):
    """Timeout agotado en una petición (ESPEC B1)."""


class ModelMissing(AgentTransportError):
    """El modelo no está descargado (ESPEC B2)."""


class OllamaClient:
    """Cliente mínimo de Ollama sin dependencias externas."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:1.7b",
        timeout_s: int = 180,
        max_retries: int = 3,
        temperature: float = 0.2,
        num_ctx: int = 4096,
        keep_alive: str = "15m",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        self.max_retries = max(1, max_retries)
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """True si el demonio responde a GET / (sin autenticación)."""
        try:
            with urllib.request.urlopen(  # noqa: S310
                f"{self.base_url}/", timeout=5
            ) as resp:
                return resp.status == 200
        except OSError as exc:
            logger.debug("ping Ollama falló: %s", exc)
            return False

    def list_models(self) -> list[str]:
        """Nombres de modelos descargados (GET /api/tags)."""
        try:
            with urllib.request.urlopen(  # noqa: S310
                f"{self.base_url}/api/tags", timeout=10
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except OSError as exc:
            raise OllamaOffline(f"No se pudo contactar {self.base_url}: {exc}")
        return [m.get("name", "") for m in data.get("models", [])]

    # ------------------------------------------------------------------
    # Chat con tools
    # ------------------------------------------------------------------

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """Envía mensajes + tools y retorna el `message` del asistente.

        Reintenta ante errores de red/timeout con backoff 1s/2s/4s.
        Lanza ModelMissing si el servidor responde 404, OllamaTimeout si
        agota el timeout en todos los intentos, OllamaOffline si no hay
        conexión.
        """
        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            }
        ).encode("utf-8")

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/api/chat",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(  # noqa: S310
                    req, timeout=self.timeout_s
                ) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("message", {})
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise ModelMissing(
                        f"El modelo '{self.model}' no está descargado. "
                        f"Ejecuta: ollama pull {self.model}"
                    )
                raise AgentTransportError(f"Ollama respondió HTTP {exc.code}")
            except TimeoutError as exc:
                last_exc = OllamaTimeout(
                    f"Ollama no respondió en {self.timeout_s}s "
                    f"(intento {attempt + 1}/{self.max_retries})"
                )
            except OSError as exc:
                last_exc = OllamaOffline(
                    f"No se pudo contactar {self.base_url}: {exc}"
                )
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # backoff 1s, 2s, 4s…

        assert last_exc is not None
        raise last_exc
