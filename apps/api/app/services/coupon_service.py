from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Coupon


class CouponService:
    """
    Deterministic Coupon Calculation & Validation Service.
    Validates limits, dates, minimum order values, and maximum discount caps.
    """

    @staticmethod
    def create_coupon(
        db: Session,
        organization_id: str,
        code: str,
        discount_type: str,
        discount_value: float,
        description: Optional[str] = None,
        minimum_order_value: float = 0.0,
        maximum_discount: Optional[float] = None,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        usage_limit: Optional[int] = None
    ) -> Coupon:
        clean_code = code.strip().upper()
        existing = db.query(Coupon).filter(
            Coupon.organization_id == organization_id,
            Coupon.code == clean_code
        ).first()
        if existing:
            return existing

        coupon = Coupon(
            organization_id=organization_id,
            code=clean_code,
            description=description,
            discount_type=discount_type.upper(),
            discount_value=discount_value,
            minimum_order_value=minimum_order_value,
            maximum_discount=maximum_discount,
            starts_at=starts_at,
            expires_at=expires_at,
            usage_limit=usage_limit,
            usage_count=0,
            is_active=True
        )
        db.add(coupon)
        db.commit()
        db.refresh(coupon)
        return coupon

    @staticmethod
    def validate_coupon(
        db: Session,
        organization_id: str,
        code: str,
        subtotal: float
    ) -> Tuple[float, Coupon]:
        clean_code = code.strip().upper()
        coupon = db.query(Coupon).filter(
            Coupon.organization_id == organization_id,
            Coupon.code == clean_code
        ).first()

        if not coupon or not coupon.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Coupon '{clean_code}' is invalid or inactive.")

        now = datetime.now(timezone.utc)
        if coupon.starts_at and now < coupon.starts_at.replace(tzinfo=timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is not yet active.")
        if coupon.expires_at and now > coupon.expires_at.replace(tzinfo=timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired.")

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit has been reached.")

        if subtotal < coupon.minimum_order_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order subtotal (₹{subtotal}) is below minimum requirement of ₹{coupon.minimum_order_value} for this coupon."
            )

        if coupon.discount_type == "PERCENTAGE":
            discount = round(subtotal * (coupon.discount_value / 100.0), 2)
            if coupon.maximum_discount:
                discount = min(discount, coupon.maximum_discount)
        else:
            discount = min(subtotal, coupon.discount_value)

        return discount, coupon

    @staticmethod
    def record_coupon_usage(db: Session, coupon_id: str):
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if coupon:
            coupon.usage_count += 1
            db.commit()
