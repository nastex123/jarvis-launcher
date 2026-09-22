"""
core/agent/policy.py - Política de seguridad del agente (ADR-014).

- DENY_PATTERNS: lista negra dura de shell (no aprobable ni por el usuario).
- SECRET_PATTERNS: enmascarado antes de devolver datos al modelo.
- Proposal: propuesta de tool_call para la tarjeta de aprobación.
- check_shell / redact / ensure_backup: primitivas del ejecutor y la UI.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.agent.policy")

# ----------------------------------------------------------------------
# Lista negra de shell: (nombre, regex, motivo). Ampliable solo con ADR.
# Se evalúa por segmentos separados por ; && || | (ver check_shell).
# ----------------------------------------------------------------------

DENY_PATTERNS: list[tuple[str, str, str]] = [
    (
        "rm_recursivo_absoluto",
        r"(^|[\s;])rm\s+.*-[a-z]*r[a-z]*.*\s+(/\s*$|/\*|~\s*$|\$HOME\s*$|%USERPROFILE%)",
        "Borrado recursivo sobre raíz/home",
    ),
    (
        "rm_rf_root",
        r"(^|[\s;])rm\s+-+[^;\s]*r[^;\s]*\s+/",
        "rm recursivo sobre /",
    ),
    (
        "rm_home",
        r"(^|[\s;])rm\s+-[a-z]*r[a-z]*\s+(~|\$HOME)(/|\s|$)",
        "rm recursivo sobre el home",
    ),
    ("mkfs", r"(^|[\s;])mkfs(\.|$|\s)", "Formateo de filesystem"),
    (
        "dd_a_dispositivo",
        r"(^|[\s;])dd\b.*\bof=/dev/",
        "Escritura directa a dispositivo",
    ),
    (
        "redirect_a_dispositivo",
        r">\s*/dev/(sd|hd|nvme|vd|mmcblk|loop|dm-)",
        "Redirección a disco",
    ),
    ("shred", r"(^|[\s;])(shred|wipefs)\b", "Borrado seguro de disco"),
    (
        "fork_bomb",
        r":\(\)\s*\{\s*:?\s*\|\s*:?\s*&\s*;?\s*\};?:?",
        "Fork-bomb",
    ),
    (
        "chmod_root",
        r"(^|[\s;])chmod\s+(-R\s+)?777\s+/\s*$",
        "Permisos abiertos sobre /",
    ),
    (
        "pipe_to_shell",
        r"(curl|wget)\b.*\|\s*(sh|bash|sudo)",
        "Pipe-to-shell (ejecución remota)",
    ),
    (
        "escalado",
        r"(^|[\s;])sudo\s+(su|-|-i|s)\b",
        "Escalado a root interactivo",
    ),
    (
        "cuentas",
        r"(^|[\s;])(passwd|usermod|userdel|visudo)\b",
        "Gestión de cuentas del sistema",
    ),
]

_COMPILED_DENY: list[tuple[str, re.Pattern, str]] = [
    (name, re.compile(rx), reason) for name, rx, reason in DENY_PATTERNS
]

# Separadores para evaluar cada segmento del comando por separado.
_SEGMENT_SPLIT = re.compile(r"(?:;|&&|\|\||\|)(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")

# ----------------------------------------------------------------------
# Secretos a enmascarar antes de devolver outputs al modelo.
# ----------------------------------------------------------------------

SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*\S+"),
]

REDACTED = "***REDACTED***"


@dataclass
class Proposal:
    """Propuesta de tool_call para la tarjeta de aprobación (ADR-014 §2)."""

    id: str
    tool: str
    args: dict
    summary: str
    risk: str = "read"  # read | write | shell
    diff: str = ""  # diff unificado si aplica (write/edit)
    extra: dict = field(default_factory=dict)


def check_shell(cmd: str) -> tuple[bool, str]:
    """Evalúa un comando contra la lista negra.

    Returns (permitida, motivo). Si no está permitida, el motivo nombra la
    regla violada y el ejecutor debe rehusar con DENIED_BY_POLICY.
    """
    segments = [s.strip() for s in _SEGMENT_SPLIT.split(cmd) if s.strip()]
    # Se evalúa el comando completo ADEMÁS de cada segmento: el particionado
    # por | ; && puede romper patrones multi-carácter (p. ej. fork-bomb).
    candidates = [cmd] + segments if segments else [cmd]
    for text in candidates:
        for name, rx, reason in _COMPILED_DENY:
            if rx.search(text):
                logger.warning("Shell bloqueado por %s: %s", name, text[:120])
                return False, f"{reason} (regla {name})"
    return True, ""


def redact(text: str) -> str:
    """Enmascara secretos en un texto antes de devolverlo al modelo."""
    for rx in SECRET_PATTERNS:
        text = rx.sub(REDACTED, text)
    return text


def ensure_backup(path: str) -> str | None:
    """Crea copia path.bak (1 generación) si el archivo existe.

    Returns la ruta del backup o None si no había nada que respaldar.
    """
    if not os.path.isfile(path):
        return None
    backup = path + ".bak"
    try:
        shutil.copy2(path, backup)
        logger.info("Backup creado: %s", backup)
        return backup
    except OSError as exc:
        logger.error("No se pudo crear backup de %s: %s", path, exc)
        raise
