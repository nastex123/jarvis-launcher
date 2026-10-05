"""
core/agent/ocr_store.py - Persistencia JSON de lecturas OCR (ADR-017).

Cada `read_image`/`see_screen` con status ok se guarda append-only en
`agent_ocr.jsonl` (una linea = un JSON) y se publica un puntero
`ocr_last.json` con la ultima lectura. `run_turn` (loop) y el gateway
reinyectan las ultimas N como bloque `[OCR reciente]` para que Llama
responda preguntas sin releer la imagen. La tool `query_ocr` recupera
cualquier lectura por id. Nunca lanza excepciones ni exige Qt.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime

try:
    from zoneinfo import ZoneInfo

    _BOGOTA = ZoneInfo("America/Bogota")
except Exception:  # noqa: BLE001 - sin tzdata
    _BOGOTA = None

logger = logging.getLogger("jarvis.agent.ocr_store")

OCR_JSONL_NAME = "agent_ocr.jsonl"
OCR_LAST_NAME = "ocr_last.json"
MAX_STORE_CHARS = 20000


def _now_iso() -> str:
    now = datetime.now(_BOGOTA) if _BOGOTA else datetime.now().astimezone()
    return now.isoformat()


def _paths(repo_root: str) -> tuple[str, str]:
    base = os.path.realpath(repo_root or ".")
    return (os.path.join(base, OCR_JSONL_NAME), os.path.join(base, OCR_LAST_NAME))


def save_ocr(result: dict, repo_root: str = ".") -> dict:
    """Persiste un resultado OCR ok. Returns entry (con id/ts) o {} si no aplica."""
    try:
        if not isinstance(result, dict) or result.get("status") != "ok":
            return {}
        text = result.get("output", "")
        if not isinstance(text, str) or not text.strip() or text.startswith("(sin texto"):
            return {}
        jsonl_path, last_path = _paths(repo_root)
        entry = {
            "id": uuid.uuid4().hex[:8],
            "ts": _now_iso(),
            "source": result.get("screenshot_path") or result.get("path", ""),
            "kind": "see_screen" if result.get("screenshot_path") else "read_image",
            "engine": result.get("engine", ""),
            "lines": int(result.get("lines", 0) or 0),
            "chars": len(text),
            "truncated": len(text) >= MAX_STORE_CHARS,
            "text": text[:MAX_STORE_CHARS],
        }
        try:
            with open(jsonl_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.debug("OCR store append fallo: %s", exc)
            return {}
        try:
            with open(last_path, "w", encoding="utf-8") as fh:
                json.dump(entry, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.debug("OCR last write fallo: %s", exc)
        return entry
    except Exception:  # noqa: BLE001 - el worker nunca debe caer
        logger.exception("OCR store fallo interno")
        return {}


def _iter_entries(jsonl_path: str):
    try:
        with open(jsonl_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict) and obj.get("id"):
                    yield obj
    except OSError:
        return


def load_recent(repo_root: str = ".", n: int = 2) -> list[dict]:
    """Ultimas n entradas (mas recientes al final). Nunca lanza."""
    try:
        n = max(0, min(20, int(n)))
    except (TypeError, ValueError):
        n = 2
    if n == 0:
        return []
    jsonl_path, _ = _paths(repo_root)
    entries = list(_iter_entries(jsonl_path))
    return entries[-n:]


def load_last(repo_root: str = ".") -> dict:
    """Ultima entrada o {} (prefiere ocr_last.json, cae a la cola del jsonl)."""
    _, last_path = _paths(repo_root)
    try:
        with open(last_path, encoding="utf-8") as fh:
            obj = json.load(fh)
        if isinstance(obj, dict) and obj.get("id"):
            return obj
    except (OSError, json.JSONDecodeError):
        pass
    recent = load_recent(repo_root, 1)
    return recent[-1] if recent else {}


def get_by_id(ocr_id: str, repo_root: str = ".") -> dict:
    """Entrada por id (prefijo de 4+ chars basta) o {}."""
    needle = (ocr_id or "").strip().lower()
    if len(needle) < 4:
        return {}
    jsonl_path, _ = _paths(repo_root)
    best: dict = {}
    for obj in _iter_entries(jsonl_path):
        if str(obj.get("id", "")).lower().startswith(needle):
            best = obj
    if best:
        return best
    last = load_last(repo_root)
    if str(last.get("id", "")).lower().startswith(needle):
        return last
    return {}


def context_block(repo_root: str = ".", n: int = 2, max_chars: int = 4000) -> str:
    """Bloque `[OCR reciente]` para inyectar al historial de Llama ("" si vacio)."""
    entries = load_recent(repo_root, n)
    if not entries:
        return ""
    try:
        per = max(400, int(max_chars) // max(1, len(entries)))
    except (TypeError, ValueError):
        per = 2000
    parts = [f"[OCR reciente: {len(entries)} lectura(s) — responde usando este texto]"]
    for i, e in enumerate(entries, 1):
        text = str(e.get("text", ""))
        if len(text) > per:
            text = text[:per] + " […recorte contexto]"
        parts.append(
            f"{i}. id={e.get('id')} · {e.get('ts', '')} · "
            f"{e.get('kind', '')} {e.get('source', '')} ({e.get('lines', 0)} líneas):\n{text}"
        )
    return "\n".join(parts)
