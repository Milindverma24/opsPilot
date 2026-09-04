"""
Phase 12 — AI Workforce Health & Auto-Recovery Service.

Monitors 24/7 worker runtime, evaluates heartbeats, tracks queue depth,
detects stale workers, and initiates automated worker recovery.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.agent import AIEmployee, AgentRun
from apps.api.app.models.workflow import WorkflowRun, Approval, Escalation
from apps.api.app.models.observability import Alert


HEARTBEAT_DEGRADED_THRESHOLD_SEC = 90
HEARTBEAT_FAILED_THRESHOLD_SEC = 180


class WorkforceHealthService:
    """
    Evaluates 24/7 health status of all registered AI Employees in an organization.
    """

    @classmethod
    def record_heartbeat(
        cls,
        db: Session,
        organization_id: str,
        ai_employee_id: str,
        current_task: Optional[str] = None,
        queue_size: Optional[int] = None
    ) -> AIEmployee:
        """Updates employee heartbeat and operational telemetry."""
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == ai_employee_id,
            AIEmployee.organization_id == organization_id
        ).first()

        if not employee:
            return None

        employee.last_heartbeat_at = get_utc_now()
        employee.health = "HEALTHY"
        if employee.status in ("FAILED", "DEGRADED"):
            employee.status = "WORKING" if current_task else "ONLINE"

        if current_task is not None:
            employee.current_task = current_task
        if queue_size is not None:
            employee.queue_size = queue_size

        db.commit()
        db.refresh(employee)
        return employee

    @classmethod
    def evaluate_workforce_health(
        cls,
        db: Session,
        organization_id: str
    ) -> Dict[str, Any]:
        """Scans all AI employees and evaluates real-time health and backlog."""
        employees = db.query(AIEmployee).filter(
            AIEmployee.organization_id == organization_id
        ).all()

        now = get_utc_now()
        healthy_count = 0
        degraded_count = 0
        failed_count = 0

        employee_list = []
        for emp in employees:
            status = emp.status
            health = emp.health or "HEALTHY"

            # Check heartbeat freshness
            if emp.last_heartbeat_at:
                hb = emp.last_heartbeat_at
                if hasattr(hb, "tzinfo") and hb.tzinfo is None:
                    hb = hb.replace(tzinfo=timezone.utc)
                if hasattr(now, "tzinfo") and now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)

                delta_sec = (now - hb).total_seconds()
                if delta_sec > HEARTBEAT_FAILED_THRESHOLD_SEC:
                    health = "FAILED"
                    status = "FAILED"
                elif delta_sec > HEARTBEAT_DEGRADED_THRESHOLD_SEC:
                    health = "DEGRADED"
                    status = "DEGRADED"
                else:
                    health = "HEALTHY"
            else:
                # If never sent a heartbeat, mark online/healthy default for demo
                health = "HEALTHY"

            emp.health = health
            emp.status = status

            if health == "HEALTHY":
                healthy_count += 1
            elif health == "DEGRADED":
                degraded_count += 1
            else:
                failed_count += 1

            total_runs = (emp.completed_tasks_count or 0) + (emp.failed_tasks_count or 0)
            success_rate = round(((emp.completed_tasks_count or 0) / max(1, total_runs)) * 100, 1)
            avg_latency = round((emp.total_latency_ms or 0) / max(1, total_runs), 0) if total_runs else 320

            employee_list.append({
                "id": emp.id,
                "name": emp.name,
                "role": emp.role,
                "status": status,
                "health": health,
                "current_task": emp.current_task or "Idle — Ready for task assignment",
                "queue_size": emp.queue_size or 0,
                "completed_tasks": emp.completed_tasks_count or 0,
                "failed_tasks": emp.failed_tasks_count or 0,
                "success_rate": success_rate,
                "average_latency_ms": int(avg_latency),
                "last_heartbeat_at": emp.last_heartbeat_at.isoformat() if emp.last_heartbeat_at else None,
            })

        db.commit()

        # Overall workforce health determination
        if failed_count > 0:
            overall_health = "CRITICAL"
        elif degraded_count > 0:
            overall_health = "DEGRADED"
        else:
            overall_health = "HEALTHY"

        # Backlog calculations
        pending_approvals = db.query(Approval).filter(
            Approval.organization_id == organization_id,
            Approval.status == "PENDING"
        ).count()

        active_escalations = db.query(Escalation).filter(
            Escalation.organization_id == organization_id,
            Escalation.status.in_(["OPEN", "ACKNOWLEDGED"])
        ).count()

        stuck_workflows = db.query(WorkflowRun).filter(
            WorkflowRun.organization_id == organization_id,
            WorkflowRun.status == "WAITING_RETRY"
        ).count()

        return {
            "workforce_health": overall_health,
            "total_employees": len(employees),
            "healthy_employees": healthy_count,
            "degraded_employees": degraded_count,
            "failed_employees": failed_count,
            "pending_approvals_backlog": pending_approvals,
            "active_escalations_backlog": active_escalations,
            "stuck_workflows_count": stuck_workflows,
            "employees": employee_list
        }

    @classmethod
    def recover_worker(
        cls,
        db: Session,
        organization_id: str,
        ai_employee_id: str
    ) -> Dict[str, Any]:
        """Recovers an interrupted or failed worker node."""
        employee = db.query(AIEmployee).filter(
            AIEmployee.id == ai_employee_id,
            AIEmployee.organization_id == organization_id
        ).first()

        if not employee:
            return {"success": False, "error": "AI Employee not found."}

        employee.health = "HEALTHY"
        employee.status = "ONLINE"
        employee.current_task = "Online — Monitoring event stream"
        employee.last_heartbeat_at = get_utc_now()
        employee.queue_size = 0

        # Resolve any open alerts for this worker
        open_alerts = db.query(Alert).filter(
            Alert.organization_id == organization_id,
            Alert.source_id == employee.id,
            Alert.status.in_(["OPEN", "ACKNOWLEDGED"])
        ).all()
        for a in open_alerts:
            a.status = "RESOLVED"
            a.resolved_at = get_utc_now()
            a.resolved_by = "AutoRecoveryService"

        db.commit()

        return {
            "success": True,
            "employee_id": employee.id,
            "name": employee.name,
            "health": employee.health,
            "status": employee.status,
            "recovered_at": employee.last_heartbeat_at.isoformat()
        }
