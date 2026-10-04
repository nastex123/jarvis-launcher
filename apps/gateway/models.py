"""Modelos Pydantic del contrato ESPEC-remoto v1 (solo gateway movil)."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ModeApp(BaseModel):
    name: str
    command: str
    args: str = ""


class ModeInfo(BaseModel):
    id: str
    name: str
    color: str = "#00FFFF"
    description: str = ""
    apps: list[ModeApp] = Field(default_factory=list)


class RunModeRequest(BaseModel):
    mode_id: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=8, max_length=128)


class RunModeResponse(BaseModel):
    mode_id: str
    mode_name: str
    launched: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, Any]] = Field(default_factory=list)


class ProposalCard(BaseModel):
    id: str
    tool: str
    summary: str
    risk: Literal["read", "write", "shell"] = "read"
    diff: str = ""
    args: dict[str, Any] = Field(default_factory=dict)


class DecisionRequest(BaseModel):
    proposal_id: str
    decision: Literal["approve", "reject", "edit"]
    new_args: dict[str, Any] | None = None


class PairingResponse(BaseModel):
    pairing_url: str
    token: str
    expires_in_s: int
