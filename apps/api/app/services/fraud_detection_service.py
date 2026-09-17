"""
Return Fraud & 'Wardrobing' Detection Engine.
Detects serial return abusers, weekend event wearers ('wardrobing'), and return policy exploitation.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from apps.api.app.models.ecommerce import Order, Return
from apps.api.app.models.operations import Customer
from apps.api.app.models.audit import AuditLog


class FraudDetectionService:
    """
    Evaluates return requests for synthetic and behavioral abuse vectors.
    Flags high-risk returns for human manager inspection before issuing labels or refunds.
    """

    WARDROBING_KEYWORDS = [
        "wore once", "event over", "party", "wedding", "weekend",
        "photoshoot", "not needed anymore", "temporary", "just for function"
    ]

    @classmethod
    def evaluate_return_fraud_risk(
        cls,
        db: Session,
        organization_id: str,
        customer_id: str,
        order_id: str,
        return_reason: str = "",
        refund_amount: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyzes customer history, return cadence, wardrobing triggers, and financial ceilings.
        Returns risk score (0.0 - 1.0) and fraud risk tier.
        """
        flags = []
        risk_score = 0.05  # Base baseline risk

        # 1. Inspect Customer Lifetime Return Rate
        total_orders = db.query(Order).filter(
            Order.organization_id == organization_id,
            Order.customer_id == customer_id
        ).count()

        total_returns = db.query(Return).filter(
            Return.organization_id == organization_id,
            Return.customer_id == customer_id
        ).count()

        return_rate_pct = 0.0
        if total_orders > 0:
            return_rate_pct = round((total_returns / total_orders) * 100, 1)

        if total_orders >= 3 and return_rate_pct > 60.0:
            risk_score += 0.35
            flags.append(f"High historical return rate ({return_rate_pct}% across {total_orders} orders)")
        elif total_orders >= 2 and return_rate_pct > 40.0:
            risk_score += 0.15
            flags.append(f"Elevated return frequency ({return_rate_pct}%)")

        # 2. Wardrobing / Serial Event-Wear Trigger Detection
        reason_lower = (return_reason or "").lower()
        matched_keywords = [kw for kw in cls.WARDROBING_KEYWORDS if kw in reason_lower]
        is_wardrobing_suspect = False

        if matched_keywords:
            risk_score += 0.45
            is_wardrobing_suspect = True
            flags.append(f"Wardrobing trigger terms detected: {matched_keywords}")

        # Weekend return timing anomaly (ordered Thu/Fri, returned Mon/Tue)
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.created_at:
            order_weekday = order.created_at.weekday()  # 4=Friday, 5=Saturday
            current_weekday = datetime.now(timezone.utc).weekday()  # 0=Monday, 1=Tuesday
            if order_weekday in (4, 5) and current_weekday in (0, 1):
                risk_score += 0.20
                is_wardrobing_suspect = True
                flags.append("Weekend event cadence detected (Ordered Friday/Saturday, Returned Monday/Tuesday)")

        # 3. High-Ticket Threshold Impact
        if refund_amount >= 3000.0:
            risk_score += 0.15
            flags.append(f"High-value garment return: ₹{refund_amount:,.2f}")

        # Cap score at 0.99
        risk_score = round(min(0.99, max(0.05, risk_score)), 2)

        # Categorize
        if risk_score >= 0.60:
            tier = "HIGH"
            action = "MANUAL_INSPECTION_REQUIRED"
        elif risk_score >= 0.35:
            tier = "MEDIUM"
            action = "INSPECT_TAGS_ON_RECEIPT"
        else:
            tier = "LOW"
            action = "AUTONOMOUS_RETURN_APPROVED"

        audit = AuditLog(
            organization_id=organization_id,
            actor_id="fraud-sentinel-ai",
            actor_type="SYSTEM",
            actor_name="Fraud Sentinel Engine",
            action="RETURN_FRAUD_EVALUATED",
            resource_type="return_assessment",
            resource_id=order_id,
            result="SUCCESS",
            log_metadata={
                "customer_id": customer_id,
                "risk_score": risk_score,
                "tier": tier,
                "flags": flags,
                "is_wardrobing": is_wardrobing_suspect
            }
        )
        db.add(audit)
        db.commit()

        return {
            "risk_score": risk_score,
            "fraud_tier": tier,
            "is_wardrobing_suspect": is_wardrobing_suspect,
            "recommended_action": action,
            "total_customer_orders": total_orders,
            "total_customer_returns": total_returns,
            "return_rate_percent": return_rate_pct,
            "flagged_signals": flags
        }
