"""
Tool Registry & Execution REST API — Phase 8.

GET  /api/v1/tools                    — list tool registry
GET  /api/v1/tools/health             — tool health/circuit breaker status
GET  /api/v1/tools/{id}               — single tool definition
POST /api/v1/tools/{id}/enable        — admin enable tool
POST /api/v1/tools/{id}/disable       — admin disable tool
POST /api/v1/tools/test               — dry-run test (no mutations)
GET  /api/v1/tool-executions          — list executions (tenant-scoped)
GET  /api/v1/tool-executions/{id}     — single execution with receipt
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models.agent import Tool, ToolExecution
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_execution_service import ToolExecutionService

router = APIRouter(tags=["Tools"])

DEMO_ORG = "org-urbanthread-001"
DEMO_AGENT_RUN = "run-demo-001"
DEMO_PERMISSIONS = [
    "orders.read", "customers.read", "products.read", "inventory.read",
    "shipments.read", "returns.read", "refunds.read", "knowledge.read",
    "support.read", "vendors.read", "purchase_orders.read",
    "support.create", "support.update", "tasks.create",
    "returns.create", "returns.approve",
    "refunds.request", "refunds.approve", "refunds.execute",
    "orders.cancel", "orders.update",
    "inventory.reserve", "inventory.release",
    "communication.send", "communication.internal",
    "purchase_orders.create", "purchase_orders.submit",
]


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class ToolResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str] = None
    description: str
    category: str
    risk_level: str
    required_permission: str
    required_permissions: List[str]
    approval_mode: str
    handler_key: Optional[str] = None
    version: str
    timeout_seconds: int
    max_retries: int
    enabled: bool
    failure_count: int

    class Config:
        from_attributes = True


class ToolExecutionResponse(BaseModel):
    id: str
    tool_name: str
    tool_version: str
    status: str
    risk_level: Optional[str] = None
    approval_required: bool
    approval_id: Optional[str] = None
    execution_mode: str
    permission_granted: Optional[bool] = None
    policy_decision: Optional[str] = None
    block_reason: Optional[str] = None
    error_code: Optional[str] = None
    execution_receipt: Optional[Dict[str, Any]] = None
    duration_ms: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class DryRunRequest(BaseModel):
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = True
    organization_id: Optional[str] = None   # optional override for multi-tenant admin


class ExecuteToolRequest(BaseModel):
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    agent_run_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    approval_id: Optional[str] = None
    execution_mode: str = Field(default="LIVE_MOCK")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/tools", response_model=List[ToolResponse])
def list_tools(
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List all tools in the registry."""
    q = db.query(Tool)
    if category:
        q = q.filter(Tool.category == category.upper())
    if risk_level:
        q = q.filter(Tool.risk_level == risk_level.upper())
    if enabled is not None:
        q = q.filter(Tool.enabled == enabled)
    tools = q.order_by(Tool.category, Tool.name).all()
    return tools


@router.get("/tools/health")
def tools_health(db: Session = Depends(get_db)):
    """Circuit breaker and health status for all tools."""
    tools = db.query(Tool).all()
    return {
        "total_tools": len(tools),
        "enabled": sum(1 for t in tools if t.enabled),
        "disabled": sum(1 for t in tools if not t.enabled),
        "circuit_breaker_open": sum(1 for t in tools if (t.failure_count or 0) >= 5),
        "tools": [
            {
                "name": t.name,
                "enabled": t.enabled,
                "failure_count": t.failure_count or 0,
                "circuit_breaker_status": "OPEN" if (t.failure_count or 0) >= 5 else "CLOSED",
                "risk_level": t.risk_level,
            }
            for t in tools
        ],
    }


@router.get("/tools/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: str, db: Session = Depends(get_db)):
    """Get a single tool definition."""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        tool = db.query(Tool).filter(Tool.name == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.post("/tools/{tool_id}/enable")
def enable_tool(tool_id: str, db: Session = Depends(get_db)):
    """Admin: enable a disabled tool."""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool.enabled = True
    tool.failure_count = 0  # Reset circuit breaker
    db.commit()
    return {"tool_id": tool_id, "name": tool.name, "enabled": True}


@router.post("/tools/{tool_id}/disable")
def disable_tool(tool_id: str, db: Session = Depends(get_db)):
    """Admin: disable a tool."""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool.enabled = False
    db.commit()
    return {"tool_id": tool_id, "name": tool.name, "enabled": False}


@router.post("/tools/test")
def dry_run_test(req: DryRunRequest, db: Session = Depends(get_db)):
    """
    Dry-run a tool: validates all pipeline checks without executing.
    Returns detailed pre-flight report.
    Default: dry_run=True (never mutates data).
    """
    org_id = req.organization_id or DEMO_ORG

    ctx = ToolContext(
        organization_id=org_id,
        agent_run_id=DEMO_AGENT_RUN,
        permissions=tuple(DEMO_PERMISSIONS),
        execution_mode="DRY_RUN",
    )
    report = ToolExecutionService.dry_run(db=db, ctx=ctx, tool_name=req.tool, input_data=req.input)
    return report


@router.post("/tools/execute")
def execute_tool(req: ExecuteToolRequest, db: Session = Depends(get_db)):
    """
    Execute a tool through the full authorization pipeline.
    Uses LIVE_MOCK mode by default.
    """
    ctx = ToolContext(
        organization_id=DEMO_ORG,
        agent_run_id=req.agent_run_id or DEMO_AGENT_RUN,
        permissions=tuple(DEMO_PERMISSIONS),
        execution_mode=req.execution_mode,
    )
    result = ToolExecutionService.execute(
        db=db,
        ctx=ctx,
        tool_name=req.tool,
        input_data=req.input,
        idempotency_key=req.idempotency_key,
        approval_id=req.approval_id,
    )
    return result


# ---------------------------------------------------------------------------
# Execution History
# ---------------------------------------------------------------------------

@router.get("/tool-executions")
def list_tool_executions(
    tool_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    agent_run_id: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List tool executions for the current organization."""
    q = db.query(ToolExecution).filter(ToolExecution.organization_id == DEMO_ORG)
    if tool_name:
        q = q.filter(ToolExecution.tool_name == tool_name)
    if status:
        q = q.filter(ToolExecution.status == status.upper())
    if agent_run_id:
        q = q.filter(ToolExecution.agent_run_id == agent_run_id)
    executions = q.order_by(ToolExecution.started_at.desc()).limit(limit).all()
    return [
        {
            "execution_id": e.id,
            "tool_name": e.tool_name,
            "status": e.status,
            "risk_level": e.risk_level,
            "approval_required": e.approval_required,
            "execution_mode": e.execution_mode,
            "duration_ms": e.duration_ms,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "error_code": e.error_code,
        }
        for e in executions
    ]


@router.get("/tool-executions/{execution_id}")
def get_tool_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get a single tool execution with full receipt and timeline."""
    exc = db.query(ToolExecution).filter(
        ToolExecution.id == execution_id,
        ToolExecution.organization_id == DEMO_ORG,
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "execution_id": exc.id,
        "tool_name": exc.tool_name,
        "tool_version": exc.tool_version,
        "status": exc.status,
        "execution_mode": exc.execution_mode,
        "risk_level": exc.risk_level,
        "risk_score": exc.risk_score,
        "approval_required": exc.approval_required,
        "approval_id": exc.approval_id,
        "approval_hash": exc.approval_hash,
        "permission_granted": exc.permission_granted,
        "policy_decision": exc.policy_decision,
        "block_reason": exc.block_reason,
        "error_code": exc.error_code,
        "input_data": exc.input_data,
        "validated_input": exc.validated_input,
        "output_data": exc.output_data,
        "execution_receipt": exc.execution_receipt,
        "duration_ms": exc.duration_ms,
        "started_at": exc.started_at.isoformat() if exc.started_at else None,
        "completed_at": exc.completed_at.isoformat() if exc.completed_at else None,
    }
