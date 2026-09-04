from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship

from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class Alert(Base, BaseModelMixin):
    """
    Phase 12 — Enterprise Operational Alert.
    Monitors workforce failure, SLA breaches, inventory anomalies, and workflow stuck states.
    """
    __tablename__ = "alerts"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    # WORKFORCE_FAILURE, WORKFLOW_FAILURE, APPROVAL_BACKLOG, ESCALATION_SLA_BREACH,
    # INVENTORY_CRITICAL, PAYMENT_FAILURE, HIGH_REFUND_VOLUME, KNOWLEDGE_CONFLICT,
    # RAG_FAILURE, TOOL_FAILURE, QUEUE_OVERLOAD

    severity = Column(String(20), default="MEDIUM", nullable=False, index=True)
    # INFO, LOW, MEDIUM, HIGH, CRITICAL

    status = Column(String(20), default="OPEN", nullable=False, index=True)
    # OPEN, ACKNOWLEDGED, RESOLVED, IGNORED

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    source_type = Column(String(50), nullable=True)   # WORKFLOW, TOOL, AGENT, APPROVAL, ESCALATION, INVENTORY, SYSTEM
    source_id = Column(String(36), nullable=True)

    alert_metadata = Column("metadata", JSON, default=dict, nullable=False)

    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_alerts_org_status_severity", "organization_id", "status", "severity"),
    )


class ObservabilityTrace(Base, BaseModelMixin):
    """
    Phase 12 — Distributed Observability Trace Waterfall.
    Captures step-by-step latency across Intent, RAG, Policy, Tool, and Response stages.
    """
    __tablename__ = "observability_traces"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id = Column(String(100), nullable=False, index=True)
    trace_id = Column(String(100), nullable=True, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    workflow_run_id = Column(String(36), nullable=True, index=True)
    tool_execution_id = Column(String(36), nullable=True)

    operation_name = Column(String(100), nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, TIMED_OUT

    spans = Column(JSON, default=list, nullable=False)
    # Example spans:
    # [
    #   {"name": "Customer Request", "offset_ms": 0, "duration_ms": 10, "status": "OK"},
    #   {"name": "Intent Detection", "offset_ms": 10, "duration_ms": 120, "status": "OK"},
    #   {"name": "RAG Retrieval", "offset_ms": 130, "duration_ms": 210, "status": "OK"},
    #   {"name": "Policy Check", "offset_ms": 340, "duration_ms": 35, "status": "OK"},
    #   {"name": "Tool Execution", "offset_ms": 375, "duration_ms": 340, "status": "OK"},
    #   {"name": "Verification", "offset_ms": 715, "duration_ms": 110, "status": "OK"},
    #   {"name": "Response", "offset_ms": 825, "duration_ms": 90, "status": "OK"}
    # ]

    trace_metadata = Column("metadata", JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_traces_org_created", "organization_id", "created_at"),
    )
