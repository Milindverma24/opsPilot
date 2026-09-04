from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.product_service import ProductService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/products", tags=["Products"])


class CreateProductRequest(BaseModel):
    sku: str = Field(..., example="UT-TSH-001")
    name: str = Field(..., example="Classic Organic Cotton Crewneck T-Shirt")
    base_price: float = Field(..., ge=0, example=1299.0)
    sale_price: Optional[float] = Field(None, ge=0, example=999.0)
    category_id: Optional[str] = None
    brand: str = "UrbanThread"
    description: Optional[str] = "Premium combed cotton with ribbed neckline"
    gender: str = "UNISEX"
    material: Optional[str] = "100% Organic Cotton"
    color: Optional[str] = "Jet Black"
    care_instructions: Optional[str] = "Machine wash cold, tumble dry low"


class CreateVariantRequest(BaseModel):
    sku: str = Field(..., example="UT-TSH-001-M-BLK")
    size: str = Field(..., example="M")
    color: str = Field(..., example="Black")
    barcode: Optional[str] = None
    price_override: Optional[float] = None
    weight: Optional[float] = 220.0


@router.get("")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    gender: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List products with database-level pagination, category filtering, and search."""
    items, total = ProductService.list_products(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status_filter=status,
        gender=gender,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )

    data = []
    for p in items:
        data.append({
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "brand": p.brand,
            "category": p.category.name if p.category else None,
            "base_price": p.base_price,
            "sale_price": p.sale_price,
            "currency": p.currency,
            "status": p.status,
            "gender": p.gender,
            "variants_count": len(p.variants),
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    return {
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "request_id": f"req_{p.id[:8] if items else 'empty'}"
        }
    }


@router.get("/{product_id}")
def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full product details including variants and inventory totals."""
    p = ProductService.get_product(db, product_id, current_user.organization_id)
    variants_data = []
    for v in p.variants:
        on_hand = sum(inv.quantity_on_hand for inv in v.inventory_items)
        reserved = sum(inv.quantity_reserved for inv in v.inventory_items)
        variants_data.append({
            "id": v.id,
            "sku": v.sku,
            "size": v.size,
            "color": v.color,
            "barcode": v.barcode,
            "price_override": v.price_override,
            "weight": v.weight,
            "is_active": v.is_active,
            "quantity_on_hand": on_hand,
            "quantity_reserved": reserved,
            "available_quantity": max(0, on_hand - reserved)
        })

    return {
        "data": {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "description": p.description,
            "brand": p.brand,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "base_price": p.base_price,
            "sale_price": p.sale_price,
            "currency": p.currency,
            "status": p.status,
            "gender": p.gender,
            "material": p.material,
            "color": p.color,
            "care_instructions": p.care_instructions,
            "is_active": p.is_active,
            "variants": variants_data,
            "created_at": p.created_at.isoformat() if p.created_at else None
        },
        "meta": {"request_id": f"req_{p.id[:8]}"}
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: CreateProductRequest,
    current_user: User = Depends(require_permission("products.create")),
    db: Session = Depends(get_db)
):
    """Create a new product in the organization catalog."""
    p = ProductService.create_product(
        db=db,
        organization_id=current_user.organization_id,
        sku=payload.sku,
        name=payload.name,
        base_price=payload.base_price,
        sale_price=payload.sale_price,
        category_id=payload.category_id,
        brand=payload.brand,
        description=payload.description,
        gender=payload.gender,
        material=payload.material,
        color=payload.color,
        care_instructions=payload.care_instructions
    )
    return {"data": {"id": p.id, "sku": p.sku, "name": p.name}, "meta": {"message": "Product created successfully."}}


@router.post("/{product_id}/variants", status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: str,
    payload: CreateVariantRequest,
    current_user: User = Depends(require_permission("products.create")),
    db: Session = Depends(get_db)
):
    """Add a size/color variant to a product."""
    v = ProductService.create_variant(
        db=db,
        organization_id=current_user.organization_id,
        product_id=product_id,
        sku=payload.sku,
        size=payload.size,
        color=payload.color,
        barcode=payload.barcode,
        price_override=payload.price_override,
        weight=payload.weight
    )
    return {"data": {"id": v.id, "sku": v.sku, "size": v.size, "color": v.color}, "meta": {"message": "Variant created."}}
