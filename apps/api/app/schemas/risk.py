from typing import List, Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class RiskFactor(BaseModel):
    category: str = Field(description="Factor category, e.g. AMOUNT, VENDOR, PO_MISMATCH, SECURITY")
    description: str = Field(description="Human-readable explanation of why this factor increases risk")
    severity: RiskLevel = Field(description="Individual severity of this specific factor")
    score_impact: int = Field(default=0, description="Additive impact on total 0-100 risk score")


class RiskAssessmentResult(BaseModel):
    risk_score: int = Field(default=10, ge=0, le=100, description="Composite risk rating from 0 to 100")
    risk_level: RiskLevel = Field(default="LOW", description="Risk tier: LOW (0-30), MEDIUM (31-60), HIGH (61-80), CRITICAL (81-100)")
    requires_human_approval: bool = Field(default=False, description="Flag indicating whether human intervention is mandatory")
    approval_role: str = Field(default="FINANCE_MANAGER", description="Designated role that must approve if required")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Specific identified risks")
    summary: str = Field(default="Standard low-risk operational transaction.", description="Summary narrative")
