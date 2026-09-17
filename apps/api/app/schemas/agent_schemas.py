"""
Phase 7 — Structured AI output schemas.

All LLM outputs are validated through these Pydantic models.
Free-form model responses are never trusted directly.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IntentType(str, Enum):
    PRODUCT_QUESTION = "PRODUCT_QUESTION"
    ORDER_STATUS = "ORDER_STATUS"
    ORDER_CHANGE = "ORDER_CHANGE"
    ORDER_CANCELLATION = "ORDER_CANCELLATION"
    SHIPPING_QUESTION = "SHIPPING_QUESTION"
    SHIPPING_DELAY = "SHIPPING_DELAY"
    RETURN_REQUEST = "RETURN_REQUEST"
    REFUND_REQUEST = "REFUND_REQUEST"
    EXCHANGE_REQUEST = "EXCHANGE_REQUEST"
    COMPLAINT = "COMPLAINT"
    SUPPORT_REQUEST = "SUPPORT_REQUEST"
    INVENTORY_QUESTION = "INVENTORY_QUESTION"
    COUPON_QUESTION = "COUPON_QUESTION"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    VENDOR_REQUEST = "VENDOR_REQUEST"
    INTERNAL_OPERATION = "INTERNAL_OPERATION"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    UNKNOWN = "UNKNOWN"


class DecisionType(str, Enum):
    ANSWER = "ANSWER"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    CREATE_TASK = "CREATE_TASK"
    CREATE_SUPPORT_TICKET = "CREATE_SUPPORT_TICKET"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    EXECUTE_ACTION = "EXECUTE_ACTION"
    ESCALATE = "ESCALATE"
    REFUSE = "REFUSE"
    NO_ACTION = "NO_ACTION"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class TriggerType(str, Enum):
    CUSTOMER_MESSAGE = "CUSTOMER_MESSAGE"
    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    BUSINESS_EVENT = "BUSINESS_EVENT"
    INTERNAL_REQUEST = "INTERNAL_REQUEST"
    SCHEDULED_TASK = "SCHEDULED_TASK"
    MANUAL_TRIGGER = "MANUAL_TRIGGER"


class ActionType(str, Enum):
    # Read-only lookups (LOW risk)
    LOOKUP_CUSTOMER = "LOOKUP_CUSTOMER"
    LOOKUP_PRODUCT = "LOOKUP_PRODUCT"
    LOOKUP_ORDER = "LOOKUP_ORDER"
    LOOKUP_SHIPMENT = "LOOKUP_SHIPMENT"
    SEARCH_KNOWLEDGE = "SEARCH_KNOWLEDGE"
    # Ticket / task creation (MEDIUM risk)
    CREATE_SUPPORT_TICKET = "CREATE_SUPPORT_TICKET"
    CREATE_TASK = "CREATE_TASK"
    UPDATE_SUPPORT_TICKET = "UPDATE_SUPPORT_TICKET"
    # Business actions (HIGH risk — require approval)
    REQUEST_RETURN = "REQUEST_RETURN"
    REQUEST_REFUND = "REQUEST_REFUND"
    UPDATE_ORDER = "UPDATE_ORDER"
    # Communication (MEDIUM risk)
    SEND_NOTIFICATION = "SEND_NOTIFICATION"
    SEND_EMAIL = "SEND_EMAIL"
    # Inventory / purchasing (HIGH risk)
    ADJUST_INVENTORY = "ADJUST_INVENTORY"
    CREATE_PURCHASE_REQUEST = "CREATE_PURCHASE_REQUEST"

    # EXPLICITLY FORBIDDEN — never allow these
    # RUN_CODE, EXECUTE_SQL, HTTP_REQUEST, SHELL_COMMAND, ARBITRARY_FUNCTION


# ---------------------------------------------------------------------------
# Normalized Agent Request
# ---------------------------------------------------------------------------

class ActorInfo(BaseModel):
    actor_type: str = Field(default="CUSTOMER", description="CUSTOMER, USER, SYSTEM, AI_EMPLOYEE")
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class AgentRequest(BaseModel):
    """Normalized input from any channel."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    source: str = Field(default="WEBSITE_CHAT", description="CUSTOMER_EMAIL, WEBSITE_CHAT, INTERNAL, MANUAL")
    actor: ActorInfo = Field(default_factory=lambda: ActorInfo(actor_type="CUSTOMER"))
    message: str
    channel: str = "WEB_CHAT"
    actor_type: str = "CUSTOMER"
    actor_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    related_entities: Dict[str, Any] = Field(default_factory=dict)
    trigger_type: TriggerType = TriggerType.MANUAL_TRIGGER
    trigger_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    execution_mode: str = Field(default="PLAN_ONLY", description="PLAN_ONLY or EXECUTE (Phase 8)")


# ---------------------------------------------------------------------------
# Intent Classification
# ---------------------------------------------------------------------------

class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities_hint: Dict[str, Any] = Field(default_factory=dict, description="Raw entity hints from classifier")
    reason: str = ""
    is_prompt_injection: bool = False
    classification_method: str = Field(default="deterministic", description="deterministic or llm")


# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------

class ExtractedEntity(BaseModel):
    value: str
    raw_text: str
    db_verified: bool = False
    db_id: Optional[str] = None   # actual DB UUID if verified


class EntityExtractionResult(BaseModel):
    order_number: Optional[ExtractedEntity] = None
    customer_id: Optional[ExtractedEntity] = None
    product_name: Optional[ExtractedEntity] = None
    sku: Optional[ExtractedEntity] = None
    variant: Optional[ExtractedEntity] = None
    size: Optional[str] = None
    color: Optional[str] = None
    tracking_number: Optional[ExtractedEntity] = None
    return_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_currency: str = "INR"
    coupon_code: Optional[str] = None
    vendor_name: Optional[str] = None
    extraction_method: str = Field(default="deterministic")
    raw_extractions: Dict[str, Any] = Field(default_factory=dict)

    # Multi-value collections & convenience fields
    order_numbers: List[str] = Field(default_factory=list)
    order_ids: List[str] = Field(default_factory=list)
    verified_order_numbers: List[str] = Field(default_factory=list)
    skus: List[str] = Field(default_factory=list)
    verified_skus: List[str] = Field(default_factory=list)
    tracking_numbers: List[str] = Field(default_factory=list)
    customer_ids: List[str] = Field(default_factory=list)
    amounts: List[float] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    untrusted_flags: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class ContextItem(BaseModel):
    """A single piece of retrieved context, always tagged with its source."""
    source_type: str = Field(description="ORDER, CUSTOMER, PRODUCT, SHIPMENT, KNOWLEDGE, POLICY, SUPPORT, EMAIL")
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    retrieved_at: str = ""
    trust_level: str = Field(default="TRUSTED_COMPANY_DATA")


class ContextBudget(BaseModel):
    max_records: int = 10
    max_rag_chunks: int = 5
    max_conversation_messages: int = 10
    max_tokens_estimate: int = 4000


class ContextRequirement(BaseModel):
    source_type: str = "ORDER"
    is_mandatory: bool = False
    query_params: Dict[str, Any] = Field(default_factory=dict)
    needs_customer: bool = False
    needs_order: bool = False
    needs_shipment: bool = False
    needs_return: bool = False
    needs_refund: bool = False
    needs_product: bool = False
    needs_inventory: bool = False
    needs_support_history: bool = False
    needs_policy: bool = False
    needs_knowledge: bool = True
    reason: str = ""


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------

class ReasoningResult(BaseModel):
    decision: DecisionType
    decision_summary: str = Field(description="Brief human-readable summary, no hidden chain-of-thought")
    reason_codes: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel = RiskLevel.LOW
    proposed_response: Optional[str] = Field(
        default=None,
        description="Draft customer-facing message. NOT sent until Phase 8 approves."
    )
    required_actions: List[str] = Field(default_factory=list)
    grounded: bool = False
    source_ids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk Assessment
# ---------------------------------------------------------------------------

class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    approval_type: str = "NONE"
    suggested_approvers: List[str] = Field(default_factory=list)
    financial_impact: Optional[float] = None
    is_financial_action: bool = False
    is_data_sensitive: bool = False
    is_irreversible: bool = False
    policy_applied: Optional[str] = None


# ---------------------------------------------------------------------------
# Action Planning
# ---------------------------------------------------------------------------

class PlannedAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_name: str = ""
    action_type: Optional[Any] = None
    target_system: str = "CORE"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    estimated_risk: str = "LOW"
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    order: int = 1
    description: str = ""
    tool_hint: Optional[str] = None             # future tool name for Phase 8
    required_permission: Optional[str] = None
    # PLAN_ONLY: actual execution blocked until Phase 8
    execution_blocked: bool = True
    block_reason: str = "Phase 7 PLAN_ONLY mode"


class ActionPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    organization_id: str = ""
    plan_summary: str = ""
    actions: List[PlannedAction] = Field(default_factory=list)
    risk_assessment: Optional[Any] = None
    requires_approval: bool = False
    approval_status: str = "NOT_REQUIRED"
    estimated_risk: RiskLevel = RiskLevel.LOW
    execution_mode: str = "PLAN_ONLY"
    plan_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    created_at: str = ""


# ---------------------------------------------------------------------------
# Tool Selection (Phase 8 preparation)
# ---------------------------------------------------------------------------

class ToolSelection(BaseModel):
    action_type: str
    tool_name: str
    required_permission: str
    risk_level: RiskLevel
    requires_approval: bool
    available: bool = False     # Will be True in Phase 8


# ---------------------------------------------------------------------------
# Full Agent Decision Output
# ---------------------------------------------------------------------------

class AgentDecision(BaseModel):
    """Complete output of one agent reasoning cycle."""
    run_id: str
    organization_id: str
    intent: IntentResult
    entities: EntityExtractionResult
    context_items: List[ContextItem] = Field(default_factory=list)
    reasoning: ReasoningResult
    risk: RiskAssessment
    plan: ActionPlan
    status: AgentRunStatus
    execution_mode: str = "PLAN_ONLY"
    total_steps: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    model_used: Optional[str] = None


# ---------------------------------------------------------------------------
# Failure codes
# ---------------------------------------------------------------------------

FAILURE_CODES = [
    "CONTEXT_NOT_FOUND",
    "LOW_CONFIDENCE",
    "POLICY_DENIED",
    "KNOWLEDGE_CONFLICT",
    "TOOL_UNAVAILABLE",
    "APPROVAL_REQUIRED",
    "AGENT_TIMEOUT",
    "MAX_STEPS_EXCEEDED",
    "MODEL_ERROR",
    "TENANT_ISOLATION_VIOLATION",
    "PERMISSION_DENIED",
    "PROMPT_INJECTION_BLOCKED",
]
