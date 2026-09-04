from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ActionStep(BaseModel):
    step_number: int = Field(default=1)
    tool_name: str = Field(description="Name of the registered tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input parameters passed to the tool")
    reason: str = Field(description="Operational justification for why this tool is called")
    requires_approval: bool = Field(default=False, description="Whether this individual tool step requires human sign-off")
    risk_level: str = Field(default="LOW", description="Risk of this specific tool invocation")


class ActionPlan(BaseModel):
    plan_id: str = Field(default="")
    goal: str = Field(description="High-level operational goal")
    requires_human_approval: bool = Field(default=False, description="Whether workflow execution must pause before tools")
    approval_reason: Optional[str] = Field(default=None, description="Detailed explanation of why approval is needed")
    approval_role: str = Field(default="FINANCE_MANAGER", description="Required role for sign-off")
    steps: List[ActionStep] = Field(default_factory=list, description="Ordered sequence of actions")
    summary: str = Field(default="", description="Narrative summary of the operational plan")
