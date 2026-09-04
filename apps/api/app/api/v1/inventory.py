from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.inventory_service import InventoryService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class AdjustStockRequest(BaseModel):
    product_variant_id: str
    warehouse_id: str
    quantity: int = Field(..., gt=0)
    operation: str = Field("INCREASE", example="INCREASE")  # INCREASE, DECREASE, RESERVE, RELEASE


@router.get("")
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    low_stock_only: bool = False,
    warehouse_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List inventory records across warehouses with on-hand, reserved, and available quantities."""
    items, total = InventoryService.list_inventory(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        low_stock_only=low_stock_only,
        warehouse_id=warehouse_id
    )

    data = []
    for inv in items:
        v = inv.variant
        p = v.product if v else None
        data.append({
            "id": inv.id,
            "product_name": p.name if p else "Unknown",
            "product_sku": p.sku if p else "",
            "variant_sku": v.sku if v else "",
            "size": v.size if v else "",
            "color": v.color if v else "",
            "warehouse_name": inv.warehouse.name if inv.warehouse else "Warehouse",
            "warehouse_code": inv.warehouse.code if inv.warehouse else "",
            "quantity_on_hand": inv.quantity_on_hand,
            "quantity_reserved": inv.quantity_reserved,
            "available_quantity": inv.available_quantity,
            "reorder_level": inv.reorder_level,
            "status": "OUT_OF_STOCK" if inv.available_quantity == 0 else ("LOW_STOCK" if inv.available_quantity <= inv.reorder_level else "IN_STOCK")
        })

    return {
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "low_stock_only": low_stock_only
        }
    }


@router.post("/adjust")
def adjust_inventory(
    payload: AdjustStockRequest,
    current_user: User = Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db)
):
    """Adjust inventory stock levels with full audit trail."""
    op = payload.operation.upper()
    if op == "INCREASE":
        inv = InventoryService.get_or_create_inventory(
            db, current_user.organization_id, payload.product_variant_id, payload.warehouse_id
        )
        inv.quantity_on_hand += payload.quantity
        db.commit()
    elif op == "DECREASE":
        inv = InventoryService.decrease_inventory(
            db, current_user.organization_id, payload.product_variant_id, payload.warehouse_id, payload.quantity, actor_id=current_user.id, from_reserved=False
        )
    elif op == "RESERVE":
        inv = InventoryService.reserve_inventory(
            db, current_user.organization_id, payload.product_variant_id, payload.warehouse_id, payload.quantity, actor_id=current_user.id
        )
    elif op == "RELEASE":
        inv = InventoryService.release_inventory(
            db, current_user.organization_id, payload.product_variant_id, payload.warehouse_id, payload.quantity, actor_id=current_user.id
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported operation '{op}'")

    return {"status": "success", "available_quantity": inv.available_quantity, "on_hand": inv.quantity_on_hand}
