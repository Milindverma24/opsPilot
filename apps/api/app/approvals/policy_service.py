"""
Approval Policy Service — Phase 10.

Evaluates whether business actions require human supervisory approval,
determines the required approver roles, risk levels, and multi-level approval modes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ApprovalPolicyService:
    """Configurable approval matrix and policy engine."""

    # Configurable matrix: action_type -> policy spec
    DEFAULT_APPROVAL_MATRIX: Dict[str, Dict[str, Any]] = {
        "REFUND": {
            "risk_level": "HIGH",
            "thresholds": [
                {"max_amount": 500, "approval_required": False, "risk_level": "LOW", "mode": "NONE"},
                {"max_amount": 5000, "approval_required": True, "risk_level": "HIGH", "roles": ["MANAGER", "ADMIN"], "mode": "ONE_APPROVER"},
                {"max_amount": 10000, "approval_required": True, "risk_level": "HIGH", "roles": ["FINANCE", "ADMIN"], "mode": "ONE_APPROVER"},
                {"max_amount": float("inf"), "approval_required": True, "risk_level": "CRITICAL", "roles": ["FINANCE", "OPERATIONS", "ADMIN"], "mode": "ALL_REQUIRED"},
            ],
        },
        "ORDER_CANCELLATION": {
            "approval_required": True,
            "risk_level": "HIGH",
            "roles": ["MANAGER", "OPERATIONS", "ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "ORDER_MODIFICATION": {
            "approval_required": True,
            "risk_level": "MEDIUM",
            "roles": ["SUPPORT_LEAD", "MANAGER", "ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "RETURN_APPROVAL": {
            "approval_required": True,
            "risk_level": "HIGH",
            "roles": ["MANAGER", "OPERATIONS", "ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "INVENTORY_ADJUSTMENT": {
            "thresholds": [
                {"max_amount": 100, "approval_required": True, "risk_level": "HIGH", "roles": ["OPERATIONS", "ADMIN"], "mode": "ONE_APPROVER"},
                {"max_amount": float("inf"), "approval_required": True, "risk_level": "CRITICAL", "roles": ["OPERATIONS", "MANAGER", "ADMIN"], "mode": "ALL_REQUIRED"},
            ],
        },
        "PURCHASE_ORDER": {
            "thresholds": [
                {"max_amount": 50000, "approval_required": True, "risk_level": "HIGH", "roles": ["OPERATIONS", "ADMIN"], "mode": "ONE_APPROVER"},
                {"max_amount": float("inf"), "approval_required": True, "risk_level": "CRITICAL", "roles": ["OPERATIONS", "FINANCE", "ADMIN"], "mode": "ALL_REQUIRED"},
            ],
        },
        "CUSTOMER_COMMUNICATION": {
            "approval_required": True,
            "risk_level": "HIGH",
            "roles": ["MANAGER", "ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "VENDOR_ACTION": {
            "approval_required": True,
            "risk_level": "HIGH",
            "roles": ["OPERATIONS", "ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "POLICY_EXCEPTION": {
            "approval_required": True,
            "risk_level": "CRITICAL",
            "roles": ["ADMIN"],
            "mode": "ONE_APPROVER",
        },
        "HIGH_RISK_OPERATION": {
            "approval_required": True,
            "risk_level": "CRITICAL",
            "roles": ["ADMIN", "MANAGER"],
            "mode": "ONE_APPROVER",
        },
    }

    @classmethod
    def evaluate_action(
        cls,
        organization_id: str,
        action_type: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates action payload against policy matrix.
        Returns:
            {
                "requires_approval": bool,
                "risk_level": str,
                "required_roles": List[str],
                "approval_mode": str,  # ONE_APPROVER, ALL_REQUIRED, ANY_ONE
                "reason": str,
            }
        """
        action_key = action_type.upper().strip()
        spec = cls.DEFAULT_APPROVAL_MATRIX.get(action_key)

        if not spec:
            # Check for partial match (e.g. execute_refund -> REFUND)
            for k in cls.DEFAULT_APPROVAL_MATRIX:
                if k in action_key:
                    spec = cls.DEFAULT_APPROVAL_MATRIX[k]
                    break

        if not spec:
            # Default conservative boundary
            return {
                "requires_approval": True,
                "risk_level": "MEDIUM",
                "required_roles": ["MANAGER", "ADMIN"],
                "approval_mode": "ONE_APPROVER",
                "reason": f"Default policy applied for action {action_type}",
            }

        # Check threshold-based rules (e.g. amounts, quantities)
        if "thresholds" in spec:
            amount = payload.get("amount") or payload.get("total_amount") or payload.get("quantity") or 0.0
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                amount = 0.0

            for rule in spec["thresholds"]:
                if amount <= rule["max_amount"]:
                    return {
                        "requires_approval": rule.get("approval_required", True),
                        "risk_level": rule.get("risk_level", "HIGH"),
                        "required_roles": rule.get("roles", ["MANAGER", "ADMIN"]),
                        "approval_mode": rule.get("mode", "ONE_APPROVER"),
                        "reason": f"Threshold matched: amount ₹{amount:,.2f} <= ₹{rule['max_amount']:,.2f}",
                        "amount": amount,
                    }

        return {
            "requires_approval": spec.get("approval_required", True),
            "risk_level": spec.get("risk_level", "HIGH"),
            "required_roles": spec.get("roles", ["MANAGER", "ADMIN"]),
            "approval_mode": spec.get("mode", "ONE_APPROVER"),
            "reason": f"Standard approval matrix matched for {action_type}",
        }
