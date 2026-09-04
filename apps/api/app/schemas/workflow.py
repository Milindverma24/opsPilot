from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WorkflowStepResponse(BaseModel):
    id: str
    step_type: str
    step_order: int
    status: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: str
    organization_id: str
    workflow_type: str
    status: str
    idempotency_key: str
    document_id: Optional[str] = None
    context: Dict[str, Any]
    error: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    steps: List[WorkflowStepResponse] = Field(default_factory=list)


class ApprovalResponse(BaseModel):
    id: str
    organization_id: str
    workflow_id: str
    request_type: str
    amount: Optional[float] = None
    currency: str = "INR"
    risk_level: str
    status: str
    requester_name: str
    ai_recommendation: str
    reason: str
    affected_entity_type: Optional[str] = None
    affected_entity_id: Optional[str] = None
    created_at: str


class ApprovalActionRequest(BaseModel):
    action: str = Field(description="APPROVE, REJECT, or REQUEST_CHANGES")
    comment: Optional[str] = Field(default=None, description="Optional reviewer feedback or rejection reason")


class CommandRequest(BaseModel):
    query: str = Field(description="Natural language operations query, e.g. 'Show invoices above 1 lakh'")


class CommandResponse(BaseModel):
    intent: str
    summary: str
    action_type: str  # QUERY, FILTER, AGGREGATE, REPORT
    data: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    confidence: float = 0.95
