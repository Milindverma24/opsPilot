import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.operations import Task
from apps.api.app.services.task_service import TaskService
from apps.api.app.services.tenant_service import TenantService

router = APIRouter(prefix="/tasks", tags=["Employee Tasks"])


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    task_type: str = Field("OPERATIONS", description="PICK_AND_PACK, RESTOCK, CUSTOMER_OUTREACH, INVOICE_REVIEW")
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    items_summary: Optional[List[Dict[str, Any]]] = None
    priority: str = Field("NORMAL", description="LOW, NORMAL, HIGH, CRITICAL")
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None


class ClaimTaskRequest(BaseModel):
    lease_seconds: int = Field(300, ge=30, le=3600)


class CompleteTaskRequest(BaseModel):
    receipt: Optional[Dict[str, Any]] = None


class FailTaskRequest(BaseModel):
    error_message: str = Field(..., min_length=3)


class EscalateTaskRequest(BaseModel):
    reason: str = Field(..., min_length=3)


@router.get("")
def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    order_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List operational and warehouse tasks for the current organization."""
    tasks = TaskService.list_tasks(
        db=db,
        organization_id=current_user.organization_id,
        status=status,
        task_type=task_type,
        priority=priority,
        assigned_to=assigned_to,
        order_id=order_id,
        limit=limit
    )
    task_items = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "task_type": t.task_type,
            "order_id": t.order_id,
            "customer_name": t.customer_name,
            "items_summary": t.items_summary,
            "priority": t.priority,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "claimed_at": t.claimed_at.isoformat() if t.claimed_at else None,
            "lease_expires_at": t.lease_expires_at.isoformat() if t.lease_expires_at else None,
            "due_at": t.due_at.isoformat() if t.due_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "retry_count": t.retry_count,
            "error_message": t.error_message,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "payload": {
                "order_id": t.order_id,
                "customer_name": t.customer_name,
                "notes": t.description,
                "items": t.items_summary,
            }
        }
        for t in tasks
    ]
    return {
        "total": len(tasks),
        "data": task_items,
        "tasks": task_items,
    }


@router.post("/recover-stale-leases")
def recover_stale_leases_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recovers tasks whose worker lease has expired back into the pool."""
    recovered = TaskService.recover_stale_leases(db, organization_id=current_user.organization_id)
    return {
        "status": "success",
        "recovered_count": len(recovered),
        "recovered_task_ids": [t.id for t in recovered]
    }


@router.post("/seed-demo-queue")
def seed_demo_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Populates realistic warehouse fulfillment and QC tasks for testing and visual showcase."""
    demo_tasks = [
        {
            "title": "Pick & Pack Order UT-8921: Oversized Silk Bomber",
            "description": "Verify size M, Midnight Black. Include UrbanThread care label & wooden hanger.",
            "task_type": "PICK_AND_PACK",
            "order_id": "UT-8921",
            "customer_name": "Rahul Sharma",
            "items_summary": ["1x Oversized Silk Bomber Jacket (M, Midnight Black)"],
            "priority": "HIGH",
        },
        {
            "title": "Quality Inspection: Return RET-4029",
            "description": "Inspect returned Classic Denim Jacket for security tag tampering or wear.",
            "task_type": "RETURN_INSPECTION",
            "order_id": "UT-68293",
            "customer_name": "Pooja Verma",
            "items_summary": ["1x Classic Denim Jacket (L, Washed Indigo)"],
            "priority": "CRITICAL",
        },
        {
            "title": "Inventory Audit: Bin A-14 Restock Verification",
            "description": "Count remaining inventory for 50x Linen Henley Shirts received from Surat mill.",
            "task_type": "INVENTORY_COUNT",
            "order_id": "PO-9912",
            "customer_name": "Devon Stock AI",
            "items_summary": ["50x Linen Henley Shirt (M, Sage Green)"],
            "priority": "NORMAL",
        },
        {
            "title": "Priority Express Pack: Order UT-9942",
            "description": "Same-day courier dispatch via Delhivery Express Air.",
            "task_type": "PICK_AND_PACK",
            "order_id": "UT-9942",
            "customer_name": "Vikram Singhania",
            "items_summary": ["2x Raw Indigo Selvedge Jeans (32/32)"],
            "priority": "HIGH",
        },
        {
            "title": "QC Inspection: Supplier Batch B-104",
            "description": "Random sampling 10 units for GSM fabric weight & seam durability.",
            "task_type": "QC_INSPECTION",
            "order_id": "PO-1048",
            "customer_name": "Priya Purchasing AI",
            "items_summary": ["100x Organic Cotton Heavy Tee (Black/White)"],
            "priority": "NORMAL",
        }
    ]

    created = []
    for dt in demo_tasks:
        t = TaskService.create_task(
            db=db,
            organization_id=current_user.organization_id,
            title=dt["title"],
            description=dt["description"],
            task_type=dt["task_type"],
            order_id=dt["order_id"],
            customer_name=dt["customer_name"],
            items_summary=dt["items_summary"],
            priority=dt["priority"],
            status="CREATED",
            created_by=current_user.id
        )
        created.append(t.id)

    return {"status": "success", "seeded_count": len(created), "task_ids": created}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually dispatch or schedule a task."""
    task = TaskService.create_task(
        db=db,
        organization_id=current_user.organization_id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        order_id=payload.order_id,
        customer_name=payload.customer_name,
        items_summary=payload.items_summary,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
        department_id=payload.department_id
    )
    return {"status": "success", "task": {"id": task.id, "title": task.title, "status": task.status}}


@router.get("/{task_id}")
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed task information."""
    task = TaskService.get_by_id(db, task_id, current_user.organization_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "order_id": task.order_id,
        "customer_name": task.customer_name,
        "items_summary": task.items_summary,
        "priority": task.priority,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
        "lease_expires_at": task.lease_expires_at.isoformat() if task.lease_expires_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "retry_count": task.retry_count,
        "error_message": task.error_message,
        "execution_receipt": task.execution_receipt,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.post("/{task_id}/claim")
def claim_task(
    task_id: str,
    payload: ClaimTaskRequest = ClaimTaskRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Employee or background worker claims task with a time-limited lease."""
    task = TaskService.claim_task(
        db=db,
        task_id=task_id,
        organization_id=current_user.organization_id,
        worker_id=current_user.id,
        lease_seconds=payload.lease_seconds
    )
    if not task:
        raise HTTPException(status_code=400, detail="Task could not be claimed or is already completed")
    return {
        "status": "success",
        "task_id": task.id,
        "task_status": task.status,
        "lease_token": task.lease_token,
        "lease_expires_at": task.lease_expires_at.isoformat() if task.lease_expires_at else None
    }


@router.post("/{task_id}/complete")
def complete_task(
    task_id: str,
    payload: CompleteTaskRequest = CompleteTaskRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks task as completed with immutable execution receipt."""
    task = TaskService.complete_task(
        db=db,
        task_id=task_id,
        organization_id=current_user.organization_id,
        worker_id=current_user.id,
        receipt=payload.receipt
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "task_id": task.id, "task_status": task.status}


@router.post("/{task_id}/fail")
def fail_task(
    task_id: str,
    payload: FailTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks task as failed and records error message."""
    task = TaskService.fail_task(
        db=db,
        task_id=task_id,
        organization_id=current_user.organization_id,
        error_message=payload.error_message
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "task_id": task.id, "task_status": task.status}


@router.post("/{task_id}/escalate")
def escalate_task(
    task_id: str,
    payload: EscalateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Escalates task to management attention with critical priority."""
    task = TaskService.escalate_task(
        db=db,
        task_id=task_id,
        organization_id=current_user.organization_id,
        reason=payload.reason
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "task_id": task.id, "task_status": task.status}
