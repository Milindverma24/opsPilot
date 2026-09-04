"""
Phase 7 — Risk Assessment Service.

Deterministic, multi-factor risk scoring engine.
Categorizes every planned decision into LOW, MEDIUM, HIGH, or CRITICAL.
Enforces human approval boundaries for all risky operations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.api.app.schemas.agent_schemas import (
    DecisionType,
    EntityExtractionResult,
    IntentType,
    RiskAssessment,
    RiskLevel,
)


class RiskAssessmentService:
    def assess_risk(
        self,
        intent: str,
        decision: DecisionType,
        entities: EntityExtractionResult,
        actions: List[str],
        confidence: float = 1.0,
    ) -> RiskAssessment:
        """
        Calculates risk score (0.0 - 1.0) and assigns risk tier + approval requirements.
        """
        score = 0.0
        factors: List[str] = []

        # 1. Security & Prompt Injection checks (CRITICAL)
        if intent == IntentType.PROMPT_INJECTION.value or "PROMPT_INJECTION" in entities.untrusted_flags:
            score = 1.0
            factors.append("Untrusted prompt injection pattern detected in input")
            return RiskAssessment(
                risk_level=RiskLevel.CRITICAL,
                risk_score=score,
                risk_factors=factors,
                requires_approval=False,  # Prompt injection is blocked immediately, not approved
                approval_type="SECURITY_REVIEW",
                suggested_approvers=["SECURITY_ADMIN"],
            )

        # 2. Financial Amount checks
        max_amount = 0.0
        if entities.amounts:
            max_amount = max(entities.amounts)

        if max_amount > 10000:
            score = max(score, 0.95)
            factors.append(f"High-value financial amount involved: ₹{max_amount:.2f} (> ₹10,000 threshold)")
        elif max_amount > 2000:
            score = max(score, 0.75)
            factors.append(f"Substantial financial amount involved: ₹{max_amount:.2f} (> ₹2,000 threshold)")
        elif max_amount > 0:
            score = max(score, 0.45)
            factors.append(f"Financial amount involved: ₹{max_amount:.2f}")

        # 3. Action / Intent checks
        action_names_upper = [a.upper() for a in actions]

        if "ISSUE_REFUND" in action_names_upper or intent == IntentType.REFUND_REQUEST.value:
            score = max(score, 0.70)
            factors.append("Refund execution requires financial controls")

        if "CANCEL_ORDER" in action_names_upper or intent == IntentType.ORDER_CANCELLATION.value:
            score = max(score, 0.65)
            factors.append("Order cancellation modifies customer order lifecycle")

        if "CREATE_RETURN_RECORD" in action_names_upper or intent == IntentType.RETURN_REQUEST.value:
            score = max(score, 0.40)
            factors.append("Return initiation involves reverse logistics")

        if intent == IntentType.COMPLAINT.value:
            score = max(score, 0.60)
            factors.append("Customer grievance requires management visibility")

        if intent == IntentType.VENDOR_REQUEST.value:
            score = max(score, 0.70)
            factors.append("Vendor communication involves B2B contractual or operational matters")

        # 4. Confidence penalties
        if confidence < 0.70:
            score = max(score, 0.65)
            factors.append(f"Low AI decision confidence ({confidence:.2f} < 0.70)")
        elif confidence < 0.85:
            score = max(score, 0.40)
            factors.append(f"Moderate AI decision confidence ({confidence:.2f} < 0.85)")

        # 5. Read-only answers with no mutating actions are inherently low risk
        if decision == DecisionType.ANSWER and not actions:
            score = min(score, 0.15)
            if not factors:
                factors.append("Informational read-only response with verified evidence")

        if decision == DecisionType.ASK_CLARIFICATION:
            score = min(score, 0.10)
            factors.append("Clarification request - zero operational side-effects")

        # Determine level & approval
        if score >= 0.85:
            level = RiskLevel.CRITICAL
            req_approval = True
            approval_type = "EXECUTIVE_APPROVAL" if max_amount > 10000 else "SECURITY_REVIEW"
            approvers = ["ADMIN", "FINANCE_DIRECTOR"]
        elif score >= 0.65:
            level = RiskLevel.HIGH
            req_approval = True
            approval_type = "FINANCIAL_APPROVAL" if "REFUND" in factors or max_amount > 0 else "OPERATIONS_REVIEW"
            approvers = ["OPERATIONS_MANAGER", "SUPPORT_LEAD"]
        elif score >= 0.35:
            level = RiskLevel.MEDIUM
            # Medium risk requires approval if explicit action requested
            req_approval = bool(actions) or decision == DecisionType.REQUEST_APPROVAL
            approval_type = "OPERATIONS_REVIEW" if req_approval else "NONE"
            approvers = ["CUSTOMER_SUPPORT_AGENT"] if req_approval else []
        else:
            level = RiskLevel.LOW
            req_approval = False
            approval_type = "NONE"
            approvers = []

        return RiskAssessment(
            risk_level=level,
            risk_score=round(score, 2),
            risk_factors=factors,
            requires_approval=req_approval,
            approval_type=approval_type,
            suggested_approvers=approvers,
        )
