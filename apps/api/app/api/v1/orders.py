from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.order_service import OrderService
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderItemInput(BaseModel):
    product_variant_id: str
    quantity: int = Field(..., gt=0, example=1)


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItemInput]
    coupon_code: Optional[str] = None
    warehouse_id: Optional[str] = None
    shipping_address_id: Optional[str] = None
    billing_address_id: Optional[str] = None
    simulate_payment_failure: bool = False


@router.get("")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "placed_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List orders with database-level pagination, customer search, and status filters."""
    items, total = OrderService.list_orders(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status,
        customer_id=customer_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    data = []
    for o in items:
        data.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "customer_name": o.customer.name if o.customer else "Unknown",
            "customer_email": o.customer.email if o.customer else "",
            "status": o.status,
            "payment_status": o.payment_status,
            "fulfillment_status": o.fulfillment_status,
            "items_count": len(o.items),
            "subtotal": o.subtotal,
            "discount_amount": o.discount_amount,
            "tax_amount": o.tax_amount,
            "shipping_amount": o.shipping_amount,
            "total_amount": o.total_amount,
            "currency": o.currency,
            "placed_at": o.placed_at.isoformat() if o.placed_at else None
        })

    return {
        "data": data,
        "meta": {"page": page, "page_size": page_size, "total": total}
    }


@router.get("/{order_id}")
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive order detail view with items, payments, shipments, returns, and refunds."""
    order = OrderService.get_order(db, order_id, current_user.organization_id)
    TenantService.verify_resource_ownership(order, current_user, db, "order")

    items_data = []
    for itm in order.items:
        items_data.append({
            "id": itm.id,
            "product_id": itm.product_id,
            "product_variant_id": itm.product_variant_id,
            "product_name": itm.product_name_snapshot,
            "sku": itm.sku_snapshot,
            "size": itm.size_snapshot,
            "color": itm.color_snapshot,
            "quantity": itm.quantity,
            "unit_price": itm.unit_price,
            "total_amount": itm.total_amount
        })

    payments_data = []
    for p in order.payments:
        payments_data.append({
            "id": p.id,
            "reference": p.payment_reference,
            "provider": p.provider,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "method": p.payment_method_type,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    shipments_data = []
    for s in order.shipments:
        shipments_data.append({
            "id": s.id,
            "tracking_number": s.tracking_number,
            "carrier": s.carrier,
            "status": s.status,
            "last_location": s.last_location,
            "estimated_delivery_date": s.estimated_delivery_date.isoformat() if s.estimated_delivery_date else None,
            "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None
        })

    returns_data = []
    for r in order.returns:
        returns_data.append({
            "id": r.id,
            "return_number": r.return_number,
            "status": r.status,
            "reason": r.reason,
            "requested_at": r.requested_at.isoformat() if r.requested_at else None
        })

    refunds_data = []
    for rf in order.refunds:
        refunds_data.append({
            "id": rf.id,
            "refund_number": rf.refund_number,
            "amount": rf.amount,
            "status": rf.status,
            "reason": rf.reason
        })

    return {
        "data": {
            "id": order.id,
            "order_number": order.order_number,
            "customer": {
                "id": order.customer.id if order.customer else None,
                "name": order.customer.name if order.customer else "",
                "email": order.customer.email if order.customer else "",
                "phone": order.customer.phone if order.customer else ""
            },
            "status": order.status,
            "payment_status": order.payment_status,
            "fulfillment_status": order.fulfillment_status,
            "currency": order.currency,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "shipping_amount": order.shipping_amount,
            "tax_amount": order.tax_amount,
            "total_amount": order.total_amount,
            "coupon_code": order.coupon.code if order.coupon else None,
            "items": items_data,
            "payments": payments_data,
            "shipments": shipments_data,
            "returns": returns_data,
            "refunds": refunds_data,
            "placed_at": order.placed_at.isoformat() if order.placed_at else None
        },
        "meta": {"request_id": f"ord_{order.id[:8]}"}
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a new e-commerce order with automatic inventory reservation and mock payment capture."""
    order = OrderService.create_order(
        db=db,
        organization_id=current_user.organization_id,
        customer_id=payload.customer_id,
        items=[itm.dict() for itm in payload.items],
        coupon_code=payload.coupon_code,
        warehouse_id=payload.warehouse_id,
        shipping_address_id=payload.shipping_address_id,
        billing_address_id=payload.billing_address_id,
        simulate_payment_failure=payload.simulate_payment_failure,
        actor_id=current_user.id
    )
    return {
        "data": {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": order.total_amount
        },
        "meta": {"message": f"Order {order.order_number} created with status {order.status}."}
    }


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    current_user: User = Depends(require_permission("orders.cancel")),
    db: Session = Depends(get_db)
):
    """Cancel an active order and release reserved inventory."""
    order = OrderService.cancel_order(
        db=db,
        order_id=order_id,
        organization_id=current_user.organization_id,
        actor_id=current_user.id
    )
    return {"status": "success", "message": f"Order {order.order_number} has been cancelled."}
