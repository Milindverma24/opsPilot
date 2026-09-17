from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.operations import Customer
from apps.api.app.models.ecommerce import CustomerAddress
from apps.api.app.models.base import generate_uuid
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/customers", tags=["Customers"])


class CreateAddressRequest(BaseModel):
    address_type: str = "SHIPPING"
    name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "India"
    phone: Optional[str] = None
    is_default: bool = False


@router.get("")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer records within tenant perimeter with PII protection."""
    query = db.query(Customer).filter(Customer.organization_id == current_user.organization_id)
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%") | Customer.email.ilike(f"%{search}%"))

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for c in items:
        data.append({
            "id": c.id,
            "customer_number": c.customer_number,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "status": c.status,
            "orders_count": len(c.orders) if hasattr(c, "orders") else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return {
        "data": data,
        "meta": {"page": page, "page_size": page_size, "total": total}
    }


@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customer profile including order history, addresses, and support tickets."""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(customer, current_user, db, "customer")

    addresses_data = []
    for a in customer.addresses:
        addresses_data.append({
            "id": a.id,
            "type": a.address_type,
            "name": a.name,
            "line1": a.address_line_1,
            "city": a.city,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "is_default": a.is_default
        })

    orders_data = []
    for o in customer.orders:
        orders_data.append({
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "payment_status": o.payment_status,
            "total_amount": o.total_amount,
            "placed_at": o.placed_at.isoformat() if o.placed_at else None
        })

    tickets_data = []
    for t in customer.support_tickets:
        tickets_data.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "subject": t.subject,
            "priority": t.priority,
            "status": t.status
        })

    return {
        "data": {
            "id": customer.id,
            "customer_number": customer.customer_number,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "status": customer.status,
            "addresses": addresses_data,
            "orders": orders_data,
            "support_tickets": tickets_data,
            "created_at": customer.created_at.isoformat() if customer.created_at else None
        },
        "meta": {"request_id": f"cust_{customer.id[:8]}"}
    }


@router.post("/{customer_id}/addresses", status_code=status.HTTP_201_CREATED)
def add_customer_address(
    customer_id: str,
    payload: CreateAddressRequest,
    current_user: User = Depends(require_permission("customers.update")),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(customer, current_user, db, "customer")

    address = CustomerAddress(
        organization_id=current_user.organization_id,
        customer_id=customer.id,
        address_type=payload.address_type.upper(),
        name=payload.name,
        address_line_1=payload.address_line_1,
        address_line_2=payload.address_line_2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country=payload.country,
        phone=payload.phone,
        is_default=payload.is_default
    )
    db.add(address)
    db.commit()
    db.refresh(address)

    return {"data": {"id": address.id, "city": address.city}, "meta": {"message": "Address added."}}


class CreateCustomerRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    status: str = "ACTIVE"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CreateCustomerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import uuid
    num = f"CUST-{generate_uuid()[:6].upper()}"
    cust = Customer(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        customer_number=num,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        status=payload.status
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return {"data": {"id": cust.id, "customer_number": cust.customer_number, "name": cust.name}}

