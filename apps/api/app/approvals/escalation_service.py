"""
Human Escalation Engine — Phase 10.

Manages multi-tiered human incident escalation, SLA deadlines,
and automatic breach progression:
LEVEL_1 -> LEVEL_2 -> LEVEL_3 -> CRITICAL

Enforces deduplication so identical operational issues do not generate duplicate tickets.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import Escalation, WorkflowRun, Approval
from apps.api.app.models.tenant import User
from apps.api.app.models.audit import AuditLog, Notification


# Configurable SLA durations in minutes
SLA_DURATIONS_MINUTES = {
    "CRITICAL": 15,
    "HIGH": 60,
    "MEDIUM": 240,
    "LOW": 1440,
}

# Escalation progression hierarchy
NEXT_ESCALATION_LEVEL = {
    "LEVEL_1": "LEVEL_2",
    "LEVEL_2": "LEVEL_3",
    "LEVEL_3": "CRITICAL",
    "CRITICAL": "CRITICAL",  # Ceiling
}

# Default team routing by level
LEVEL_TO_TEAM_MAP = {
    "LEVEL_1": "SUPPORT",
    "LEVEL_2": "SUPPORT_MANAGEMENT",
    "LEVEL_3": "OPERATIONS",
    "CRITICAL": "EXECUTIVE_RESPONSE",
}


def compute_escalation_dedup_key(org_id: str, wf_run_id: Optional[str], reason: str, level: str) -> str:
    raw = f"{org_id}:{wf_run_id or 'none'}:{reason[:60]}:{level}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


class EscalationService:
    """Orchestrates incident escalation creation, assignment, SLA checks, and resolution."""

    @classmethod
    def create_escalation(
        cls,
        db: Session,
        organization_id: str,
        reason: str,
        level: str = "LEVEL_1",
        severity: str = "HIGH",
        workflow_run_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        assigned_team: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Escalation:
        """
        Creates an escalation record with SLA deadline and deduplication.
        """
        level_upper = level.upper()
        severity_upper = severity.upper()

        dedup_key = compute_escalation_dedup_key(organization_id, workflow_run_id, reason, level_upper)

        # 1. Deduplication check: return existing open escalation if duplicate
        existing = db.query(Escalation).filter(
            Escalation.organization_id == organization_id,
            Escalation.dedup_key == dedup_key,
            Escalation.status.in_(["OPEN", "ACKNOWLEDGED", "IN_PROGRESS"]),
        ).first()
        if existing:
            return existing

        # 2. Compute SLA due_at
        sla_mins = SLA_DURATIONS_MINUTES.get(severity_upper, 60)
        due_at = get_utc_now() + timedelta(minutes=sla_mins)

        team = assigned_team or LEVEL_TO_TEAM_MAP.get(level_upper, "OPERATIONS")

        esc = Escalation(
            organization_id=organization_id,
            workflow_run_id=workflow_run_id,
            agent_run_id=agent_run_id,
            approval_id=approval_id,
            level=level_upper,
            reason=reason,
            severity=severity_upper,
            status="OPEN",
            assigned_team=team,
            due_at=due_at,
            dedup_key=dedup_key,
            metadata_=metadata or {},
        )
        db.add(esc)
        db.commit()
        db.refresh(esc)

        # 3. Notification & Audit Log
        notif = Notification(
            organization_id=organization_id,
            title=f"Escalation [{level_upper} - {severity_upper}]: {team}",
            message=f"{reason}. SLA Deadline: {sla_mins}m",
            notification_type="DANGER" if severity_upper in ("HIGH", "CRITICAL") else "WARNING",
            link="/escalations",
        )
        db.add(notif)

        audit = AuditLog(
            organization_id=organization_id,
            actor_id="escalation-service",
            actor_type="SYSTEM",
            actor_name="OpsPilot Escalation Engine",
            action="ESCALATION_CREATED",
            resource_type="escalation",
            resource_id=esc.id,
            workflow_id=workflow_run_id,
            result="SUCCESS",
            payload={
                "level": level_upper,
                "severity": severity_upper,
                "reason": reason,
                "due_at": due_at.isoformat(),
            },
        )
        db.add(audit)
        db.commit()

        return esc

    @classmethod
    def acknowledge_escalation(
        cls,
        db: Session,
        escalation_id: str,
        user: User,
    ) -> Escalation:
        esc = db.query(Escalation).filter(
            Escalation.id == escalation_id,
            Escalation.organization_id == user.organization_id,
        ).first()
        if not esc:
            raise ValueError("Escalation not found")

        esc.status = "ACKNOWLEDGED"
        esc.assigned_to = user.id
        db.commit()

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="ESCALATION_ACKNOWLEDGED",
            resource_type="escalation",
            resource_id=esc.id,
            result="SUCCESS",
            payload={"assigned_to": user.id},
        )
        db.add(audit)
        db.commit()
        return esc

    @classmethod
    def resolve_escalation(
        cls,
        db: Session,
        escalation_id: str,
        user: User,
        resolution: str,
    ) -> Escalation:
        esc = db.query(Escalation).filter(
            Escalation.id == escalation_id,
            Escalation.organization_id == user.organization_id,
        ).first()
        if not esc:
            raise ValueError("Escalation not found")

        esc.status = "RESOLVED"
        esc.resolution = resolution
        esc.resolved_at = get_utc_now()
        esc.assigned_to = user.id
        db.commit()

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="ESCALATION_RESOLVED",
            resource_type="escalation",
            resource_id=esc.id,
            result="SUCCESS",
            payload={"resolution": resolution},
        )
        db.add(audit)
        db.commit()
        return esc

    @classmethod
    def escalate_next_level(
        cls,
        db: Session,
        escalation: Escalation,
        reason: Optional[str] = None,
    ) -> Escalation:
        """Promotes escalation to the next tier when SLA is breached or unresolved."""
        current_level = escalation.level
        next_level = NEXT_ESCALATION_LEVEL.get(current_level, "CRITICAL")

        if next_level == current_level and current_level == "CRITICAL":
            # Already at ceiling
            return escalation

        escalation.level = next_level
        escalation.assigned_team = LEVEL_TO_TEAM_MAP.get(next_level, "EXECUTIVE_RESPONSE")
        # Extend SLA for next tier
        sla_mins = SLA_DURATIONS_MINUTES.get(escalation.severity, 30)
        escalation.due_at = get_utc_now() + timedelta(minutes=sla_mins)
        db.commit()

        audit = AuditLog(
            organization_id=escalation.organization_id,
            actor_id="escalation-service",
            actor_type="SYSTEM",
            actor_name="OpsPilot Escalation Engine",
            action="ESCALATION_SLA_BREACHED",
            resource_type="escalation",
            resource_id=escalation.id,
            result="SUCCESS",
            payload={
                "previous_level": current_level,
                "promoted_level": next_level,
                "reason": reason or "SLA deadline exceeded",
            },
        )
        db.add(audit)
        db.commit()
        return escalation

    @classmethod
    def check_sla_breaches(cls, db: Session) -> int:
        """
        Scans for open escalations whose due_at has passed and advances them to next level.
        Returns count of breached escalations promoted.
        """
        now = get_utc_now()
        breached = db.query(Escalation).filter(
            Escalation.status.in_(["OPEN", "ACKNOWLEDGED", "IN_PROGRESS"]),
            Escalation.due_at != None,
            Escalation.due_at <= now,
        ).all()

        promoted_count = 0
        for esc in breached:
            cls.escalate_next_level(db, esc, reason="Automatic SLA breach promotion")
            promoted_count += 1

        return promoted_count
