"""
Phase 7 — Read-Only Context Providers.

Architecture Principle:
- Context adapters are strictly READ-ONLY.
- Tenant isolation (organization_id) is enforced on EVERY query.
- Returns normalized List[ContextItem] with provenance and trust levels.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.schemas.agent_schemas import ContextItem
from apps.api.app.models.operations import Customer, Complaint
from apps.api.app.models.ecommerce import (
    Order, OrderItem, Product, ProductVariant, Inventory,
    Shipment, Return, Refund, Coupon, CustomerConversation, ConversationMessage,
    SupportTicket
)
from apps.api.app.models.policy import Policy, PolicyRule
from apps.api.app.models.document import Document, DocumentChunk


class BaseContextProvider(ABC):
    @abstractmethod
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        """Gather context items matching the criteria within the organization."""
        ...


class CustomerContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        customer_id = criteria.get("customer_id")
        email = criteria.get("email")
        phone = criteria.get("phone")

        query = db.query(Customer).filter(Customer.organization_id == organization_id)
        customer = None
        if customer_id:
            customer = query.filter(Customer.id == customer_id).first()
        elif email:
            customer = query.filter(Customer.email == email.lower()).first()
        elif phone:
            customer = query.filter(Customer.phone == phone).first()

        if customer:
            order_count = db.query(Order).filter(
                Order.organization_id == organization_id,
                Order.customer_id == customer.id
            ).count()
            
            content = (
                f"Customer ID: {customer.id}\n"
                f"Name: {customer.name}\n"
                f"Email: {customer.email or 'N/A'}\n"
                f"Phone: {customer.phone or 'N/A'}\n"
                f"Status: {customer.status}\n"
                f"Total Orders: {order_count}"
            )
            items.append(ContextItem(
                source_type="CUSTOMER",
                source_id=customer.id,
                content=content,
                metadata={"name": customer.name, "email": customer.email, "order_count": order_count},
                confidence=1.0,
                trust_level="TRUSTED"
            ))
        return items


class OrderContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        order_id = criteria.get("order_id")
        order_number = criteria.get("order_number")

        query = db.query(Order).filter(Order.organization_id == organization_id)
        order = None
        if order_number:
            order = query.filter(Order.order_number == order_number.upper()).first()
        elif order_id:
            order = query.filter(Order.id == order_id).first()

        if order:
            order_items = db.query(OrderItem).filter(
                OrderItem.organization_id == organization_id,
                OrderItem.order_id == order.id
            ).all()

            items_str = ", ".join([f"{item.product_name} (x{item.quantity}, ₹{item.total_price})" for item in order_items]) if order_items else "None"
            content = (
                f"Order Number: {order.order_number}\n"
                f"Order ID: {order.id}\n"
                f"Customer ID: {order.customer_id}\n"
                f"Status: {order.status}\n"
                f"Payment Status: {order.payment_status}\n"
                f"Fulfillment Status: {order.fulfillment_status}\n"
                f"Total Amount: {order.currency} {order.total_amount}\n"
                f"Created At: {order.created_at.isoformat() if order.created_at else 'N/A'}\n"
                f"Items: {items_str}"
            )
            items.append(ContextItem(
                source_type="ORDER",
                source_id=order.id,
                content=content,
                metadata={
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "payment_status": order.payment_status,
                    "customer_id": order.customer_id,
                    "created_at": order.created_at.isoformat() if order.created_at else None
                },
                confidence=1.0,
                trust_level="TRUSTED"
            ))
        return items


class ProductContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        sku = criteria.get("sku")
        product_id = criteria.get("product_id")
        query_text = criteria.get("query")

        query = db.query(Product).filter(Product.organization_id == organization_id)
        product = None
        if sku:
            product = query.filter(Product.sku == sku.upper()).first()
            if not product:
                variant = db.query(ProductVariant).filter(
                    ProductVariant.organization_id == organization_id,
                    ProductVariant.sku == sku.upper()
                ).first()
                if variant:
                    product = db.query(Product).filter(
                        Product.organization_id == organization_id,
                        Product.id == variant.product_id
                    ).first()
        elif product_id:
            product = query.filter(Product.id == product_id).first()
        elif query_text:
            product = query.filter(Product.name.ilike(f"%{query_text}%")).first()

        if product:
            variants = db.query(ProductVariant).filter(
                ProductVariant.organization_id == organization_id,
                ProductVariant.product_id == product.id
            ).all()
            variant_str = ", ".join([f"{v.size}/{v.color} ({v.sku}, Price: ₹{v.price_override or product.base_price})" for v in variants]) if variants else "None"

            content = (
                f"Product: {product.name}\n"
                f"SKU: {product.sku}\n"
                f"Brand: {product.brand}\n"
                f"Base Price: {product.currency} {product.base_price}\n"
                f"Sale Price: {product.currency} {product.sale_price if product.sale_price else 'N/A'}\n"
                f"Status: {product.status}\n"
                f"Material: {product.material or 'N/A'}\n"
                f"Care: {product.care_instructions or 'N/A'}\n"
                f"Variants: {variant_str}"
            )
            items.append(ContextItem(
                source_type="PRODUCT",
                source_id=product.id,
                content=content,
                metadata={
                    "name": product.name,
                    "sku": product.sku,
                    "base_price": product.base_price,
                    "status": product.status
                },
                confidence=1.0,
                trust_level="TRUSTED"
            ))
        return items


class ShipmentContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        tracking_number = criteria.get("tracking_number")
        order_id = criteria.get("order_id")
        shipment_id = criteria.get("shipment_id")

        query = db.query(Shipment).filter(Shipment.organization_id == organization_id)
        shipments: List[Shipment] = []
        if tracking_number:
            s = query.filter(Shipment.tracking_number == tracking_number.upper()).first()
            if s:
                shipments = [s]
        elif shipment_id:
            s = query.filter(Shipment.id == shipment_id).first()
            if s:
                shipments = [s]
        elif order_id:
            shipments = query.filter(Shipment.order_id == order_id).all()

        for shipment in shipments:
            est_del = getattr(shipment, "estimated_delivery_date", None) or getattr(shipment, "estimated_delivery", None)
            content = (
                f"Shipment ID: {shipment.id}\n"
                f"Order ID: {shipment.order_id}\n"
                f"Carrier: {shipment.carrier}\n"
                f"Tracking Number: {shipment.tracking_number}\n"
                f"Status: {shipment.status}\n"
                f"Shipped At: {shipment.shipped_at.isoformat() if shipment.shipped_at else 'N/A'}\n"
                f"Estimated Delivery: {est_del.isoformat() if est_del else 'N/A'}\n"
                f"Delivered At: {shipment.delivered_at.isoformat() if shipment.delivered_at else 'N/A'}"
            )
            items.append(ContextItem(
                source_type="SHIPMENT",
                source_id=shipment.id,
                content=content,
                metadata={
                    "tracking_number": shipment.tracking_number,
                    "carrier": shipment.carrier,
                    "status": shipment.status,
                    "estimated_delivery": est_del.isoformat() if est_del else None
                },
                confidence=1.0,
                trust_level="TRUSTED"
            ))
        return items


class SupportContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        ticket_id = criteria.get("ticket_id")
        customer_id = criteria.get("customer_id")

        if ticket_id:
            ticket = db.query(SupportTicket).filter(
                SupportTicket.organization_id == organization_id,
                SupportTicket.id == ticket_id
            ).first()
            if ticket:
                content = (
                    f"Support Ticket: {ticket.ticket_number}\n"
                    f"Subject: {ticket.subject}\n"
                    f"Status: {ticket.status}\n"
                    f"Priority: {ticket.priority}\n"
                    f"Description: {ticket.description or 'N/A'}"
                )
                items.append(ContextItem(
                    source_type="SUPPORT",
                    source_id=ticket.id,
                    content=content,
                    metadata={"ticket_number": ticket.ticket_number, "status": ticket.status},
                    confidence=1.0,
                    trust_level="TRUSTED"
                ))

        if customer_id:
            complaints = db.query(Complaint).filter(
                Complaint.organization_id == organization_id,
                Complaint.customer_id == customer_id
            ).order_by(Complaint.created_at.desc()).limit(3).all()

            for c in complaints:
                content = (
                    f"Complaint: {c.complaint_number}\n"
                    f"Category: {c.category}\n"
                    f"Status: {c.status}\n"
                    f"Description: {c.description}"
                )
                items.append(ContextItem(
                    source_type="SUPPORT",
                    source_id=c.id,
                    content=content,
                    metadata={"complaint_number": c.complaint_number, "status": c.status},
                    confidence=0.9,
                    trust_level="TRUSTED"
                ))
        return items


class InventoryContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        sku = criteria.get("sku")

        if sku:
            variant = db.query(ProductVariant).filter(
                ProductVariant.organization_id == organization_id,
                ProductVariant.sku == sku.upper()
            ).first()

            if variant:
                inv_items = db.query(Inventory).filter(
                    Inventory.organization_id == organization_id,
                    Inventory.product_variant_id == variant.id
                ).all()

                total_on_hand = sum(i.quantity_on_hand for i in inv_items)
                total_reserved = sum(i.quantity_reserved for i in inv_items)
                total_available = sum(i.available_quantity for i in inv_items)

                content = (
                    f"Inventory for SKU: {variant.sku}\n"
                    f"Variant: {variant.size} / {variant.color}\n"
                    f"Total On Hand: {total_on_hand}\n"
                    f"Total Reserved: {total_reserved}\n"
                    f"Available to Sell: {total_available}\n"
                    f"In Stock: {'YES' if total_available > 0 else 'NO'}"
                )
                items.append(ContextItem(
                    source_type="INVENTORY",
                    source_id=variant.id,
                    content=content,
                    metadata={
                        "sku": variant.sku,
                        "available": total_available,
                        "in_stock": total_available > 0
                    },
                    confidence=1.0,
                    trust_level="TRUSTED"
                ))
        return items


class KnowledgeContextProvider(BaseContextProvider):
    def gather(self, db: Session, organization_id: str, criteria: Dict[str, Any]) -> List[ContextItem]:
        items: List[ContextItem] = []
        keyword = criteria.get("keyword") or criteria.get("intent", "")

        query = db.query(Policy).filter(
            Policy.organization_id == organization_id,
            Policy.enabled == True
        )
        if keyword:
            kw_clean = keyword.lower().replace("_", " ")
            query = query.filter(
                (Policy.name.ilike(f"%{kw_clean}%")) |
                (Policy.description.ilike(f"%{kw_clean}%")) |
                (Policy.category.ilike(f"%{kw_clean}%"))
            )

        policies = query.limit(3).all()
        for p in policies:
            rules = db.query(PolicyRule).filter(
                PolicyRule.organization_id == organization_id,
                PolicyRule.policy_id == p.id,
                PolicyRule.enabled == True
            ).all()
            rules_str = "\n".join([f"- {r.name or 'Rule'}: condition={r.condition} => {r.action}" for r in rules])
            content = (
                f"Policy: {p.name} ({p.category})\n"
                f"Description: {p.description or 'N/A'}\n"
                f"Rules:\n{rules_str or 'None'}"
            )
            items.append(ContextItem(
                source_type="POLICY",
                source_id=p.id,
                content=content,
                metadata={"policy_name": p.name, "category": p.category},
                confidence=1.0,
                trust_level="TRUSTED"
            ))
        return items
