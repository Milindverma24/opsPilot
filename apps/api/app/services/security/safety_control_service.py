"""
Phase 14 — Safety Control & Emergency Kill Switch Service.
Provides centralized server-side controls to immediately halt AI operations,
disable individual agents/tools/workflows, and enforce risk boundaries.
"""
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from apps.api.app.models.security import SystemSafetyControl, SecurityEvent
from apps.api.app.models.base import get_utc_now


class SafetyControlService:
    """
    Authoritative server-side safety control gate.
    """

    @classmethod
    def get_or_create_controls(cls, db: Session, organization_id: str) -> SystemSafetyControl:
        ctrl = db.query(SystemSafetyControl).filter(
            SystemSafetyControl.organization_id == organization_id
        ).first()

        if not ctrl:
            ctrl = SystemSafetyControl(
                organization_id=organization_id,
                ai_workforce_enabled=True,
                customer_ai_enabled=True,
                automated_actions_enabled=True,
                high_risk_actions_enabled=True,
                global_ai_kill_switch=False,
                disabled_agent_ids=[],
                disabled_tool_names=[],
                disabled_workflow_ids=[],
                security_score=98
            )
            db.add(ctrl)
            db.commit()
            db.refresh(ctrl)

        return ctrl

    @classmethod
    def set_global_kill_switch(
        cls,
        db: Session,
        organization_id: str,
        active: bool,
        actor_id: str,
        reason: Optional[str] = None
    ) -> SystemSafetyControl:
        ctrl = cls.get_or_create_controls(db, organization_id)
        ctrl.global_ai_kill_switch = active
        ctrl.kill_switch_activated_at = get_utc_now() if active else None
        ctrl.kill_switch_activated_by = actor_id if active else None
        ctrl.kill_switch_reason = reason if active else None

        # Record Security Event
        event = SecurityEvent(
            organization_id=organization_id,
            event_type="KILL_SWITCH_TRIGGERED" if active else "KILL_SWITCH_DEACTIVATED",
            severity="CRITICAL" if active else "MEDIUM",
            actor_id=actor_id,
            actor_type="USER",
            details={"active": active, "reason": reason}
        )
        db.add(event)
        db.commit()
        db.refresh(ctrl)
        return ctrl

    @classmethod
    def can_execute_action(
        cls,
        db: Session,
        organization_id: str,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        risk_level: str = "LOW"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if an action is permitted by current safety controls.
        """
        ctrl = cls.get_or_create_controls(db, organization_id)

        # 1. Global Kill Switch
        if ctrl.global_ai_kill_switch:
            return False, f"Blocked: Global AI Kill Switch is ACTIVE. Reason: {ctrl.kill_switch_reason or 'Emergency shutdown'}"

        # 2. Workforce master switch
        if not ctrl.ai_workforce_enabled:
            return False, "Blocked: AI Workforce is currently disabled."

        # 3. Agent-specific switch
        if agent_id and agent_id in (ctrl.disabled_agent_ids or []):
            return False, f"Blocked: AI Employee #{agent_id} has been suspended by safety operations."

        # 4. Tool-specific switch
        if tool_name and tool_name in (ctrl.disabled_tool_names or []):
            return False, f"Blocked: Tool '{tool_name}' is currently disabled."

        # 5. Automated actions switch (blocks mutations)
        if not ctrl.automated_actions_enabled and tool_name not in ("get_order", "get_product", "track_shipment", "get_customer"):
            return False, "Blocked: Automated business mutations are currently paused."

        # 6. High-risk actions switch
        if not ctrl.high_risk_actions_enabled and risk_level in ("HIGH", "CRITICAL"):
            return False, f"Blocked: High-risk actions are disabled. Action risk level is {risk_level}."

        return True, None
