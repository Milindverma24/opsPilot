from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.product_service import ProductService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/categories", tags=["Categories"])


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., example="T-Shirts")
    slug: str = Field(..., example="t-shirts")
    parent_id: Optional[str] = None
    description: Optional[str] = "Casual everyday t-shirts and polo shirts"


@router.get("")
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List hierarchical product categories."""
    cats = ProductService.list_categories(db, current_user.organization_id)
    data = []
    for c in cats:
        data.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "parent_id": c.parent_id,
            "parent_name": c.parent.name if c.parent else None,
            "description": c.description,
            "products_count": len(c.products)
        })
    return {"data": data, "meta": {"total": len(data)}}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CreateCategoryRequest,
    current_user: User = Depends(require_permission("products.create")),
    db: Session = Depends(get_db)
):
    cat = ProductService.create_category(
        db=db,
        organization_id=current_user.organization_id,
        name=payload.name,
        slug=payload.slug,
        parent_id=payload.parent_id,
        description=payload.description
    )
    return {"data": {"id": cat.id, "name": cat.name, "slug": cat.slug}, "meta": {"message": "Category created."}}
