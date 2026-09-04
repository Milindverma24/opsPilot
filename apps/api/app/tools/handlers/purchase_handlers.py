"""
Purchase Tool Handlers — Phase 8.
create_purchase_order, submit_purchase_order.
"""
from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.models.operations import Vendor, PurchaseOrder
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import CreatePurchaseOrderInput, SubmitPurchaseOrderInput


def handle_create_purchase_order(db: Session, ctx: ToolContext, inp: CreatePurchaseOrderInput) -> Dict[str, Any]:
    vendor = db.query(Vendor).filter(
        Vendor.id == inp.vendor_id,
        Vendor.organization_id == ctx.organization_id,
    ).first()
    if not vendor:
        return {"success": False, "error": "Vendor not found in this organization"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "vendor_id": inp.vendor_id, "items_count": len(inp.items)}

    total = sum(float(item.get("unit_price", 0)) * int(item.get("quantity", 1)) for item in inp.items)
    po = PurchaseOrder(
        organization_id=ctx.organization_id,
        vendor_id=inp.vendor_id,
        po_number=f"PO-{get_utc_now().strftime('%Y%m%d')}-{generate_uuid()[:6].upper()}",
        status="DRAFT",
        total_amount=total,
        notes=inp.notes,
        created_by="AI_AGENT",
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return {
        "success": True,
        "po_id": po.id,
        "po_number": po.po_number,
        "status": "DRAFT",
        "total_amount": total,
        "vendor_id": inp.vendor_id,
    }


def handle_submit_purchase_order(db: Session, ctx: ToolContext, inp: SubmitPurchaseOrderInput) -> Dict[str, Any]:
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == inp.purchase_order_id,
        PurchaseOrder.organization_id == ctx.organization_id,
    ).first()
    if not po:
        return {"success": False, "error": "Purchase order not found"}
    if po.status != "DRAFT":
        return {"success": False, "error": f"PO cannot be submitted from status '{po.status}'"}

    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "po_id": inp.purchase_order_id}

    po.status = "SUBMITTED"
    db.commit()
    return {"success": True, "po_id": po.id, "status": "SUBMITTED"}
