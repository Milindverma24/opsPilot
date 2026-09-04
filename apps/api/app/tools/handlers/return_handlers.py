"""
Return Tool Handlers — Phase 8.
request_return, approve_return, reject_return.
All call ReturnService — no direct DB writes.
"""
from __future__ import annotations

from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.models.ecommerce import Return, Order
from apps.api.app.models.operations import Customer
from apps.api.app.services.return_service import ReturnService
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import RequestReturnInput, ApproveReturnInput, RejectReturnInput


def handle_request_return(db: Session, ctx: ToolContext, inp: RequestReturnInput) -> Dict[str, Any]:
    # Ownership: customer must own this order
    order = db.query(Order).filter(
        Order.id == inp.order_id,
        Order.organization_id == ctx.organization_id,
        Order.customer_id == inp.customer_id,
    ).first()
    if not order:
        return {"success": False, "error": "Order not found or customer does not own this order"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "order_id": inp.order_id, "would_create_return": True}

    try:
        return_obj = ReturnService.create_return(
            db=db,
            organization_id=ctx.organization_id,
            order_id=inp.order_id,
            customer_id=inp.customer_id,
            reason=inp.reason,
            item_ids=inp.order_item_ids,
        )
        return {
            "success": True,
            "return_id": return_obj.id,
            "order_id": inp.order_id,
            "status": return_obj.status,
            "reason": inp.reason,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_approve_return(db: Session, ctx: ToolContext, inp: ApproveReturnInput) -> Dict[str, Any]:
    ret = db.query(Return).filter(
        Return.id == inp.return_id,
        Return.organization_id == ctx.organization_id,
    ).first()
    if not ret:
        return {"success": False, "error": "Return not found"}
    if ret.status not in ("REQUESTED", "PENDING"):
        return {"success": False, "error": f"Return cannot be approved in status '{ret.status}'"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "return_id": inp.return_id}

    try:
        result = ReturnService.approve_return(
            db=db,
            organization_id=ctx.organization_id,
            return_id=inp.return_id,
            approved_by=inp.approved_by,
            notes=inp.notes,
        )
        return {"success": True, "return_id": inp.return_id, "status": "APPROVED"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_reject_return(db: Session, ctx: ToolContext, inp: RejectReturnInput) -> Dict[str, Any]:
    ret = db.query(Return).filter(
        Return.id == inp.return_id,
        Return.organization_id == ctx.organization_id,
    ).first()
    if not ret:
        return {"success": False, "error": "Return not found"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "return_id": inp.return_id}

    try:
        result = ReturnService.reject_return(
            db=db,
            organization_id=ctx.organization_id,
            return_id=inp.return_id,
            rejected_by=inp.rejected_by,
            reason=inp.reason,
        )
        return {"success": True, "return_id": inp.return_id, "status": "REJECTED"}
    except Exception as e:
        return {"success": False, "error": str(e)}
