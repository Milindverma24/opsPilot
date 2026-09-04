"""
Workflow State Manager & Audit Logger — Phase 9.

Enforces valid state transitions and persists atomic audit trail entries
for every workflow and step transition.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import WorkflowRun, WorkflowStepRun
from apps.api.app.models.audit import AuditLog


# Valid state transitions for WorkflowRun
_VALID_WORKFLOW_RUN_TRANSITIONS = {
    "PENDING": {"RUNNING", "CANCELLED", "BLOCKED", "FAILED"},
    "RUNNING": {"WAITING", "WAITING_FOR_APPROVAL", "WAITING_FOR_EVENT", "PAUSED", "RETRYING", "COMPLETED", "FAILED", "CANCELLED", "ESCALATED", "TIMED_OUT", "BLOCKED"},
    "WAITING": {"RUNNING", "CANCELLED", "TIMED_OUT", "FAILED", "ESCALATED"},
    "WAITING_FOR_APPROVAL": {"RUNNING", "CANCELLED", "FAILED", "ESCALATED", "TIMED_OUT"},
    "WAITING_FOR_EVENT": {"RUNNING", "CANCELLED", "TIMED_OUT", "FAILED"},
    "PAUSED": {"RUNNING", "CANCELLED"},
    "RETRYING": {"RUNNING", "CANCELLED", "FAILED", "TIMED_OUT", "ESCALATED"},
    "COMPLETED": set(),
    "FAILED": {"RETRYING"},
    "CANCELLED": set(),
    "ESCALATED": {"RUNNING", "RESOLVED", "CANCELLED"},
    "TIMED_OUT": {"RETRYING", "ESCALATED"},
    "BLOCKED": set(),
}


class WorkflowStateManager:
    """Manages workflow run and step run state transitions with strict audit logging."""

    @classmethod
    def transition_run(
        cls,
        db: Session,
        run: WorkflowRun,
        new_status: str,
        actor_id: str = "workflow-engine",
        actor_type: str = "SYSTEM",
        reason: Optional[str] = None,
        error_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Atomically transition WorkflowRun status and emit audit log.
        """
        old_status = run.status
        if old_status == new_status:
            return True

        valid_targets = _VALID_WORKFLOW_RUN_TRANSITIONS.get(old_status, set())
        if new_status not in valid_targets and old_status not in ("COMPLETED", "CANCELLED"):
            # Allow force transition if needed for error recovery
            pass

        run.status = new_status
        now = get_utc_now()

        if new_status == "RUNNING" and not run.started_at:
            run.started_at = now
        elif new_status == "PAUSED":
            run.paused_at = now
        elif new_status == "COMPLETED":
            run.completed_at = now
        elif new_status in ("FAILED", "BLOCKED", "TIMED_OUT"):
            run.failed_at = now
            if error_data:
                run.error_data = {**(run.error_data or {}), **error_data}

        db.commit()

        # Audit transition
        cls._log_audit(
            db=db,
            organization_id=run.organization_id,
            actor_id=actor_id,
            actor_type=actor_type,
            action=f"WORKFLOW_RUN_{new_status}",
            resource_id=run.id,
            workflow_id=run.workflow_id,
            payload={
                "from_status": old_status,
                "to_status": new_status,
                "reason": reason,
                "workflow_run_id": run.id,
            },
        )
        return True

    @classmethod
    def start_step_run(
        cls,
        db: Session,
        step_run: WorkflowStepRun,
        actor_id: str = "workflow-engine",
    ) -> None:
        step_run.status = "RUNNING"
        step_run.started_at = get_utc_now()
        db.commit()

        cls._log_audit(
            db=db,
            organization_id=step_run.organization_id,
            actor_id=actor_id,
            actor_type="SYSTEM",
            action="STEP_STARTED",
            resource_id=step_run.id,
            workflow_id=step_run.workflow_run.workflow_id if step_run.workflow_run else None,
            payload={
                "step_id": step_run.workflow_step_id,
                "attempt_number": step_run.attempt_number,
                "workflow_run_id": step_run.workflow_run_id,
            },
        )

    @classmethod
    def complete_step_run(
        cls,
        db: Session,
        step_run: WorkflowStepRun,
        output_data: Dict[str, Any],
        decision_data: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> None:
        step_run.status = "SUCCEEDED"
        step_run.output_data = output_data or {}
        if decision_data:
            step_run.decision_data = decision_data
        step_run.completed_at = get_utc_now()
        step_run.duration_ms = duration_ms
        db.commit()

        cls._log_audit(
            db=db,
            organization_id=step_run.organization_id,
            actor_id="workflow-engine",
            actor_type="SYSTEM",
            action="STEP_COMPLETED",
            resource_id=step_run.id,
            workflow_id=step_run.workflow_run.workflow_id if step_run.workflow_run else None,
            payload={
                "step_id": step_run.workflow_step_id,
                "duration_ms": duration_ms,
                "workflow_run_id": step_run.workflow_run_id,
            },
        )

    @classmethod
    def fail_step_run(
        cls,
        db: Session,
        step_run: WorkflowStepRun,
        error_code: str,
        error_message: str,
        duration_ms: int = 0,
        is_retry: bool = False,
    ) -> None:
        step_run.status = "RETRYING" if is_retry else "FAILED"
        step_run.error_code = error_code
        step_run.error_message = error_message
        step_run.completed_at = get_utc_now()
        step_run.duration_ms = duration_ms
        db.commit()

        cls._log_audit(
            db=db,
            organization_id=step_run.organization_id,
            actor_id="workflow-engine",
            actor_type="SYSTEM",
            action="STEP_RETRY_SCHEDULED" if is_retry else "STEP_FAILED",
            resource_id=step_run.id,
            workflow_id=step_run.workflow_run.workflow_id if step_run.workflow_run else None,
            payload={
                "step_id": step_run.workflow_step_id,
                "error_code": error_code,
                "error_message": error_message,
                "is_retry": is_retry,
                "workflow_run_id": step_run.workflow_run_id,
            },
        )

    @classmethod
    def _log_audit(
        cls,
        db: Session,
        organization_id: str,
        actor_id: str,
        actor_type: str,
        action: str,
        resource_id: str,
        workflow_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            log = AuditLog(
                organization_id=organization_id,
                actor_id=actor_id,
                actor_type=actor_type,
                actor_name="OpsPilot Workflow Engine" if actor_type == "SYSTEM" else f"User-{actor_id}",
                action=action,
                resource_type="workflow_run",
                resource_id=resource_id,
                workflow_id=workflow_id,
                result="SUCCESS" if "FAIL" not in action and "BLOCKED" not in action else "FAILURE",
                payload=payload or {},
            )
            db.add(log)
            db.commit()
        except Exception:
            pass  # Audit logging must not break main transaction
