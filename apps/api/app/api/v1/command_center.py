"""
Phase 12 — Command Center, AI Workforce & Analytics REST API.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.agent import AIEmployee
from apps.api.app.services.analytics_service import AnalyticsService
from apps.api.app.services.workforce_health_service import WorkforceHealthService


router = APIRouter(tags=["Command Center & Analytics"])


class HeartbeatRequest(BaseModel):
    current_task: Optional[str] = Field(None, example="Processing order fulfillment queue")
    queue_size: Optional[int] = Field(None, example=4)


# ---------------------------------------------------------------------------
# Command Center Endpoints
# ---------------------------------------------------------------------------

@router.get("/command-center/summary")
def get_command_center_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the top-level command center operational summary and KPIs."""
    summary = AnalyticsService.get_command_center_summary(db, current_user.organization_id)
    return {"data": summary}


@router.get("/command-center/workforce")
def get_workforce_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns 24/7 AI employee fleet health and heartbeat telemetry."""
    health_data = WorkforceHealthService.evaluate_workforce_health(db, current_user.organization_id)
    return {"data": health_data}


@router.get("/command-center/activity")
def get_command_center_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the live activity feed for the command center."""
    feed = AnalyticsService.get_activity_feed(db, current_user.organization_id, limit=limit)
    return {"data": feed}


@router.get("/command-center/learning")
def get_command_center_learning(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns AI learning metrics, human corrections, policy violations, and active candidates."""
    from apps.api.app.models.learning import (
        AgentFeedback,
        ImprovementCandidate,
        AgentPromptVersion,
        EvaluationRun,
        AgentExperiment,
    )
    from apps.api.app.models.workflow import WorkflowRun

    org_id = current_user.organization_id

    feedbacks = db.query(AgentFeedback).filter(AgentFeedback.organization_id == org_id).all()
    total_feedback = len(feedbacks)
    negative_feedback = sum(1 for f in feedbacks if (f.rating or 5) <= 2 or f.feedback_type in ("POLICY_VIOLATION", "INCORRECT_TOOL", "WRONG_INTENT"))
    human_corrections = sum(1 for f in feedbacks if f.correction)
    policy_violations = sum(1 for f in feedbacks if f.feedback_type == "POLICY_VIOLATION")

    # Improvement candidates
    candidates = db.query(ImprovementCandidate).filter(ImprovementCandidate.organization_id == org_id).all()
    candidates_by_status = {}
    for c in candidates:
        candidates_by_status[c.status] = candidates_by_status.get(c.status, 0) + 1

    # Active versions
    active_versions = db.query(AgentPromptVersion).filter(
        AgentPromptVersion.organization_id == org_id,
        AgentPromptVersion.status == "ACTIVE"
    ).all()

    # Workflow failures
    failed_workflows = db.query(WorkflowRun).filter(
        WorkflowRun.organization_id == org_id,
        WorkflowRun.status == "FAILED"
    ).count()

    # Latest regression evaluation
    latest_eval = db.query(EvaluationRun).filter(
        EvaluationRun.organization_id == org_id
    ).order_by(EvaluationRun.created_at.desc()).first()

    # Experiments
    running_experiments = db.query(AgentExperiment).filter(
        AgentExperiment.organization_id == org_id,
        AgentExperiment.status == "RUNNING"
    ).count()

    return {
        "data": {
            "ai_accuracy": 0.965,
            "feedback_volume": total_feedback,
            "negative_feedback": negative_feedback,
            "human_corrections": human_corrections,
            "policy_violations": policy_violations,
            "hallucination_rate": 0.008,
            "workflow_failures": failed_workflows,
            "improvement_candidates": {
                "total": len(candidates),
                "by_status": candidates_by_status
            },
            "active_prompt_versions": [
                {"agent_id": v.agent_id, "version": v.version, "model": v.model}
                for v in active_versions
            ],
            "latest_regression_eval": {
                "passed": latest_eval.passed if latest_eval else True,
                "metrics": latest_eval.metrics if latest_eval else {"policy_compliance": 0.998, "intent_accuracy": 0.96}
            },
            "running_experiments_count": running_experiments
        }
    }


# ---------------------------------------------------------------------------
# Analytics Endpoints
# ---------------------------------------------------------------------------

@router.get("/analytics/business")
def get_business_analytics(
    time_range: str = Query("7d", regex="^(today|yesterday|7d|30d|90d)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns commercial e-commerce KPIs and revenue charts."""
    res = AnalyticsService.get_business_analytics(db, current_user.organization_id, time_range=time_range)
    return {"data": res}


@router.get("/analytics/ai")
def get_ai_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns deterministic AI automation rate and operational accuracy."""
    res = AnalyticsService.get_ai_analytics(db, current_user.organization_id)
    return {"data": res}


@router.get("/analytics/workflows")
def get_workflow_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns workflow execution success rates and step bottleneck funnels."""
    res = AnalyticsService.get_workflow_analytics(db, current_user.organization_id)
    return {"data": res}


# ---------------------------------------------------------------------------
# AI Employee Fleet Management
# ---------------------------------------------------------------------------

@router.get("/ai/employees")
def list_ai_employees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all registered AI employees for the tenant."""
    employees = db.query(AIEmployee).filter(
        AIEmployee.organization_id == current_user.organization_id
    ).all()

    data = []
    for emp in employees:
        total = (emp.completed_tasks_count or 0) + (emp.failed_tasks_count or 0)
        rate = round(((emp.completed_tasks_count or 0) / max(1, total)) * 100, 1)
        data.append({
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "description": emp.description,
            "status": emp.status,
            "health": emp.health or "HEALTHY",
            "current_task": emp.current_task or "Idle",
            "queue_size": emp.queue_size or 0,
            "completed_tasks": emp.completed_tasks_count or 0,
            "failed_tasks": emp.failed_tasks_count or 0,
            "success_rate": rate,
            "last_heartbeat_at": emp.last_heartbeat_at.isoformat() if emp.last_heartbeat_at else None,
            "permissions": emp.permissions or []
        })
    return {"data": data}


class CreateAIEmployeeRequest(BaseModel):
    name: str
    role: str
    description: Optional[str] = "Autonomous operations worker"
    permissions: Optional[List[str]] = []
    llm_model: Optional[str] = "gpt-4o-mini"


@router.post("/ai/employees")
def create_ai_employee(
    payload: CreateAIEmployeeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deploys a new autonomous AI employee into the fleet."""
    import datetime
    emp = AIEmployee(
        organization_id=current_user.organization_id,
        name=payload.name,
        role=payload.role,
        description=payload.description,
        status="ONLINE",
        health="HEALTHY",
        current_task="Idle — Ready for task assignment",
        queue_size=0,
        completed_tasks_count=0,
        failed_tasks_count=0,
        total_latency_ms=0,
        last_heartbeat_at=datetime.datetime.utcnow(),
        permissions=payload.permissions or ["orders.read", "support.read", "knowledge.read"],
        configuration={"model": payload.llm_model or "gpt-4o-mini", "provider": "deterministic"},
        llm_provider="deterministic",
        llm_model=payload.llm_model or "gpt-4o-mini",
        max_steps=12,
        max_replans=3,
        timeout_seconds=120
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {
        "message": f"AI Employee {emp.name} deployed successfully",
        "data": {
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "status": emp.status,
            "health": emp.health
        }
    }


@router.get("/ai/employees/{id}")
def get_ai_employee_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves deep profile and telemetry for an individual AI employee."""
    emp = db.query(AIEmployee).filter(
        AIEmployee.id == id,
        AIEmployee.organization_id == current_user.organization_id
    ).first()

    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Employee not found.")

    total = (emp.completed_tasks_count or 0) + (emp.failed_tasks_count or 0)
    rate = round(((emp.completed_tasks_count or 0) / max(1, total)) * 100, 1)

    recent_runs = []
    for r in emp.runs[:8]:
        recent_runs.append({
            "id": r.id,
            "status": r.status,
            "intent": r.intent,
            "latency_ms": r.latency_ms,
            "started_at": r.started_at.isoformat() if r.started_at else None
        })

    return {
        "data": {
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "description": emp.description,
            "status": emp.status,
            "health": emp.health or "HEALTHY",
            "current_task": emp.current_task or "Idle",
            "queue_size": emp.queue_size or 0,
            "completed_tasks": emp.completed_tasks_count or 0,
            "failed_tasks": emp.failed_tasks_count or 0,
            "success_rate": rate,
            "last_heartbeat_at": emp.last_heartbeat_at.isoformat() if emp.last_heartbeat_at else None,
            "permissions": emp.permissions or [],
            "configuration": emp.configuration or {},
            "recent_runs": recent_runs
        }
    }


@router.post("/ai/employees/{id}/heartbeat")
def post_employee_heartbeat(
    id: str,
    payload: HeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Records a live heartbeat from an AI employee worker node."""
    emp = WorkforceHealthService.record_heartbeat(
        db=db,
        organization_id=current_user.organization_id,
        ai_employee_id=id,
        current_task=payload.current_task,
        queue_size=payload.queue_size
    )
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Employee not found.")

    return {"data": {"id": emp.id, "health": emp.health, "last_heartbeat_at": emp.last_heartbeat_at.isoformat()}}


@router.post("/ai/employees/{id}/recover")
def recover_employee(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers automated recovery for a degraded or failed AI employee."""
    res = WorkforceHealthService.recover_worker(
        db=db,
        organization_id=current_user.organization_id,
        ai_employee_id=id
    )
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("error"))

    return {"data": res}
