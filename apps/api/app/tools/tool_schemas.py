"""
Tool Schemas — Phase 8.

Strict Pydantic input/output schemas for all 27 registered tools.
These schemas are the ONLY accepted input format for tool execution.
The ToolExecutionService validates all inputs against these schemas
before any handler is called.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class ToolOutput(BaseModel):
    """Every tool output wraps in this envelope."""
    tool: str
    status: str  # SUCCESS, PARTIAL_SUCCESS, FAILED, UNKNOWN
    data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# READ — Order
# ---------------------------------------------------------------------------

class GetOrderInput(BaseModel):
    order_number: str = Field(..., min_length=1, max_length=50)

    @field_validator("order_number")
    @classmethod
    def sanitize_order_number(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[A-Za-z0-9\-_]+$', v):
            raise ValueError("Invalid order number format")
        return v.upper()


class GetOrderOutput(BaseModel):
    order_id: str
    order_number: str
    status: str
    payment_status: str
    total_amount: float
    currency: str
    customer_id: str
    created_at: str
    items_count: int


# ---------------------------------------------------------------------------
# READ — Customer
# ---------------------------------------------------------------------------

class GetCustomerInput(BaseModel):
    customer_id: Optional[str] = None
    email: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class GetProductInput(BaseModel):
    product_id: Optional[str] = None
    sku: Optional[str] = None
    name_search: Optional[str] = Field(None, max_length=200)


class GetInventoryInput(BaseModel):
    product_id: Optional[str] = None
    variant_id: Optional[str] = None
    sku: Optional[str] = None
    warehouse_id: Optional[str] = None


class GetShipmentInput(BaseModel):
    shipment_id: Optional[str] = None
    order_id: Optional[str] = None
    tracking_number: Optional[str] = None


class GetReturnInput(BaseModel):
    return_id: Optional[str] = None
    order_id: Optional[str] = None


class GetRefundInput(BaseModel):
    refund_id: Optional[str] = None
    order_id: Optional[str] = None


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    category: Optional[str] = None


class GetSupportTicketInput(BaseModel):
    ticket_id: Optional[str] = None
    order_id: Optional[str] = None
    customer_id: Optional[str] = None


class GetVendorInput(BaseModel):
    vendor_id: Optional[str] = None
    name_search: Optional[str] = Field(None, max_length=200)


class GetPurchaseOrderInput(BaseModel):
    po_id: Optional[str] = None
    vendor_id: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# SUPPORT
# ---------------------------------------------------------------------------

class CreateSupportTicketInput(BaseModel):
    customer_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="MEDIUM")
    order_id: Optional[str] = None
    channel: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH", "URGENT"}
        if v.upper() not in allowed:
            raise ValueError(f"Priority must be one of {allowed}")
        return v.upper()


class UpdateSupportTicketInput(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    status: Optional[str] = None
    resolution: Optional[str] = Field(None, max_length=5000)
    internal_note: Optional[str] = Field(None, max_length=5000)


class AssignSupportTicketInput(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    assignee_id: str = Field(..., min_length=1)


class CreateInternalTaskInput(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="MEDIUM")
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None


# ---------------------------------------------------------------------------
# RETURN
# ---------------------------------------------------------------------------

class RequestReturnInput(BaseModel):
    order_id: str = Field(..., min_length=1)
    order_item_ids: List[str] = Field(..., min_length=1)
    reason: str = Field(..., min_length=10, max_length=2000)
    customer_id: str = Field(..., min_length=1)


class ApproveReturnInput(BaseModel):
    return_id: str = Field(..., min_length=1)
    approved_by: str = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)


class RejectReturnInput(BaseModel):
    return_id: str = Field(..., min_length=1)
    rejected_by: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=5, max_length=2000)


# ---------------------------------------------------------------------------
# REFUND
# ---------------------------------------------------------------------------

class RequestRefundInput(BaseModel):
    order_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0, le=999999)
    reason: str = Field(..., min_length=5, max_length=2000)
    customer_id: str = Field(..., min_length=1)
    return_id: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 2)


class ApproveRefundInput(BaseModel):
    refund_id: str = Field(..., min_length=1)
    approved_by: str = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)


class ExecuteRefundInput(BaseModel):
    refund_id: str = Field(..., min_length=1)
    payment_method: str = Field(default="ORIGINAL_PAYMENT_METHOD")
    mock_scenario: str = Field(default="SUCCESS")  # SUCCESS, FAILED, TIMEOUT, ALREADY_REFUNDED

    @field_validator("mock_scenario")
    @classmethod
    def validate_scenario(cls, v: str) -> str:
        allowed = {"SUCCESS", "FAILED", "TIMEOUT", "ALREADY_REFUNDED", "PARTIAL_REFUND"}
        if v.upper() not in allowed:
            raise ValueError(f"mock_scenario must be one of {allowed}")
        return v.upper()


# ---------------------------------------------------------------------------
# ORDER
# ---------------------------------------------------------------------------

class CancelOrderInput(BaseModel):
    order_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)   # ownership validation
    reason: str = Field(..., min_length=5, max_length=2000)


class UpdateOrderInput(BaseModel):
    order_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    shipping_address_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# INVENTORY
# ---------------------------------------------------------------------------

class ReserveInventoryInput(BaseModel):
    variant_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = Field(..., gt=0, le=10000)
    order_id: Optional[str] = None


class ReleaseInventoryInput(BaseModel):
    variant_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = Field(..., gt=0, le=10000)
    order_id: Optional[str] = None


# ---------------------------------------------------------------------------
# COMMUNICATION
# ---------------------------------------------------------------------------

class SendCustomerEmailInput(BaseModel):
    customer_id: str = Field(..., min_length=1)   # resolved to email server-side; LLM never provides raw email
    subject: str = Field(..., min_length=2, max_length=200)
    body: str = Field(..., min_length=10, max_length=10000)
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    template_id: Optional[str] = None


class SendInternalNotificationInput(BaseModel):
    recipient_user_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=2, max_length=200)
    message: str = Field(..., min_length=5, max_length=5000)
    severity: str = Field(default="INFO")
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v.upper()


# ---------------------------------------------------------------------------
# PURCHASE
# ---------------------------------------------------------------------------

class CreatePurchaseOrderInput(BaseModel):
    vendor_id: str = Field(..., min_length=1)
    items: List[Dict[str, Any]] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)
    expected_delivery_date: Optional[str] = None


class SubmitPurchaseOrderInput(BaseModel):
    purchase_order_id: str = Field(..., min_length=1)
    submitted_by: str = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# Schema registry — maps handler_key → input schema class
# ---------------------------------------------------------------------------

TOOL_INPUT_SCHEMAS: Dict[str, type] = {
    "get_order": GetOrderInput,
    "get_customer": GetCustomerInput,
    "get_product": GetProductInput,
    "get_inventory": GetInventoryInput,
    "get_shipment": GetShipmentInput,
    "get_return": GetReturnInput,
    "get_refund": GetRefundInput,
    "search_knowledge": SearchKnowledgeInput,
    "get_support_ticket": GetSupportTicketInput,
    "get_vendor": GetVendorInput,
    "get_purchase_order": GetPurchaseOrderInput,
    "create_support_ticket": CreateSupportTicketInput,
    "update_support_ticket": UpdateSupportTicketInput,
    "assign_support_ticket": AssignSupportTicketInput,
    "create_internal_task": CreateInternalTaskInput,
    "request_return": RequestReturnInput,
    "approve_return": ApproveReturnInput,
    "reject_return": RejectReturnInput,
    "request_refund": RequestRefundInput,
    "approve_refund": ApproveRefundInput,
    "execute_refund": ExecuteRefundInput,
    "cancel_order": CancelOrderInput,
    "update_order": UpdateOrderInput,
    "reserve_inventory": ReserveInventoryInput,
    "release_inventory": ReleaseInventoryInput,
    "send_customer_email": SendCustomerEmailInput,
    "send_internal_notification": SendInternalNotificationInput,
    "create_purchase_order": CreatePurchaseOrderInput,
    "submit_purchase_order": SubmitPurchaseOrderInput,
}
