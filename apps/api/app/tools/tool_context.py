"""
Tool Context — Phase 8.

Immutable execution context passed to every tool handler.
The handler derives all tenant/agent information from this object.
It NEVER accepts organization_id or permissions from LLM output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass(frozen=True)
class ToolContext:
    """
    Immutable context provided by the platform to every tool execution.
    Constructed server-side; never from LLM-supplied data.
    """
    organization_id: str
    agent_run_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Who is executing (resolved server-side)
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    requested_by_type: str = "AI_AGENT"   # AI_AGENT | USER | SYSTEM

    # Permissions resolved from AIEmployee / User record — never from LLM
    permissions: tuple = field(default_factory=tuple)

    # Execution mode — controls whether mutations actually happen
    execution_mode: str = "LIVE_MOCK"   # PLAN_ONLY | DRY_RUN | LIVE_MOCK

    def has_permission(self, permission: str) -> bool:
        """Check if this context has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: list) -> bool:
        """Check if this context has at least one of the given permissions."""
        return any(p in self.permissions for p in permissions)

    def is_dry_run(self) -> bool:
        return self.execution_mode in ("PLAN_ONLY", "DRY_RUN")

    def is_plan_only(self) -> bool:
        return self.execution_mode == "PLAN_ONLY"
