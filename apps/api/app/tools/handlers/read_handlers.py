"""
Read-Only Tool Handlers — Phase 8.

All 11 read-only tools. These query existing business services
and return structured data to the agent. No mutations.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.ecommerce import Order, Product, ProductVariant, Inventory, Shipment, Return, Refund, SupportTicket, Warehouse
from apps.api.app.models.operations import Customer, Vendor, PurchaseOrder
from apps.api.app.services.knowledge_service import KnowledgeService
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import (
    GetOrderInput, GetCustomerInput, GetProductInput, GetInventoryInput,
    GetShipmentInput, GetReturnInput, GetRefundInput, SearchKnowledgeInput,
    GetSupportTicketInput, GetVendorInput, GetPurchaseOrderInput,
)


def handle_get_order(db: Session, ctx: ToolContext, inp: GetOrderInput) -> Dict[str, Any]:
    order = db.query(Order).filter(
        Order.organization_id == ctx.organization_id,
        Order.order_number == inp.order_number,
    ).first()
    if not order:
        return {"found": False, "order_number": inp.order_number}
    return {
        "found": True,
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_amount": float(order.total_amount or 0),
        "currency": order.currency or "INR",
        "customer_id": order.customer_id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items_count": len(order.items) if hasattr(order, "items") and order.items else 0,
    }


def handle_get_customer(db: Session, ctx: ToolContext, inp: GetCustomerInput) -> Dict[str, Any]:
    q = db.query(Customer).filter(Customer.organization_id == ctx.organization_id)
    if inp.customer_id:
        q = q.filter(Customer.id == inp.customer_id)
    elif inp.email:
        q = q.filter(Customer.email == inp.email.lower())
    customer = q.first()
    if not customer:
        return {"found": False}
    full_name = " ".join(filter(None, [customer.first_name, customer.last_name])) or customer.name or ""
    return {
        "found": True,
        "customer_id": customer.id,
        "name": full_name,
        "email": customer.email,
        "status": customer.status,
    }


def handle_get_product(db: Session, ctx: ToolContext, inp: GetProductInput) -> Dict[str, Any]:
    q = db.query(Product).filter(Product.organization_id == ctx.organization_id)
    if inp.product_id:
        q = q.filter(Product.id == inp.product_id)
    elif inp.sku:
        q = q.filter(Product.sku == inp.sku.upper())
    elif inp.name_search:
        q = q.filter(Product.name.ilike(f"%{inp.name_search}%"))
    products = q.limit(5).all()
    if not products:
        return {"found": False, "products": []}
    return {
        "found": True,
        "products": [
            {
                "product_id": p.id,
                "name": p.name,
                "sku": p.sku,
                "base_price": float(p.base_price or 0),
                "status": p.status,
            }
            for p in products
        ],
    }


def handle_get_inventory(db: Session, ctx: ToolContext, inp: GetInventoryInput) -> Dict[str, Any]:
    q = db.query(Inventory).filter(Inventory.organization_id == ctx.organization_id)
    if inp.variant_id:
        q = q.filter(Inventory.variant_id == inp.variant_id)
    if inp.warehouse_id:
        q = q.filter(Inventory.warehouse_id == inp.warehouse_id)
    items = q.limit(20).all()
    return {
        "found": len(items) > 0,
        "inventory": [
            {
                "variant_id": i.variant_id,
                "warehouse_id": i.warehouse_id,
                "quantity_on_hand": i.quantity_on_hand,
                "quantity_reserved": i.quantity_reserved,
                "quantity_available": (i.quantity_on_hand or 0) - (i.quantity_reserved or 0),
            }
            for i in items
        ],
    }


def handle_get_shipment(db: Session, ctx: ToolContext, inp: GetShipmentInput) -> Dict[str, Any]:
    q = db.query(Shipment).filter(Shipment.organization_id == ctx.organization_id)
    if inp.shipment_id:
        q = q.filter(Shipment.id == inp.shipment_id)
    elif inp.order_id:
        q = q.filter(Shipment.order_id == inp.order_id)
    elif inp.tracking_number:
        q = q.filter(Shipment.tracking_number == inp.tracking_number)
    shipment = q.first()
    if not shipment:
        return {"found": False}
    return {
        "found": True,
        "shipment_id": shipment.id,
        "status": shipment.status,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "estimated_delivery_date": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
    }


def handle_get_return(db: Session, ctx: ToolContext, inp: GetReturnInput) -> Dict[str, Any]:
    q = db.query(Return).filter(Return.organization_id == ctx.organization_id)
    if inp.return_id:
        q = q.filter(Return.id == inp.return_id)
    elif inp.order_id:
        q = q.filter(Return.order_id == inp.order_id)
    ret = q.first()
    if not ret:
        return {"found": False}
    return {
        "found": True,
        "return_id": ret.id,
        "order_id": ret.order_id,
        "status": ret.status,
        "reason": ret.reason,
        "requested_at": ret.created_at.isoformat() if ret.created_at else None,
    }


def handle_get_refund(db: Session, ctx: ToolContext, inp: GetRefundInput) -> Dict[str, Any]:
    q = db.query(Refund).filter(Refund.organization_id == ctx.organization_id)
    if inp.refund_id:
        q = q.filter(Refund.id == inp.refund_id)
    elif inp.order_id:
        q = q.filter(Refund.order_id == inp.order_id)
    refund = q.first()
    if not refund:
        return {"found": False}
    return {
        "found": True,
        "refund_id": refund.id,
        "order_id": refund.order_id,
        "amount": float(refund.amount or 0),
        "status": refund.status,
        "reason": refund.reason,
    }


def handle_search_knowledge(db: Session, ctx: ToolContext, inp: SearchKnowledgeInput) -> Dict[str, Any]:
    try:
        svc = KnowledgeService()
        results = svc.search(db, ctx.organization_id, inp.query, top_k=inp.top_k)
        return {
            "found": len(results) > 0,
            "results": results,
            "query": inp.query,
        }
    except Exception as e:
        return {"found": False, "results": [], "error": str(e)}


def handle_get_support_ticket(db: Session, ctx: ToolContext, inp: GetSupportTicketInput) -> Dict[str, Any]:
    q = db.query(SupportTicket).filter(SupportTicket.organization_id == ctx.organization_id)
    if inp.ticket_id:
        q = q.filter(SupportTicket.id == inp.ticket_id)
    elif inp.customer_id:
        q = q.filter(SupportTicket.customer_id == inp.customer_id)
    ticket = q.order_by(SupportTicket.created_at.desc()).first()
    if not ticket:
        return {"found": False}
    return {
        "found": True,
        "ticket_id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }


def handle_get_vendor(db: Session, ctx: ToolContext, inp: GetVendorInput) -> Dict[str, Any]:
    q = db.query(Vendor).filter(Vendor.organization_id == ctx.organization_id)
    if inp.vendor_id:
        q = q.filter(Vendor.id == inp.vendor_id)
    elif inp.name_search:
        q = q.filter(Vendor.name.ilike(f"%{inp.name_search}%"))
    vendor = q.first()
    if not vendor:
        return {"found": False}
    return {
        "found": True,
        "vendor_id": vendor.id,
        "name": vendor.name,
        "status": vendor.status,
        "contact_email": vendor.contact_email,
    }


def handle_get_purchase_order(db: Session, ctx: ToolContext, inp: GetPurchaseOrderInput) -> Dict[str, Any]:
    q = db.query(PurchaseOrder).filter(PurchaseOrder.organization_id == ctx.organization_id)
    if inp.po_id:
        q = q.filter(PurchaseOrder.id == inp.po_id)
    elif inp.vendor_id:
        q = q.filter(PurchaseOrder.vendor_id == inp.vendor_id)
    po = q.order_by(PurchaseOrder.created_at.desc()).first()
    if not po:
        return {"found": False}
    return {
        "found": True,
        "po_id": po.id,
        "vendor_id": po.vendor_id,
        "status": po.status,
        "total_amount": float(po.total_amount or 0),
    }
