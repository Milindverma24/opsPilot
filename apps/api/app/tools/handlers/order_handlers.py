"""
Order Tool Handlers — Phase 8: cancel_order, update_order.
Business rules enforced: cannot cancel delivered/completed orders.
Ownership validated: customer_id must match order.customer_id.
"""
from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.models.ecommerce import Order
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import CancelOrderInput, UpdateOrderInput

UNCANCELLABLE_STATUSES = {"DELIVERED", "COMPLETED", "CANCELLED", "REFUNDED"}


def handle_cancel_order(db: Session, ctx: ToolContext, inp: CancelOrderInput) -> Dict[str, Any]:
    order = db.query(Order).filter(
        Order.id == inp.order_id,
        Order.organization_id == ctx.organization_id,
    ).first()
    if not order:
        return {"success": False, "error": "Order not found"}
    # Ownership check
    if order.customer_id != inp.customer_id:
        return {"success": False, "error": "Access denied: customer does not own this order"}
    if order.status in UNCANCELLABLE_STATUSES:
        return {"success": False, "error": f"Order cannot be cancelled in status '{order.status}'"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "order_id": inp.order_id, "current_status": order.status}

    order.status = "CANCELLED"
    order.cancellation_reason = inp.reason
    db.commit()
    db.refresh(order)
    # Verification
    assert order.status == "CANCELLED", "Verification failed after cancel"
    return {"success": True, "order_id": order.id, "status": "CANCELLED", "reason": inp.reason}


def handle_update_order(db: Session, ctx: ToolContext, inp: UpdateOrderInput) -> Dict[str, Any]:
    order = db.query(Order).filter(
        Order.id == inp.order_id,
        Order.organization_id == ctx.organization_id,
    ).first()
    if not order:
        return {"success": False, "error": "Order not found"}
    if order.customer_id != inp.customer_id:
        return {"success": False, "error": "Access denied: customer does not own this order"}
    if order.status in ("COMPLETED", "CANCELLED", "DELIVERED"):
        return {"success": False, "error": f"Order cannot be modified in status '{order.status}'"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "order_id": inp.order_id}

    if inp.shipping_address_id:
        order.shipping_address_id = inp.shipping_address_id
    db.commit()
    return {"success": True, "order_id": order.id, "status": order.status}
