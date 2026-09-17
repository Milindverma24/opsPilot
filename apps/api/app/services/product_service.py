from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Product, ProductVariant, ProductCategory
from apps.api.app.models.audit import AuditLog


class ProductService:
    """
    Product and Category Service with deterministic catalog management and pricing validation.
    """

    @staticmethod
    def list_categories(db: Session, organization_id: str) -> List[ProductCategory]:
        return db.query(ProductCategory).filter(
            ProductCategory.organization_id == organization_id,
            ProductCategory.is_active == True
        ).all()

    @staticmethod
    def create_category(
        db: Session,
        organization_id: str,
        name: str,
        slug: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> ProductCategory:
        existing = db.query(ProductCategory).filter(
            ProductCategory.organization_id == organization_id,
            ProductCategory.slug == slug.lower().strip()
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{slug}' already exists."
            )

        cat = ProductCategory(
            organization_id=organization_id,
            parent_id=parent_id,
            name=name.strip(),
            slug=slug.lower().strip(),
            description=description,
            is_active=True
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def list_products(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        gender: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Product], int]:
        query = db.query(Product).filter(Product.organization_id == organization_id)

        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if status_filter:
            query = query.filter(Product.status == status_filter.upper())
        if gender:
            query = query.filter(Product.gender == gender.upper())
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        total = query.count()

        # Sorting
        sort_col = getattr(Product, sort_by, Product.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        offset = max(0, (page - 1) * page_size)
        items = query.offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def get_product(db: Session, product_id: str, organization_id: str) -> Product:
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.organization_id == organization_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or access denied."
            )
        return product

    @staticmethod
    def create_product(
        db: Session,
        organization_id: str,
        sku: str,
        name: str,
        base_price: float,
        sale_price: Optional[float] = None,
        category_id: Optional[str] = None,
        brand: str = "UrbanThread",
        description: Optional[str] = None,
        gender: str = "UNISEX",
        material: Optional[str] = None,
        color: Optional[str] = None,
        care_instructions: Optional[str] = None,
        image_url: Optional[str] = None,
        featured_badge: Optional[str] = None,
        status_val: str = "ACTIVE",
        is_active: bool = True
    ) -> Product:
        # Validations
        if base_price < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Base price cannot be negative.")
        if sale_price is not None:
            if sale_price < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale price cannot be negative.")
            if sale_price > base_price:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale price cannot exceed base price.")

        clean_sku = sku.strip().upper()
        existing = db.query(Product).filter(
            Product.organization_id == organization_id,
            Product.sku == clean_sku
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{clean_sku}' already exists."
            )

        product = Product(
            organization_id=organization_id,
            category_id=category_id,
            sku=clean_sku,
            name=name.strip(),
            brand=brand,
            description=description,
            base_price=base_price,
            sale_price=sale_price,
            currency="INR",
            status=status_val.upper(),
            gender=gender.upper(),
            material=material,
            color=color,
            care_instructions=care_instructions,
            image_url=image_url,
            featured_badge=featured_badge,
            is_active=is_active
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def create_variant(
        db: Session,
        organization_id: str,
        product_id: str,
        sku: str,
        size: str,
        color: str,
        barcode: Optional[str] = None,
        price_override: Optional[float] = None,
        weight: Optional[float] = None
    ) -> ProductVariant:
        product = ProductService.get_product(db, product_id, organization_id)
        clean_sku = sku.strip().upper()

        existing = db.query(ProductVariant).filter(
            ProductVariant.organization_id == organization_id,
            ProductVariant.sku == clean_sku
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variant with SKU '{clean_sku}' already exists."
            )

        variant = ProductVariant(
            organization_id=organization_id,
            product_id=product.id,
            sku=clean_sku,
            size=size.upper(),
            color=color.strip(),
            barcode=barcode,
            price_override=price_override,
            weight=weight,
            is_active=True
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        return variant
