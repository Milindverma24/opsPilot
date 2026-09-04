from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import (
    Order, OrderItem, Product, ProductVariant, Warehouse, CustomerAddress
)
from apps.api.app.models.operations import Customer
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.services.inventory_service import InventoryService
from apps.api.app.services.coupon_service import CouponService
from apps.api.app.services.payment_service import PaymentService
from apps.api.app.services.shipment_service import ShipmentService
from apps.api.app.events.publisher import BusinessEventPublisher


class OrderService:
    """
    Central E-Commerce Order Orchestration Service.
    Enforces product status, inventory reservation, snapshot preservation,
    deterministic pricing/taxation, mock payment, and fulfillment pipelines.
    """

    @staticmethod
    def create_order(
        db: Session,
        organization_id: str,
        customer_id: str,
        items: List[Dict[str, Any]],
        coupon_code: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        shipping_address_id: Optional[str] = None,
        billing_address_id: Optional[str] = None,
        simulate_payment_failure: bool = False,
        actor_id: str = "system"
    ) -> Order:
        # 1. Customer Verification
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id
        ).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found or access denied.")
        if customer.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Customer account is {customer.status.lower()}.")

        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain at least one item.")

        # 2. Resolve default warehouse if not specified
        if not warehouse_id:
            wh = db.query(Warehouse).filter(
                Warehouse.organization_id == organization_id,
                Warehouse.is_active == True
            ).first()
            if not wh:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active fulfillment warehouse configured.")
            warehouse_id = wh.id

        # 3. Item Validation & Inventory Reservation
        subtotal = 0.0
        validated_items = []
        reserved_records = []

        try:
            for item in items:
                variant_id = item["product_variant_id"]
                qty = int(item["quantity"])
                if qty <= 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive.")

                variant = db.query(ProductVariant).filter(
                    ProductVariant.id == variant_id,
                    ProductVariant.organization_id == organization_id
                ).first()
                if not variant or not variant.is_active:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product variant {variant_id} is unavailable or inactive.")

                product = variant.product
                if not product or product.status != "ACTIVE" or not product.is_active:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name if product else variant_id}' is inactive and cannot be ordered.")

                # Reserve inventory (will throw 400 if insufficient)
                inv = InventoryService.reserve_inventory(
                    db=db,
                    organization_id=organization_id,
                    product_variant_id=variant.id,
                    warehouse_id=warehouse_id,
                    quantity=qty,
                    actor_id=actor_id
                )
                reserved_records.append((variant.id, warehouse_id, qty))

                unit_price = variant.price_override if variant.price_override is not None else (product.sale_price if product.sale_price is not None else product.base_price)
                line_total = round(unit_price * qty, 2)
                subtotal += line_total

                validated_items.append({
                    "product_id": product.id,
                    "product_variant_id": variant.id,
                    "product_name_snapshot": product.name,
                    "sku_snapshot": variant.sku,
                    "size_snapshot": variant.size,
                    "color_snapshot": variant.color,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_amount": line_total
                })
        except Exception as e:
            # Roll back any partial reservations
            for v_id, w_id, q in reserved_records:
                try:
                    InventoryService.release_inventory(db, organization_id, v_id, w_id, q, actor_id)
                except Exception:
                    pass
            raise e

        # 4. Coupon Calculation
        discount_amount = 0.0
        coupon_id = None
        if coupon_code:
            discount_amount, coupon = CouponService.validate_coupon(db, organization_id, coupon_code, subtotal)
            coupon_id = coupon.id

        # 5. Tax & Shipping Calculation (Standard 12% GST on fashion; free shipping over ₹1500)
        taxable_amount = max(0.0, subtotal - discount_amount)
        tax_amount = round(taxable_amount * 0.12, 2)
        shipping_amount = 0.0 if subtotal >= 1500.0 else 100.0
        total_amount = round(taxable_amount + tax_amount + shipping_amount, 2)

        # 6. Create Order
        order_num = f"ORD-{generate_uuid()[:8].upper()}"
        order = Order(
            organization_id=organization_id,
            customer_id=customer_id,
            coupon_id=coupon_id,
            order_number=order_num,
            status="PROCESSING",
            payment_status="PENDING",
            fulfillment_status="UNFULFILLED",
            currency="INR",
            subtotal=round(subtotal, 2),
            discount_amount=discount_amount,
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            shipping_address_id=shipping_address_id,
            billing_address_id=billing_address_id,
            placed_at=get_utc_now()
        )
        db.add(order)
        db.flush()

        # 7. Add Order Items
        for vi in validated_items:
            oi = OrderItem(
                organization_id=organization_id,
                order_id=order.id,
                product_id=vi["product_id"],
                product_variant_id=vi["product_variant_id"],
                product_name_snapshot=vi["product_name_snapshot"],
                sku_snapshot=vi["sku_snapshot"],
                size_snapshot=vi["size_snapshot"],
                color_snapshot=vi["color_snapshot"],
                quantity=vi["quantity"],
                unit_price=vi["unit_price"],
                discount_amount=0.0,
                tax_amount=round(vi["total_amount"] * 0.12, 2),
                total_amount=vi["total_amount"]
            )
            db.add(oi)
        db.commit()

        # 8. Process Mock Payment
        payment = PaymentService.capture_payment(
            db=db,
            organization_id=organization_id,
            order_id=order.id,
            amount=total_amount,
            simulate_failure=simulate_payment_failure
        )

        if payment.status == "CAPTURED":
            order.payment_status = "PAID"
            order.status = "CONFIRMED"
            if coupon_id:
                CouponService.record_coupon_usage(db, coupon_id)

            # Create shipment
            ShipmentService.create_shipment(db, organization_id, order.id)

            # Publish events
            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="ORDER_CREATED",
                title=f"Order {order.order_number} placed by {customer.name}",
                content=f"Order total: ₹{total_amount}. Items: {len(validated_items)}.",
                metadata={"order_id": order.id, "order_number": order.order_number, "customer_id": customer_id}
            )
            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="ORDER_CONFIRMED",
                title=f"Order {order.order_number} confirmed and paid",
                content="Payment captured successfully. Ready for dispatch.",
                metadata={"order_id": order.id, "total": total_amount}
            )

            # Real-Time Employee Task Dispatch (Warehouse Pick & Pack)
            try:
                from apps.api.app.services.task_service import TaskService
                TaskService.create_task(
                    db=db,
                    organization_id=organization_id,
                    title=f"Pick & Pack Order #{order.order_number}",
                    description=f"Customer: {customer.name}. Items: {len(validated_items)}.",
                    task_type="PICK_AND_PACK",
                    order_id=order.id,
                    customer_name=customer.name,
                    items_summary=validated_items,
                    priority="NORMAL",
                    status="CREATED"
                )
            except Exception:
                pass

            # Trigger Order Operations AI Workflow
            try:
                from apps.api.app.workflows.trigger_service import WorkflowTriggerService
                WorkflowTriggerService.trigger_event(
                    db=db,
                    organization_id=organization_id,
                    event_type="ORDER_CREATED",
                    event_id=order.id,
                    payload={"order_id": order.id, "order_number": order.order_number, "customer_name": customer.name, "total": total_amount}
                )
            except Exception:
                pass
        else:
            # Payment failed: cancel order & release reserved inventory
            order.payment_status = "FAILED"
            order.status = "CANCELLED"
            for v_id, w_id, q in reserved_records:
                InventoryService.release_inventory(db, organization_id, v_id, w_id, q, actor_id)

            BusinessEventPublisher.publish(
                db=db,
                organization_id=organization_id,
                event_type="ORDER_CANCELLED",
                title=f"Order {order.order_number} cancelled due to payment failure",
                content="Inventory released back to available pool.",
                metadata={"order_id": order.id, "reason": "Payment failed"}
            )

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_order(db: Session, order_id: str, organization_id: str) -> Order:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.organization_id == organization_id
        ).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied.")
        return order

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: str,
        organization_id: str,
        reason: str = "Customer requested cancellation",
        actor_id: str = "system"
    ) -> Order:
        order = OrderService.get_order(db, order_id, organization_id)
        if order.status in ["DELIVERED", "COMPLETED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivered orders cannot be cancelled directly; please initiate a return.")
        if order.status == "CANCELLED":
            return order

        # Release inventory if not yet fulfilled
        if order.fulfillment_status != "FULFILLED":
            wh = db.query(Warehouse).filter(Warehouse.organization_id == organization_id).first()
            if wh:
                for item in order.items:
                    if item.product_variant_id:
                        InventoryService.release_inventory(
                            db=db,
                            organization_id=organization_id,
                            product_variant_id=item.product_variant_id,
                            warehouse_id=wh.id,
                            quantity=item.quantity,
                            actor_id=actor_id
                        )

        order.status = "CANCELLED"
        db.commit()

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="ORDER_CANCELLED",
            title=f"Order {order.order_number} cancelled",
            content=f"Reason: {reason}",
            metadata={"order_id": order.id, "reason": reason}
        )
        return order

    @staticmethod
    def list_orders(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        customer_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "placed_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Order], int]:
        query = db.query(Order).filter(Order.organization_id == organization_id)

        if status_filter:
            query = query.filter(Order.status == status_filter.upper())
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if search:
            query = query.filter(Order.order_number.ilike(f"%{search}%"))

        total = query.count()

        sort_col = getattr(Order, sort_by, Order.placed_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        offset = max(0, (page - 1) * page_size)
        items = query.offset(offset).limit(page_size).all()
        return items, total
