from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.ecommerce import Payment
from apps.api.app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


class CapturePaymentRequest(BaseModel):
    order_id: str
    amount: float = Field(..., gt=0)
    payment_method_type: str = "UPI"
    simulate_failure: bool = False


@router.get("")
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Payment).filter(Payment.organization_id == current_user.organization_id)
    if status:
        query = query.filter(Payment.status == status.upper())

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(Payment.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for p in items:
        data.append({
            "id": p.id,
            "order_id": p.order_id,
            "order_number": p.order.order_number if p.order else None,
            "payment_reference": p.payment_reference,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "method": p.payment_method_type,
            "provider": p.provider,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/capture", status_code=status.HTTP_201_CREATED)
def capture_payment(
    payload: CapturePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = PaymentService.capture_payment(
        db=db,
        organization_id=current_user.organization_id,
        order_id=payload.order_id,
        amount=payload.amount,
        payment_method_type=payload.payment_method_type,
        simulate_failure=payload.simulate_failure
    )
    return {"data": {"id": p.id, "reference": p.payment_reference, "status": p.status, "amount": p.amount}}
