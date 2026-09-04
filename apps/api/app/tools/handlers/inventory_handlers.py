"""
Inventory Tool Handlers — Phase 8: reserve_inventory, release_inventory.
Calls InventoryService — atomic operations with negative-stock prevention.
"""
from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.services.inventory_service import InventoryService
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import ReserveInventoryInput, ReleaseInventoryInput


def _resolve_variant_and_warehouse(db: Session, org_id: str, variant_id: str | None, sku: str | None, warehouse_id: str | None) -> tuple[str | None, str | None]:
    if not variant_id and sku:
        from apps.api.app.models.ecommerce import ProductVariant
        pv = db.query(ProductVariant).filter(
            ProductVariant.organization_id == org_id,
            ProductVariant.sku == sku,
        ).first()
        if pv:
            variant_id = pv.id

    if not warehouse_id and variant_id:
        from apps.api.app.models.ecommerce import Inventory, Warehouse
        inv = db.query(Inventory).filter(
            Inventory.organization_id == org_id,
            Inventory.product_variant_id == variant_id,
        ).first()
        if inv:
            warehouse_id = inv.warehouse_id
        else:
            wh = db.query(Warehouse).filter(Warehouse.organization_id == org_id).first()
            if wh:
                warehouse_id = wh.id
                # Ensure an inventory row exists
                InventoryService.get_or_create_inventory(
                    db=db,
                    organization_id=org_id,
                    product_variant_id=variant_id,
                    warehouse_id=warehouse_id,
                    initial_quantity=100,
                )
    return variant_id, warehouse_id


def handle_reserve_inventory(db: Session, ctx: ToolContext, inp: ReserveInventoryInput) -> Dict[str, Any]:
    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "variant_id": inp.variant_id or inp.sku, "quantity": inp.quantity}
    try:
        variant_id, warehouse_id = _resolve_variant_and_warehouse(
            db, ctx.organization_id, inp.variant_id, inp.sku, inp.warehouse_id
        )
        if not variant_id or not warehouse_id:
            return {"success": False, "error": f"Could not resolve variant or warehouse for sku={inp.sku}, variant_id={inp.variant_id}"}

        InventoryService.reserve_inventory(
            db=db,
            organization_id=ctx.organization_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            quantity=inp.quantity,
        )
        return {"success": True, "variant_id": variant_id, "quantity_reserved": inp.quantity}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_release_inventory(db: Session, ctx: ToolContext, inp: ReleaseInventoryInput) -> Dict[str, Any]:
    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "variant_id": inp.variant_id or inp.sku, "quantity": inp.quantity}
    try:
        variant_id, warehouse_id = _resolve_variant_and_warehouse(
            db, ctx.organization_id, inp.variant_id, inp.sku, inp.warehouse_id
        )
        if not variant_id or not warehouse_id:
            return {"success": False, "error": f"Could not resolve variant or warehouse for sku={inp.sku}, variant_id={inp.variant_id}"}

        InventoryService.release_inventory(
            db=db,
            organization_id=ctx.organization_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            quantity=inp.quantity,
        )
        return {"success": True, "variant_id": variant_id, "quantity_released": inp.quantity}
    except Exception as e:
        return {"success": False, "error": str(e)}
