from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.ecommerce import Warehouse
from apps.api.app.services.inventory_service import InventoryService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


class CreateWarehouseRequest(BaseModel):
    name: str = Field(..., example="Mumbai Central Fulfillment Center")
    code: str = Field(..., example="WH-MUM-01")
    city: str = Field(..., example="Mumbai")
    state: str = Field(..., example="Maharashtra")
    country: str = "India"
    address: Optional[str] = "Gala 402, Bhiwandi Logistics Park"


@router.get("")
def list_warehouses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    whs = db.query(Warehouse).filter(
        Warehouse.organization_id == current_user.organization_id,
        Warehouse.is_active == True
    ).all()
    data = []
    for w in whs:
        data.append({
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "city": w.city,
            "state": w.state,
            "country": w.country,
            "address": w.address,
            "inventory_records": len(w.inventory_items)
        })
    return {"data": data, "meta": {"total": len(data)}}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: CreateWarehouseRequest,
    current_user: User = Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db)
):
    wh = InventoryService.create_warehouse(
        db=db,
        organization_id=current_user.organization_id,
        name=payload.name,
        code=payload.code,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        address=payload.address
    )
    return {"data": {"id": wh.id, "name": wh.name, "code": wh.code}, "meta": {"message": "Warehouse registered."}}
