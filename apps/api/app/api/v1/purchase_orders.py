from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.operations import PurchaseOrder, PurchaseOrderItem

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("")
def list_purchase_orders(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(PurchaseOrder).filter(PurchaseOrder.organization_id == current_user.organization_id)
    if status:
        q = q.filter(PurchaseOrder.status == status)

    orders = q.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()
    results = []
    for po in orders:
        results.append({
            "id": po.id,
            "po_number": po.po_number,
            "vendor_name": po.vendor.name if po.vendor else "Supplier",
            "department": po.department or "Inventory",
            "subtotal": po.subtotal,
            "tax": po.tax,
            "total": po.total,
            "currency": po.currency,
            "status": po.status,
            "issue_date": po.issue_date.isoformat() if po.issue_date else None,
            "created_at": po.created_at.isoformat() if po.created_at else None,
            "items_count": len(po.items)
        })
    return {"purchase_orders": results, "total": len(results)}


@router.get("/{po_id}")
def get_purchase_order(
    po_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == po_id,
        PurchaseOrder.organization_id == current_user.organization_id
    ).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PO_NOT_FOUND", "message": f"Purchase order '{po_id}' not found."}}
        )

    return {
        "id": po.id,
        "po_number": po.po_number,
        "vendor_name": po.vendor.name if po.vendor else "Supplier",
        "department": po.department,
        "subtotal": po.subtotal,
        "tax": po.tax,
        "total": po.total,
        "currency": po.currency,
        "status": po.status,
        "issue_date": po.issue_date.isoformat() if po.issue_date else None,
        "created_at": po.created_at.isoformat() if po.created_at else None,
        "items": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            } for item in po.items
        ]
    }
