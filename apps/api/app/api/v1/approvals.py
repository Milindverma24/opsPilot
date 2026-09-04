"""
Approvals API Endpoints — Phase 10.

Endpoints:
- GET    /api/v1/approvals
- GET    /api/v1/approvals/pending
- GET    /api/v1/approvals/{id}
- POST   /api/v1/approvals/{id}/approve
- POST   /api/v1/approvals/{id}/reject
- POST   /api/v1/approvals/{id}/cancel
- POST   /api/v1/approvals/{id}/comments
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.workflow import Approval, ApprovalComment
from apps.api.app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approval Center"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ApprovalActionRequest(BaseModel):
    comment: Optional[str] = None
    reason: Optional[str] = None  # required for reject


class ApprovalCommentRequest(BaseModel):
    comment: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_approvals(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    approval_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Approval).filter(Approval.organization_id == current_user.organization_id)
    if status:
        q = q.filter(Approval.status == status)
    if risk_level:
        q = q.filter(Approval.risk_level == risk_level)
    if approval_type:
        q = q.filter(Approval.approval_type == approval_type)

    approvals = q.order_by(Approval.created_at.desc()).limit(limit).all()
    results = []
    for a in approvals:
        results.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "workflow_id": a.workflow_id,
            "workflow_run_id": a.workflow_run_id,
            "approval_type": a.approval_type or a.request_type,
            "risk_level": a.risk_level,
            "status": a.status,
            "amount": a.amount,
            "currency": a.currency,
            "reason": a.reason,
            "requested_by": a.requested_by,
            "requested_by_type": a.requested_by_type,
            "approval_mode": a.approval_mode,
            "required_roles": a.required_roles,
            "approvals_received": a.approvals_received,
            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "approved_at": a.approved_at.isoformat() if a.approved_at else None,
            "rejected_at": a.rejected_at.isoformat() if a.rejected_at else None,
            "rejection_reason": a.rejection_reason,
            # Legacy compatibility
            "request_type": a.approval_type or a.request_type,
            "requester_name": a.requested_by,
            "ai_recommendation": a.ai_recommendation,
            "affected_entity_type": a.affected_entity_type,
            "affected_entity_id": a.affected_entity_id,
            "decided_at": a.approved_at.isoformat() if a.approved_at else None,
        })

    return {"approvals": results, "total": len(results)}


@router.get("/pending")
def list_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_approvals(status="PENDING", current_user=current_user, db=db)


@router.get("/{approval_id}")
def get_approval_detail(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.query(Approval).filter(
        Approval.id == approval_id,
        Approval.organization_id == current_user.organization_id,
    ).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    comments_data = []
    for c in a.comments:
        comments_data.append({
            "id": c.id,
            "user_id": c.user_id,
            "user_name": c.user.full_name if c.user else "User",
            "comment": c.comment,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "workflow_id": a.workflow_id,
        "workflow_run_id": a.workflow_run_id,
        "approval_type": a.approval_type or a.request_type,
        "risk_level": a.risk_level,
        "status": a.status,
        "reason": a.reason,
        "amount": a.amount,
        "currency": a.currency,
        "action_type": a.action_type,
        "action_payload": a.action_payload,
        "action_payload_hash": a.action_payload_hash,
        "policy_snapshot": a.policy_snapshot,
        "risk_snapshot": a.risk_snapshot,
        "approval_mode": a.approval_mode,
        "required_roles": a.required_roles,
        "approvals_received": a.approvals_received,
        "requested_by": a.requested_by,
        "requested_by_type": a.requested_by_type,
        "expires_at": a.expires_at.isoformat() if a.expires_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "approved_at": a.approved_at.isoformat() if a.approved_at else None,
        "rejected_at": a.rejected_at.isoformat() if a.rejected_at else None,
        "rejection_reason": a.rejection_reason,
        "decision_reason": a.decision_reason,
        "comments": comments_data,
        # Legacy compatibility
        "request_type": a.approval_type or a.request_type,
        "requester_name": a.requested_by,
        "ai_recommendation": a.ai_recommendation,
        "affected_entity_type": a.affected_entity_type,
        "affected_entity_id": a.affected_entity_id,
        "decided_at": a.approved_at.isoformat() if a.approved_at else None,
    }


@router.post("/{approval_id}/approve")
def approve_request(
    approval_id: str,
    payload: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService.approve(approval_id, current_user, payload.comment, db)
    return result


@router.post("/{approval_id}/reject")
def reject_request(
    approval_id: str,
    payload: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reason = payload.reason or payload.comment or "Rejected by reviewer"
    result = ApprovalService.reject(approval_id, current_user, reason, db)
    return result


@router.post("/{approval_id}/cancel")
def cancel_request(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService.cancel(approval_id, current_user, db)
    return result


@router.post("/{approval_id}/comments")
def add_approval_comment(
    approval_id: str,
    payload: ApprovalCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.comment or not payload.comment.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment cannot be empty")

    comm = ApprovalService.add_comment(
        db, approval_id, current_user.organization_id, current_user.id, payload.comment
    )
    return {
        "id": comm.id,
        "approval_id": approval_id,
        "user_id": comm.user_id,
        "comment": comm.comment,
        "created_at": comm.created_at.isoformat() if comm.created_at else None,
    }
