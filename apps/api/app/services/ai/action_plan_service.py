"""
Phase 7 — Action Planning & Tool Selection Service.

Architecture Principle:
- Strict allowlisted action vocabulary.
- Mode is PLAN_ONLY: generates structured action plans but NEVER executes them.
- Validates parameters and assigns per-action approval flags.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.schemas.agent_schemas import (
    ActionPlan,
    DecisionType,
    EntityExtractionResult,
    IntentType,
    PlannedAction,
    ReasoningResult,
    RiskAssessment,
    RiskLevel,
)
from apps.api.app.models.agent import Tool


ALLOWLISTED_ACTIONS = {
    "SEND_MESSAGE": {
        "description": "Send message or email reply to customer or vendor",
        "target_system": "COMMUNICATIONS",
        "default_risk": "LOW",
        "required_permission": "communications.write",
    },
    "CANCEL_ORDER": {
        "description": "Cancel order and release reserved stock",
        "target_system": "ECOMMERCE_CORE",
        "default_risk": "HIGH",
        "required_permission": "orders.cancel",
    },
    "ISSUE_REFUND": {
        "description": "Issue refund for cancelled or returned order",
        "target_system": "PAYMENT_GATEWAY",
        "default_risk": "HIGH",
        "required_permission": "refunds.create",
    },
    "CREATE_RETURN_RECORD": {
        "description": "Generate reverse logistics return authorization and label",
        "target_system": "LOGISTICS",
        "default_risk": "MEDIUM",
        "required_permission": "returns.create",
    },
    "CREATE_SUPPORT_TICKET": {
        "description": "Create support ticket in internal ticketing system",
        "target_system": "SUPPORT",
        "default_risk": "LOW",
        "required_permission": "tickets.create",
    },
    "CREATE_OPERATIONS_TASK": {
        "description": "Create internal operational task for human review",
        "target_system": "WORKFLOWS",
        "default_risk": "LOW",
        "required_permission": "tasks.create",
    },
    "UPDATE_INVENTORY": {
        "description": "Adjust warehouse inventory quantity",
        "target_system": "INVENTORY",
        "default_risk": "HIGH",
        "required_permission": "inventory.adjust",
    },
    "ESCALATE_TO_HUMAN": {
        "description": "Route conversation directly to human operations team",
        "target_system": "SUPERVISOR",
        "default_risk": "LOW",
        "required_permission": "agents.escalate",
    },
}

FORBIDDEN_ACTIONS = {
    "DROP_DATABASE", "EXECUTE_SHELL", "RAW_SQL", "DELETE_USER", "ACCESS_CREDENTIALS", "HTTP_REQUEST", "EVAL"
}


class ActionPlanningService:
    def create_plan(
        self,
        reasoning: ReasoningResult,
        intent: str,
        entities: EntityExtractionResult,
        risk: RiskAssessment,
        organization_id: str,
    ) -> ActionPlan:
        """
        Build an ActionPlan adhering to strict allowlisted vocabulary.
        In Phase 7, all actions are purely planned (never executed).
        """
        planned_actions: List[PlannedAction] = []
        order_num = entities.order_numbers[0] if entities.order_numbers else None
        order_id = entities.order_ids[0] if entities.order_ids else None
        customer_id = entities.customer_ids[0] if entities.customer_ids else None
        amount = entities.amounts[0] if entities.amounts else None

        step_idx = 1

        for act_name in reasoning.required_actions:
            clean_name = act_name.strip().upper()

            # Security: check forbidden actions
            if clean_name in FORBIDDEN_ACTIONS or "DROP" in clean_name or "SQL" in clean_name:
                # Discard dangerous action immediately
                continue

            if clean_name not in ALLOWLISTED_ACTIONS:
                # If unlisted, fall back to safe operations task
                clean_name = "CREATE_OPERATIONS_TASK"

            spec = ALLOWLISTED_ACTIONS[clean_name]
            params: Dict[str, Any] = {"organization_id": organization_id}

            if clean_name == "CANCEL_ORDER":
                params["order_number"] = order_num
                params["order_id"] = order_id
                params["reason"] = reasoning.decision_summary

            elif clean_name == "ISSUE_REFUND":
                params["order_number"] = order_num
                params["amount"] = amount
                params["reason"] = reasoning.decision_summary

            elif clean_name == "CREATE_RETURN_RECORD":
                params["order_number"] = order_num
                params["customer_id"] = customer_id
                params["skus"] = entities.skus

            elif clean_name == "CREATE_SUPPORT_TICKET":
                params["subject"] = f"AI Escalation: {intent}"
                params["description"] = reasoning.decision_summary
                params["customer_id"] = customer_id

            elif clean_name == "CREATE_OPERATIONS_TASK":
                params["title"] = f"Review needed for {intent}"
                params["details"] = reasoning.decision_summary

            act_risk = spec["default_risk"]
            needs_approval = (act_risk in ("HIGH", "CRITICAL")) or risk.requires_approval

            planned_actions.append(PlannedAction(
                action_name=clean_name,
                target_system=spec["target_system"],
                parameters=params,
                estimated_risk=act_risk,
                requires_approval=needs_approval,
                order=step_idx,
                description=spec["description"],
            ))
            step_idx += 1

        # If decision was ANSWER, include SEND_MESSAGE action
        if reasoning.decision == DecisionType.ANSWER and reasoning.proposed_response:
            planned_actions.append(PlannedAction(
                action_name="SEND_MESSAGE",
                target_system="COMMUNICATIONS",
                parameters={"content": reasoning.proposed_response, "channel": "WEB_CHAT"},
                estimated_risk="LOW",
                requires_approval=False,
                order=step_idx,
                description="Send generated response to recipient",
            ))

        return ActionPlan(
            run_id="",  # set by caller
            organization_id=organization_id,
            plan_summary=f"Plan for intent {intent}: {len(planned_actions)} action(s) prepared.",
            actions=planned_actions,
            risk_assessment=risk,
            requires_approval=risk.requires_approval,
            approval_status="PENDING_APPROVAL" if risk.requires_approval else "NOT_REQUIRED",
            execution_mode="PLAN_ONLY",  # Strict Phase 7 constraint
        )


class ToolSelectionService:
    def verify_tools(self, db: Session, organization_id: str, plan: ActionPlan) -> List[Dict[str, Any]]:
        """
        Validates whether corresponding tools exist in the system for each planned action.
        """
        results: List[Dict[str, Any]] = []
        for action in plan.actions:
            tool = db.query(Tool).filter(
                (Tool.organization_id == organization_id) | (Tool.organization_id.is_(None)),
                Tool.name == action.action_name,
                Tool.enabled == True,
            ).first()

            results.append({
                "action_name": action.action_name,
                "tool_found": tool is not None,
                "tool_id": tool.id if tool else None,
                "is_executable": False,  # Phase 7 constraint
            })
        return results
