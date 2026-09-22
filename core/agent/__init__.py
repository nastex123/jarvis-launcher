"""
core/agent - Subsistema del asistente IA local (Fase 1: Chat + Sistema).

Contrato normativo: docs/ESPEC-agente-fase1.md.
Decisiones: docs/ADR-013 (motor Ollama) y docs/ADR-014 (confirmar-todo).
"""

from core.agent.loop import AGENT_SYS_V1, AGENT_SYS_V2, AGENT_SYS_V3, MAX_STEPS, AgentWorker, run_turn
from core.agent.ollama import (
    AgentTransportError,
    ModelMissing,
    OllamaClient,
    OllamaOffline,
    OllamaTimeout,
)
from core.agent.policy import Proposal, check_shell, redact
from core.agent.tools import REGISTRY, TOOLS, ToolSpec, execute_tool, ollama_tools

__all__ = [
    "AGENT_SYS_V1",
    "AGENT_SYS_V2",
    "AGENT_SYS_V3",
    "MAX_STEPS",
    "AgentTransportError",
    "AgentWorker",
    "ModelMissing",
    "OllamaClient",
    "OllamaOffline",
    "OllamaTimeout",
    "Proposal",
    "REGISTRY",
    "TOOLS",
    "ToolSpec",
    "check_shell",
    "execute_tool",
    "ollama_tools",
    "redact",
    "run_turn",
]
