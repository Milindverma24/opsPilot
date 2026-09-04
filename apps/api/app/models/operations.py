from datetime import date
from sqlalchemy import (
    Column, String, Integer, Float, Text, Date, ForeignKey, JSON, Boolean, DateTime,
    CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class Vendor(Base, BaseModelMixin):
    __tablename__ = "vendors"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_code = Column(String(100), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    tax_id = Column(String(100), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(512), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, PENDING_REVIEW, BLOCKED
    approved = Column(Boolean, default=True, nullable=False)
    risk_level = Column(String(20), default="LOW", nullable=False)    # LOW, MEDIUM, HIGH, CRITICAL
    bank_details = Column(JSON, default=dict, nullable=False)

    risk_tier = synonym("risk_level")

    invoices = relationship("Invoice", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class Customer(Base, BaseModelMixin):
    __tablename__ = "customers"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_number = Column(String(100), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(255), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    date_of_birth = Column(Date, nullable=True)

    customer_code = synonym("customer_number")

    complaints = relationship("Complaint", back_populates="customer")
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")
    conversations = relationship("CustomerConversation", back_populates="customer")


class PurchaseOrder(Base, BaseModelMixin):
    __tablename__ = "purchase_orders"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    po_number = Column(String(100), nullable=False, index=True)
    issue_date = Column(Date, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="APPROVED", nullable=False)  # DRAFT, APPROVED, FULFILLED, CANCELLED
    department = Column(String(100), nullable=True)

    order_date = synonym("issue_date")
    amount = synonym("total")

    vendor = relationship("Vendor", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="chk_po_subtotal_positive"),
        CheckConstraint("tax >= 0", name="chk_po_tax_positive"),
        CheckConstraint("total >= 0", name="chk_po_total_positive"),
        Index("ix_po_org_num", "organization_id", "po_number"),
    )


class PurchaseOrderItem(Base, BaseModelMixin):
    __tablename__ = "purchase_order_items"

    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")


class Invoice(Base, BaseModelMixin):
    __tablename__ = "invoices"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)

    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    purchase_order_number = Column(String(100), nullable=True, index=True)
    payment_terms = Column(String(100), nullable=True)
    status = Column(String(50), default="RECEIVED", nullable=False, index=True)  # RECEIVED, PROCESSING, PENDING_REVIEW, PENDING_APPROVAL, APPROVED, REJECTED, PAID, FAILED, DUPLICATE
    risk_level = Column(String(20), default="LOW", nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    ai_confidence = Column(Float, default=1.0, nullable=False)
    bank_details = Column(JSON, default=dict, nullable=False)
    payment_reference = Column(String(100), nullable=True)

    payment_status = synonym("status")

    document = relationship("Document", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total >= 0", name="chk_invoice_total_positive"),
        CheckConstraint("subtotal >= 0", name="chk_invoice_subtotal_positive"),
        CheckConstraint("tax >= 0", name="chk_invoice_tax_positive"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_invoice_risk_score"),
        CheckConstraint("ai_confidence >= 0 AND ai_confidence <= 1", name="chk_invoice_ai_confidence"),
        Index("ix_invoice_org_num", "organization_id", "invoice_number"),
    )


class InvoiceLineItem(Base, BaseModelMixin):
    __tablename__ = "invoice_line_items"

    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)

    invoice = relationship("Invoice", back_populates="line_items")


class Complaint(Base, BaseModelMixin):
    __tablename__ = "complaints"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    source_email_id = Column(String(36), ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True)

    order_id = Column(String(100), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    category = Column(String(50), default="OTHER", nullable=False)  # DELIVERY, PAYMENT, PRODUCT, REFUND, ACCOUNT, TECHNICAL, OTHER
    description = Column(Text, nullable=False)
    sentiment = Column(String(20), default="NEUTRAL", nullable=False)  # POSITIVE, NEUTRAL, NEGATIVE
    urgency = Column(String(20), default="MEDIUM", nullable=False)     # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(10), default="P3", nullable=False)        # P1, P2, P3, P4
    requested_resolution = Column(String(255), nullable=True)
    refund_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)        # OPEN, INVESTIGATING, RESOLVED, CLOSED
    ai_confidence = Column(Float, default=1.0, nullable=False)
    ai_draft_response = Column(Text, nullable=True)

    issue = synonym("description")

    customer = relationship("Customer", back_populates="complaints")
    document = relationship("Document", back_populates="complaints")


class Task(Base, BaseModelMixin):
    __tablename__ = "tasks"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), default="OPERATIONS", nullable=False, index=True) # PICK_AND_PACK, RESTOCK, CUSTOMER_OUTREACH, INVOICE_REVIEW
    order_id = Column(String(100), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    items_summary = Column(JSON, default=list, nullable=False)

    priority = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL, NORMAL
    status = Column(String(50), default="CREATED", nullable=False, index=True)
    # Statuses: CREATED, ASSIGNED, CLAIMED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED, ESCALATED, EXPIRED

    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Worker lease & Crash recovery
    claimed_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    lease_token = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    execution_receipt = Column(JSON, default=dict, nullable=False)

    assigned_user_id = synonym("assigned_to")
    due_date = synonym("due_at")
