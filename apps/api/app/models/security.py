"""
Phase 14 — Security Hardening, AI Security, Events, and Incident Models.
Enforces multi-tenant isolation, prompt injection tracking, immutable audit trails,
and emergency AI kill switch controls.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship

from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class SecurityEvent(Base, BaseModelMixin):
    """
    Immutable security telemetry record for adversarial attempts,
    prompt injection, unauthorized access, SSRF, and approval tampering.
    """
    __tablename__ = "security_events"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event types:
    # AUTH_FAILURE, SUSPICIOUS_LOGIN, PRIVILEGE_ESCALATION, TENANT_ACCESS_VIOLATION,
    # PROMPT_INJECTION, TOOL_POLICY_VIOLATION, APPROVAL_BYPASS_ATTEMPT, APPROVAL_HASH_MISMATCH,
    # DATA_EXFILTRATION_ATTEMPT, SSRF_BLOCKED, MALICIOUS_FILE, RATE_LIMIT_EXCEEDED,
    # AI_LOOP_DETECTED, SECRET_EXPOSURE_ATTEMPT, KILL_SWITCH_TRIGGERED
    event_type = Column(String(50), nullable=False, index=True)

    # Severity: LOW, MEDIUM, HIGH, CRITICAL
    severity = Column(String(20), default="MEDIUM", nullable=False, index=True)

    actor_id = Column(String(100), nullable=True, index=True)
    actor_type = Column(String(50), default="ANONYMOUS", nullable=False)  # USER, CUSTOMER, AI_AGENT, ANONYMOUS

    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    trace_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)

    details = Column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_sec_event_org_type_sev", "organization_id", "event_type", "severity"),
    )


class SecurityIncident(Base, BaseModelMixin):
    """
    Operational security incident requiring human investigation, containment,
    and formal root-cause resolution.
    """
    __tablename__ = "security_incidents"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    incident_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="HIGH", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL

    # Status: OPEN, INVESTIGATING, CONTAINED, RESOLVED, FALSE_POSITIVE
    status = Column(String(50), default="OPEN", nullable=False, index=True)

    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    assigned_to = Column(String(36), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)


class SystemSafetyControl(Base, BaseModelMixin):
    """
    Tenant-level and platform-wide safety flags, emergency kill switch,
    and granular AI employee / tool / workflow disable toggles.
    """
    __tablename__ = "system_safety_controls"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    ai_workforce_enabled = Column(Boolean, default=True, nullable=False)
    customer_ai_enabled = Column(Boolean, default=True, nullable=False)
    automated_actions_enabled = Column(Boolean, default=True, nullable=False)
    high_risk_actions_enabled = Column(Boolean, default=True, nullable=False)

    global_ai_kill_switch = Column(Boolean, default=False, nullable=False)
    kill_switch_activated_at = Column(DateTime, nullable=True)
    kill_switch_activated_by = Column(String(36), nullable=True)
    kill_switch_reason = Column(Text, nullable=True)

    disabled_agent_ids = Column(JSON, default=list, nullable=False)
    disabled_tool_names = Column(JSON, default=list, nullable=False)
    disabled_workflow_ids = Column(JSON, default=list, nullable=False)

    security_score = Column(Integer, default=98, nullable=False)
