from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Refund, Order, Payment
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.services.payment_service import PaymentService
from apps.api.app.events.publisher import BusinessEventPublisher


class RefundService:
    """
    Refund Management & Financial Safeguard Service.
    Guarantees refund amounts never exceed paid totals and logs all disbursements.
    """

    @staticmethod
    def request_refund(
        db: Session,
        organization_id: str,
        order_id: str,
        customer_id: str,
        amount: float,
        reason: str = "Return approved refund",
        payment_id: Optional[str] = None,
        actor_id: str = "system"
    ) -> Refund:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.organization_id == organization_id,
            Order.customer_id == customer_id
        ).first()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or customer mismatch.")

        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount must be positive.")

        # Calculate already refunded or pending approval refunds
        existing_refunded = db.query(func.coalesce(func.sum(Refund.amount), 0.0)).filter(
            Refund.organization_id == organization_id,
            Refund.order_id == order_id,
            Refund.status.in_(["REQUESTED", "PENDING_APPROVAL", "APPROVED", "PROCESSING", "COMPLETED"])
        ).scalar()

        eligible_balance = round(order.total_amount - existing_refunded, 2)
        if amount > eligible_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested refund (₹{amount}) exceeds eligible balance (₹{eligible_balance})."
            )

        # Resolve payment if not specified
        if not payment_id and order.payments:
            captured_payment = next((p for p in order.payments if p.status == "CAPTURED"), None)
            if captured_payment:
                payment_id = captured_payment.id

        ref_num = f"REF-{generate_uuid()[:8].upper()}"
        refund = Refund(
            organization_id=organization_id,
            order_id=order_id,
            customer_id=customer_id,
            payment_id=payment_id,
            refund_number=ref_num,
            amount=amount,
            currency="INR",
            reason=reason,
            status="APPROVED"
        )
        db.add(refund)
        db.commit()
        db.refresh(refund)

        # Audit & Event
        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="USER" if actor_id != "system" else "SYSTEM",
            actor_name="Operations Staff",
            action="REFUND_REQUESTED",
            resource_type="refund",
            resource_id=refund.id,
            result="SUCCESS",
            log_metadata={"refund_number": ref_num, "amount": amount, "reason": reason}
        )
        db.add(audit)
        db.commit()

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="REFUND_REQUESTED",
            title=f"Refund {ref_num} requested: ₹{amount}",
            content=f"Order {order.order_number}. Reason: {reason}",
            metadata={"refund_id": refund.id, "order_id": order_id, "amount": amount}
        )

        return refund

    @staticmethod
    def execute_refund(db: Session, refund_id: str, organization_id: str, actor_id: str = "system") -> Refund:
        refund = db.query(Refund).filter(
            Refund.id == refund_id,
            Refund.organization_id == organization_id
        ).first()

        if not refund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund record not found.")

        if refund.status == "COMPLETED":
            return refund

        # Update payment status if linked
        if refund.payment_id:
            PaymentService.refund_payment(db, organization_id, refund.payment_id, refund.amount)

        # Update order payment status
        order = refund.order
        if order:
            total_completed_refunds = db.query(func.coalesce(func.sum(Refund.amount), 0.0)).filter(
                Refund.organization_id == organization_id,
                Refund.order_id == order.id,
                Refund.status == "COMPLETED"
            ).scalar() + refund.amount

            order.payment_status = "REFUNDED" if total_completed_refunds >= order.total_amount else "PARTIALLY_REFUNDED"

        refund.status = "COMPLETED"
        db.commit()
        db.refresh(refund)

        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="SYSTEM",
            actor_name="Refund Engine",
            action="REFUND_COMPLETED",
            resource_type="refund",
            resource_id=refund.id,
            result="SUCCESS",
            log_metadata={"refund_number": refund.refund_number, "amount": refund.amount}
        )
        db.add(audit)
        db.commit()

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="REFUND_COMPLETED",
            title=f"Refund {refund.refund_number} completed: ₹{refund.amount}",
            content=f"Funds reversed for order {order.order_number if order else 'unknown'}.",
            metadata={"refund_id": refund.id, "amount": refund.amount}
        )

        return refund

    @staticmethod
    def list_refunds(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Refund], int]:
        query = db.query(Refund).filter(Refund.organization_id == organization_id)
        if status_filter:
            query = query.filter(Refund.status == status_filter.upper())
        total = query.count()
        offset = max(0, (page - 1) * page_size)
        items = query.order_by(Refund.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total
