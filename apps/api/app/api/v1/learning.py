"""
Phase 13 — Learning, Improvements, Evaluations & Experiments REST API.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.learning import (
    LearningExample,
    ImprovementCandidate,
    AgentPromptVersion,
    EvaluationRun,
    AgentExperiment,
)
from apps.api.app.services.ai.agent_learning_service import AgentLearningService
from apps.api.app.services.ai.agent_evaluation_service import AgentEvaluationService
from apps.api.app.models.base import get_utc_now


router = APIRouter(tags=["AI Learning & Improvements"])


# ---------------------------------------------------------------------------
# Learning Examples & Dataset Export
# ---------------------------------------------------------------------------

class CreateLearningExampleRequest(BaseModel):
    category: str = Field(..., example="INTENT_CLASSIFICATION")
    input: str = Field(..., example="Can I exchange my shirt for a smaller size?")
    expected_output: str = Field(..., example="Yes, UrbanThread allows size exchanges within 30 days.")
    actual_output: Optional[str] = None
    correction: Optional[str] = None
    source_type: str = Field("MANUAL_EXAMPLE", example="MANUAL_EXAMPLE")
    dataset_version: str = Field("v1.0", example="v1.0")


@router.get("/learning/examples")
def list_learning_examples(
    category: Optional[str] = None,
    approved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists curated dataset training examples."""
    query = db.query(LearningExample).filter(LearningExample.organization_id == current_user.organization_id)
    if category:
        query = query.filter(LearningExample.category == category)
    if approved is not None:
        query = query.filter(LearningExample.approved == approved)

    examples = query.order_by(LearningExample.created_at.desc()).all()
    return {
        "data": [
            {
                "id": ex.id,
                "category": ex.category,
                "source_type": ex.source_type,
                "input": ex.input,
                "expected_output": ex.expected_output,
                "actual_output": ex.actual_output,
                "correction": ex.correction,
                "approved": ex.approved,
                "quality_score": ex.quality_score,
                "dataset_version": ex.dataset_version,
                "created_at": ex.created_at.isoformat() if ex.created_at else None
            }
            for ex in examples
        ]
    }


@router.post("/learning/examples", status_code=status.HTTP_201_CREATED)
def create_learning_example(
    payload: CreateLearningExampleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds a new learning example to the dataset."""
    ex = LearningExample(
        organization_id=current_user.organization_id,
        category=payload.category,
        input=payload.input,
        expected_output=payload.expected_output,
        actual_output=payload.actual_output,
        correction=payload.correction,
        source_type=payload.source_type,
        approved=True,
        reviewer_id=current_user.id,
        dataset_version=payload.dataset_version
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return {"data": {"id": ex.id, "approved": ex.approved}}


@router.get("/learning/export")
def export_dataset_jsonl(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exports approved learning examples formatted as standard fine-tuning JSONL."""
    jsonl_content = AgentLearningService.export_finetuning_dataset_jsonl(
        db=db,
        organization_id=current_user.organization_id,
        category=category,
        only_approved=True
    )
    return Response(
        content=jsonl_content,
        media_type="application/x-jsonlines",
        headers={"Content-Disposition": "attachment; filename=urbanthread_finetuning.jsonl"}
    )


# ---------------------------------------------------------------------------
# Improvement Candidates System
# ---------------------------------------------------------------------------

class CreateCandidateRequest(BaseModel):
    agent_id: str = Field(..., example="aria-support-ai")
    candidate_type: str = Field(..., example="PROMPT_IMPROVEMENT")
    title: str = Field(..., example="Enforce 30-Day Return Window Clarification")
    description: str = Field(..., example="Customer feedback identified ambiguity in return policy timing.")
    proposed_change: Dict[str, Any] = Field(..., example={"behavior_rules": ["Explicitly clarify 30 days from delivery date"]})
    expected_impact: Optional[str] = Field("Prevents customer confusion on return deadlines")
    risk: str = Field("LOW", example="LOW")


@router.get("/improvements")
def list_improvement_candidates(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists improvement candidate proposals."""
    query = db.query(ImprovementCandidate).filter(
        ImprovementCandidate.organization_id == current_user.organization_id
    )
    if status:
        query = query.filter(ImprovementCandidate.status == status.upper())
    if agent_id:
        query = query.filter(ImprovementCandidate.agent_id == agent_id)

    candidates = query.order_by(ImprovementCandidate.created_at.desc()).all()
    return {
        "data": [
            {
                "id": c.id,
                "agent_id": c.agent_id,
                "candidate_type": c.candidate_type,
                "title": c.title,
                "description": c.description,
                "proposed_change": c.proposed_change,
                "expected_impact": c.expected_impact,
                "risk": c.risk,
                "status": c.status,
                "created_by": c.created_by,
                "reviewed_by": c.reviewed_by,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "deployed_at": c.deployed_at.isoformat() if c.deployed_at else None
            }
            for c in candidates
        ]
    }


@router.post("/improvements", status_code=status.HTTP_201_CREATED)
def create_improvement_candidate(
    payload: CreateCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new improvement candidate proposal."""
    cand = AgentLearningService.generate_candidate(
        db=db,
        organization_id=current_user.organization_id,
        agent_id=payload.agent_id,
        candidate_type=payload.candidate_type,
        title=payload.title,
        description=payload.description,
        proposed_change=payload.proposed_change,
        expected_impact=payload.expected_impact,
        risk=payload.risk,
        created_by=current_user.id
    )
    return {"data": {"id": cand.id, "status": cand.status, "title": cand.title}}


@router.post("/improvements/{id}/approve")
def approve_candidate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Human operations manager approves an improvement candidate."""
    try:
        cand = AgentLearningService.approve_candidate(
            db=db,
            organization_id=current_user.organization_id,
            candidate_id=id,
            reviewer_id=current_user.id
        )
        return {"data": {"id": cand.id, "status": cand.status}}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/improvements/{id}/reject")
def reject_candidate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejects an improvement candidate."""
    try:
        cand = AgentLearningService.reject_candidate(
            db=db,
            organization_id=current_user.organization_id,
            candidate_id=id,
            reviewer_id=current_user.id
        )
        return {"data": {"id": cand.id, "status": cand.status}}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/improvements/{id}/deploy")
def deploy_candidate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Promotes an approved improvement candidate into an active production version."""
    try:
        new_v = AgentLearningService.deploy_candidate(
            db=db,
            organization_id=current_user.organization_id,
            candidate_id=id,
            deployed_by=current_user.id
        )
        return {"data": {"version": new_v.version, "status": new_v.status, "agent_id": new_v.agent_id}}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/improvements/{id}/rollback")
def rollback_candidate(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rolls back a deployed candidate to the previous active version."""
    try:
        restored = AgentLearningService.rollback_candidate(
            db=db,
            organization_id=current_user.organization_id,
            candidate_id=id,
            actor_id=current_user.id
        )
        return {"data": {"restored_version": restored.version, "status": restored.status}}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Evaluation & Regression Testing
# ---------------------------------------------------------------------------

class RunEvaluationRequest(BaseModel):
    agent_id: str = Field(..., example="aria-support-ai")
    version_id: Optional[str] = None
    dataset_version: str = Field("v1.0", example="v1.0")


@router.get("/evaluations")
def list_evaluations(
    agent_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists regression benchmark evaluations."""
    query = db.query(EvaluationRun).filter(EvaluationRun.organization_id == current_user.organization_id)
    if agent_id:
        query = query.filter(EvaluationRun.agent_id == agent_id)

    evals = query.order_by(EvaluationRun.created_at.desc()).limit(20).all()
    return {
        "data": [
            {
                "id": ev.id,
                "agent_id": ev.agent_id,
                "version_id": ev.version_id,
                "dataset_version": ev.dataset_version,
                "metrics": ev.metrics,
                "passed": ev.passed,
                "failure_reasons": ev.failure_reasons,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in evals
        ]
    }


@router.post("/evaluations/run")
def run_evaluation(
    payload: RunEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes regression evaluation against benchmark dataset."""
    ev = AgentEvaluationService.run_regression_evaluation(
        db=db,
        organization_id=current_user.organization_id,
        agent_id=payload.agent_id,
        version_id=payload.version_id,
        dataset_version=payload.dataset_version
    )
    return {
        "data": {
            "id": ev.id,
            "passed": ev.passed,
            "metrics": ev.metrics,
            "failure_reasons": ev.failure_reasons
        }
    }


# ---------------------------------------------------------------------------
# A/B Experiments
# ---------------------------------------------------------------------------

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., example="Test Sizing Few-Shot Prompt v1.2")
    agent_id: str = Field(..., example="aria-support-ai")
    baseline_version: str = Field("v1.0", example="v1.0")
    candidate_version: str = Field("v1.2", example="v1.2")
    traffic_percentage: float = Field(10.0, ge=1.0, le=50.0, example=10.0)


@router.get("/experiments")
def list_experiments(
    agent_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists A/B testing experiments."""
    query = db.query(AgentExperiment).filter(AgentExperiment.organization_id == current_user.organization_id)
    if agent_id:
        query = query.filter(AgentExperiment.agent_id == agent_id)

    experiments = query.order_by(AgentExperiment.created_at.desc()).all()
    return {
        "data": [
            {
                "id": ex.id,
                "name": ex.name,
                "agent_id": ex.agent_id,
                "baseline_version": ex.baseline_version,
                "candidate_version": ex.candidate_version,
                "traffic_percentage": ex.traffic_percentage,
                "metrics": ex.metrics,
                "status": ex.status,
                "start_at": ex.start_at.isoformat() if ex.start_at else None
            }
            for ex in experiments
        ]
    }


@router.post("/experiments", status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: CreateExperimentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new A/B experiment routing a fraction of traffic to candidate."""
    exp = AgentEvaluationService.create_experiment(
        db=db,
        organization_id=current_user.organization_id,
        name=payload.name,
        agent_id=payload.agent_id,
        baseline_version=payload.baseline_version,
        candidate_version=payload.candidate_version,
        traffic_percentage=payload.traffic_percentage
    )
    return {"data": {"id": exp.id, "name": exp.name, "status": exp.status}}


# ---------------------------------------------------------------------------
# Agent Prompt Versions
# ---------------------------------------------------------------------------

@router.get("/agents/{id}/versions")
def list_agent_versions(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists version history for a specific AI agent."""
    versions = db.query(AgentPromptVersion).filter(
        AgentPromptVersion.organization_id == current_user.organization_id,
        AgentPromptVersion.agent_id == id
    ).order_by(AgentPromptVersion.created_at.desc()).all()

    # Fallback to initial version if empty
    if not versions:
        initial = AgentPromptVersion(
            organization_id=current_user.organization_id,
            agent_id=id,
            version="v1.0",
            system_prompt="You are Aria, an autonomous customer operations AI employee for UrbanThread.",
            behavior_rules=["Enforce 30-day return window", "Never execute unverified refunds"],
            output_schema={"type": "object"},
            model="gpt-4o-mini",
            status="ACTIVE",
            created_by=current_user.id,
            activated_at=get_utc_now()
        )
        db.add(initial)
        db.commit()
        db.refresh(initial)
        versions = [initial]

    return {
        "data": [
            {
                "id": v.id,
                "version": v.version,
                "system_prompt": v.system_prompt,
                "behavior_rules": v.behavior_rules,
                "model": v.model,
                "temperature": v.temperature,
                "status": v.status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "activated_at": v.activated_at.isoformat() if v.activated_at else None
            }
            for v in versions
        ]
    }


class CreateAgentVersionRequest(BaseModel):
    version: str = Field(..., example="v1.2")
    system_prompt: str = Field(..., example="You are Aria, an autonomous customer operations AI employee.")
    behavior_rules: Optional[List[str]] = Field(default_factory=list)
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.1
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None


@router.post("/agents/{id}/versions", status_code=status.HTTP_201_CREATED)
def create_agent_version(
    id: str,
    payload: CreateAgentVersionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new draft prompt & configuration version for an agent."""
    ver = AgentPromptVersion(
        organization_id=current_user.organization_id,
        agent_id=id,
        version=payload.version,
        system_prompt=payload.system_prompt,
        behavior_rules=payload.behavior_rules or [],
        model=payload.model or "gpt-4o-mini",
        temperature=payload.temperature if payload.temperature is not None else 0.1,
        output_schema=payload.output_schema or {},
        configuration=payload.configuration or {},
        status="DRAFT",
        created_by=current_user.id
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)
    return {"data": {"id": ver.id, "version": ver.version, "status": ver.status}}


@router.post("/agents/{id}/versions/{version}/test")
def test_agent_version(
    id: str,
    version: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes regression benchmark suite against a target version."""
    ev = AgentEvaluationService.run_regression_evaluation(
        db=db,
        organization_id=current_user.organization_id,
        agent_id=id,
        version_id=version
    )
    return {
        "data": {
            "version": version,
            "passed": ev.passed,
            "metrics": ev.metrics,
            "failure_reasons": ev.failure_reasons
        }
    }


@router.post("/agents/{id}/versions/{version}/activate")
def activate_agent_version(
    id: str,
    version: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Promotes an approved version to ACTIVE and retires predecessor."""
    target_ver = db.query(AgentPromptVersion).filter(
        AgentPromptVersion.organization_id == current_user.organization_id,
        AgentPromptVersion.agent_id == id,
        AgentPromptVersion.version == version
    ).first()

    if not target_ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version '{version}' not found for agent '{id}'.")

    # Retire current active
    db.query(AgentPromptVersion).filter(
        AgentPromptVersion.organization_id == current_user.organization_id,
        AgentPromptVersion.agent_id == id,
        AgentPromptVersion.status == "ACTIVE"
    ).update({"status": "RETIRED"})

    target_ver.status = "ACTIVE"
    target_ver.approved_by = current_user.id
    target_ver.activated_at = get_utc_now()
    db.commit()
    db.refresh(target_ver)

    return {"data": {"agent_id": id, "version": target_ver.version, "status": target_ver.status}}
