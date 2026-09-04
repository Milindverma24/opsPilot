"""
Workflow Timeout Manager — Phase 9.

Monitors and enforces:
- Workflow total execution timeout
- Step execution timeout
- Approval waiting timeout
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple
from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowStepRun, Approval


class WorkflowTimeoutManager:
    """Evaluates timeouts across workflows, steps, and pending approvals."""

    @classmethod
    def is_workflow_timed_out(cls, workflow: Workflow, run: WorkflowRun) -> Tuple[bool, int]:
        """
        Check if total workflow run duration has exceeded configured timeout.
        Returns (is_timed_out, elapsed_seconds).
        """
        timeout_secs = workflow.timeout_seconds or 3600
        now = get_utc_now()
        started_at = run.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        elapsed = int((now - started_at).total_seconds())
        return elapsed >= timeout_secs, elapsed

    @classmethod
    def is_step_timed_out(cls, step: WorkflowStep, step_run: WorkflowStepRun) -> Tuple[bool, int]:
        """
        Check if active step run has exceeded step-level timeout.
        """
        timeout_secs = step.timeout_seconds or 300
        now = get_utc_now()
        started_at = step_run.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        elapsed = int((now - started_at).total_seconds())
        return elapsed >= timeout_secs, elapsed

    @classmethod
    def is_approval_timed_out(cls, approval: Approval) -> bool:
        """
        Check if an approval has passed its expires_at deadline.
        """
        if not approval.expires_at:
            return False

        now = get_utc_now()
        expires_at = approval.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        return now >= expires_at
