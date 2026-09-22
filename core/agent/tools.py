"""
core/agent/tools.py - Catálogo de tools de Fase 1 (ESPEC §3.3).

9 tools: read_file, list_dir, search, write_file, edit_file, run_shell,
open_app, list_apps, get_system_info. Solo stdlib. Cada ToolSpec lleva su
JSON-schema, nivel de riesgo y plantilla de resumen en español (el resumen
lo construye código local, nunca el modelo — ADR-014 §2).
"""

from __future__ import annotations

import fnmatch
import glob
import json
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

from core.agent.policy import check_shell, ensure_backup

logger = logging.getLogger("jarvis.agent.tools")

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_WRITE_BYTES = 1 * 1024 * 1024
MAX_LIST_ENTRIES = 2000


# ----------------------------------------------------------------------
# Descriptor
# ----------------------------------------------------------------------

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    risk: str = "read"  # read | write | shell
    summary_template: str = ""


def _validate(spec: ToolSpec, args: dict) -> tuple[bool, dict, str]:
    """Valida un subconjunto de JSON-schema. Returns (ok, args_con_defaults, error)."""
    if not isinstance(args, dict):
        return False, {}, "args debe ser un objeto"
    schema = spec.parameters
    props: dict = schema.get("properties", {})
    out = dict(args)
    for req in schema.get("required", []):
        if req not in out:
            return False, {}, f"falta parámetro requerido: {req}"
    for key, value in list(out.items()):
        decl = props.get(key)
        if decl is None:
            continue  # se toleran extras (el modelo a veces añade)
        want = decl.get("type")
        if want == "string" and not isinstance(value, str):
            return False, {}, f"{key} debe ser string"
        if want == "integer" and not isinstance(value, int):
            return False, {}, f"{key} debe ser entero"
        if want == "boolean" and not isinstance(value, bool):
            return False, {}, f"{key} debe ser booleano"
    for key, decl in props.items():
        if key not in out and "default" in decl:
            out[key] = decl["default"]
        if isinstance(out.get(key), int):
            if "minimum" in decl and out[key] < decl["minimum"]:
                return False, {}, f"{key} por debajo del mínimo"
            if "maximum" in decl and out[key] > decl["maximum"]:
                return False, {}, f"{key} por encima del máximo"
    return True, out, ""


def build_summary(spec: ToolSpec, args: dict) -> str:
    """Resumen determinista en español para la tarjeta (ADR-014 §2)."""
    try:
        return spec.summary_template.format(**{k: str(v)[:160] for k, v in args.items()})
    except (KeyError, IndexError):
        return f"Ejecutar {spec.name} con {len(args)} parámetros"


# ----------------------------------------------------------------------
# Utilidades de rutas
# ----------------------------------------------------------------------

def _resolve(path: str, repo_root: str) -> str:
    """Resuelve una ruta (absoluta o relativa al repo) a absoluta real."""
    if not os.path.isabs(path):
        path = os.path.join(repo_root, path)
    return os.path.realpath(path)


def _is_binary(path: str) -> bool:
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(8192)
    except OSError:
        return False


_EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}


# ----------------------------------------------------------------------
# Ejecutores
# ----------------------------------------------------------------------

def _exec_read_file(args: dict, ctx: dict) -> dict:
    path = _resolve(args["path"], ctx["repo_root"])
    if not os.path.exists(path):
        return _err("FILE_NOT_FOUND", path)
    if not os.path.isfile(path):
        return _err("NOT_A_FILE", path)
    try:
        size = os.path.getsize(path)
    except OSError:
        return _err("PERMISSION_DENIED", path)
    if size > MAX_FILE_BYTES:
        return _err("FILE_TOO_LARGE", f"{size} bytes > 10 MB")
    if _is_binary(path):
        return _err("BINARY_FILE", path)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read(args.get("max_chars", 20000))
    except OSError as exc:
        return _err("PERMISSION_DENIED", str(exc))
    return {"status": "ok", "output": content, "path": path, "truncated": len(content) >= args.get("max_chars", 20000)}


def _exec_list_dir(args: dict, ctx: dict) -> dict:
    path = _resolve(args.get("path", "."), ctx["repo_root"])
    if not os.path.exists(path):
        return _err("DIR_NOT_FOUND", path)
    if not os.path.isdir(path):
        return _err("NOT_A_DIR", path)
    pattern = args.get("glob", "")
    entries = []
    try:
        names = sorted(os.listdir(path))
    except OSError as exc:
        return _err("PERMISSION_DENIED", str(exc))
    for name in names:
        if not pattern.startswith(".") and name.startswith("."):
            continue
        if pattern and not fnmatch.fnmatch(name, pattern):
            continue
        if name in ("__pycache__",) and not pattern:
            continue
        full = os.path.join(path, name)
        if os.path.isdir(full) and not os.path.islink(full):
            kind = "dir"
        elif os.path.islink(full):
            kind = "link"
        else:
            kind = "file"
        size = 0
        if kind == "file":
            try:
                size = os.path.getsize(full)
            except OSError:
                size = -1
        entries.append({"name": name, "type": kind, "size_bytes": size})
    entries.sort(key=lambda e: (0 if e["type"] == "dir" else 1, e["name"].lower()))
    total = len(entries)
    return {
        "status": "ok",
        "output": entries[:MAX_LIST_ENTRIES],
        "truncated": total > MAX_LIST_ENTRIES,
        "total": total,
    }


def _exec_search(args: dict, ctx: dict) -> dict:
    try:
        rx = re.compile(args["pattern"])
    except re.error as exc:
        return _err("BAD_REGEX", str(exc))
    base = _resolve(args.get("path", "."), ctx["repo_root"])
    if not os.path.exists(base):
        return _err("PATH_NOT_FOUND", base)
    file_glob = args.get("file_glob", "*.py")
    max_hits = args.get("max_hits", 50)
    hits = []
    if os.path.isfile(base):
        candidates = [base]
    else:
        candidates = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
            for fn in files:
                if fnmatch.fnmatch(fn, file_glob):
                    candidates.append(os.path.join(root, fn))
    for cand in candidates:
        if len(hits) >= max_hits:
            break
        try:
            with open(cand, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if rx.search(line):
                        hits.append({
                            "file": os.path.relpath(cand, ctx["repo_root"]),
                            "line": i,
                            "text": line.rstrip("\n")[:240],
                        })
                        if len(hits) >= max_hits:
                            break
        except OSError:
            continue
    return {"status": "ok", "output": hits, "total": len(hits)}


def _exec_write_file(args: dict, ctx: dict) -> dict:
    path = _resolve(args["path"], ctx["repo_root"])
    content = args["content"]
    if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
        return _err("CONTENT_TOO_LARGE", "> 1 MB")
    if os.path.isdir(path):
        return _err("IS_DIRECTORY", path)
    existed = os.path.exists(path)
    try:
        if existed:
            ensure_backup(path)
        else:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        return _err("PERMISSION_DENIED", str(exc))
    return {"status": "ok", "path": path, "created": not existed,
            "output": f"{'creado' if not existed else 'sobrescrito'} ({len(content.splitlines())} líneas)"}


def _exec_edit_file(args: dict, ctx: dict) -> dict:
    path = _resolve(args["path"], ctx["repo_root"])
    if not os.path.isfile(path):
        return _err("FILE_NOT_FOUND", path)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            original = fh.read()
    except OSError as exc:
        return _err("PERMISSION_DENIED", str(exc))
    old, new = args["old"], args["new"]
    count = original.count(old)
    if count == 0:
        return _err("OLD_NOT_FOUND", "el bloque no existe en el archivo")
    if count > 1:
        return _err("OLD_NOT_UNIQUE", f"{count} ocurrencias; amplía el contexto")
    try:
        ensure_backup(path)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new, 1))
    except OSError as exc:
        return _err("PERMISSION_DENIED", str(exc))
    return {"status": "ok", "path": path, "output": "reemplazo aplicado (1 ocurrencia)"}


def _exec_run_shell(args: dict, ctx: dict) -> dict:
    ok, motivo = check_shell(args["cmd"])
    if not ok:
        return {"status": "error", "error_code": "DENIED_BY_POLICY", "error_detail": motivo}
    cwd = _resolve(args.get("cwd", ctx["repo_root"]), ctx["repo_root"])
    if not os.path.isdir(cwd):
        return _err("BAD_CWD", cwd)
    timeout = args.get("timeout_s", 120)
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", GIT_TERMINAL_PROMPT="0")
    try:
        proc = subprocess.run(
            args["cmd"], shell=True,
            executable="/bin/bash" if sys.platform != "win32" else None,
            capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or "") + (exc.stderr or "")
        return {"status": "error", "error_code": "TIMEOUT",
                "error_detail": f"excedió {timeout}s (proceso terminado)",
                "partial_output": partial[-4000:]}
    except OSError as exc:
        return _err("LAUNCH_FAILED", str(exc))
    combined = f"[stdout]\n{proc.stdout}[stderr]\n{proc.stderr}".strip()
    if proc.returncode != 0:
        return {"status": "error", "error_code": "NONZERO_EXIT",
                "error_detail": f"rc={proc.returncode}", "output": combined}
    return {"status": "ok", "rc": proc.returncode, "output": combined or "(sin salida)"}


def _exec_open_app(args: dict, ctx: dict) -> dict:
    from core.launcher import AppLauncher

    launcher = AppLauncher()
    resolved = launcher._resolve_command(args["name"])
    if resolved is None:
        suggestions = _suggest_apps(args["name"])
        return {"status": "error", "error_code": "APP_NOT_FOUND",
                "error_detail": f"no se encontró '{args['name']}'",
                "suggestions": suggestions}
    ok = launcher._open_app(args["name"], "")
    return {"status": "ok" if ok else "error",
            "error_code": None if ok else "LAUNCH_FAILED",
            "launched": ok, "resolved": resolved}


def _suggest_apps(needle: str, limit: int = 5) -> list[str]:
    needle = needle.lower()
    names: list[str] = []
    if sys.platform.startswith("linux"):
        from core.platform import linux_desktop_dirs

        for d in linux_desktop_dirs():
            try:
                for entry in os.listdir(d):
                    if entry.lower().endswith(".desktop") and entry.lower().startswith(needle[:3]):
                        names.append(os.path.splitext(entry)[0])
            except OSError:
                continue
    return sorted(set(names))[:limit]


def _exec_list_apps(args: dict, ctx: dict) -> dict:
    names: list[str] = []
    if sys.platform.startswith("linux"):
        from core.platform import linux_desktop_dirs

        for d in linux_desktop_dirs():
            try:
                for entry in os.listdir(d):
                    if entry.lower().endswith(".desktop"):
                        names.append(os.path.splitext(entry)[0])
            except OSError:
                continue
    else:
        for base in (
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                         r"Microsoft\Windows\Start Menu\Programs"),
        ):
            for lnk in glob.glob(os.path.join(base, "**", "*.lnk"), recursive=True):
                names.append(os.path.splitext(os.path.basename(lnk))[0])
    names = sorted(set(names))[:500]
    return {"status": "ok", "output": names, "total": len(names)}


def _exec_system_info(args: dict, ctx: dict) -> dict:
    ram_total = ram_free = "unknown"
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            mem = dict(line.split(":") for line in fh.read().splitlines() if ":" in line)
        ram_total = f"{int(mem['MemTotal'].split()[0]) // 1024} MB"
        ram_free = f"{int(mem['MemAvailable'].split()[0]) // 1024} MB"
    except (OSError, KeyError, ValueError):
        pass
    try:
        from core.version import get_app_version

        app_version = get_app_version()
    except Exception:  # noqa: BLE001
        app_version = "unknown"
    try:
        disk_free = f"{shutil.disk_usage(ctx['repo_root']).free // (1024 ** 3)} GB"
    except OSError:
        disk_free = "unknown"
    return {
        "status": "ok",
        "output": {
            "os": f"{platform.system()} {platform.release()}",
            "session": os.environ.get("XDG_SESSION_TYPE", "?"),
            "cpu_count": os.cpu_count(),
            "ram_total": ram_total,
            "ram_free": ram_free,
            "disk_free_repo": disk_free,
            "ollama_model": ctx.get("model", "unknown"),
            "app_version": app_version,
        },
    }


def _err(code: str, detail: str) -> dict:
    return {"status": "error", "error_code": code, "error_detail": detail}


# ----------------------------------------------------------------------
# Catálogo
# ----------------------------------------------------------------------

TOOLS: list[ToolSpec] = [
    ToolSpec(
        "read_file", "Lee un archivo de texto (máx 10 MB).",
        {"type": "object",
         "properties": {"path": {"type": "string"},
                        "max_chars": {"type": "integer", "default": 20000,
                                      "minimum": 1, "maximum": 100000}},
         "required": ["path"]},
        "read", "Leer el archivo {path}"),
    ToolSpec(
        "list_dir", "Lista un directorio (máx 2000 entradas).",
        {"type": "object",
         "properties": {"path": {"type": "string", "default": "."},
                        "glob": {"type": "string", "default": ""}},
         "required": []},
        "read", "Listar el directorio {path}"),
    ToolSpec(
        "search", "Busca una regex en archivos (excluye .git/.venv/__pycache__).",
        {"type": "object",
         "properties": {"pattern": {"type": "string"},
                        "path": {"type": "string", "default": "."},
                        "file_glob": {"type": "string", "default": "*.py"},
                        "max_hits": {"type": "integer", "default": 50,
                                     "minimum": 1, "maximum": 200}},
         "required": ["pattern"]},
        "read", "Buscar «{pattern}» en {path}"),
    ToolSpec(
        "write_file", "Crea o sobrescribe un archivo (con respaldo .bak).",
        {"type": "object",
         "properties": {"path": {"type": "string"},
                        "content": {"type": "string"}},
         "required": ["path", "content"]},
        "write", "Escribir el archivo {path}"),
    ToolSpec(
        "edit_file", "Reemplaza un bloque exacto y único (con respaldo .bak).",
        {"type": "object",
         "properties": {"path": {"type": "string"}, "old": {"type": "string"},
                        "new": {"type": "string"}},
         "required": ["path", "old", "new"]},
        "write", "Editar el archivo {path}"),
    ToolSpec(
        "run_shell",
        "Ejecuta un comando bash no interactivo (timeout 120 s, lista negra). "
        "Prohibido: borrado masivo, sudo, pipe-to-shell.",
        {"type": "object",
         "properties": {"cmd": {"type": "string"},
                        "cwd": {"type": "string", "default": ""},
                        "timeout_s": {"type": "integer", "default": 120,
                                      "minimum": 1, "maximum": 600}},
         "required": ["cmd"]},
        "shell", "Ejecutar en shell: {cmd}"),
    ToolSpec(
        "open_app", "Abre una aplicación instalada por nombre (PATH/.desktop).",
        {"type": "object",
         "properties": {"name": {"type": "string"}},
         "required": ["name"]},
        "read", "Abrir la aplicación {name}"),
    ToolSpec(
        "list_apps", "Enumera aplicaciones instaladas (máx 500).",
        {"type": "object", "properties": {}, "required": []},
        "read", "Listar aplicaciones instaladas"),
    ToolSpec(
        "get_system_info", "SO, CPU, RAM, disco, modelo y versión.",
        {"type": "object", "properties": {}, "required": []},
        "read", "Consultar información del sistema"),
]

REGISTRY: dict[str, callable] = {
    "read_file": _exec_read_file,
    "list_dir": _exec_list_dir,
    "search": _exec_search,
    "write_file": _exec_write_file,
    "edit_file": _exec_edit_file,
    "run_shell": _exec_run_shell,
    "open_app": _exec_open_app,
    "list_apps": _exec_list_apps,
    "get_system_info": _exec_system_info,
}


def ollama_tools() -> list[dict]:
    """Catálogo en formato `tools` de Ollama."""
    return [
        {"type": "function", "function": {
            "name": t.name, "description": t.description,
            "parameters": t.parameters}} for t in TOOLS
    ]


def execute_tool(name: str, args: dict, ctx: dict) -> dict:
    """Valida schema y ejecuta. Nunca lanza excepciones (INTERNAL)."""
    spec = next((t for t in TOOLS if t.name == name), None)
    if spec is None:
        return _err("UNKNOWN_TOOL", name)
    ok, full_args, problem = _validate(spec, args)
    if not ok:
        return {"status": "error", "error_code": "INVALID_ARGS",
                "error_detail": problem}
    try:
        return REGISTRY[name](full_args, ctx)
    except Exception as exc:  # noqa: BLE001 - el worker nunca debe caer
        logger.exception("Fallo interno en tool %s", name)
        return {"status": "error", "error_code": "INTERNAL",
                "error_detail": f"{type(exc).__name__}: {exc}"}
