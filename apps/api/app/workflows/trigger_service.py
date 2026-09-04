"""
Workflow Trigger Engine — Phase 9.

Deterministically maps incoming business events, customer interactions,
and scheduled tasks to workflows.
Guarantees event deduplication and enforces concurrency limits.
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import Workflow, WorkflowRun
from apps.api.app.workflows.concurrency import (
    ConcurrencyManager, compute_dedup_key
)
from apps.api.app.workflows.runner import WorkflowRunner


# Deterministic mapping from event/trigger type to default workflow types
TRIGGER_TO_WORKFLOW_TYPE_MAP: Dict[str, str] = {
    "ORDER_CREATED": "ORDER_FULFILLMENT",
    "SHIPMENT_DELAYED": "SHIPMENT_DELAY_RESOLUTION",
    "INVENTORY_LOW": "INVENTORY_REPLENISHMENT",
    "INVENTORY_THRESHOLD": "INVENTORY_REPLENISHMENT",
    "RETURN_REQUESTED": "RETURN_PROCESSING",
    "PAYMENT_FAILED": "PAYMENT_EXCEPTION",
    "PAYMENT_TIMEOUT": "PAYMENT_RECOVERY",
    "SUPPORT_TICKET_CREATED": "CUSTOMER_SUPPORT_TRIAGE",
    "CUSTOMER_MESSAGE": "CUSTOMER_MESSAGE_RESOLUTION",
    "EMAIL_RECEIVED": "EMAIL_TRIAGE",
}


class WorkflowTriggerService:
    """Service to ingest events and instantiate/trigger workflows."""

    @classmethod
    def trigger_event(
        cls,
        db: Session,
        organization_id: str,
        event_type: str,
        event_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        execute_immediately: bool = True,
    ) -> Tuple[Optional[WorkflowRun], str]:
        """
        Trigger matching workflows for an incoming event.
        Returns (workflow_run, status_message).
        """
        payload = payload or {}
        if not event_id:
            event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())

        # 1. Resolve workflow definition for this event
        target_wf_type = TRIGGER_TO_WORKFLOW_TYPE_MAP.get(event_type, event_type)

        workflow = db.query(Workflow).filter(
            Workflow.organization_id == organization_id,
            Workflow.enabled == True,
            (Workflow.trigger_type == event_type) | (Workflow.workflow_type == target_wf_type),
        ).first()

        if not workflow:
            # Check for generic event type match
            workflow = db.query(Workflow).filter(
                Workflow.organization_id == organization_id,
                Workflow.enabled == True,
                Workflow.trigger_type == "BUSINESS_EVENT",
            ).first()

        if not workflow:
            return None, f"No active workflow configured for event '{event_type}'"

        # 2. Deduplication check: event_id + workflow_id + organization_id
        existing_run = ConcurrencyManager.check_event_duplicate(
            db, organization_id, workflow.id, event_id
        )
        if existing_run:
            return existing_run, "IDEMPOTENT_DUPLICATE_IGNORED"

        # 3. Check concurrency limit
        can_start, limit_reason = ConcurrencyManager.can_start_run(db, workflow, organization_id)
        initial_status = "PENDING" if not can_start else "RUNNING"

        dedup_key = compute_dedup_key(event_id, workflow.id, organization_id)

        # 4. Create persistent WorkflowRun
        run = WorkflowRun(
            organization_id=organization_id,
            workflow_id=workflow.id,
            trigger_event_id=event_id,
            idempotency_key=dedup_key,
            status=initial_status,
            current_step_order=1,
            input_data=payload,
            context_data={"event_type": event_type, "event_id": event_id, **payload},
            started_at=get_utc_now(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 5. Execute immediately if not queued
        if execute_immediately and initial_status == "RUNNING":
            runner = WorkflowRunner(db)
            run = runner.execute_run(run)

        msg = "RUNNING" if initial_status == "RUNNING" else f"QUEUED: {limit_reason}"
        return run, msg
