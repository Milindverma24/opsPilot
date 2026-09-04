"""
Seed Script — Phase 9 & Phase 10 Autonomous Business Workflows.

Seeds the 4 required autonomous workflows for UrbanThread:
1. ORDER_FULFILLMENT (ORDER_CREATED)
2. SHIPMENT_DELAY_RESOLUTION (SHIPMENT_DELAYED)
3. INVENTORY_REPLENISHMENT (INVENTORY_LOW)
4. RETURN_PROCESSING (RETURN_REQUESTED)
"""
from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization
from apps.api.app.models.workflow import Workflow, WorkflowStep


REQUIRED_WORKFLOWS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # WORKFLOW A — ORDER FULFILLMENT
    # -----------------------------------------------------------------------
    {
        "name": "Autonomous Order Fulfillment",
        "description": "Validates inventory, reserves stock, coordinates payment, and prepares shipment upon order creation.",
        "workflow_type": "ORDER_FULFILLMENT",
        "trigger_type": "ORDER_CREATED",
        "enabled": True,
        "version": "v1",
        "configuration": {"auto_fulfill": True, "currency": "INR"},
        "max_concurrent_runs": 20,
        "timeout_seconds": 1800,
        "steps": [
            {
                "name": "Gather Order Context",
                "step_order": 1,
                "step_type": "CONTEXT_GATHER",
                "configuration": {"entities": ["order", "customer"]},
            },
            {
                "name": "Reserve Stock in Warehouse",
                "step_order": 2,
                "step_type": "TOOL_EXECUTION",
                "configuration": {
                    "tool_name": "reserve_inventory",
                    "arguments": {
                        "sku": "{{context.order.sku or 'UT-SHIRT-001'}}",
                        "quantity": 1,
                        "order_id": "{{context.order.id}}",
                    },
                },
            },
            {
                "name": "Verify Stock Reservation",
                "step_order": 3,
                "step_type": "VERIFICATION",
                "configuration": {
                    "entity_type": "inventory",
                    "field": "sku",
                    "expected_value": "UT-SHIRT-001",
                },
            },
            {
                "name": "Send Confirmation Email",
                "step_order": 4,
                "step_type": "NOTIFICATION",
                "configuration": {
                    "title": "Order Placed & Stock Reserved",
                    "message": "Your UrbanThread order is being processed for dispatch.",
                    "type": "SUCCESS",
                },
            },
            {
                "name": "Fulfillment Complete",
                "step_order": 5,
                "step_type": "COMPLETE",
                "configuration": {},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # WORKFLOW B — SHIPMENT DELAY RESOLUTION
    # -----------------------------------------------------------------------
    {
        "name": "Shipment Delay Resolution",
        "description": "Evaluates carrier tracking updates, classifies severity with AI, applies policy, and notifies or escalates.",
        "workflow_type": "SHIPMENT_DELAY_RESOLUTION",
        "trigger_type": "SHIPMENT_DELAYED",
        "enabled": True,
        "version": "v1",
        "configuration": {"policy_threshold_days": 2},
        "max_concurrent_runs": 15,
        "timeout_seconds": 3600,
        "steps": [
            {
                "name": "Gather Shipment Context",
                "step_order": 1,
                "step_type": "CONTEXT_GATHER",
                "configuration": {"entities": ["order", "customer", "shipment"]},
            },
            {
                "name": "AI Severity Classification",
                "step_order": 2,
                "step_type": "AI_DECISION",
                "configuration": {"task": "CLASSIFY_SEVERITY"},
            },
            {
                "name": "Check Critical Delay Condition",
                "step_order": 3,
                "step_type": "CONDITION",
                "configuration": {
                    "condition": {"field": "decisions.severity", "operator": "==", "value": "CRITICAL"},
                    "on_true_order": 7,   # Jump to Immediate Escalation
                    "on_false_order": 4,  # Continue to standard notification
                    "on_true_name": "Critical Escalation",
                    "on_false_name": "Standard Communication",
                },
            },
            {
                "name": "Create Customer Support Task",
                "step_order": 4,
                "step_type": "TOOL_EXECUTION",
                "configuration": {
                    "tool_name": "create_internal_task",
                    "arguments": {
                        "title": "Follow up on Delayed Shipment",
                        "description": "Shipment delay detected by monitoring engine. Tracking update required.",
                        "assigned_team": "SUPPORT",
                        "priority": "MEDIUM",
                    },
                },
            },
            {
                "name": "Send Delay Notification Email",
                "step_order": 5,
                "step_type": "NOTIFICATION",
                "configuration": {
                    "title": "UrbanThread Shipment Update",
                    "message": "We noticed your shipment is running slightly behind schedule. Our logistics team is monitoring it.",
                    "type": "WARNING",
                },
            },
            {
                "name": "Resolution Complete",
                "step_order": 6,
                "step_type": "COMPLETE",
                "configuration": {},
            },
            {
                "name": "Immediate Operations Escalation",
                "step_order": 7,
                "step_type": "ESCALATION",
                "configuration": {
                    "level": "CRITICAL",
                    "severity": "CRITICAL",
                    "reason": "Severe shipment delay exceeded critical threshold (7+ days). Human intervention required.",
                    "team": "OPERATIONS",
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    # WORKFLOW C — INVENTORY REPLENISHMENT
    # -----------------------------------------------------------------------
    {
        "name": "Automated Inventory Replenishment",
        "description": "Calculates sales velocity, predicts demand, enforces PO policies, and requests supervisory approval before ordering.",
        "workflow_type": "INVENTORY_REPLENISHMENT",
        "trigger_type": "INVENTORY_LOW",
        "enabled": True,
        "version": "v1",
        "configuration": {"sales_velocity_lookback_days": 30},
        "max_concurrent_runs": 10,
        "timeout_seconds": 7200,
        "steps": [
            {
                "name": "Gather Inventory & Product Data",
                "step_order": 1,
                "step_type": "CONTEXT_GATHER",
                "configuration": {"entities": ["inventory"]},
            },
            {
                "name": "AI Demand & Velocity Estimation",
                "step_order": 2,
                "step_type": "AI_DECISION",
                "configuration": {"task": "RECOMMEND_REPLENISHMENT", "sales_velocity": 15},
            },
            {
                "name": "Replenishment Policy Validation",
                "step_order": 3,
                "step_type": "POLICY_CHECK",
                "configuration": {
                    "policy_name": "INVENTORY_REORDER_POLICY",
                    "max_amount": 50000,
                },
            },
            {
                "name": "Manager Approval Boundary",
                "step_order": 4,
                "step_type": "APPROVAL",
                "configuration": {
                    "action_type": "PURCHASE_ORDER",
                    "title": "Purchase Order Approval for Low Stock Replenishment",
                    "reason": "Stock fallen below minimum reorder buffer. Replenishment requested.",
                    "action_payload": {
                        "sku": "{{context.inventory.sku or 'UT-SHIRT-001'}}",
                        "quantity": "{{decisions.recommended_quantity or 50}}",
                        "amount": 25000.0,
                    },
                    "timeout_minutes": 60,
                },
            },
            {
                "name": "Create Purchase Order Record",
                "step_order": 5,
                "step_type": "TOOL_EXECUTION",
                "configuration": {
                    "tool_name": "create_purchase_order",
                    "arguments": {
                        "vendor_id": "vendor-ut-supplier-01",
                        "items": [{"sku": "UT-SHIRT-001", "quantity": 50, "unit_price": 500.0}],
                        "total_amount": 25000.0,
                    },
                },
            },
            {
                "name": "Notify Warehouse Team",
                "step_order": 6,
                "step_type": "NOTIFICATION",
                "configuration": {
                    "title": "Purchase Order Submitted to Supplier",
                    "message": "Replenishment PO of 50 units submitted to vendor.",
                    "type": "SUCCESS",
                },
            },
            {
                "name": "Replenishment Complete",
                "step_order": 7,
                "step_type": "COMPLETE",
                "configuration": {},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # WORKFLOW D — RETURN PROCESSING
    # -----------------------------------------------------------------------
    {
        "name": "Autonomous Return & Refund Processing",
        "description": "Checks customer return eligibility against 30-day policy, gates high-value refunds behind human approval, and verifies disbursement.",
        "workflow_type": "RETURN_PROCESSING",
        "trigger_type": "RETURN_REQUESTED",
        "enabled": True,
        "version": "v1",
        "configuration": {"max_auto_refund_limit": 500.0},
        "max_concurrent_runs": 15,
        "timeout_seconds": 3600,
        "steps": [
            {
                "name": "Gather Return & Customer Context",
                "step_order": 1,
                "step_type": "CONTEXT_GATHER",
                "configuration": {"entities": ["order", "customer", "return"]},
            },
            {
                "name": "AI Return Policy Eligibility Check",
                "step_order": 2,
                "step_type": "AI_DECISION",
                "configuration": {"task": "EXTRACT_RETURN_ELIGIBILITY"},
            },
            {
                "name": "Eligibility Condition Evaluation",
                "step_order": 3,
                "step_type": "CONDITION",
                "configuration": {
                    "condition": {"field": "decisions.is_eligible", "operator": "==", "value": True},
                    "on_true_order": 4,   # Valid return -> proceed to approval
                    "on_false_order": 8,  # Invalid return -> reject
                    "on_true_name": "Eligible Return",
                    "on_false_name": "Ineligible Return",
                },
            },
            {
                "name": "Refund Approval Boundary",
                "step_order": 4,
                "step_type": "APPROVAL",
                "configuration": {
                    "action_type": "REFUND",
                    "title": "Customer Return Refund Authorization",
                    "reason": "Return item inspected and verified. Refund authorization requested.",
                    "action_payload": {
                        "order_id": "{{context.order.id}}",
                        "amount": "{{input.amount or 2499.0}}",
                        "reason": "CUSTOMER_RETURN",
                    },
                    "timeout_minutes": 30,
                },
            },
            {
                "name": "Disburse Approved Refund",
                "step_order": 5,
                "step_type": "TOOL_EXECUTION",
                "configuration": {
                    "tool_name": "execute_refund",
                    "arguments": {
                        "refund_id": "{{input.refund_id or 'ref-pending-01'}}",
                        "amount": 2499.0,
                    },
                },
            },
            {
                "name": "Customer Refund Notification",
                "step_order": 6,
                "step_type": "NOTIFICATION",
                "configuration": {
                    "title": "Your Refund Has Been Processed",
                    "message": "Your refund of ₹2,499 has been credited back to your original payment method.",
                    "type": "SUCCESS",
                },
            },
            {
                "name": "Return Completed Successfully",
                "step_order": 7,
                "step_type": "COMPLETE",
                "configuration": {},
            },
            {
                "name": "Reject Ineligible Return",
                "step_order": 8,
                "step_type": "NOTIFICATION",
                "configuration": {
                    "title": "Return Request Rejected",
                    "message": "Item outside the 30-day return policy window.",
                    "type": "DANGER",
                },
            },
        ],
    },
]


def seed_workflows(db: Session, organization_id: str) -> List[Workflow]:
    """Seeds the 4 autonomous workflows for an organization."""
    seeded: List[Workflow] = []

    for wf_data in REQUIRED_WORKFLOWS:
        steps_data = wf_data.pop("steps", [])

        # Check existing
        existing = db.query(Workflow).filter(
            Workflow.organization_id == organization_id,
            Workflow.workflow_type == wf_data["workflow_type"],
        ).first()

        if not existing:
            wf = Workflow(
                organization_id=organization_id,
                name=wf_data["name"],
                description=wf_data["description"],
                workflow_type=wf_data["workflow_type"],
                trigger_type=wf_data["trigger_type"],
                status="ACTIVE",
                enabled=wf_data.get("enabled", True),
                version=wf_data.get("version", "v1"),
                configuration=wf_data.get("configuration", {}),
                max_concurrent_runs=wf_data.get("max_concurrent_runs", 10),
                timeout_seconds=wf_data.get("timeout_seconds", 3600),
                idempotency_key=f"wf-{wf_data['workflow_type'].lower()}-{organization_id[:8]}",
            )
            db.add(wf)
            db.commit()
            db.refresh(wf)
            existing = wf
        else:
            # Update fields
            existing.name = wf_data["name"]
            existing.description = wf_data["description"]
            existing.trigger_type = wf_data["trigger_type"]
            existing.configuration = wf_data.get("configuration", {})
            existing.enabled = True
            db.commit()

        # Seed steps
        existing_step_orders = {s.step_order for s in existing.steps}
        for s_data in steps_data:
            if s_data["step_order"] not in existing_step_orders:
                step = WorkflowStep(
                    workflow_id=existing.id,
                    organization_id=organization_id,
                    name=s_data["name"],
                    step_order=s_data["step_order"],
                    step_type=s_data["step_type"],
                    configuration=s_data.get("configuration", {}),
                    timeout_seconds=s_data.get("timeout_seconds", 300),
                    max_retries=s_data.get("max_retries", 3),
                    retry_backoff_seconds=s_data.get("retry_backoff_seconds", 5),
                    continue_on_failure=s_data.get("continue_on_failure", False),
                )
                db.add(step)
        db.commit()
        db.refresh(existing)
        seeded.append(existing)

    return seeded


if __name__ == "__main__":
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        if org:
            wfs = seed_workflows(db, org.id)
            print(f"Successfully seeded {len(wfs)} workflows for organization {org.name} ({org.id})")
        else:
            print("No organization found to seed workflows for.")
    finally:
        db.close()
