from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Payment, Order
from apps.api.app.models.base import generate_uuid
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher


class PaymentService:
    """
    Mock Payment Gateway Service.
    Never persists real card numbers, CVVs, or bank secrets.
    Provides deterministic payment capture, failure simulation, and refund updates.
    """

    @staticmethod
    def capture_payment(
        db: Session,
        organization_id: str,
        order_id: str,
        amount: float,
        payment_method_type: str = "UPI",
        simulate_failure: bool = False
    ) -> Payment:
        ref = f"PAY-MOCK-{generate_uuid()[:8].upper()}"
        pay_status = "FAILED" if simulate_failure else "CAPTURED"

        payment = Payment(
            organization_id=organization_id,
            order_id=order_id,
            payment_reference=ref,
            provider="MOCK_PAYMENT_GATEWAY",
            amount=amount,
            currency="INR",
            status=pay_status,
            payment_method_type=payment_method_type.upper()
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Audit log
        audit = AuditLog(
            organization_id=organization_id,
            actor_id="system",
            actor_type="SYSTEM",
            actor_name="Payment Gateway",
            action="PAYMENT_CAPTURED" if pay_status == "CAPTURED" else "PAYMENT_FAILED",
            resource_type="payment",
            resource_id=payment.id,
            result="SUCCESS" if pay_status == "CAPTURED" else "FAILURE",
            log_metadata={"payment_reference": ref, "amount": amount, "method": payment_method_type}
        )
        db.add(audit)
        db.commit()

        # Publish event
        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="PAYMENT_COMPLETED" if pay_status == "CAPTURED" else "PAYMENT_FAILED",
            title=f"Payment {ref} ({pay_status}): ₹{amount}",
            content=f"Payment for order {order_id} recorded as {pay_status}.",
            metadata={"payment_id": payment.id, "order_id": order_id, "amount": amount, "status": pay_status}
        )

        return payment

    @staticmethod
    def refund_payment(
        db: Session,
        organization_id: str,
        payment_id: str,
        refund_amount: float
    ) -> Payment:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.organization_id == organization_id
        ).first()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

        if payment.status not in ["CAPTURED", "PARTIALLY_REFUNDED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only captured payments can be refunded.")

        payment.status = "REFUNDED" if refund_amount >= payment.amount else "PARTIALLY_REFUNDED"
        db.commit()
        db.refresh(payment)
        return payment
