from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.agent import Agent, AgentRun, AgentMessage
from apps.api.app.models.base import get_utc_now


class AgentService:
    @staticmethod
    def register_agent(
        db: Session,
        name: str,
        agent_type: str,
        system_prompt: str,
        description: Optional[str] = None,
        model: str = "gpt-4o",
        enabled: bool = True,
        organization_id: Optional[str] = None
    ) -> Agent:
        agent = Agent(
            name=name,
            agent_type=agent_type,
            system_prompt=system_prompt,
            description=description,
            model=model,
            enabled=enabled,
            organization_id=organization_id
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_by_type(db: Session, agent_type: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.agent_type == agent_type).first()

    @staticmethod
    def list_agents(db: Session, organization_id: Optional[str] = None) -> List[Agent]:
        q = db.query(Agent)
        if organization_id:
            q = q.filter((Agent.organization_id == organization_id) | (Agent.organization_id.is_(None)))
        return q.all()

    @staticmethod
    def record_run(
        db: Session,
        organization_id: str,
        agent_id: str,
        workflow_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "COMPLETED",
        confidence: Optional[float] = 1.0,
        token_usage: int = 0,
        estimated_cost: float = 0.0,
        latency_ms: int = 0,
        error: Optional[str] = None
    ) -> AgentRun:
        run = AgentRun(
            organization_id=organization_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            input_data=input_data or {},
            output_data=output_data or {},
            status=status,
            confidence=confidence,
            token_usage=token_usage,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
            started_at=get_utc_now(),
            completed_at=get_utc_now(),
            error=error
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def add_message(
        db: Session,
        agent_run_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        msg = AgentMessage(
            agent_run_id=agent_run_id,
            role=role,
            content=content,
            msg_metadata=metadata or {}
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
