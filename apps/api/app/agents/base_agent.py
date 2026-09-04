import time
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.app.core.ai_provider import get_ai_provider, BaseAIProvider
from apps.api.app.models.agent import AgentRun


class AgentExecutionResult(BaseModel):
    agent_code: str
    status: str  # SUCCESS, FAILED
    output: Dict[str, Any]
    confidence: float = 0.95
    latency_ms: int = 0
    error: Optional[str] = None


class BaseAgent:
    def __init__(self, code: str, name: str, system_prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.1):
        self.code = code
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.provider: BaseAIProvider = get_ai_provider()

    def run(
        self,
        input_data: Dict[str, Any],
        organization_id: str,
        workflow_id: Optional[str] = None,
        step_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> AgentExecutionResult:
        start_time = time.time()
        try:
            output_model = self._execute_logic(input_data)
            latency_ms = int((time.time() - start_time) * 1000)
            output_dict = output_model.model_dump() if hasattr(output_model, "model_dump") else output_model
            confidence = getattr(output_model, "confidence", 0.95)

            if db:
                self._record_run(db, organization_id, workflow_id, step_id, "SUCCESS", input_data, output_dict, latency_ms, confidence)

            return AgentExecutionResult(
                agent_code=self.code,
                status="SUCCESS",
                output=output_dict,
                confidence=confidence,
                latency_ms=latency_ms
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            if db:
                self._record_run(db, organization_id, workflow_id, step_id, "FAILED", input_data, {}, latency_ms, 0.0, error=str(e))
            return AgentExecutionResult(
                agent_code=self.code,
                status="FAILED",
                output={},
                confidence=0.0,
                latency_ms=latency_ms,
                error=str(e)
            )

    def _execute_logic(self, input_data: Dict[str, Any]) -> Any:
        raise NotImplementedError

    def _record_run(self, db: Session, org_id: str, workflow_id: Optional[str], step_id: Optional[str], status: str, input_data: dict, output_data: dict, latency_ms: int, confidence: float, error: Optional[str] = None):
        try:
            run = AgentRun(
                organization_id=org_id,
                agent_id=self.code,
                workflow_id=workflow_id,
                step_id=step_id,
                status=status,
                input_data=input_data,
                output_data=output_data,
                latency_ms=latency_ms,
                confidence=confidence,
                cost_estimate=0.002,
                error=error
            )
            db.add(run)
            db.commit()
        except Exception:
            db.rollback()
