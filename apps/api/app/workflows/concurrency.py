"""
Workflow Concurrency & Idempotency Manager — Phase 9.

Enforces:
1. Event Deduplication: event_id + workflow_id + organization_id based idempotency.
2. Business Object Locking: prevents duplicate concurrent execution for the same order/return/SKU.
3. Concurrency Limits: enforces max_concurrent_runs at workflow and organization levels.
   If limit reached, marks run as QUEUED (status=PENDING) instead of failing.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from apps.api.app.models.workflow import Workflow, WorkflowRun


def compute_dedup_key(event_id: str, workflow_id: str, organization_id: str) -> str:
    """Generate deterministic deduplication key for a triggered event."""
    raw = f"{organization_id}:{workflow_id}:{event_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def compute_business_object_lock_key(organization_id: str, workflow_type: str, entity_type: str, entity_id: str) -> str:
    """Generate business object concurrency lock key."""
    raw = f"{organization_id}:{workflow_type}:{entity_type}:{entity_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


class ConcurrencyManager:
    """
    Manages concurrency locks, deduplication, and max_concurrent_runs limits.
    """

    @classmethod
    def check_event_duplicate(
        cls,
        db: Session,
        organization_id: str,
        workflow_id: str,
        event_id: str,
    ) -> Optional[WorkflowRun]:
        """
        Check if an event was already processed by this workflow for this tenant.
        Returns existing WorkflowRun if duplicate, else None.
        """
        dedup_key = compute_dedup_key(event_id, workflow_id, organization_id)
        existing = db.query(WorkflowRun).filter(
            WorkflowRun.organization_id == organization_id,
            WorkflowRun.workflow_id == workflow_id,
            WorkflowRun.idempotency_key == dedup_key,
        ).first()

        if existing:
            return existing

        # Also check by trigger_event_id directly
        existing_by_event = db.query(WorkflowRun).filter(
            WorkflowRun.organization_id == organization_id,
            WorkflowRun.workflow_id == workflow_id,
            WorkflowRun.trigger_event_id == event_id,
        ).first()

        return existing_by_event

    @classmethod
    def check_business_object_conflict(
        cls,
        db: Session,
        organization_id: str,
        workflow_type: str,
        entity_id: Optional[str] = None,
        entity_type: str = "order",
    ) -> Optional[WorkflowRun]:
        """
        Ensure only one active workflow operates on the same business entity (e.g. order_id, return_id).
        Active states: RUNNING, WAITING, WAITING_FOR_APPROVAL, RETRYING.
        """
        if not entity_id:
            return None

        active_statuses = ["RUNNING", "WAITING", "WAITING_FOR_APPROVAL", "WAITING_FOR_EVENT", "RETRYING"]

        # Search active runs where input_data contains this entity_id
        active_runs = db.query(WorkflowRun).join(Workflow).filter(
            WorkflowRun.organization_id == organization_id,
            Workflow.workflow_type == workflow_type,
            WorkflowRun.status.in_(active_statuses),
        ).all()

        for run in active_runs:
            inp = run.input_data or {}
            ctx = run.context_data or {}
            if inp.get(f"{entity_type}_id") == entity_id or inp.get("id") == entity_id:
                return run
            if ctx.get(f"{entity_type}_id") == entity_id:
                return run

        return None

    @classmethod
    def can_start_run(
        cls,
        db: Session,
        workflow: Workflow,
        organization_id: str,
    ) -> Tuple[bool, str]:
        """
        Check if workflow run can start immediately or should be queued due to max_concurrent_runs.
        Returns (can_start, reason).
        """
        max_concurrent = workflow.max_concurrent_runs or 10

        active_count = db.query(WorkflowRun).filter(
            WorkflowRun.workflow_id == workflow.id,
            WorkflowRun.organization_id == organization_id,
            WorkflowRun.status.in_(["RUNNING", "WAITING", "WAITING_FOR_APPROVAL", "RETRYING"]),
        ).count()

        if active_count >= max_concurrent:
            return False, f"Workflow concurrency limit of {max_concurrent} reached ({active_count} currently active)"

        return True, "OK"
