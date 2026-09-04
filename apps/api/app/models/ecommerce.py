from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Text, Date, ForeignKey, JSON, Boolean, DateTime,
    CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class ProductCategory(Base, BaseModelMixin):
    __tablename__ = "product_categories"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), nullable=False, index=True)
    description = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    parent = relationship("ProductCategory", remote_side="ProductCategory.id", backref="children")
    products = relationship("Product", back_populates="category")

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
    )


class Product(Base, BaseModelMixin):
    __tablename__ = "products"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), default="UrbanThread", nullable=False)
    base_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)  # DRAFT, ACTIVE, INACTIVE, DISCONTINUED
    gender = Column(String(20), default="UNISEX", nullable=False)  # MEN, WOMEN, UNISEX, KIDS
    material = Column(String(100), nullable=True)                  # e.g., 100% Organic Cotton, Linen Blend
    color = Column(String(50), nullable=True)
    care_instructions = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("ProductCategory", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
        CheckConstraint("base_price >= 0", name="chk_product_base_price_nonneg"),
        CheckConstraint("sale_price IS NULL OR sale_price >= 0", name="chk_product_sale_price_nonneg"),
    )


class ProductVariant(Base, BaseModelMixin):
    __tablename__ = "product_variants"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    size = Column(String(50), nullable=False)  # XS, S, M, L, XL, XXL, FREE
    color = Column(String(50), nullable=False)
    barcode = Column(String(100), nullable=True, index=True)
    price_override = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)  # in grams
    is_active = Column(Boolean, default=True, nullable=False)

    product = relationship("Product", back_populates="variants")
    inventory_items = relationship("Inventory", back_populates="variant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_variant_org_sku"),
    )


class Warehouse(Base, BaseModelMixin):
    __tablename__ = "warehouses"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)  # e.g., WH-MUM-01
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), default="India", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    inventory_items = relationship("Inventory", back_populates="warehouse", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouse_org_code"),
    )


class Inventory(Base, BaseModelMixin):
    __tablename__ = "inventory"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_variant_id = Column(String(36), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)
    reorder_quantity = Column(Integer, default=50, nullable=False)

    variant = relationship("ProductVariant", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    __table_args__ = (
        UniqueConstraint("organization_id", "product_variant_id", "warehouse_id", name="uq_inventory_org_var_wh"),
        CheckConstraint("quantity_on_hand >= 0", name="chk_inventory_on_hand_nonneg"),
        CheckConstraint("quantity_reserved >= 0", name="chk_inventory_reserved_nonneg"),
        CheckConstraint("quantity_reserved <= quantity_on_hand", name="chk_inventory_reserved_lte_on_hand"),
    )


class CustomerAddress(Base, BaseModelMixin):
    __tablename__ = "customer_addresses"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type = Column(String(20), default="SHIPPING", nullable=False)  # BILLING, SHIPPING
    name = Column(String(255), nullable=False)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="India", nullable=False)
    phone = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    customer = relationship("Customer", back_populates="addresses")


class Coupon(Base, BaseModelMixin):
    __tablename__ = "coupons"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    discount_type = Column(String(20), default="PERCENTAGE", nullable=False)  # PERCENTAGE, FIXED_AMOUNT
    discount_value = Column(Float, nullable=False)
    minimum_order_value = Column(Float, default=0.0, nullable=False)
    maximum_discount = Column(Float, nullable=True)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_coupon_org_code"),
        CheckConstraint("discount_value > 0", name="chk_coupon_discount_pos"),
    )


class Order(Base, BaseModelMixin):
    __tablename__ = "orders"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, COMPLETED
    payment_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, AUTHORIZED, PAID, FAILED, REFUNDED, PARTIALLY_REFUNDED
    fulfillment_status = Column(String(50), default="UNFULFILLED", nullable=False)  # UNFULFILLED, PARTIALLY_FULFILLED, FULFILLED
    currency = Column(String(10), default="INR", nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    shipping_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    shipping_address_id = Column(String(36), nullable=True)
    billing_address_id = Column(String(36), nullable=True)
    placed_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)

    customer = relationship("Customer", back_populates="orders")
    coupon = relationship("Coupon")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="order", cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="order")
    refunds = relationship("Refund", back_populates="order")

    __table_args__ = (
        UniqueConstraint("organization_id", "order_number", name="uq_order_org_number"),
        CheckConstraint("total_amount >= 0", name="chk_order_total_nonneg"),
    )


class OrderItem(Base, BaseModelMixin):
    __tablename__ = "order_items"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_variant_id = Column(String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    product_name_snapshot = Column(String(255), nullable=False)
    sku_snapshot = Column(String(100), nullable=False)
    size_snapshot = Column(String(50), nullable=False)
    color_snapshot = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_qty_pos"),
        CheckConstraint("unit_price >= 0", name="chk_order_item_price_nonneg"),
    )


class Payment(Base, BaseModelMixin):
    __tablename__ = "payments"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_reference = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), default="MOCK_PAYMENT_GATEWAY", nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, AUTHORIZED, CAPTURED, FAILED, REFUNDED, PARTIALLY_REFUNDED
    payment_method_type = Column(String(50), default="UPI", nullable=False)   # CARD, UPI, NET_BANKING, WALLET, COD

    order = relationship("Order", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_nonneg"),
    )


class Shipment(Base, BaseModelMixin):
    __tablename__ = "shipments"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    tracking_number = Column(String(100), nullable=False, index=True)
    carrier = Column(String(100), default="BlueDart Express", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PACKED, SHIPPED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, DELAYED, LOST, CANCELLED
    estimated_delivery_date = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    last_location = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="shipments")


class Return(Base, BaseModelMixin):
    __tablename__ = "returns"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    return_number = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="REQUESTED", nullable=False, index=True)  # REQUESTED, UNDER_REVIEW, APPROVED, REJECTED, RECEIVED, COMPLETED, CANCELLED
    reason = Column(String(50), default="WRONG_SIZE", nullable=False)  # WRONG_SIZE, WRONG_ITEM, DAMAGED, DEFECTIVE, NOT_AS_EXPECTED, CHANGED_MIND, OTHER
    requested_at = Column(DateTime, default=get_utc_now, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="returns")
    items = relationship("ReturnItem", back_populates="return_obj", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "return_number", name="uq_return_org_number"),
    )


class ReturnItem(Base, BaseModelMixin):
    __tablename__ = "return_items"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    return_id = Column(String(36), ForeignKey("returns.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    reason = Column(String(100), nullable=True)
    condition = Column(String(50), default="NEW", nullable=False)  # NEW, OPENED, USED, DAMAGED

    return_obj = relationship("Return", back_populates="items")


class Refund(Base, BaseModelMixin):
    __tablename__ = "refunds"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    refund_number = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), default="REQUESTED", nullable=False, index=True)  # REQUESTED, PENDING_APPROVAL, APPROVED, PROCESSING, COMPLETED, FAILED, REJECTED

    order = relationship("Order", back_populates="refunds")
    payment = relationship("Payment", back_populates="refunds")

    __table_args__ = (
        UniqueConstraint("organization_id", "refund_number", name="uq_refund_org_number"),
        CheckConstraint("amount > 0", name="chk_refund_amount_pos"),
    )


class SupportTicket(Base, BaseModelMixin):
    __tablename__ = "support_tickets"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_number = Column(String(100), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, IN_PROGRESS, WAITING_FOR_CUSTOMER, RESOLVED, CLOSED
    assigned_team_id = Column(String(36), nullable=True)
    assigned_user_id = Column(String(36), nullable=True)

    customer = relationship("Customer", back_populates="support_tickets")

    __table_args__ = (
        UniqueConstraint("organization_id", "ticket_number", name="uq_ticket_org_number"),
    )


class CustomerConversation(Base, BaseModelMixin):
    __tablename__ = "customer_conversations"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for guest shoppers
    channel = Column(String(50), default="WEBSITE_CHAT", nullable=False)  # WEBSITE_CHAT, EMAIL, WHATSAPP, SMS, SOCIAL
    status = Column(String(50), default="OPEN", nullable=False, index=True)      # OPEN, WAITING_FOR_HUMAN, RESOLVED, CLOSED
    assigned_agent_id = Column(String(36), nullable=True, index=True)  # AI employee ID or human employee user ID
    context = Column(JSON, default=dict, nullable=False)  # Active intent, order tracking, pending action
    rating = Column(Integer, nullable=True)  # 1 to 5 customer satisfaction rating
    feedback = Column(Text, nullable=True)  # Customer text feedback notes
    was_helpful = Column(Boolean, nullable=True)  # Thumbs up/down
    closed_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")


class ConversationMessage(Base, BaseModelMixin):
    __tablename__ = "conversation_messages"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("customer_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(String(50), default="CUSTOMER", nullable=False)  # CUSTOMER, AI_AGENT, HUMAN_AGENT, SYSTEM, EMPLOYEE
    sender_id = Column(String(100), nullable=True)
    message_type = Column(String(50), default="TEXT", nullable=False)  # TEXT, SUGGESTION, ORDER_CARD, SHIPMENT_CARD, CONFIRMATION, HANDOFF, RESOLUTION
    content = Column(Text, nullable=False)
    msg_metadata = Column("metadata", JSON, default=dict, nullable=False)
    is_untrusted = Column(Boolean, default=True, nullable=False)  # True for customer inputs to guard against prompt injection

    conversation = relationship("CustomerConversation", back_populates="messages")

