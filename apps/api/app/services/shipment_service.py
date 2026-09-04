from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Shipment, Order
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher


class ShipmentService:
    """
    Mock Carrier & Shipment Tracking Service.
    Generates synthetic tracking barcodes and manages transit state updates.
    """

    @staticmethod
    def create_shipment(
        db: Session,
        organization_id: str,
        order_id: str,
        carrier: str = "BlueDart Express"
    ) -> Shipment:
        trk = f"BD-URB-{generate_uuid()[:8].upper()}"
        est_delivery = datetime.now(timezone.utc) + timedelta(days=3)

        shipment = Shipment(
            organization_id=organization_id,
            order_id=order_id,
            tracking_number=trk,
            carrier=carrier,
            status="PACKED",
            estimated_delivery_date=est_delivery,
            last_location="Mumbai Fulfillment Hub"
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        audit = AuditLog(
            organization_id=organization_id,
            actor_id="system",
            actor_type="SYSTEM",
            actor_name="Fulfillment Engine",
            action="SHIPMENT_CREATED",
            resource_type="shipment",
            resource_id=shipment.id,
            result="SUCCESS",
            log_metadata={"tracking_number": trk, "carrier": carrier}
        )
        db.add(audit)
        db.commit()

        return shipment

    @staticmethod
    def update_shipment_status(
        db: Session,
        shipment_id: str,
        organization_id: str,
        new_status: str,
        last_location: Optional[str] = None
    ) -> Shipment:
        shipment = db.query(Shipment).filter(
            Shipment.id == shipment_id,
            Shipment.organization_id == organization_id
        ).first()

        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

        shipment.status = new_status.upper()
        if last_location:
            shipment.last_location = last_location

        if shipment.status == "SHIPPED" and not shipment.shipped_at:
            shipment.shipped_at = get_utc_now()
        elif shipment.status == "DELIVERED":
            shipment.delivered_at = get_utc_now()

        db.commit()
        db.refresh(shipment)

        if shipment.status == "DELAYED":
            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="SHIPMENT_DELAYED",
                title=f"Shipment {shipment.tracking_number} delayed in transit",
                content=f"Shipment for order {shipment.order_id} is delayed at {shipment.last_location}.",
                metadata={"shipment_id": shipment.id, "order_id": shipment.order_id, "tracking": shipment.tracking_number}
            )
        elif shipment.status == "DELIVERED":
            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="SHIPMENT_DELIVERED",
                title=f"Shipment {shipment.tracking_number} delivered successfully",
                content=f"Order {shipment.order_id} delivered.",
                metadata={"shipment_id": shipment.id, "order_id": shipment.order_id}
            )

        return shipment
