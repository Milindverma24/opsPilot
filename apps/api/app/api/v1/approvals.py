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
from fastapi.responses import HTMLResponse
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


@router.get("/interactive-action", response_class=HTMLResponse)
def execute_interactive_action(
    token: str = Query(..., description="Signed 1-click action token"),
    db: Session = Depends(get_db)
):
    """
    Executes 1-click approval or rejection from Slack or external emails without requiring login.
    Cryptographically verifies the HMAC signature and time-to-live before mutation.
    """
    from apps.api.app.services.notification_service import NotificationService
    verified = NotificationService.verify_approval_action_token(token)
    if not verified:
        return HTMLResponse(
            status_code=400,
            content="""<!DOCTYPE html><html><body style="font-family:system-ui;text-align:center;padding:50px;background:#0f172a;color:#f87171;">
            <h1>❌ Invalid or Expired Approval Token</h1>
            <p>This approval link has expired or the cryptographic signature was invalid.</p>
            <a href="http://localhost:3000/approvals" style="color:#38bdf8;">Open OpsPilot Approvals Dashboard</a>
            </body></html>"""
        )

    aid = verified["aid"]
    act = verified["act"]
    org_id = verified["org"]

    approval = db.query(Approval).filter(Approval.id == aid, Approval.organization_id == org_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Find system/admin actor
    admin_user = db.query(User).filter(User.organization_id == org_id).first()

    if act == "APPROVE":
        ApprovalService.approve(aid, admin_user, "Approved via 1-Click Interactive Token", db)
        msg = f"✅ Successfully APPROVED payout for ₹{approval.amount:,.2f} ({approval.title})"
        color = "#34d399"
    else:
        ApprovalService.reject(aid, admin_user, "Rejected via 1-Click Interactive Token", db)
        msg = f"❌ Successfully REJECTED request: {approval.title}"
        color = "#f87171"

    return HTMLResponse(
        content=f"""<!DOCTYPE html><html><body style="font-family:system-ui;text-align:center;padding:50px;background:#0f172a;color:#f8fafc;">
        <h1 style="color:{color};">{msg}</h1>
        <p style="color:#94a3b8;">Cryptographic action verification succeeded. State has been committed to the immutable audit log.</p>
        <div style="margin-top:30px;">
            <a href="http://localhost:3000/approvals" style="display:inline-block;padding:10px 20px;background:#2563eb;color:#ffffff;border-radius:6px;text-decoration:none;font-weight:600;">Return to OpsPilot Console</a>
        </div>
        </body></html>"""
    )


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


@router.get("/{approval_id}/slack-card")
def get_slack_approval_card(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates Slack Block Kit payload with signed 1-click approval tokens."""
    approval = db.query(Approval).filter(
        Approval.id == approval_id,
        Approval.organization_id == current_user.organization_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    from apps.api.app.services.notification_service import NotificationService
    return NotificationService.build_slack_approval_card(approval)
