from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TestScenario(BaseModel):
    id: str
    name: str
    category: str
    description: str
    sample_input: Dict[str, Any]
    expected_result: Dict[str, Any]


class TestScenarioResult(BaseModel):
    test_id: str
    scenario_name: str
    category: str
    status: str  # PASSED, FAILED, RUNNING
    passed: bool
    execution_time_ms: int
    input_summary: str
    expected_output: str
    actual_output: str
    risk_level: str
    approval_triggered: bool
    tool_blocked: bool
    workflow_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
