from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.ecommerce import Shipment
from apps.api.app.services.shipment_service import ShipmentService
from apps.api.app.services.tenant_service import TenantService

router = APIRouter(prefix="/shipments", tags=["Shipments"])


class UpdateShipmentStatusRequest(BaseModel):
    status: str
    last_location: Optional[str] = None


@router.get("")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Shipment).filter(Shipment.organization_id == current_user.organization_id)
    if status:
        query = query.filter(Shipment.status == status.upper())

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(Shipment.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for s in items:
        data.append({
            "id": s.id,
            "order_id": s.order_id,
            "order_number": s.order.order_number if s.order else None,
            "tracking_number": s.tracking_number,
            "carrier": s.carrier,
            "status": s.status,
            "last_location": s.last_location,
            "estimated_delivery_date": s.estimated_delivery_date.isoformat() if s.estimated_delivery_date else None,
            "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.put("/{shipment_id}/status")
def update_shipment_status(
    shipment_id: str,
    payload: UpdateShipmentStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shipment = ShipmentService.update_shipment_status(
        db=db,
        shipment_id=shipment_id,
        organization_id=current_user.organization_id,
        new_status=payload.status,
        last_location=payload.last_location
    )
    return {"status": "success", "tracking_number": shipment.tracking_number, "new_status": shipment.status}


class CreateShipmentRequest(BaseModel):
    order_id: str
    carrier: Optional[str] = "BlueDart Express Courier"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_shipment(
    payload: CreateShipmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shipment = ShipmentService.create_shipment(
        db=db,
        organization_id=current_user.organization_id,
        order_id=payload.order_id,
        carrier=payload.carrier or "BlueDart Express Courier"
    )
    return {
        "data": {
            "id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier,
            "status": shipment.status
        },
        "meta": {"message": f"Shipment {shipment.tracking_number} created."}
    }


from fastapi.responses import HTMLResponse


@router.get("/{shipment_id}/label", response_class=HTMLResponse)
def get_shipment_label(
    shipment_id: str,
    db: Session = Depends(get_db)
):
    """Returns a printable 4x6 inch thermal shipping label with scannable barcode."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    order = shipment.order
    customer = getattr(order, "customer", None) if order else None
    customer_name = getattr(customer, "name", None) if customer else "Rahul Sharma"
    order_num = order.order_number if order else "UT-DEMO"
    shipping_addr = getattr(order, "shipping_address", None) or "A-402, Sea Crest Towers, Bandra West"

    from apps.api.app.services.label_service import LabelService
    label_html = LabelService.render_shipping_label_html(
        tracking_number=shipment.tracking_number,
        carrier=shipment.carrier or "BlueDart Express",
        order_number=order_num,
        recipient_name=customer_name,
        recipient_address=shipping_addr or "Flat 12, Palm Grove, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        pincode="400050",
        weight_kg=0.75,
        sku_summary="Classic Denim Jacket (M, Indigo)",
        is_return=False
    )
    return HTMLResponse(content=label_html)

