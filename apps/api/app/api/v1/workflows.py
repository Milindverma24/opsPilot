"""
Workflows and Workflow Runs API Endpoints — Phase 9.

Endpoints:
- GET    /api/v1/workflows
- POST   /api/v1/workflows
- GET    /api/v1/workflows/{id}
- PATCH  /api/v1/workflows/{id}
- POST   /api/v1/workflows/{id}/enable
- POST   /api/v1/workflows/{id}/disable
- POST   /api/v1/workflows/{id}/test (PLAN_ONLY, DRY_RUN, LIVE_MOCK)
- GET    /api/v1/workflow-runs
- GET    /api/v1/workflow-runs/{id}
- POST   /api/v1/workflow-runs/{id}/pause
- POST   /api/v1/workflow-runs/{id}/resume
- POST   /api/v1/workflow-runs/{id}/cancel
- POST   /api/v1/workflow-runs/{id}/retry
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.workflow import Workflow, WorkflowStep, WorkflowRun, WorkflowStepRun
from apps.api.app.workflows.engine import WorkflowEngine
from apps.api.app.workflows.runner import WorkflowRunner
from apps.api.app.models.base import get_utc_now

router = APIRouter(tags=["Workflow Engine"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str
    trigger_type: str = "BUSINESS_EVENT"
    enabled: bool = True
    version: str = "v1"
    configuration: Dict[str, Any] = Field(default_factory=dict)
    max_concurrent_runs: int = 10
    timeout_seconds: int = 3600
    steps: Optional[List[Dict[str, Any]]] = None

    # Legacy trigger compatibility
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = "MANUAL_UPLOAD"
    idempotency_key: Optional[str] = None


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None
    max_concurrent_runs: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WorkflowTestRequest(BaseModel):
    execution_mode: str = "DRY_RUN"  # PLAN_ONLY, DRY_RUN, LIVE_MOCK
    payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Workflow Definitions
# ---------------------------------------------------------------------------

@router.get("/workflows")
def list_workflows(
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Workflow).filter(Workflow.organization_id == current_user.organization_id)
    if status:
        q = q.filter(Workflow.status == status)
    if workflow_type:
        q = q.filter(Workflow.workflow_type == workflow_type)
    if enabled is not None:
        q = q.filter(Workflow.enabled == enabled)

    wfs = q.order_by(Workflow.created_at.desc()).all()
    results = []
    for w in wfs:
        results.append({
            "id": w.id,
            "name": w.name or w.context.get("title", "Operational Workflow"),
            "description": w.description,
            "workflow_type": w.workflow_type,
            "trigger_type": w.trigger_type,
            "status": w.status,
            "enabled": w.enabled,
            "version": w.version,
            "configuration": w.configuration,
            "max_concurrent_runs": w.max_concurrent_runs,
            "timeout_seconds": w.timeout_seconds,
            "step_count": len(w.steps),
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "updated_at": w.updated_at.isoformat() if w.updated_at else None,
            # Legacy fields for backward compatibility
            "title": w.name or w.context.get("title", "Operational Workflow"),
            "idempotency_key": w.idempotency_key,
            "started_at": w.started_at.isoformat() if w.started_at else None,
            "completed_at": w.completed_at.isoformat() if w.completed_at else None,
        })

    return {"workflows": results, "total": len(results)}


@router.post("/workflows")
def create_or_trigger_workflow(
    payload: WorkflowCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Support legacy title/content trigger invocation
    if payload.content and not payload.steps:
        engine = WorkflowEngine(db)
        wf = engine.start_workflow(
            organization_id=current_user.organization_id,
            title=payload.title or payload.name,
            content=payload.content,
            source=payload.source or "MANUAL_UPLOAD",
            idempotency_key=payload.idempotency_key,
        )
        return {
            "id": wf.id,
            "workflow_type": wf.workflow_type,
            "status": wf.status,
            "context": wf.context,
            "error": wf.error,
        }

    # Standard Phase 9 workflow definition creation
    wf = Workflow(
        organization_id=current_user.organization_id,
        name=payload.name,
        description=payload.description,
        workflow_type=payload.workflow_type,
        trigger_type=payload.trigger_type,
        status="ACTIVE",
        enabled=payload.enabled,
        version=payload.version,
        configuration=payload.configuration,
        max_concurrent_runs=payload.max_concurrent_runs,
        timeout_seconds=payload.timeout_seconds,
        idempotency_key=payload.idempotency_key or f"wf-{payload.workflow_type.lower()}-{current_user.organization_id[:8]}",
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    # Optional initial steps creation
    if payload.steps:
        for idx, s in enumerate(payload.steps, start=1):
            step = WorkflowStep(
                workflow_id=wf.id,
                organization_id=current_user.organization_id,
                name=s.get("name", f"Step {idx}"),
                description=s.get("description"),
                step_order=s.get("step_order", idx),
                step_type=s.get("step_type", "CONTEXT_GATHER"),
                configuration=s.get("configuration", {}),
                timeout_seconds=s.get("timeout_seconds", 300),
                max_retries=s.get("max_retries", 3),
                retry_backoff_seconds=s.get("retry_backoff_seconds", 5),
                continue_on_failure=s.get("continue_on_failure", False),
            )
            db.add(step)
        db.commit()
        db.refresh(wf)

    return {
        "id": wf.id,
        "name": wf.name,
        "workflow_type": wf.workflow_type,
        "trigger_type": wf.trigger_type,
        "status": wf.status,
        "enabled": wf.enabled,
        "step_count": len(wf.steps),
    }


@router.get("/workflows/{workflow_id}")
def get_workflow_detail(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id,
    ).first()

    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    steps_data = []
    for s in sorted(wf.steps, key=lambda x: x.step_order):
        steps_data.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "step_type": s.step_type,
            "step_order": s.step_order,
            "configuration": s.configuration,
            "timeout_seconds": s.timeout_seconds,
            "max_retries": s.max_retries,
            "retry_backoff_seconds": s.retry_backoff_seconds,
            "continue_on_failure": s.continue_on_failure,
            # Legacy compatibility
            "status": s.status,
            "input": s.step_input,
            "output": s.step_output,
            "error": s.error,
        })

    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "workflow_type": wf.workflow_type,
        "trigger_type": wf.trigger_type,
        "status": wf.status,
        "enabled": wf.enabled,
        "version": wf.version,
        "configuration": wf.configuration,
        "max_concurrent_runs": wf.max_concurrent_runs,
        "timeout_seconds": wf.timeout_seconds,
        "steps": steps_data,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        # Legacy compatibility
        "idempotency_key": wf.idempotency_key,
        "context": wf.context,
        "error": wf.error,
        "started_at": wf.started_at.isoformat() if wf.started_at else None,
        "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
    }


@router.patch("/workflows/{workflow_id}")
def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if payload.name is not None:
        wf.name = payload.name
    if payload.description is not None:
        wf.description = payload.description
    if payload.enabled is not None:
        wf.enabled = payload.enabled
    if payload.configuration is not None:
        wf.configuration = payload.configuration
    if payload.max_concurrent_runs is not None:
        wf.max_concurrent_runs = payload.max_concurrent_runs
    if payload.timeout_seconds is not None:
        wf.timeout_seconds = payload.timeout_seconds

    db.commit()
    db.refresh(wf)
    return {"id": wf.id, "status": wf.status, "enabled": wf.enabled}


@router.post("/workflows/{workflow_id}/enable")
def enable_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    wf.enabled = True
    wf.status = "ACTIVE"
    db.commit()
    return {"id": wf.id, "enabled": True, "status": "ACTIVE"}


@router.post("/workflows/{workflow_id}/disable")
def disable_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    wf.enabled = False
    wf.status = "DISABLED"
    db.commit()
    return {"id": wf.id, "enabled": False, "status": "DISABLED"}


@router.post("/workflows/{workflow_id}/test")
def test_workflow(
    workflow_id: str,
    payload: WorkflowTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test endpoint supporting PLAN_ONLY, DRY_RUN, LIVE_MOCK modes. Default: DRY_RUN.
    """
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    mode = payload.execution_mode.upper()
    if mode not in ("PLAN_ONLY", "DRY_RUN", "LIVE_MOCK"):
        mode = "DRY_RUN"

    if mode == "PLAN_ONLY":
        return {
            "mode": "PLAN_ONLY",
            "workflow_id": wf.id,
            "workflow_type": wf.workflow_type,
            "planned_steps": [
                {"order": s.step_order, "type": s.step_type, "name": s.name}
                for s in sorted(wf.steps, key=lambda x: x.step_order)
            ],
            "input_payload": payload.payload,
            "message": "PLAN_ONLY mode: Execution plan generated without validation or mutation.",
        }

    # Create run and execute in DRY_RUN or LIVE_MOCK
    run = WorkflowRun(
        organization_id=current_user.organization_id,
        workflow_id=wf.id,
        status="RUNNING",
        current_step_order=1,
        input_data=payload.payload,
        context_data={"test_mode": mode, **payload.payload},
        started_at=get_utc_now(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    runner = WorkflowRunner(db)
    executed_run = runner.execute_run(run)

    return {
        "mode": mode,
        "run_id": executed_run.id,
        "status": executed_run.status,
        "completed_at": executed_run.completed_at.isoformat() if executed_run.completed_at else None,
        "execution_data": executed_run.execution_data,
        "error_data": executed_run.error_data,
    }


# ---------------------------------------------------------------------------
# Workflow Runs
# ---------------------------------------------------------------------------

@router.get("/workflow-runs")
def list_workflow_runs(
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WorkflowRun).filter(WorkflowRun.organization_id == current_user.organization_id)
    if status:
        q = q.filter(WorkflowRun.status == status)
    if workflow_id:
        q = q.filter(WorkflowRun.workflow_id == workflow_id)

    runs = q.order_by(WorkflowRun.started_at.desc()).limit(limit).all()
    results = []
    for r in runs:
        results.append({
            "id": r.id,
            "workflow_id": r.workflow_id,
            "workflow_name": r.workflow.name if r.workflow else "Workflow",
            "workflow_type": r.workflow.workflow_type if r.workflow else "UNKNOWN",
            "status": r.status,
            "current_step_order": r.current_step_order,
            "retry_count": r.retry_count,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "failed_at": r.failed_at.isoformat() if r.failed_at else None,
            "step_run_count": len(r.step_runs),
        })

    return {"workflow_runs": results, "total": len(results)}


@router.get("/workflow-runs/{run_id}")
def get_workflow_run_detail(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(WorkflowRun).filter(
        WorkflowRun.id == run_id,
        WorkflowRun.organization_id == current_user.organization_id,
    ).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    step_runs_data = []
    for sr in sorted(run.step_runs, key=lambda x: (x.workflow_step.step_order if x.workflow_step else 0, x.attempt_number)):
        step_runs_data.append({
            "id": sr.id,
            "step_id": sr.workflow_step_id,
            "step_name": sr.workflow_step.name if sr.workflow_step else "Step",
            "step_type": sr.workflow_step.step_type if sr.workflow_step else "UNKNOWN",
            "step_order": sr.workflow_step.step_order if sr.workflow_step else 0,
            "status": sr.status,
            "attempt_number": sr.attempt_number,
            "input_data": sr.input_data,
            "output_data": sr.output_data,
            "decision_data": sr.decision_data,
            "error_code": sr.error_code,
            "error_message": sr.error_message,
            "duration_ms": sr.duration_ms,
            "tool_execution_id": sr.tool_execution_id,
            "approval_id": sr.approval_id,
            "started_at": sr.started_at.isoformat() if sr.started_at else None,
            "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
        })

    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "workflow_name": run.workflow.name if run.workflow else "Workflow",
        "workflow_type": run.workflow.workflow_type if run.workflow else "UNKNOWN",
        "status": run.status,
        "current_step_order": run.current_step_order,
        "retry_count": run.retry_count,
        "input_data": run.input_data,
        "context_data": run.context_data,
        "decision_data": run.decision_data,
        "execution_data": run.execution_data,
        "error_data": run.error_data,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "paused_at": run.paused_at.isoformat() if run.paused_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "failed_at": run.failed_at.isoformat() if run.failed_at else None,
        "step_runs": step_runs_data,
    }


@router.post("/workflow-runs/{run_id}/pause")
def pause_workflow_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runner = WorkflowRunner(db)
    run = runner.pause_run(run_id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return {"id": run.id, "status": run.status}


@router.post("/workflow-runs/{run_id}/resume")
def resume_workflow_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runner = WorkflowRunner(db)
    run = runner.resume_run(run_id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return {"id": run.id, "status": run.status}


@router.post("/workflow-runs/{run_id}/cancel")
def cancel_workflow_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runner = WorkflowRunner(db)
    run = runner.cancel_run(run_id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return {"id": run.id, "status": run.status}


@router.post("/workflow-runs/{run_id}/retry")
def retry_workflow_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runner = WorkflowRunner(db)
    run = runner.retry_run(run_id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return {"id": run.id, "status": run.status}
