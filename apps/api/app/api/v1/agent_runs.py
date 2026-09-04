"""
Phase 7 — AI Agent Runs & Employee REST API.

Provides endpoints for creating, inspecting, testing, and managing AI employee runs.
Strict tenant isolation enforced on every request.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.agent import AIEmployee, AgentRun, AgentStep
from apps.api.app.schemas.agent_schemas import AgentRequest
from apps.api.app.agents.supervisor import AgentSupervisor

router = APIRouter(prefix="/agents", tags=["AI Employee & Runs"])


class TestRequest(BaseModel):
    message: str
    channel: str = "WEB_CHAT"
    actor_id: Optional[str] = None
    trigger_type: str = "MANUAL_TRIGGER"


class UpdateEmployeeRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    confidence_threshold_auto: Optional[float] = None
    confidence_threshold_review: Optional[float] = None
    max_steps: Optional[int] = None
    permissions: Optional[List[str]] = None


def _format_run(run: AgentRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "organization_id": run.organization_id,
        "ai_employee_id": run.ai_employee_id,
        "status": run.status,
        "current_step": run.current_step,
        "trigger_type": run.trigger_type,
        "actor_type": run.actor_type,
        "actor_id": run.actor_id,
        "intent": run.intent,
        "intent_confidence": run.intent_confidence,
        "risk_level": run.risk_level,
        "risk_score": run.risk_score,
        "confidence": run.confidence,
        "decision_summary": run.decision_summary,
        "reason_codes": run.reason_codes,
        "evidence_ids": run.evidence_ids,
        "requires_human_approval": run.requires_human_approval,
        "planned_actions": run.planned_actions,
        "decisions": run.decisions,
        "extracted_data": run.extracted_data,
        "context_data": run.context_data,
        "input_data": run.input_data,
        "latency_ms": run.latency_ms,
        "total_steps": run.total_steps,
        "model_used": run.model_used,
        "error": run.error,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


# ---------------------------------------------------------------------------
# AI Employee Persona Endpoints
# ---------------------------------------------------------------------------

@router.get("/employee")
def get_ai_employee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(AIEmployee).filter(
        AIEmployee.organization_id == current_user.organization_id
    ).first()

    if not employee:
        # Auto-create default persona if missing
        employee = AIEmployee(
            organization_id=current_user.organization_id,
            name="UrbanThread Operations AI",
            role="AI_OPERATIONS_EMPLOYEE",
            description="Autonomous business operations AI for customer orders, shipping, and store operations.",
            status="ACTIVE",
            permissions=[
                "orders.read", "orders.cancel", "products.read", "shipments.read",
                "inventory.read", "refunds.read", "communications.write"
            ],
            configuration={"provider": "deterministic", "model": "gpt-4o-mini"},
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

    # Calculate run stats
    total_runs = db.query(AgentRun).filter(AgentRun.organization_id == current_user.organization_id).count()
    completed_runs = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.status == "COMPLETED"
    ).count()
    waiting_approval = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.status == "WAITING_FOR_APPROVAL"
    ).count()

    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "description": employee.description,
        "status": employee.status,
        "permissions": employee.permissions,
        "llm_provider": employee.llm_provider,
        "llm_model": employee.llm_model,
        "confidence_threshold_auto": employee.confidence_threshold_auto,
        "confidence_threshold_review": employee.confidence_threshold_review,
        "max_steps": employee.max_steps,
        "stats": {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "waiting_approval": waiting_approval,
            "success_rate": round((completed_runs / total_runs * 100), 1) if total_runs > 0 else 100.0,
        }
    }


@router.put("/employee")
def update_ai_employee(
    payload: UpdateEmployeeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(AIEmployee).filter(
        AIEmployee.organization_id == current_user.organization_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="AI Employee persona not found")

    if payload.name is not None:
        employee.name = payload.name
    if payload.role is not None:
        employee.role = payload.role
    if payload.description is not None:
        employee.description = payload.description
    if payload.status is not None:
        employee.status = payload.status
    if payload.confidence_threshold_auto is not None:
        employee.confidence_threshold_auto = payload.confidence_threshold_auto
    if payload.confidence_threshold_review is not None:
        employee.confidence_threshold_review = payload.confidence_threshold_review
    if payload.max_steps is not None:
        employee.max_steps = payload.max_steps
    if payload.permissions is not None:
        employee.permissions = payload.permissions

    db.commit()
    db.refresh(employee)
    return {"status": "SUCCESS", "employee": employee.name, "id": employee.id}


# ---------------------------------------------------------------------------
# Runs Endpoints
# ---------------------------------------------------------------------------

@router.post("/runs", status_code=status.HTTP_201_CREATED)
def create_agent_run(
    payload: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supervisor = AgentSupervisor()
    idempotency_key = payload.metadata.get("idempotency_key") if payload.metadata else None
    run = supervisor.process_request(
        db=db,
        organization_id=current_user.organization_id,
        request=payload,
        idempotency_key=idempotency_key,
    )
    return {"status": "SUCCESS", "run": _format_run(run)}


@router.get("/runs")
def list_agent_runs(
    status: Optional[str] = None,
    intent: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AgentRun).filter(AgentRun.organization_id == current_user.organization_id)
    if status:
        query = query.filter(AgentRun.status == status.upper())
    if intent:
        query = query.filter(AgentRun.intent == intent.upper())
    if risk_level:
        query = query.filter(AgentRun.risk_level == risk_level.upper())

    total = query.count()
    runs = query.order_by(AgentRun.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "runs": [_format_run(r) for r in runs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs/{run_id}")
def get_agent_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.id == run_id,
    ).first()

    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    steps = db.query(AgentStep).filter(
        AgentStep.organization_id == current_user.organization_id,
        AgentStep.agent_run_id == run.id,
    ).order_by(AgentStep.step_index.asc()).all()

    formatted = _format_run(run)
    formatted["steps"] = [
        {
            "id": s.id,
            "step_index": s.step_index,
            "step_type": s.step_type,
            "status": s.status,
            "input_data": s.input_data,
            "output_data": s.output_data,
            "duration_ms": s.duration_ms,
            "error": s.error,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in steps
    ]
    return formatted


@router.post("/runs/{run_id}/cancel")
def cancel_agent_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.id == run_id,
    ).first()

    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    if run.status in ("COMPLETED", "FAILED", "CANCELLED", "BLOCKED"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel run in status {run.status}")

    run.status = "CANCELLED"
    db.commit()
    return {"status": "SUCCESS", "message": f"Run {run_id} cancelled"}


@router.get("/runs/{run_id}/steps")
def get_run_steps(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.id == run_id,
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    steps = db.query(AgentStep).filter(
        AgentStep.organization_id == current_user.organization_id,
        AgentStep.agent_run_id == run.id,
    ).order_by(AgentStep.step_index.asc()).all()

    return {
        "run_id": run.id,
        "total_steps": len(steps),
        "steps": [
            {
                "step_index": s.step_index,
                "step_type": s.step_type,
                "status": s.status,
                "input_data": s.input_data,
                "output_data": s.output_data,
                "duration_ms": s.duration_ms,
            }
            for s in steps
        ],
    }


@router.get("/runs/{run_id}/plan")
def get_run_plan(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.id == run_id,
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    return {
        "run_id": run.id,
        "planned_actions": run.planned_actions,
        "risk_level": run.risk_level,
        "risk_score": run.risk_score,
        "requires_human_approval": run.requires_human_approval,
        "execution_mode": "PLAN_ONLY",
    }


@router.get("/runs/{run_id}/decision")
def get_run_decision(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(AgentRun).filter(
        AgentRun.organization_id == current_user.organization_id,
        AgentRun.id == run_id,
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    return {
        "run_id": run.id,
        "decision_summary": run.decision_summary,
        "reason_codes": run.reason_codes,
        "evidence_ids": run.evidence_ids,
        "confidence": run.confidence,
        "decisions": run.decisions,
    }


# ---------------------------------------------------------------------------
# Safe Test Lab Endpoint
# ---------------------------------------------------------------------------

@router.post("/test")
def test_agent_cognition(
    payload: TestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes a safe PLAN_ONLY simulation run for evaluation and testing.
    Zero side-effects, full audit trail.
    """
    supervisor = AgentSupervisor()
    agent_req = AgentRequest(
        message=payload.message,
        channel=payload.channel,
        actor_type="USER",
        actor_id=payload.actor_id,
        trigger_type=payload.trigger_type,
    )
    run = supervisor.process_request(
        db=db,
        organization_id=current_user.organization_id,
        request=agent_req,
    )
    return {
        "status": "SUCCESS",
        "run_id": run.id,
        "intent": run.intent,
        "intent_confidence": run.intent_confidence,
        "risk_level": run.risk_level,
        "risk_score": run.risk_score,
        "requires_human_approval": run.requires_human_approval,
        "decision_summary": run.decision_summary,
        "reason_codes": run.reason_codes,
        "proposed_response": run.decisions[0].get("proposed_response") if run.decisions else None,
        "planned_actions": run.planned_actions,
        "total_steps": run.total_steps,
        "latency_ms": run.latency_ms,
    }
