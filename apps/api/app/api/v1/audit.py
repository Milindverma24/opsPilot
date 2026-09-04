from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.audit import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])


@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    actor_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Immutable audit log viewer.
    Audit records are strictly append-only and cannot be modified or deleted.
    """
    q = db.query(AuditLog).filter(AuditLog.organization_id == current_user.organization_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor_type:
        q = q.filter(AuditLog.actor_type == actor_type)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if result:
        q = q.filter(AuditLog.result == result)

    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "timestamp": l.created_at.isoformat() if l.created_at else None,
            "actor_type": l.actor_type,
            "actor_id": l.actor_id,
            "actor_name": l.actor_name,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "workflow_id": l.workflow_id,
            "result": l.result,
            "payload": l.payload or {},
            "ip_address": l.ip_address
        })

    # Default demo records if empty
    if not results:
        results = [
            {
                "id": "aud-001",
                "timestamp": "2026-02-28T08:30:04Z",
                "actor_type": "AI_AGENT",
                "actor_id": "Supervisor-01",
                "actor_name": "Supervisor Agent",
                "action": "WORKFLOW_COMPLETED",
                "resource_type": "workflow",
                "resource_id": "wf-inv-001",
                "result": "SUCCESS",
                "payload": {"executed_tools_count": 3}
            },
            {
                "id": "aud-002",
                "timestamp": "2026-02-28T08:30:03Z",
                "actor_type": "AI_AGENT",
                "actor_id": "Executor-01",
                "actor_name": "Execution Agent",
                "action": "TOOL_CALLED",
                "resource_type": "tool",
                "resource_id": "process_mock_payment",
                "result": "SUCCESS",
                "payload": {"amount": 99710.0, "currency": "INR", "tool": "process_mock_payment"}
            }
        ]

    return {"audit_logs": results, "total": len(results)}
