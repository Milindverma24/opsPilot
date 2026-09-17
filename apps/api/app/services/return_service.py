from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Return, ReturnItem, Order, OrderItem
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher

RETURN_WINDOW_DAYS = 14


class ReturnEligibilityService:
    """
    Deterministic Return Policy Engine.
    Evaluates order fulfillment status, delivery timestamps, and allowable return windows.
    """

    @staticmethod
    def check_eligibility(order: Order, evaluation_date: Optional[datetime] = None) -> Tuple[bool, str]:
        if order.status != "DELIVERED":
            return False, f"Order status is '{order.status}'. Returns are only permitted for delivered orders."

        now = evaluation_date or datetime.now(timezone.utc)
        delivery_date = None

        # Check shipment delivery date
        if order.shipments:
            for s in order.shipments:
                if s.status == "DELIVERED" and s.delivered_at:
                    delivery_date = s.delivered_at
                    break

        # Fallback to order placement date if delivery timestamp missing
        ref_date = delivery_date or order.placed_at
        if ref_date:
            if ref_date.tzinfo is None:
                ref_date = ref_date.replace(tzinfo=timezone.utc)
            deadline = ref_date + timedelta(days=RETURN_WINDOW_DAYS)
            if now > deadline:
                days_elapsed = (now - ref_date).days
                return False, f"Return window expired ({days_elapsed} days elapsed; allowed limit is {RETURN_WINDOW_DAYS} days)."

        return True, "Order items are eligible for return under company policy."


class ReturnService:
    """
    Return Management Service.
    Orchestrates return requests, inspection condition checks, and approval lifecycle.
    """

    @staticmethod
    def request_return(
        db: Session,
        organization_id: str,
        order_id: str,
        customer_id: str,
        items: List[Dict[str, Any]],
        reason: str = "WRONG_SIZE",
        actor_id: str = "customer"
    ) -> Return:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.organization_id == organization_id,
            Order.customer_id == customer_id
        ).first()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or customer mismatch.")

        # Check policy eligibility
        is_eligible, eligibility_reason = ReturnEligibilityService.check_eligibility(order)
        if not is_eligible:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=eligibility_reason)

        ret_num = f"RET-{generate_uuid()[:8].upper()}"
        ret = Return(
            organization_id=organization_id,
            order_id=order_id,
            customer_id=customer_id,
            return_number=ret_num,
            status="REQUESTED",
            reason=reason.upper(),
            requested_at=get_utc_now()
        )
        db.add(ret)
        db.flush()

        for itm in items:
            ri = ReturnItem(
                organization_id=organization_id,
                return_id=ret.id,
                order_item_id=itm["order_item_id"],
                quantity=itm.get("quantity", 1),
                reason=itm.get("reason", reason),
                condition=itm.get("condition", "NEW").upper()
            )
            db.add(ri)

        db.commit()
        db.refresh(ret)

        # Audit & event
        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="USER",
            actor_name="Customer",
            action="RETURN_REQUESTED",
            resource_type="return",
            resource_id=ret.id,
            result="SUCCESS",
            log_metadata={"return_number": ret_num, "reason": reason}
        )
        db.add(audit)
        db.commit()

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="RETURN_REQUESTED",
            title=f"Return {ret_num} requested for order {order.order_number}",
            content=f"Reason: {reason}.",
            metadata={"return_id": ret.id, "order_id": order_id}
        )

        return ret

    @staticmethod
    def approve_return(db: Session, return_id: str, organization_id: str, actor_id: str = "system") -> Return:
        ret = db.query(Return).filter(
            Return.id == return_id,
            Return.organization_id == organization_id
        ).first()

        if not ret:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return record not found.")

        ret.status = "APPROVED"
        ret.approved_at = get_utc_now()
        db.commit()
        db.refresh(ret)

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="RETURN_APPROVED",
            title=f"Return {ret.return_number} approved",
            content="Customer authorized to dispatch return parcel.",
            metadata={"return_id": ret.id, "order_id": ret.order_id}
        )
        return ret

    @staticmethod
    def reject_return(db: Session, return_id: str, organization_id: str, reason: str = "Inspection condition failed", actor_id: str = "system") -> Return:
        ret = db.query(Return).filter(
            Return.id == return_id,
            Return.organization_id == organization_id
        ).first()

        if not ret:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return record not found.")

        ret.status = "REJECTED"
        db.commit()
        db.refresh(ret)
        return ret

    @staticmethod
    def list_returns(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Return], int]:
        query = db.query(Return).filter(Return.organization_id == organization_id)
        if status_filter:
            query = query.filter(Return.status == status_filter.upper())
        total = query.count()
        offset = max(0, (page - 1) * page_size)
        items = query.order_by(Return.requested_at.desc()).offset(offset).limit(page_size).all()
        return items, total
