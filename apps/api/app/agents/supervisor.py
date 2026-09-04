"""
Phase 7 — AI Supervisor Orchestration Engine.

Orchestrates the bounded THINK + PLAN cognitive loop:
INPUT -> CLASSIFY -> EXTRACT -> CONTEXT -> REASON -> RISK -> PLAN -> EVALUATE_APPROVAL

Strict Principles:
1. Pure THINK + PLAN mode — zero tool execution (Phase 8).
2. Append-only persistence: every step logged to AgentStep.
3. Strict tenant isolation: organization_id is never bypassed.
4. Idempotency guarantees: deduplication via idempotency_key.
5. Prompt injection treated as untrusted data, never executed.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.models.base import get_utc_now
from apps.api.app.models.agent import AIEmployee, AgentRun, AgentStep
from apps.api.app.schemas.agent_schemas import (
    ActionPlan,
    AgentRequest,
    DecisionType,
    EntityExtractionResult,
    IntentResult,
    IntentType,
    ReasoningResult,
    RiskAssessment,
    RiskLevel,
)
from apps.api.app.services.ai.intent_service import IntentClassificationService
from apps.api.app.services.ai.entity_service import EntityExtractionService
from apps.api.app.services.ai.context_service import ContextGatheringService
from apps.api.app.services.ai.reasoning_service import ReasoningService
from apps.api.app.services.ai.risk_service import RiskAssessmentService
from apps.api.app.services.ai.action_plan_service import ActionPlanningService, ToolSelectionService
from apps.api.app.services.ai.memory_service import MemoryService


class AgentSupervisor:
    def __init__(self):
        self.intent_service = IntentClassificationService()
        self.entity_service = EntityExtractionService()
        self.context_service = ContextGatheringService()
        self.reasoning_service = ReasoningService()
        self.risk_service = RiskAssessmentService()
        self.planning_service = ActionPlanningService()
        self.tool_service = ToolSelectionService()
        self.memory_service = MemoryService()

    def process_request(
        self,
        db: Session,
        organization_id: str,
        request: AgentRequest,
        ai_employee_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> AgentRun:
        """
        Execute the full cognitive orchestration loop.
        Survives restarts and is completely auditable.
        """
        start_time = time.time()

        # -------------------------------------------------------------------
        # 1. Idempotency Check
        # -------------------------------------------------------------------
        if idempotency_key:
            existing = db.query(AgentRun).filter(
                AgentRun.organization_id == organization_id,
                AgentRun.idempotency_key == idempotency_key,
            ).first()
            if existing:
                return existing

        # -------------------------------------------------------------------
        # 2. Identify AI Employee Persona
        # -------------------------------------------------------------------
        ai_employee = None
        if ai_employee_id:
            ai_employee = db.query(AIEmployee).filter(
                AIEmployee.organization_id == organization_id,
                AIEmployee.id == ai_employee_id,
            ).first()

        if not ai_employee:
            ai_employee = db.query(AIEmployee).filter(
                AIEmployee.organization_id == organization_id,
                AIEmployee.status == "ACTIVE",
            ).first()

        # -------------------------------------------------------------------
        # 3. Create Persistent AgentRun Record
        # -------------------------------------------------------------------
        trigger_val = request.trigger_type.value if hasattr(request.trigger_type, "value") else str(request.trigger_type or "CUSTOMER_MESSAGE")
        run = AgentRun(
            organization_id=organization_id,
            ai_employee_id=ai_employee.id if ai_employee else None,
            idempotency_key=idempotency_key,
            trigger_type=trigger_val,
            trigger_id=request.trigger_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            status="RUNNING",
            current_step="INITIALIZING",
            input_data=request.model_dump(),
            context_data=[],
            extracted_data={},
            decisions=[],
            policy_results=[],
            planned_actions=[],
            completed_actions=[],
            reason_codes=[],
            evidence_ids=[],
            errors=[],
            model_used=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
            started_at=get_utc_now(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        step_counter = 0

        try:
            # ---------------------------------------------------------------
            # Step 0: Intent Classification
            # ---------------------------------------------------------------
            run.current_step = "CLASSIFYING"
            step_0 = self._start_step(db, run.id, organization_id, step_counter, "CLASSIFY", {"message": request.message})
            intent_result: IntentResult = self.intent_service.classify(request.message)
            self._complete_step(db, step_0, intent_result.model_dump())
            step_counter += 1

            run.intent = intent_result.intent.value
            run.intent_confidence = intent_result.confidence
            db.commit()

            # ---------------------------------------------------------------
            # Security Gate: Block prompt injection immediately after classify
            # ---------------------------------------------------------------
            if intent_result.intent == IntentType.PROMPT_INJECTION or getattr(intent_result, "is_prompt_injection", False):
                run.status = "BLOCKED"
                run.risk_level = RiskLevel.CRITICAL.value
                run.risk_score = 1.0
                run.requires_human_approval = False
                run.total_steps = step_counter
                run.latency_ms = int((time.time() - start_time) * 1000)
                run.completed_at = get_utc_now()
                run.current_step = "FINISHED"
                run.decision_summary = "Request blocked: prompt injection pattern detected."
                run.reason_codes = ["PROMPT_INJECTION", "SECURITY_PROMPT_INJECTION"]
                db.commit()
                db.refresh(run)
                return run

            # ---------------------------------------------------------------
            # Step 1: Entity Extraction & DB Verification
            # ---------------------------------------------------------------
            run.current_step = "EXTRACTING_ENTITIES"
            step_1 = self._start_step(db, run.id, organization_id, step_counter, "EXTRACT_ENTITIES", {"message": request.message})
            entity_result: EntityExtractionResult = self.entity_service.extract(db, organization_id, request.message)
            self._complete_step(db, step_1, entity_result.model_dump())
            step_counter += 1

            run.extracted_data = entity_result.model_dump()
            db.commit()

            # ---------------------------------------------------------------
            # Step 2: Bounded Context Gathering (Read-Only)
            # ---------------------------------------------------------------
            run.current_step = "GATHERING_CONTEXT"
            step_2 = self._start_step(
                db, run.id, organization_id, step_counter, "GATHER_CONTEXT",
                {"intent": run.intent, "entities": entity_result.model_dump()}
            )
            context_items = self.context_service.gather_context(
                db=db,
                organization_id=organization_id,
                intent=run.intent,
                entities=entity_result,
                actor_id=request.actor_id,
                additional_params=request.metadata,
                max_items=getattr(settings, "MAX_AGENT_STEPS", 12),
            )
            self._complete_step(db, step_2, {"items_count": len(context_items), "items": [c.model_dump() for c in context_items]})
            step_counter += 1

            run.context_data = [c.model_dump() for c in context_items]
            db.commit()

            # ---------------------------------------------------------------
            # Step 3: Cognitive Reasoning
            # ---------------------------------------------------------------
            run.current_step = "REASONING"
            step_3 = self._start_step(db, run.id, organization_id, step_counter, "REASON", {"intent": run.intent})
            reasoning_result: ReasoningResult = self.reasoning_service.reason(
                intent=run.intent,
                entities=entity_result,
                context_items=context_items,
                user_message=request.message,
                channel=request.channel,
            )
            self._complete_step(db, step_3, reasoning_result.model_dump())
            step_counter += 1

            run.decisions = [reasoning_result.model_dump()]
            run.decision_summary = reasoning_result.decision_summary
            run.reason_codes = reasoning_result.reason_codes
            run.evidence_ids = reasoning_result.evidence_ids
            run.confidence = reasoning_result.confidence
            db.commit()

            # ---------------------------------------------------------------
            # Step 4: Risk Assessment & Approval Gates
            # ---------------------------------------------------------------
            run.current_step = "ASSESSING_RISK"
            step_4 = self._start_step(db, run.id, organization_id, step_counter, "ASSESS_RISK", {"decision": reasoning_result.decision.value})
            risk_assessment: RiskAssessment = self.risk_service.assess_risk(
                intent=run.intent,
                decision=reasoning_result.decision,
                entities=entity_result,
                actions=reasoning_result.required_actions,
                confidence=reasoning_result.confidence,
            )
            self._complete_step(db, step_4, risk_assessment.model_dump())
            step_counter += 1

            run.risk_level = risk_assessment.risk_level.value
            run.risk_score = risk_assessment.risk_score
            run.requires_human_approval = risk_assessment.requires_approval
            db.commit()

            # ---------------------------------------------------------------
            # Step 5: Action Planning (Strict PLAN_ONLY)
            # ---------------------------------------------------------------
            run.current_step = "PLANNING_ACTIONS"
            step_5 = self._start_step(db, run.id, organization_id, step_counter, "PLAN_ACTIONS", {"risk_level": run.risk_level})
            action_plan: ActionPlan = self.planning_service.create_plan(
                reasoning=reasoning_result,
                intent=run.intent,
                entities=entity_result,
                risk=risk_assessment,
                organization_id=organization_id,
            )
            action_plan.run_id = run.id
            self._complete_step(db, step_5, action_plan.model_dump())
            step_counter += 1

            run.planned_actions = action_plan.model_dump().get("actions", [])
            db.commit()

            # ---------------------------------------------------------------
            # Finalize Run Status & Metrics
            # ---------------------------------------------------------------
            run.total_steps = step_counter
            duration_ms = int((time.time() - start_time) * 1000)
            run.latency_ms = duration_ms
            run.completed_at = get_utc_now()

            # Determine final status (prompt injection already short-circuits above)
            if run.requires_human_approval:
                run.status = "WAITING_FOR_APPROVAL"
            else:
                run.status = "COMPLETED"

            run.current_step = "FINISHED"
            db.commit()
            db.refresh(run)
            return run

        except Exception as e:
            # Audit trail: Record failed step and fail run safely
            duration_ms = int((time.time() - start_time) * 1000)
            run.status = "FAILED"
            run.error = str(e)
            run.failure_code = "ORCHESTRATION_ERROR"
            run.failure_summary = f"Supervisor pipeline interrupted: {str(e)}"
            run.latency_ms = duration_ms
            run.completed_at = get_utc_now()
            db.commit()
            db.refresh(run)
            return run

    def _start_step(
        self,
        db: Session,
        run_id: str,
        organization_id: str,
        index: int,
        step_type: str,
        input_data: Dict[str, Any],
    ) -> AgentStep:
        step = AgentStep(
            agent_run_id=run_id,
            organization_id=organization_id,
            step_index=index,
            step_type=step_type,
            status="RUNNING",
            input_data=input_data,
            output_data={},
            started_at=get_utc_now(),
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    def _complete_step(
        self,
        db: Session,
        step: AgentStep,
        output_data: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        step.status = "FAILED" if error else "COMPLETED"
        step.output_data = output_data
        step.error = error
        step.completed_at = get_utc_now()
        if step.started_at and step.completed_at:
            s_at = step.started_at.replace(tzinfo=None)
            c_at = step.completed_at.replace(tzinfo=None)
            delta = (c_at - s_at).total_seconds()
            step.duration_ms = max(0, int(delta * 1000))
        db.commit()
