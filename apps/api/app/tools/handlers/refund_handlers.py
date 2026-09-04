"""
Refund Tool Handlers — Phase 8.

request_refund → approve_refund → execute_refund

Three intentionally separate steps with separate permissions.
execute_refund calls MockPaymentProvider — never a real payment gateway.
Verification after execution is mandatory.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from apps.api.app.models.ecommerce import Refund, Order, Payment
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import RequestRefundInput, ApproveRefundInput, ExecuteRefundInput
from apps.api.app.tools.mock_providers import MockPaymentProvider


# Max auto-refund without approval (₹10,000)
AUTO_REFUND_LIMIT = 10_000.0


def handle_request_refund(db: Session, ctx: ToolContext, inp: RequestRefundInput) -> Dict[str, Any]:
    # Verify order ownership
    order = db.query(Order).filter(
        Order.id == inp.order_id,
        Order.organization_id == ctx.organization_id,
        Order.customer_id == inp.customer_id,
    ).first()
    if not order:
        return {"success": False, "error": "Order not found or customer does not own this order"}

    # Check payment exists and is paid
    payment = db.query(Payment).filter(
        Payment.order_id == inp.order_id,
        Payment.organization_id == ctx.organization_id,
        Payment.status == "COMPLETED",
    ).first()
    if not payment:
        return {"success": False, "error": "No completed payment found for this order"}

    # Validate amount does not exceed order total
    if inp.amount > float(order.total_amount or 0):
        return {"success": False, "error": f"Refund amount ₹{inp.amount} exceeds order total ₹{order.total_amount}"}

    if ctx.is_dry_run():
        return {
            "success": True,
            "dry_run": True,
            "order_id": inp.order_id,
            "amount": inp.amount,
            "requires_approval": inp.amount > AUTO_REFUND_LIMIT,
        }

    refund = Refund(
        organization_id=ctx.organization_id,
        order_id=inp.order_id,
        payment_id=payment.id,
        amount=inp.amount,
        reason=inp.reason,
        status="PENDING_APPROVAL" if inp.amount > AUTO_REFUND_LIMIT else "PENDING",
        initiated_by="AI_AGENT",
        return_id=inp.return_id,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return {
        "success": True,
        "refund_id": refund.id,
        "order_id": inp.order_id,
        "amount": float(inp.amount),
        "status": refund.status,
        "requires_approval": inp.amount > AUTO_REFUND_LIMIT,
    }


def handle_approve_refund(db: Session, ctx: ToolContext, inp: ApproveRefundInput) -> Dict[str, Any]:
    refund = db.query(Refund).filter(
        Refund.id == inp.refund_id,
        Refund.organization_id == ctx.organization_id,
    ).first()
    if not refund:
        return {"success": False, "error": "Refund not found"}
    if refund.status not in ("PENDING_APPROVAL", "PENDING"):
        return {"success": False, "error": f"Refund cannot be approved in status '{refund.status}'"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "refund_id": inp.refund_id}

    refund.status = "APPROVED"
    refund.approved_by = inp.approved_by
    db.commit()
    return {
        "success": True,
        "refund_id": refund.id,
        "status": "APPROVED",
        "approved_by": inp.approved_by,
    }


def handle_execute_refund(db: Session, ctx: ToolContext, inp: ExecuteRefundInput) -> Dict[str, Any]:
    """
    Executes an approved refund through MockPaymentProvider.
    Mandatory verification after provider response.
    Returns UNKNOWN if provider times out — caller must NOT assume failure.
    """
    refund = db.query(Refund).filter(
        Refund.id == inp.refund_id,
        Refund.organization_id == ctx.organization_id,
    ).first()
    if not refund:
        return {"success": False, "status": "FAILED", "error": "Refund not found"}

    # Revalidate state — policy rechecked at this moment, not from Phase 7
    if refund.status not in ("APPROVED",):
        return {
            "success": False,
            "status": "BLOCKED",
            "error": f"Refund is not in APPROVED state (current: {refund.status}). Cannot execute.",
        }

    if ctx.is_dry_run():
        return {
            "success": True,
            "dry_run": True,
            "refund_id": inp.refund_id,
            "amount": float(refund.amount),
        }

    # Call mock payment provider
    provider_result = MockPaymentProvider.execute_refund(
        refund_id=refund.id,
        amount=float(refund.amount),
        scenario=inp.mock_scenario,
    )

    provider_status = provider_result.get("status")

    if provider_status == "SUCCESS":
        refund.status = "COMPLETED"
        refund.transaction_id = provider_result.get("transaction_id")
        refund.processed_at = datetime.now(timezone.utc)
        db.commit()
        # Verification: reload and confirm
        db.refresh(refund)
        verified = (refund.status == "COMPLETED")
        return {
            "success": True,
            "status": "SUCCEEDED",
            "refund_id": refund.id,
            "transaction_id": provider_result.get("transaction_id"),
            "amount": float(refund.amount),
            "verified": verified,
        }
    elif provider_status == "TIMEOUT":
        # Do NOT mark as failed — status unknown
        # Caller must query provider status before retrying
        return {
            "success": False,
            "status": "UNKNOWN",
            "refund_id": refund.id,
            "message": "Payment provider timed out. Do not retry without querying provider status first.",
            "provider_reference": provider_result.get("reference"),
        }
    elif provider_status == "ALREADY_REFUNDED":
        refund.status = "ALREADY_PROCESSED"
        db.commit()
        return {
            "success": False,
            "status": "FAILED",
            "error_code": "ALREADY_REFUNDED",
            "refund_id": refund.id,
        }
    else:
        # FAILED
        refund.status = "FAILED"
        db.commit()
        return {
            "success": False,
            "status": "FAILED",
            "error_code": provider_result.get("error_code", "PROVIDER_FAILURE"),
            "refund_id": refund.id,
            "message": provider_result.get("message"),
        }
