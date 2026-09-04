from dataclasses import dataclass, field
from typing import List, Set, Optional
from fastapi import HTTPException, status

# Forbidden capabilities that AI agents are permanently barred from possessing
PROHIBITED_AI_PERMISSIONS = {
    "users.delete",
    "organization.delete",
    "audit.delete",
    "payments.direct_disburse",
    "roles.manage",
    "permissions.manage"
}


@dataclass
class AIIdentity:
    """
    Controlled Security Context for AI Agents.
    The AI Agent is NEVER a superuser and cannot bypass RBAC or tenant isolation.
    """
    agent_id: str
    agent_type: str
    organization_id: str
    allowed_permissions: Set[str] = field(default_factory=set)

    def __post_init__(self):
        # Automatically strip any dangerous/prohibited permissions
        self.allowed_permissions = {p for p in self.allowed_permissions if p not in PROHIBITED_AI_PERMISSIONS}

    def has_permission(self, permission: str) -> bool:
        """Verifies explicit permission. Wildcards are NOT expanded to superuser privileges."""
        if permission in PROHIBITED_AI_PERMISSIONS:
            return False
        return permission in self.allowed_permissions

    def require_permission(self, permission: str):
        """Raises HTTP 403 if the agent attempts an action beyond its assigned mandate."""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"AI Agent '{self.agent_type}' is prohibited from executing action '{permission}'"
            )


# Default scoped permissions for specialized agents
DEFAULT_AGENT_PERMISSIONS = {
    "INTAKE": {"documents.read", "documents.upload"},
    "CLASSIFICATION": {"documents.read"},
    "EXTRACTION": {"documents.read"},
    "VALIDATION": {"documents.read", "vendors.read", "purchase_orders.read", "invoices.read"},
    "POLICY": {"policies.read", "invoices.read", "complaints.read"},
    "RISK": {"invoices.read", "vendors.read", "complaints.read"},
    "PLANNING": {"workflows.read", "approvals.read"},
    "EXECUTION": {"tools.execute", "tasks.create"},
    "COMMUNICATION": {"complaints.update", "notifications.create"},
    "SUPERVISOR": {"workflows.create", "workflows.read", "approvals.read", "approvals.create", "tasks.create"}
}


def get_agent_identity(agent_id: str, agent_type: str, organization_id: str) -> AIIdentity:
    """Instantiates a strictly-scoped AI identity for multi-agent workflows."""
    scoped_perms = DEFAULT_AGENT_PERMISSIONS.get(agent_type, set())
    return AIIdentity(
        agent_id=agent_id,
        agent_type=agent_type,
        organization_id=organization_id,
        allowed_permissions=scoped_perms
    )
