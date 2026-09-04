from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.ecommerce import Coupon
from apps.api.app.services.coupon_service import CouponService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/coupons", tags=["Coupons"])


class CreateCouponRequest(BaseModel):
    code: str = Field(..., example="SUMMER20")
    discount_type: str = Field("PERCENTAGE", example="PERCENTAGE")
    discount_value: float = Field(..., gt=0, example=20.0)
    description: Optional[str] = "20% off on all summer essentials"
    minimum_order_value: float = Field(0.0, ge=0, example=1000.0)
    maximum_discount: Optional[float] = Field(None, example=500.0)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, example=1000)


class ValidateCouponRequest(BaseModel):
    code: str
    subtotal: float = Field(..., ge=0)


@router.get("")
def list_coupons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    coupons = db.query(Coupon).filter(Coupon.organization_id == current_user.organization_id).all()
    data = []
    for c in coupons:
        data.append({
            "id": c.id,
            "code": c.code,
            "description": c.description,
            "type": c.discount_type,
            "value": c.discount_value,
            "minimum_order_value": c.minimum_order_value,
            "maximum_discount": c.maximum_discount,
            "usage_count": c.usage_count,
            "usage_limit": c.usage_limit,
            "is_active": c.is_active,
            "starts_at": c.starts_at.isoformat() if c.starts_at else None,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None
        })
    return {"data": data, "meta": {"total": len(data)}}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_coupon(
    payload: CreateCouponRequest,
    current_user: User = Depends(require_permission("coupons.create")),
    db: Session = Depends(get_db)
):
    c = CouponService.create_coupon(
        db=db,
        organization_id=current_user.organization_id,
        code=payload.code,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        description=payload.description,
        minimum_order_value=payload.minimum_order_value,
        maximum_discount=payload.maximum_discount,
        starts_at=payload.starts_at,
        expires_at=payload.expires_at,
        usage_limit=payload.usage_limit
    )
    return {"data": {"id": c.id, "code": c.code, "value": c.discount_value}, "meta": {"message": "Coupon created."}}


@router.post("/validate")
def validate_coupon(
    payload: ValidateCouponRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    discount, coupon = CouponService.validate_coupon(
        db=db,
        organization_id=current_user.organization_id,
        code=payload.code,
        subtotal=payload.subtotal
    )
    return {
        "data": {
            "code": coupon.code,
            "discount_amount": discount,
            "effective_total": max(0.0, payload.subtotal - discount)
        },
        "meta": {"valid": True}
    }
