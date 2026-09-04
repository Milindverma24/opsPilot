from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.refund_service import RefundService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/refunds", tags=["Refunds"])


class RequestRefundPayload(BaseModel):
    order_id: str
    customer_id: str
    amount: float = Field(..., gt=0)
    reason: str = "Return approved refund"
    payment_id: Optional[str] = None


@router.get("")
def list_refunds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = RefundService.list_refunds(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status
    )
    data = []
    for rf in items:
        data.append({
            "id": rf.id,
            "refund_number": rf.refund_number,
            "order_id": rf.order_id,
            "order_number": rf.order.order_number if rf.order else None,
            "customer_id": rf.customer_id,
            "customer_name": rf.order.customer.name if rf.order and rf.order.customer else "",
            "amount": rf.amount,
            "currency": rf.currency,
            "status": rf.status,
            "reason": rf.reason,
            "created_at": rf.created_at.isoformat() if rf.created_at else None
        })
    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("", status_code=status.HTTP_201_CREATED)
def request_refund(
    payload: RequestRefundPayload,
    current_user: User = Depends(require_permission("refunds.create")),
    db: Session = Depends(get_db)
):
    """Initiates a refund request with validation against paid order total balance."""
    rf = RefundService.request_refund(
        db=db,
        organization_id=current_user.organization_id,
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        reason=payload.reason,
        payment_id=payload.payment_id,
        actor_id=current_user.id
    )
    return {"data": {"id": rf.id, "refund_number": rf.refund_number, "amount": rf.amount, "status": rf.status}}


@router.post("/{refund_id}/execute")
def execute_refund(
    refund_id: str,
    current_user: User = Depends(require_permission("refunds.approve")),
    db: Session = Depends(get_db)
):
    """Executes the refund through mock payment reversal and updates payment status."""
    rf = RefundService.execute_refund(
        db=db,
        refund_id=refund_id,
        organization_id=current_user.organization_id,
        actor_id=current_user.id
    )
    return {"status": "success", "refund_number": rf.refund_number, "new_status": rf.status}
