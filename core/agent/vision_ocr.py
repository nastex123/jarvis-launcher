"""
core/agent/vision_ocr.py - Lectura de imagenes con motor PaddleOCR (Fase 2 OCR).

Estrategia (ADR nueva):
- Motor preferido: `rapidocr-onnxruntime` (modelos PP-OCR via ONNX, ligero,
  funciona en Windows + Python 3.14 sin `paddlepaddle` de ~1 GB).
- Alterno: `paddleocr` clasico (PaddleOCR 3.x PP-OCRv5) si el usuario lo instala.
- Sin motor: degradado elegante con hint de instalacion (nunca crashea el worker).

Ambos exponen texto en espanol (lang es). La captura de pantalla reutiliza
QScreen.grab si PyQt6 esta disponible, si no PIL ImageGrab (Windows) con
downscale max 1600 px + JPEG q70 (PLAN-fases Fase 2).
"""

from __future__ import annotations

import logging
import os
import tempfile

logger = logging.getLogger("jarvis.agent.ocr")

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARS = 20000
MAX_SIDE_PX = 1600

_engine = None
_engine_kind = ""
_engine_error = ""


def _try_init_engine():
    """Inicializa lazy el motor OCR. Returns (engine, kind) o (None, '')."""
    global _engine, _engine_kind, _engine_error
    if _engine is not None or _engine_error:
        return _engine, _engine_kind
    # 1. RapidOCR ONNX (ligero, ya instalado en este PC).
    try:
        from rapidocr_onnxruntime import RapidOCR

        _engine = RapidOCR()
        _engine_kind = "rapidocr-onnxruntime (PP-OCR via ONNX)"
        logger.info("Motor OCR: %s", _engine_kind)
        return _engine, _engine_kind
    except Exception as exc:  # noqa: BLE001
        logger.debug("RapidOCR no disponible: %s", exc)
    # 2. PaddleOCR clasico (pesado, opcional).
    try:
        from paddleocr import PaddleOCR  # type: ignore

        _engine = PaddleOCR(lang="es", show_log=False)
        _engine_kind = "paddleocr (PP-OCRv5, lang=es)"
        logger.info("Motor OCR: %s", _engine_kind)
        return _engine, _engine_kind
    except Exception as exc:  # noqa: BLE001
        _engine_error = (
            "Sin motor OCR. Instala el ligero: pip install rapidocr-onnxruntime pillow "
            f"// o el clasico: pip install paddleocr paddlepaddle ({exc})"
        )
        logger.warning(_engine_error)
        return None, ""


def ocr_available() -> tuple[bool, str]:
    """True + nombre del motor, o False + hint de instalacion."""
    eng, kind = _try_init_engine()
    if eng is not None:
        return True, kind
    return False, _engine_error or "motor OCR ausente"


def _extract_text(result) -> tuple[str, int]:
    """Normaliza salida RapidOCR y PaddleOCR a (texto, n_lineas)."""
    lines: list[str] = []
    try:
        # RapidOCR 1.x: [ [box4, txt, conf], ... ] (+ elapse en tupla).
        # PaddleOCR 3.x: [ [[box, (txt, conf)], ...] ] por pagina.
        data = result
        if isinstance(data, tuple) and len(data) == 2 and isinstance(data[0], list):
            data = data[0]
        if not isinstance(data, list):
            return "", 0
        detections: list = []
        if data and isinstance(data[0], list):
            first = data[0]
            # Deteccion plana RapidOCR: [box, txt, conf] donde box es lista de puntos.
            if len(first) >= 2 and isinstance(first[0], list):
                detections = data
            else:
                for page in data:  # paginas PaddleOCR
                    if isinstance(page, list):
                        detections.extend(page)
                    elif page is not None:
                        detections.append(page)
        else:
            detections = data
        for det in detections:
            txt = ""
            if isinstance(det, (list, tuple)) and len(det) == 2:
                inner = det[1]
                if isinstance(inner, (list, tuple)) and inner:
                    txt = str(inner[0])
                else:
                    txt = str(inner)
            elif isinstance(det, (list, tuple)) and len(det) >= 3:
                txt = str(det[1])
            elif isinstance(det, str):
                txt = det
            txt = txt.strip()
            if txt and not txt.startswith("["):
                lines.append(txt)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Parse OCR: %s", exc)
    return "\n".join(lines), len(lines)


def ocr_image_file(path: str, repo_root: str = ".", persist: bool = True) -> dict:
    """Lee texto de una imagen local con PaddleOCR.

    Returns dict ToolResult-compatible: status ok/error + output/error_code.
    Si persist y el resultado es ok, guarda el JSON en ocr_store (ocr_id).
    Nunca lanza excepciones.
    """
    try:
        if not os.path.isabs(path):
            path = os.path.join(repo_root, path)
        real = os.path.realpath(path)
        if not os.path.exists(real):
            return {"status": "error", "error_code": "FILE_NOT_FOUND", "error_detail": real}
        if not os.path.isfile(real):
            return {"status": "error", "error_code": "NOT_A_FILE", "error_detail": real}
        ext = os.path.splitext(real)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
            return {"status": "error", "error_code": "NOT_AN_IMAGE",
                    "error_detail": f"extension {ext or '?'} no soportada (png/jpg/bmp/tiff/webp)"}
        try:
            size = os.path.getsize(real)
        except OSError as exc:
            return {"status": "error", "error_code": "PERMISSION_DENIED", "error_detail": str(exc)}
        if size > MAX_IMAGE_BYTES:
            return {"status": "error", "error_code": "FILE_TOO_LARGE",
                    "error_detail": f"{size} bytes > 20 MB"}
        eng, kind = _try_init_engine()
        if eng is None:
            return {"status": "error", "error_code": "OCR_UNAVAILABLE", "error_detail": ocr_available()[1]}
        result, _ = eng(real)
        text, n = _extract_text(result)
        if not text.strip():
            return {"status": "ok", "output": "(sin texto detectable en la imagen)",
                    "path": real, "engine": kind, "lines": 0}
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS] + "\n[…truncado]"
        out = {"status": "ok", "output": text, "path": real, "engine": kind, "lines": n}
        if persist:
            try:
                import os as _os

                from core.agent.ocr_store import OCR_LAST_NAME, save_ocr

                entry = save_ocr(out, repo_root=repo_root)
                if entry:
                    out["ocr_id"] = entry["id"]
                    out["json_path"] = _os.path.join(_os.path.realpath(repo_root), OCR_LAST_NAME)
            except Exception:  # noqa: BLE001 - persistencia nunca rompe el OCR
                logger.debug("OCR store omitido")
        return out
    except Exception as exc:  # noqa: BLE001
        logger.exception("OCR fallo interno")
        return {"status": "error", "error_code": "INTERNAL",
                "error_detail": f"{type(exc).__name__}: {exc}"}


def capture_screen(repo_root: str = ".") -> dict:
    """Captura la pantalla principal, la guarda temporal y le aplica OCR.

    Downscale max 1600 px lado mayor (PLAN-fases). Returns ToolResult con
    output=texto + screenshot_path para mostrar en UI si se quiere.
    """
    shot_path = ""
    try:
        # 1. Intento Qt (nitido, multi-monitor aware).
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QBuffer, QIODevice

            app = QApplication.instance()
            if app is not None:
                screen = app.primaryScreen()
                if screen is not None:
                    pix = screen.grabWindow(0)
                    fd, shot_path = tempfile.mkstemp(prefix="jarvis_shot_", suffix=".png")
                    os.close(fd)
                    pix.save(shot_path, "PNG")
        except Exception as exc:  # noqa: BLE001
            logger.debug("Captura Qt no disponible: %s", exc)
        # 2. Fallback Windows/macOS: PIL ImageGrab.
        if not shot_path or not os.path.exists(shot_path):
            try:
                from PIL import ImageGrab

                img = ImageGrab.grab()
                w, h = img.size
                scale = min(1.0, MAX_SIDE_PX / max(w, h))
                if scale < 1.0:
                    img = img.resize((int(w * scale), int(h * scale)))
                fd, shot_path = tempfile.mkstemp(prefix="jarvis_shot_", suffix=".png")
                os.close(fd)
                img.save(shot_path, "PNG")
            except Exception as exc:  # noqa: BLE001
                return {"status": "error", "error_code": "CAPTURE_FAILED",
                        "error_detail": f"sin QScreen ni ImageGrab: {exc}"}
        res = ocr_image_file(shot_path, repo_root=repo_root, persist=False)
        res["screenshot_path"] = shot_path
        if res.get("status") == "ok":
            try:
                import os as _os

                from core.agent.ocr_store import OCR_LAST_NAME, save_ocr

                entry = save_ocr(res, repo_root=repo_root)
                if entry:
                    res["ocr_id"] = entry["id"]
                    res["json_path"] = _os.path.join(_os.path.realpath(repo_root), OCR_LAST_NAME)
            except Exception:  # noqa: BLE001 - persistencia nunca rompe la captura
                logger.debug("OCR store omitido")
        return res
    except Exception as exc:  # noqa: BLE001
        logger.exception("Captura fallo interno")
        return {"status": "error", "error_code": "INTERNAL",
                "error_detail": f"{type(exc).__name__}: {exc}"}
