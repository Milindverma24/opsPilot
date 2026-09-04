from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import Inventory, Warehouse, ProductVariant
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher


class InventoryService:
    """
    Inventory Management Service with deterministic reservation, release,
    negative stock prevention, and low-inventory threshold triggers.
    """

    @staticmethod
    def create_warehouse(
        db: Session,
        organization_id: str,
        name: str,
        code: str,
        city: str,
        state: str,
        country: str = "India",
        address: Optional[str] = None
    ) -> Warehouse:
        clean_code = code.strip().upper()
        existing = db.query(Warehouse).filter(
            Warehouse.organization_id == organization_id,
            Warehouse.code == clean_code
        ).first()
        if existing:
            return existing

        wh = Warehouse(
            organization_id=organization_id,
            name=name.strip(),
            code=clean_code,
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            address=address,
            is_active=True
        )
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return wh

    @staticmethod
    def get_or_create_inventory(
        db: Session,
        organization_id: str,
        product_variant_id: str,
        warehouse_id: str,
        initial_quantity: int = 0,
        reorder_level: int = 10,
        reorder_quantity: int = 50
    ) -> Inventory:
        inv = db.query(Inventory).filter(
            Inventory.organization_id == organization_id,
            Inventory.product_variant_id == product_variant_id,
            Inventory.warehouse_id == warehouse_id
        ).first()
        if not inv:
            inv = Inventory(
                organization_id=organization_id,
                product_variant_id=product_variant_id,
                warehouse_id=warehouse_id,
                quantity_on_hand=initial_quantity,
                quantity_reserved=0,
                reorder_level=reorder_level,
                reorder_quantity=reorder_quantity
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
        return inv

    @staticmethod
    def reserve_inventory(
        db: Session,
        organization_id: str,
        product_variant_id: str,
        warehouse_id: str,
        quantity: int,
        actor_id: str = "system"
    ) -> Inventory:
        if quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation quantity must be positive.")

        inv = db.query(Inventory).filter(
            Inventory.organization_id == organization_id,
            Inventory.product_variant_id == product_variant_id,
            Inventory.warehouse_id == warehouse_id
        ).with_for_update().first()

        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found.")

        available = inv.quantity_on_hand - inv.quantity_reserved
        if quantity > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory available ({available} available, {quantity} requested)."
            )

        inv.quantity_reserved += quantity
        new_available = inv.quantity_on_hand - inv.quantity_reserved

        # Audit event
        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="SYSTEM",
            actor_name="Inventory Engine",
            action="INVENTORY_CHANGED",
            resource_type="inventory",
            resource_id=inv.id,
            result="SUCCESS",
            log_metadata={
                "operation": "RESERVE",
                "quantity": quantity,
                "on_hand": inv.quantity_on_hand,
                "reserved": inv.quantity_reserved,
                "available": new_available
            }
        )
        db.add(audit)

        # Trigger INVENTORY_LOW event if threshold reached
        if new_available <= inv.reorder_level:
            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="INVENTORY_LOW" if new_available > 0 else "INVENTORY_OUT",
                title=f"Stock alert: Variant {product_variant_id} is low ({new_available} left)",
                content=f"Available stock ({new_available}) has reached or breached reorder level ({inv.reorder_level}).",
                metadata={"product_variant_id": product_variant_id, "warehouse_id": warehouse_id, "available": new_available}
            )

        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def release_inventory(
        db: Session,
        organization_id: str,
        product_variant_id: str,
        warehouse_id: str,
        quantity: int,
        actor_id: str = "system"
    ) -> Inventory:
        inv = db.query(Inventory).filter(
            Inventory.organization_id == organization_id,
            Inventory.product_variant_id == product_variant_id,
            Inventory.warehouse_id == warehouse_id
        ).with_for_update().first()

        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found.")

        inv.quantity_reserved = max(0, inv.quantity_reserved - quantity)

        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="SYSTEM",
            actor_name="Inventory Engine",
            action="INVENTORY_CHANGED",
            resource_type="inventory",
            resource_id=inv.id,
            result="SUCCESS",
            log_metadata={
                "operation": "RELEASE",
                "quantity": quantity,
                "on_hand": inv.quantity_on_hand,
                "reserved": inv.quantity_reserved
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def decrease_inventory(
        db: Session,
        organization_id: str,
        product_variant_id: str,
        warehouse_id: str,
        quantity: int,
        actor_id: str = "system",
        from_reserved: bool = True
    ) -> Inventory:
        inv = db.query(Inventory).filter(
            Inventory.organization_id == organization_id,
            Inventory.product_variant_id == product_variant_id,
            Inventory.warehouse_id == warehouse_id
        ).with_for_update().first()

        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found.")

        if quantity > inv.quantity_on_hand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot decrease inventory below zero."
            )

        inv.quantity_on_hand -= quantity
        if from_reserved:
            inv.quantity_reserved = max(0, inv.quantity_reserved - quantity)

        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="SYSTEM",
            actor_name="Inventory Engine",
            action="INVENTORY_CHANGED",
            resource_type="inventory",
            resource_id=inv.id,
            result="SUCCESS",
            log_metadata={
                "operation": "DECREASE",
                "quantity": quantity,
                "on_hand": inv.quantity_on_hand,
                "reserved": inv.quantity_reserved
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def list_inventory(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 50,
        low_stock_only: bool = False,
        warehouse_id: Optional[str] = None
    ) -> Tuple[List[Inventory], int]:
        query = db.query(Inventory).filter(Inventory.organization_id == organization_id)
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)
        if low_stock_only:
            query = query.filter(Inventory.quantity_on_hand - Inventory.quantity_reserved <= Inventory.reorder_level)

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        items = query.offset(offset).limit(page_size).all()
        return items, total
