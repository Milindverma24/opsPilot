import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import Task
from apps.api.app.models.base import get_utc_now, generate_uuid


class TaskService:
    @staticmethod
    def create_task(
        db: Session,
        organization_id: str,
        title: str,
        description: Optional[str] = None,
        task_type: str = "OPERATIONS",
        order_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        items_summary: Optional[List[Dict[str, Any]]] = None,
        priority: str = "NORMAL",
        status: str = "CREATED",
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        department_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        due_at: Optional[datetime] = None
    ) -> Task:
        task = Task(
            id=generate_uuid(),
            organization_id=organization_id,
            title=title,
            description=description,
            task_type=task_type,
            order_id=order_id,
            customer_name=customer_name,
            items_summary=items_summary or [],
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            created_by=created_by,
            department_id=department_id,
            team_id=team_id,
            workflow_id=workflow_id,
            due_at=due_at or (get_utc_now() + timedelta(hours=4))
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_by_id(db: Session, task_id: str, organization_id: str) -> Optional[Task]:
        return db.query(Task).filter(
            Task.id == task_id,
            Task.organization_id == organization_id
        ).first()

    @staticmethod
    def list_tasks(
        db: Session,
        organization_id: str,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        query = db.query(Task).filter(Task.organization_id == organization_id)
        if status:
            query = query.filter(Task.status == status.upper())
        if task_type:
            query = query.filter(Task.task_type == task_type.upper())
        if priority:
            query = query.filter(Task.priority == priority.upper())
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)
        if order_id:
            query = query.filter(Task.order_id == order_id)
        return query.order_by(Task.created_at.desc()).limit(limit).all()

    @staticmethod
    def assign_task(db: Session, task_id: str, organization_id: str, user_id: str) -> Optional[Task]:
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task:
            return None
        task.assigned_to = user_id
        task.status = "ASSIGNED"
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def claim_task(
        db: Session,
        task_id: str,
        organization_id: str,
        worker_id: str,
        lease_seconds: int = 300
    ) -> Optional[Task]:
        """Claims task and assigns lease expiration to detect worker crashes."""
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task or task.status in ["COMPLETED", "CANCELLED"]:
            return None

        token = f"lease-{uuid.uuid4().hex[:8]}"
        task.status = "CLAIMED"
        task.assigned_to = worker_id
        task.claimed_at = get_utc_now()
        task.lease_expires_at = get_utc_now() + timedelta(seconds=lease_seconds)
        task.lease_token = token
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def heartbeat(
        db: Session,
        task_id: str,
        organization_id: str,
        lease_token: str,
        extend_seconds: int = 300
    ) -> bool:
        """Worker heartbeat extending lease validity."""
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task or task.lease_token != lease_token:
            return False
        task.lease_expires_at = get_utc_now() + timedelta(seconds=extend_seconds)
        task.status = "IN_PROGRESS"
        db.commit()
        return True

    @staticmethod
    def complete_task(
        db: Session,
        task_id: str,
        organization_id: str,
        worker_id: Optional[str] = None,
        receipt: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task:
            return None
        task.status = "COMPLETED"
        task.completed_at = get_utc_now()
        task.lease_token = None
        task.lease_expires_at = None
        if receipt:
            task.execution_receipt = receipt
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def fail_task(
        db: Session,
        task_id: str,
        organization_id: str,
        error_message: str
    ) -> Optional[Task]:
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task:
            return None
        task.status = "FAILED"
        task.error_message = error_message
        task.lease_token = None
        task.lease_expires_at = None
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def escalate_task(
        db: Session,
        task_id: str,
        organization_id: str,
        reason: str
    ) -> Optional[Task]:
        task = TaskService.get_by_id(db, task_id, organization_id)
        if not task:
            return None
        task.status = "ESCALATED"
        task.priority = "CRITICAL"
        task.error_message = reason
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def recover_stale_leases(db: Session, organization_id: Optional[str] = None) -> List[Task]:
        """
        Discovers tasks whose workers crashed (lease expired while in CLAIMED or IN_PROGRESS).
        Safely resets them to CREATED for reassignment without duplicating mutations.
        """
        now = get_utc_now()
        query = db.query(Task).filter(
            Task.status.in_(["CLAIMED", "IN_PROGRESS"]),
            Task.lease_expires_at != None,
            Task.lease_expires_at <= now
        )
        if organization_id:
            query = query.filter(Task.organization_id == organization_id)

        stale_tasks = query.all()
        recovered = []
        for t in stale_tasks:
            t.status = "CREATED"
            t.assigned_to = None
            t.lease_token = None
            t.lease_expires_at = None
            t.retry_count = (t.retry_count or 0) + 1
            t.error_message = f"Worker lease expired at {now.isoformat()}. Auto-recovered."
            recovered.append(t)

        if recovered:
            db.commit()

        return recovered
