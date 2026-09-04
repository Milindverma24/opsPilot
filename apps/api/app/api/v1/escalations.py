"""
Escalations API Endpoints — Phase 10.

Endpoints:
- GET    /api/v1/escalations
- GET    /api/v1/escalations/{id}
- POST   /api/v1/escalations/{id}/acknowledge
- POST   /api/v1/escalations/{id}/resolve
- POST   /api/v1/escalations/{id}/escalate
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.workflow import Escalation
from apps.api.app.approvals.escalation_service import EscalationService

router = APIRouter(prefix="/escalations", tags=["Escalation Center"])


class EscalationResolveRequest(BaseModel):
    resolution: str


class EscalationCreateRequest(BaseModel):
    reason: str
    level: str = "LEVEL_1"
    severity: str = "HIGH"
    workflow_run_id: Optional[str] = None
    assigned_team: Optional[str] = None


@router.get("")
def list_escalations(
    status: Optional[str] = None,
    level: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Escalation).filter(Escalation.organization_id == current_user.organization_id)
    if status:
        q = q.filter(Escalation.status == status)
    if level:
        q = q.filter(Escalation.level == level)
    if severity:
        q = q.filter(Escalation.severity == severity)

    escs = q.order_by(Escalation.created_at.desc()).limit(limit).all()
    results = []
    for e in escs:
        results.append({
            "id": e.id,
            "level": e.level,
            "severity": e.severity,
            "status": e.status,
            "reason": e.reason,
            "assigned_team": e.assigned_team,
            "assigned_to": e.assigned_to,
            "assigned_user_name": e.assigned_user.full_name if e.assigned_user else None,
            "workflow_run_id": e.workflow_run_id,
            "approval_id": e.approval_id,
            "due_at": e.due_at.isoformat() if e.due_at else None,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            "resolution": e.resolution,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })

    return {"escalations": results, "total": len(results)}


@router.post("")
def create_escalation(
    payload: EscalationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    esc = EscalationService.create_escalation(
        db=db,
        organization_id=current_user.organization_id,
        reason=payload.reason,
        level=payload.level,
        severity=payload.severity,
        workflow_run_id=payload.workflow_run_id,
        assigned_team=payload.assigned_team,
    )
    return {
        "id": esc.id,
        "level": esc.level,
        "severity": esc.severity,
        "status": esc.status,
        "due_at": esc.due_at.isoformat() if esc.due_at else None,
    }


@router.get("/{escalation_id}")
def get_escalation_detail(
    escalation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    e = db.query(Escalation).filter(
        Escalation.id == escalation_id,
        Escalation.organization_id == current_user.organization_id,
    ).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")

    return {
        "id": e.id,
        "level": e.level,
        "severity": e.severity,
        "status": e.status,
        "reason": e.reason,
        "assigned_team": e.assigned_team,
        "assigned_to": e.assigned_to,
        "assigned_user_name": e.assigned_user.full_name if e.assigned_user else None,
        "workflow_run_id": e.workflow_run_id,
        "approval_id": e.approval_id,
        "due_at": e.due_at.isoformat() if e.due_at else None,
        "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
        "resolution": e.resolution,
        "metadata": e.metadata_,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.post("/{escalation_id}/acknowledge")
def acknowledge_escalation(
    escalation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        esc = EscalationService.acknowledge_escalation(db, escalation_id, current_user)
        return {"id": esc.id, "status": esc.status, "assigned_to": esc.assigned_to}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{escalation_id}/resolve")
def resolve_escalation(
    escalation_id: str,
    payload: EscalationResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        esc = EscalationService.resolve_escalation(db, escalation_id, current_user, payload.resolution)
        return {"id": esc.id, "status": esc.status, "resolved_at": esc.resolved_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{escalation_id}/escalate")
def escalate_to_next_level(
    escalation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    e = db.query(Escalation).filter(
        Escalation.id == escalation_id,
        Escalation.organization_id == current_user.organization_id,
    ).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")

    esc = EscalationService.escalate_next_level(db, e, reason=f"Manual escalation by {current_user.full_name}")
    return {
        "id": esc.id,
        "level": esc.level,
        "assigned_team": esc.assigned_team,
        "due_at": esc.due_at.isoformat() if esc.due_at else None,
    }
