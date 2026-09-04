"""
Phase 13 — Feedback REST API.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user, get_current_user_optional
from apps.api.app.models.tenant import User
from apps.api.app.models.learning import AgentFeedback, CustomerMessageFeedback
from apps.api.app.services.ai.agent_learning_service import AgentLearningService


router = APIRouter(prefix="/feedback", tags=["AI Feedback"])


class AgentFeedbackRequest(BaseModel):
    agent_id: str = Field(..., example="aria-support-ai")
    feedback_type: str = Field(..., example="POLICY_VIOLATION")
    rating: int = Field(..., ge=1, le=5, example=2)
    correction: Optional[str] = Field(None, example="Return window is 30 days, not 14 days.")
    comment: Optional[str] = Field(None, example="AI quoted wrong policy window.")
    expected_behavior: Optional[str] = Field(None, example="Inform customer that returns are accepted within 30 days.")
    actual_behavior: Optional[str] = Field(None, example="AI stated return window was 14 days.")
    agent_run_id: Optional[str] = None
    workflow_run_id: Optional[str] = None


class CustomerFeedbackRequest(BaseModel):
    conversation_id: str = Field(..., example="conv-001")
    message_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, example=5)
    was_helpful: bool = Field(True, example=True)
    comment: Optional[str] = Field(None, example="Aria answered my sizing question accurately!")
    reason: Optional[str] = None


@router.post("/agent", status_code=status.HTTP_201_CREATED)
def submit_agent_feedback(
    payload: AgentFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits human staff review on an AI decision."""
    fb = AgentLearningService.record_human_feedback(
        db=db,
        organization_id=current_user.organization_id,
        agent_id=payload.agent_id,
        reviewer_user_id=current_user.id,
        feedback_type=payload.feedback_type,
        rating=payload.rating,
        correction=payload.correction,
        comment=payload.comment,
        expected_behavior=payload.expected_behavior,
        actual_behavior=payload.actual_behavior,
        agent_run_id=payload.agent_run_id,
        workflow_run_id=payload.workflow_run_id
    )
    return {
        "data": {
            "id": fb.id,
            "feedback_type": fb.feedback_type,
            "rating": fb.rating,
            "auto_generated_example": bool(payload.correction and payload.expected_behavior)
        }
    }


@router.post("/customer", status_code=status.HTTP_201_CREATED)
def submit_customer_feedback(
    payload: CustomerFeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Submits turn-by-turn customer chat feedback."""
    org_id = current_user.organization_id if current_user else "org-urbanthread-001"
    cust_id = current_user.id if current_user else None

    fb = AgentLearningService.record_customer_feedback(
        db=db,
        organization_id=org_id,
        conversation_id=payload.conversation_id,
        message_id=payload.message_id,
        customer_id=cust_id,
        rating=payload.rating,
        was_helpful=payload.was_helpful,
        comment=payload.comment,
        reason=payload.reason
    )
    return {"data": {"id": fb.id, "rating": fb.rating, "was_helpful": fb.was_helpful}}


@router.get("")
def list_feedback(
    agent_id: Optional[str] = None,
    feedback_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists human review feedback records."""
    query = db.query(AgentFeedback).filter(AgentFeedback.organization_id == current_user.organization_id)
    if agent_id:
        query = query.filter(AgentFeedback.agent_id == agent_id)
    if feedback_type:
        query = query.filter(AgentFeedback.feedback_type == feedback_type)

    feedbacks = query.order_by(AgentFeedback.created_at.desc()).all()
    return {
        "data": [
            {
                "id": f.id,
                "agent_id": f.agent_id,
                "reviewer_user_id": f.reviewer_user_id,
                "feedback_type": f.feedback_type,
                "rating": f.rating,
                "comment": f.comment,
                "correction": f.correction,
                "expected_behavior": f.expected_behavior,
                "actual_behavior": f.actual_behavior,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in feedbacks
        ]
    }
