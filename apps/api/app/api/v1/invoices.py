from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.operations import Invoice, InvoiceLineItem
from apps.api.app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("")
def list_invoices(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Invoice).filter(Invoice.organization_id == current_user.organization_id)
    if status:
        q = q.filter(Invoice.status == status)

    invoices = q.order_by(Invoice.created_at.desc()).limit(limit).all()
    results = []
    for inv in invoices:
        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_name": inv.vendor.name if inv.vendor else "Vendor",
            "total": inv.total,
            "currency": inv.currency,
            "status": inv.status,
            "risk_level": inv.risk_level,
            "purchase_order_number": inv.purchase_order_number,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    return {"invoices": results, "total": len(results)}


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tenant-isolated invoice retrieval.
    If the invoice does not belong to the user's organization, returns 404.
    """
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.organization_id == current_user.organization_id
    ).first()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or access denied"
        )

    lines = []
    for li in inv.line_items:
        lines.append({
            "id": li.id,
            "description": li.description,
            "quantity": li.quantity,
            "unit_price": li.unit_price,
            "tax": li.tax,
            "total": li.total
        })

    return {
        "id": inv.id,
        "organization_id": inv.organization_id,
        "invoice_number": inv.invoice_number,
        "vendor_id": inv.vendor_id,
        "vendor_name": inv.vendor.name if inv.vendor else None,
        "purchase_order_number": inv.purchase_order_number,
        "subtotal": inv.subtotal,
        "tax": inv.tax,
        "total": inv.total,
        "currency": inv.currency,
        "status": inv.status,
        "risk_level": inv.risk_level,
        "risk_score": inv.risk_score,
        "ai_confidence": inv.ai_confidence,
        "line_items": lines,
        "created_at": inv.created_at.isoformat() if inv.created_at else None
    }
