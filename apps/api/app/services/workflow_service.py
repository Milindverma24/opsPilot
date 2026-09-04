from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.workflow import Workflow, WorkflowStep
from apps.api.app.models.base import get_utc_now


class WorkflowService:
    @staticmethod
    def create_workflow(
        db: Session,
        organization_id: str,
        workflow_type: str,
        idempotency_key: str,
        business_event_id: Optional[str] = None,
        document_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        wf = Workflow(
            organization_id=organization_id,
            workflow_type=workflow_type,
            idempotency_key=idempotency_key,
            business_event_id=business_event_id,
            document_id=document_id,
            status="PENDING",
            input_data=input_data or {},
            output_data={},
            context=context or {},
            started_at=get_utc_now()
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        return wf

    @staticmethod
    def get_by_id(db: Session, workflow_id: str, organization_id: str) -> Optional[Workflow]:
        return db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == organization_id
        ).first()

    @staticmethod
    def list_workflows(db: Session, organization_id: str, limit: int = 100) -> List[Workflow]:
        return db.query(Workflow).filter(
            Workflow.organization_id == organization_id
        ).order_by(Workflow.started_at.desc()).limit(limit).all()

    @staticmethod
    def add_step(
        db: Session,
        workflow_id: str,
        step_type: str,
        step_order: int,
        status: str = "PENDING",
        agent_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowStep:
        step = WorkflowStep(
            workflow_id=workflow_id,
            step_type=step_type,
            step_order=step_order,
            status=status,
            agent_id=agent_id,
            input_data=input_data or {},
            output_data={},
            started_at=get_utc_now()
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step
