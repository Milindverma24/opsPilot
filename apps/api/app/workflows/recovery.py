"""
Workflow Recovery Service — Phase 9.

On worker or application startup / recovery scan:
1. Finds RUNNING workflows interrupted by a crash/restart and safely resumes them.
2. Finds WAITING workflows whose wait interval has elapsed.
3. Finds RETRYING workflows whose next_retry_at <= now.
4. Finds TIMED_OUT workflows and transitions them safely.
5. Never blindly reruns a mutating action — uses idempotency and step run history.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import WorkflowRun, Approval
from apps.api.app.workflows.state_manager import WorkflowStateManager
from apps.api.app.workflows.runner import WorkflowRunner
from apps.api.app.workflows.timeout_manager import WorkflowTimeoutManager


class WorkflowRecoveryService:
    """Discovers and safely recovers interrupted or pending workflow runs."""

    @classmethod
    def recover_all(cls, db: Session) -> Dict[str, int]:
        """
        Run startup or periodic scan across all organizations.
        Returns counts of recovered, resumed, and timed-out runs.
        """
        stats = {
            "crashed_resumed": 0,
            "waits_resumed": 0,
            "retries_resumed": 0,
            "timed_out": 0,
            "approvals_expired": 0,
        }

        now = get_utc_now()
        runner = WorkflowRunner(db)

        # 1. Check for expired pending approvals
        pending_approvals = db.query(Approval).filter(
            Approval.status == "PENDING",
            Approval.expires_at != None,
            Approval.expires_at <= now,
        ).all()

        for appr in pending_approvals:
            appr.status = "EXPIRED"
            db.commit()
            stats["approvals_expired"] += 1
            # If associated with a workflow run, escalate or fail
            if appr.workflow_run_id:
                run = db.query(WorkflowRun).filter(WorkflowRun.id == appr.workflow_run_id).first()
                if run and run.status == "WAITING_FOR_APPROVAL":
                    WorkflowStateManager.transition_run(
                        db, run, "ESCALATED", reason="Approval expired without decision"
                    )

        # 2. Check for timed-out workflow runs
        active_runs = db.query(WorkflowRun).filter(
            WorkflowRun.status.in_(["RUNNING", "WAITING", "WAITING_FOR_APPROVAL", "RETRYING"])
        ).all()

        for run in active_runs:
            if run.workflow:
                is_timed_out, elapsed = WorkflowTimeoutManager.is_workflow_timed_out(run.workflow, run)
                if is_timed_out:
                    WorkflowStateManager.transition_run(
                        db, run, "TIMED_OUT",
                        reason=f"Workflow run timed out ({elapsed}s >= {run.workflow.timeout_seconds}s)"
                    )
                    stats["timed_out"] += 1

        # 3. Recover RETRYING runs whose retry interval elapsed
        retrying_runs = db.query(WorkflowRun).filter(
            WorkflowRun.status == "RETRYING",
            WorkflowRun.next_run_at != None,
            WorkflowRun.next_run_at <= now,
        ).all()

        for run in retrying_runs:
            stats["retries_resumed"] += 1
            runner.execute_run(run)

        # 4. Recover WAITING runs whose wait condition elapsed
        waiting_runs = db.query(WorkflowRun).filter(
            WorkflowRun.status == "WAITING",
            WorkflowRun.next_run_at != None,
            WorkflowRun.next_run_at <= now,
        ).all()

        for run in waiting_runs:
            stats["waits_resumed"] += 1
            runner.execute_run(run)

        # 5. Recover crashed RUNNING runs
        crashed_runs = db.query(WorkflowRun).filter(
            WorkflowRun.status == "RUNNING"
        ).all()

        for run in crashed_runs:
            stats["crashed_resumed"] += 1
            runner.execute_run(run)

        return stats
