"""
Workflow Runner — Phase 9.

Durable, restart-safe step-by-step executor.
Handles:
- Step iteration and condition branching
- Pause/resume state retention
- Approval boundaries
- Retries with exponential backoff
- Timeout enforcement
- Compensation triggers
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import (
    Workflow, WorkflowRun, WorkflowStep, WorkflowStepRun
)
from apps.api.app.workflows.step_executor import WorkflowStepExecutor, StepExecutionResult
from apps.api.app.workflows.state_manager import WorkflowStateManager
from apps.api.app.workflows.retry_manager import WorkflowRetryManager
from apps.api.app.workflows.timeout_manager import WorkflowTimeoutManager


MAX_STEP_DEPTH = 15


class WorkflowRunner:
    """Executes workflow runs to completion or pause boundaries."""

    def __init__(self, db: Session):
        self.db = db

    def execute_run(self, run: WorkflowRun) -> WorkflowRun:
        """
        Execute active or resumed workflow run until completion, pause, or failure.
        All transitions are persisted immediately in DB.
        """
        workflow = run.workflow
        if not workflow or not workflow.enabled:
            WorkflowStateManager.transition_run(
                self.db, run, "BLOCKED", reason="Workflow is disabled or missing"
            )
            return run

        # Set running if pending
        if run.status in ("PENDING", "RETRYING"):
            WorkflowStateManager.transition_run(self.db, run, "RUNNING")

        # Load ordered steps
        steps = sorted(workflow.steps, key=lambda s: s.step_order)
        if not steps:
            WorkflowStateManager.transition_run(
                self.db, run, "COMPLETED", reason="Workflow has no steps"
            )
            return run

        total_steps_executed = 0
        MAX_STEP_DEPTH = 15

        while run.status == "RUNNING":
            total_steps_executed += 1
            if total_steps_executed > MAX_STEP_DEPTH:
                WorkflowStateManager.transition_run(
                    self.db, run, "FAILED",
                    reason=f"Recursion circuit breaker tripped: Exceeded maximum execution depth limit of {MAX_STEP_DEPTH} steps."
                )
                return run

            # 1. Check workflow timeout
            is_timed_out, elapsed = WorkflowTimeoutManager.is_workflow_timed_out(workflow, run)
            if is_timed_out:
                WorkflowStateManager.transition_run(
                    self.db, run, "TIMED_OUT",
                    reason=f"Workflow run timed out after {elapsed}s (limit: {workflow.timeout_seconds}s)"
                )
                return run

            # 2. Find step corresponding to current_step_order
            current_step = next((s for s in steps if s.step_order == run.current_step_order), None)
            if not current_step:
                # No more steps -> completed
                WorkflowStateManager.transition_run(
                    self.db, run, "COMPLETED", reason="All steps completed successfully"
                )
                return run

            # 3. Create or resolve WorkflowStepRun
            attempt = 1
            existing_step_runs = [sr for sr in run.step_runs if sr.workflow_step_id == current_step.id]
            if existing_step_runs:
                attempt = max(sr.attempt_number for sr in existing_step_runs) + 1

            step_run = WorkflowStepRun(
                organization_id=run.organization_id,
                workflow_run_id=run.id,
                workflow_step_id=current_step.id,
                status="RUNNING",
                attempt_number=attempt,
                input_data=run.context_data or {},
                started_at=get_utc_now(),
            )
            self.db.add(step_run)
            self.db.commit()
            self.db.refresh(step_run)

            # 4. Execute Step
            start_ts = time.time()
            res = WorkflowStepExecutor.execute_step(self.db, workflow, run, current_step, step_run)
            duration_ms = int((time.time() - start_ts) * 1000)

            # 5. Handle step results
            if res.status == "SUCCEEDED":
                WorkflowStateManager.complete_step_run(
                    self.db, step_run, res.output_data, res.decision_data, duration_ms
                )
                # Next step order
                if res.next_step_order is not None:
                    run.current_step_order = res.next_step_order
                else:
                    # Advance to next sequential step
                    next_steps = [s for s in steps if s.step_order > current_step.step_order]
                    if next_steps:
                        run.current_step_order = next_steps[0].step_order
                    else:
                        run.current_step_order = current_step.step_order + 1
                self.db.commit()

            elif res.status == "WAITING_FOR_APPROVAL":
                step_run.status = "WAITING_FOR_APPROVAL"
                step_run.approval_id = res.approval_id
                self.db.commit()
                WorkflowStateManager.transition_run(
                    self.db, run, "WAITING_FOR_APPROVAL", reason="Step paused for human approval"
                )
                return run

            elif res.status == "WAITING":
                step_run.status = "WAITING"
                self.db.commit()
                WorkflowStateManager.transition_run(
                    self.db, run, "WAITING", reason="Step paused for external wait condition"
                )
                return run

            elif res.status == "FAILED":
                # Check retry policy
                should_ret = WorkflowRetryManager.should_retry(
                    current_step, attempt, res.error_code, res.error_message
                )
                if should_ret:
                    next_retry = WorkflowRetryManager.calculate_next_retry_time(current_step, attempt)
                    run.retry_count = (run.retry_count or 0) + 1
                    run.next_run_at = next_retry
                    self.db.commit()
                    WorkflowStateManager.fail_step_run(
                        self.db, step_run, res.error_code or "FAILED", res.error_message or "", duration_ms, is_retry=True
                    )
                    WorkflowStateManager.transition_run(
                        self.db, run, "RETRYING", reason=f"Retrying step {current_step.name} (attempt {attempt})"
                    )
                    return run
                else:
                    # Unrecoverable failure
                    WorkflowStateManager.fail_step_run(
                        self.db, step_run, res.error_code or "FAILED", res.error_message or "", duration_ms, is_retry=False
                    )

                    if current_step.continue_on_failure:
                        # Advance anyway if configured
                        next_steps = [s for s in steps if s.step_order > current_step.step_order]
                        run.current_step_order = next_steps[0].step_order if next_steps else current_step.step_order + 1
                        self.db.commit()
                    else:
                        # Trigger compensation
                        WorkflowStepExecutor.run_compensation(self.db, run, current_step)
                        WorkflowStateManager.transition_run(
                            self.db, run, "FAILED",
                            reason=f"Step '{current_step.name}' failed: {res.error_message}",
                            error_data={"code": res.error_code, "message": res.error_message}
                        )
                        return run

        return run

    def pause_run(self, run_id: str, organization_id: str, reason: str = "Paused by user") -> WorkflowRun:
        run = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == run_id, WorkflowRun.organization_id == organization_id
        ).first()
        if run and run.status in ("RUNNING", "WAITING", "RETRYING"):
            WorkflowStateManager.transition_run(self.db, run, "PAUSED", reason=reason)
        return run

    def resume_run(self, run_id: str, organization_id: str) -> WorkflowRun:
        run = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == run_id, WorkflowRun.organization_id == organization_id
        ).first()
        if run and run.status in ("PAUSED", "WAITING", "RETRYING"):
            WorkflowStateManager.transition_run(self.db, run, "RUNNING", reason="Resumed by user")
            return self.execute_run(run)
        return run

    def cancel_run(self, run_id: str, organization_id: str, reason: str = "Cancelled by user") -> WorkflowRun:
        run = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == run_id, WorkflowRun.organization_id == organization_id
        ).first()
        if run and run.status not in ("COMPLETED", "CANCELLED"):
            WorkflowStateManager.transition_run(self.db, run, "CANCELLED", reason=reason)
        return run

    def retry_run(self, run_id: str, organization_id: str) -> WorkflowRun:
        run = self.db.query(WorkflowRun).filter(
            WorkflowRun.id == run_id, WorkflowRun.organization_id == organization_id
        ).first()
        if run and run.status in ("FAILED", "TIMED_OUT"):
            WorkflowStateManager.transition_run(self.db, run, "RUNNING", reason="Manual retry initiated")
            return self.execute_run(run)
        return run
