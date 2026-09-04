"""
Approval Service — Phase 10.

Enterprise Human-in-the-Loop Governance:
1. Approver authorization & RBAC (ApprovalAuthorizationService)
2. Cryptographic payload integrity verification (SHA-256 action_payload_hash)
3. Separation of duties (Requester cannot approve, AI cannot self-approve)
4. Multi-level approvals (ONE_APPROVER, ALL_REQUIRED, ANY_ONE)
5. Pre-execution revalidation
6. Safe workflow run resumption
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import Approval, ApprovalComment, Workflow, WorkflowRun, WorkflowStepRun
from apps.api.app.models.tenant import User
from apps.api.app.models.audit import AuditLog, Notification
from apps.api.app.approvals.authorization_service import ApprovalAuthorizationService


def compute_payload_hash(action_type: str, payload: Dict[str, Any]) -> str:
    """Deterministic cryptographic hash for action payload integrity."""
    raw = json.dumps({"action": action_type, "payload": payload or {}}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class ApprovalService:
    """Manages approval lifecycle, authorizations, and secure workflow resumption."""

    @classmethod
    def get_pending_approvals(cls, organization_id: str, db: Session) -> List[Approval]:
        return db.query(Approval).filter(
            Approval.organization_id == organization_id,
            Approval.status == "PENDING",
        ).order_by(Approval.created_at.desc()).all()

    @classmethod
    def approve(
        cls,
        approval_id: str,
        current_user: User,
        comment: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Grants human approval with strict security gates:
        1. Tenant check
        2. Approver eligibility and separation of duties
        3. Expiration verification
        4. SHA-256 payload integrity check
        5. Multi-level approval resolution
        6. Workflow resumption
        """
        approval = db.query(Approval).filter(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        ).first()

        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval request is already {approval.status}",
            )

        # 1. Expiration check
        now = get_utc_now()
        exp = approval.expires_at
        if exp:
            if exp.tzinfo is None and now.tzinfo is not None:
                exp = exp.replace(tzinfo=timezone.utc)
            elif exp.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            if exp <= now:
                approval.status = "EXPIRED"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Approval request has expired and cannot be approved",
                )

        # 2. Authorization & Separation of Duties check
        is_auth, auth_reason = ApprovalAuthorizationService.can_user_approve(current_user, approval)
        if not is_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=auth_reason,
            )

        # 3. Cryptographic Payload Hash Integrity check
        if approval.action_payload_hash:
            computed_hash = compute_payload_hash(approval.action_type or "", approval.action_payload or {})
            if computed_hash != approval.action_payload_hash:
                # Payload was tampered with!
                approval.status = "CANCELLED"
                # Audit security alert and log SecurityEvent
                try:
                    from apps.api.app.models.security import SecurityEvent
                    sec_event = SecurityEvent(
                        organization_id=current_user.organization_id,
                        event_type="APPROVAL_HASH_MISMATCH",
                        severity="CRITICAL",
                        actor_id=current_user.id,
                        actor_type="USER",
                        details={"approval_id": approval.id, "reason": "Action payload hash mismatch. Potential tampering detected."}
                    )
                    db.add(sec_event)
                except Exception:
                    pass
                db.commit()
                cls._log_audit(
                    db, current_user.organization_id, current_user.id, "USER",
                    "APPROVAL_TAMPERING_BLOCKED", approval.id,
                    {"reason": "Action payload hash mismatch. Potential tampering detected."},
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security violation: Action payload hash mismatch. Operation blocked.",
                )

        # 4. Multi-level approval handling
        user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role or "MANAGER")
        approval_signature = {
            "user_id": current_user.id,
            "user_name": current_user.full_name,
            "role": user_role,
            "approved_at": now.isoformat(),
            "comment": comment or "",
        }

        existing_signatures = list(approval.approvals_received or [])
        existing_signatures.append(approval_signature)
        approval.approvals_received = existing_signatures

        # Check multi-level threshold
        mode = approval.approval_mode or "ONE_APPROVER"
        is_fully_approved = True

        if mode == "ALL_REQUIRED":
            required_roles = approval.required_roles or ["MANAGER"]
            signed_roles = [sig["role"].upper() for sig in existing_signatures]
            for req in required_roles:
                if not any(req.upper() in r for r in signed_roles):
                    is_fully_approved = False
                    break

        if is_fully_approved:
            approval.status = "APPROVED"
            approval.approved_by = current_user.id
            approval.approved_at = now
            approval.decision_reason = comment or "Approved by reviewer"

        db.commit()

        # Add comment record if provided
        if comment:
            cls.add_comment(db, approval.id, current_user.organization_id, current_user.id, comment)

        # Audit log
        cls._log_audit(
            db=db,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            actor_type="USER",
            action="APPROVED" if is_fully_approved else "APPROVAL_PARTIAL_SIGNATURE",
            resource_id=approval.id,
            workflow_id=approval.workflow_id,
            payload={
                "fully_approved": is_fully_approved,
                "role": user_role,
                "comment": comment,
                "amount": approval.amount,
            },
        )

        # 5. Resume workflow if fully approved
        resumed_run = None
        if is_fully_approved:
            resumed_run = cls._resume_associated_workflow(db, approval)

        if approval.workflow_id and not approval.workflow_run_id and resumed_run is not None:
            return resumed_run

        return {
            "status": approval.status,
            "approval_id": approval.id,
            "fully_approved": is_fully_approved,
            "workflow_run_id": approval.workflow_run_id,
            "message": "Approval granted successfully" if is_fully_approved else "Partial signature recorded. Awaiting remaining approvers.",
        }

    @classmethod
    def reject(
        cls,
        approval_id: str,
        current_user: User,
        reason: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Rejects approval request with mandatory reason and marks workflow.
        """
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is mandatory",
            )

        approval = db.query(Approval).filter(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        ).first()

        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval request is already {approval.status}",
            )

        is_auth, auth_reason = ApprovalAuthorizationService.can_user_approve(current_user, approval)
        if not is_auth:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=auth_reason)

        now = get_utc_now()
        approval.status = "REJECTED"
        approval.rejected_by = current_user.id
        approval.rejected_at = now
        approval.rejection_reason = reason
        approval.decision_reason = reason
        db.commit()

        cls.add_comment(db, approval.id, current_user.organization_id, current_user.id, f"Rejected: {reason}")

        cls._log_audit(
            db=db,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            actor_type="USER",
            action="APPROVAL_REJECTED",
            resource_id=approval.id,
            workflow_id=approval.workflow_id,
            payload={"rejection_reason": reason, "amount": approval.amount},
        )

        # Notify requester
        notif = Notification(
            organization_id=current_user.organization_id,
            title=f"Request Rejected: {approval.title}",
            message=f"Rejected by {current_user.full_name}. Reason: {reason}",
            notification_type="DANGER",
            link="/approvals",
        )
        db.add(notif)
        db.commit()

        # Update WorkflowRun or legacy Workflow
        if approval.workflow_run_id:
            from apps.api.app.workflows.state_manager import WorkflowStateManager
            from apps.api.app.workflows.runner import WorkflowRunner

            run = db.query(WorkflowRun).filter(WorkflowRun.id == approval.workflow_run_id).first()
            if run:
                WorkflowStateManager.transition_run(
                    db, run, "CANCELLED", reason=f"Approval rejected: {reason}"
                )
        elif approval.workflow_id:
            wf = db.query(Workflow).filter(Workflow.id == approval.workflow_id).first()
            if wf:
                wf.status = "CANCELLED"
                wf.error = f"Rejected by {current_user.full_name}: {reason}"
                db.commit()

        return {
            "status": "REJECTED",
            "approval_id": approval.id,
            "rejection_reason": reason,
        }

    @classmethod
    def cancel(cls, approval_id: str, current_user: User, db: Session) -> Dict[str, Any]:
        approval = db.query(Approval).filter(
            Approval.id == approval_id,
            Approval.organization_id == current_user.organization_id,
        ).first()
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

        approval.status = "CANCELLED"
        approval.cancelled_at = get_utc_now()
        db.commit()

        cls._log_audit(
            db, current_user.organization_id, current_user.id, "USER",
            "APPROVAL_CANCELLED", approval.id, {}
        )
        return {"status": "CANCELLED", "approval_id": approval.id}

    @classmethod
    def add_comment(
        cls,
        db: Session,
        approval_id: str,
        organization_id: str,
        user_id: str,
        comment_text: str,
    ) -> ApprovalComment:
        comm = ApprovalComment(
            approval_id=approval_id,
            organization_id=organization_id,
            user_id=user_id,
            comment=comment_text,
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)
        return comm

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    @classmethod
    def _resume_associated_workflow(cls, db: Session, approval: Approval) -> Optional[WorkflowRun]:
        """Resumes active workflow run after human approval."""
        if approval.workflow_run_id:
            from apps.api.app.workflows.runner import WorkflowRunner
            from apps.api.app.workflows.state_manager import WorkflowStateManager

            run = db.query(WorkflowRun).filter(WorkflowRun.id == approval.workflow_run_id).first()
            if run and run.status == "WAITING_FOR_APPROVAL":
                # Advance step order past the approval step
                run.current_step_order = (run.current_step_order or 1) + 1
                WorkflowStateManager.transition_run(db, run, "RUNNING", reason="Approved by human reviewer")
                runner = WorkflowRunner(db)
                return runner.execute_run(run)

        elif approval.workflow_id:
            # Legacy WorkflowEngine execution
            from apps.api.app.workflows.engine import WorkflowEngine
            wf = db.query(Workflow).filter(Workflow.id == approval.workflow_id).first()
            if wf and wf.status == "WAITING_APPROVAL":
                engine = WorkflowEngine(db)
                return engine.execute_approved_actions(wf, is_approved=True)

        return None

    @classmethod
    def _log_audit(
        cls,
        db: Session,
        organization_id: str,
        actor_id: str,
        actor_type: str,
        action: str,
        resource_id: str,
        payload: Dict[str, Any],
        workflow_id: Optional[str] = None,
    ) -> None:
        try:
            log = AuditLog(
                organization_id=organization_id,
                actor_id=actor_id,
                actor_type=actor_type,
                actor_name=f"User-{actor_id}" if actor_type == "USER" else "System",
                action=action,
                resource_type="approval",
                resource_id=resource_id,
                workflow_id=workflow_id,
                result="SUCCESS" if "REJECT" not in action and "BLOCKED" not in action else "FAILURE",
                payload=payload,
            )
            db.add(log)
            db.commit()
        except Exception:
            pass
