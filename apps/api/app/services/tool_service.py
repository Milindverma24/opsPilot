from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.agent import Tool, ToolExecution
from apps.api.app.models.base import get_utc_now


class ToolService:
    @staticmethod
    def register_tool(
        db: Session,
        name: str,
        description: str,
        required_permission: str,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        risk_level: str = "LOW",
        enabled: bool = True,
        organization_id: Optional[str] = None
    ) -> Tool:
        tool = Tool(
            name=name,
            description=description,
            required_permission=required_permission,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            risk_level=risk_level,
            enabled=enabled,
            organization_id=organization_id
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool

    @staticmethod
    def get_tool(db: Session, name: str) -> Optional[Tool]:
        return db.query(Tool).filter(Tool.name == name).first()

    @staticmethod
    def list_tools(db: Session, organization_id: Optional[str] = None) -> List[Tool]:
        q = db.query(Tool)
        if organization_id:
            q = q.filter((Tool.organization_id == organization_id) | (Tool.organization_id.is_(None)))
        return q.all()

    @staticmethod
    def record_execution(
        db: Session,
        organization_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str = "SUCCESS",
        tool_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        duration_ms: int = 0,
        error: Optional[str] = None,
        is_mock: bool = True
    ) -> ToolExecution:
        exec_record = ToolExecution(
            organization_id=organization_id,
            tool_id=tool_id,
            tool_name=tool_name,
            workflow_id=workflow_id,
            agent_run_id=agent_run_id,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error=error,
            duration_ms=duration_ms,
            is_mock=is_mock,
            started_at=get_utc_now(),
            completed_at=get_utc_now()
        )
        db.add(exec_record)
        db.commit()
        db.refresh(exec_record)
        return exec_record
