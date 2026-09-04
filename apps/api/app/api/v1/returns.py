from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.return_service import ReturnService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/returns", tags=["Returns"])


class ReturnItemInput(BaseModel):
    order_item_id: str
    quantity: int = Field(1, ge=1)
    reason: Optional[str] = "WRONG_SIZE"
    condition: Optional[str] = "NEW"


class RequestReturnPayload(BaseModel):
    order_id: str
    customer_id: str
    items: List[ReturnItemInput]
    reason: str = "WRONG_SIZE"


@router.get("")
def list_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = ReturnService.list_returns(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status
    )
    data = []
    for r in items:
        data.append({
            "id": r.id,
            "return_number": r.return_number,
            "order_id": r.order_id,
            "order_number": r.order.order_number if r.order else None,
            "customer_id": r.customer_id,
            "customer_name": r.order.customer.name if r.order and r.order.customer else "",
            "status": r.status,
            "reason": r.reason,
            "items_count": len(r.items),
            "requested_at": r.requested_at.isoformat() if r.requested_at else None,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None
        })
    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("", status_code=status.HTTP_201_CREATED)
def request_return(
    payload: RequestReturnPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiates return with company policy return window eligibility evaluation."""
    ret = ReturnService.request_return(
        db=db,
        organization_id=current_user.organization_id,
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        items=[itm.dict() for itm in payload.items],
        reason=payload.reason,
        actor_id=current_user.id
    )
    return {
        "data": {
            "id": ret.id,
            "return_number": ret.return_number,
            "status": ret.status
        },
        "meta": {"message": f"Return {ret.return_number} requested successfully."}
    }


@router.post("/{return_id}/approve")
def approve_return(
    return_id: str,
    current_user: User = Depends(require_permission("returns.approve")),
    db: Session = Depends(get_db)
):
    ret = ReturnService.approve_return(
        db=db,
        return_id=return_id,
        organization_id=current_user.organization_id,
        actor_id=current_user.id
    )
    return {"status": "success", "return_number": ret.return_number, "new_status": ret.status}
