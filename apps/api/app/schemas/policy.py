from typing import List, Optional
from pydantic import BaseModel, Field


class TriggeredRule(BaseModel):
    rule_id: str
    rule_name: str
    policy_code: str
    condition_field: str
    operator: str
    threshold_value: str
    actual_value: str
    action: str  # REQUIRE_APPROVAL, BLOCK_EXECUTION, FLAG_HIGH_RISK, AUTO_APPROVE
    priority: str


class PolicyEvaluationResult(BaseModel):
    passed: bool = Field(default=True, description="Whether all mandatory business policies passed without violation")
    approval_required: bool = Field(default=False, description="Whether policy rules require human sign-off")
    block_execution: bool = Field(default=False, description="Whether tool execution must be unconditionally blocked")
    triggered_rules: List[TriggeredRule] = Field(default_factory=list, description="List of policy rules triggered")
    summary: str = Field(default="All operational policies evaluated successfully.", description="Explanation of evaluation")
