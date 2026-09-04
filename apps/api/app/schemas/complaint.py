from typing import Optional, Literal
from pydantic import BaseModel, Field

ComplaintCategory = Literal[
    "DELIVERY",
    "PAYMENT",
    "PRODUCT",
    "REFUND",
    "ACCOUNT",
    "TECHNICAL",
    "OTHER"
]

ComplaintSentiment = Literal["POSITIVE", "NEUTRAL", "NEGATIVE"]

ComplaintUrgency = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

ComplaintPriority = Literal["P1", "P2", "P3", "P4"]


class ComplaintExtractionResult(BaseModel):
    customer_name: Optional[str] = Field(default=None, description="Extracted sender / customer name")
    customer_email: Optional[str] = Field(default=None, description="Customer contact email")
    customer_id: Optional[str] = Field(default=None, description="Customer account ID if mentioned")
    order_id: Optional[str] = Field(default=None, description="Associated Order ID if mentioned")
    issue_summary: str = Field(description="Normalized summary of customer issue")
    category: ComplaintCategory = Field(default="OTHER", description="Complaint domain category")
    sentiment: ComplaintSentiment = Field(default="NEGATIVE", description="Customer sentiment")
    urgency: ComplaintUrgency = Field(default="HIGH", description="Assessed issue urgency")
    priority: ComplaintPriority = Field(default="P2", description="Assigned ticket priority")
    requested_resolution: Optional[str] = Field(default=None, description="e.g. Immediate refund, replacement")
    refund_requested: bool = Field(default=False, description="Whether customer requested financial refund")
    refund_amount: float = Field(default=0.0, description="Refund amount requested, if specified")
    confidence: float = Field(default=0.92, ge=0.0, le=1.0, description="AI extraction confidence")
    recommended_response: Optional[str] = Field(default=None, description="AI drafted courteous resolution email")
