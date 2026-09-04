"""
Workflow and Human Approval Domain Models — Phase 9 & Phase 10.

Includes:
- Workflow: template/definition of multi-step business automation
- WorkflowStep: step definition within a workflow
- WorkflowRun: durable execution instance of a workflow
- WorkflowStepRun: durable execution instance of a specific step attempt
- Approval: human review boundary with SHA-256 payload integrity
- ApprovalComment: audit comments on approval requests
- Escalation: SLA-governed incident and human routing record
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, DateTime, Index
)
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now, generate_uuid


# ---------------------------------------------------------------------------
# Workflow (Definition / Template)
# ---------------------------------------------------------------------------

class Workflow(Base, BaseModelMixin):
    __tablename__ = "workflows"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False, default="Operational Workflow")
    description = Column(Text, nullable=True)
    workflow_type = Column(String(100), nullable=False, default="INVOICE_PROCESSING", index=True)
    trigger_type = Column(String(50), nullable=False, default="BUSINESS_EVENT", index=True)
    # Triggers: BUSINESS_EVENT, CUSTOMER_MESSAGE, EMAIL_RECEIVED, SCHEDULED, MANUAL,
    # INVENTORY_THRESHOLD, ORDER_CREATED, SHIPMENT_DELAYED, RETURN_REQUESTED, SUPPORT_TICKET_CREATED, PAYMENT_FAILED, PAYMENT_TIMEOUT

    status = Column(String(50), nullable=False, default="ACTIVE", index=True)
    # Statuses: DRAFT, ACTIVE, PAUSED, DISABLED, ARCHIVED
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(String(20), default="v1", nullable=False)
    configuration = Column(JSON, default=dict, nullable=False)
    max_concurrent_runs = Column(Integer, default=10, nullable=False)
    timeout_seconds = Column(Integer, default=3600, nullable=False)  # 1 hour default

    # Backward compatibility columns from Phase 2
    business_event_id = Column(String(36), ForeignKey("business_events.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    current_step = Column(String(100), nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    context = Column(JSON, default=dict, nullable=False)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="workflow", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# WorkflowStep (Definition)
# ---------------------------------------------------------------------------

class WorkflowStep(Base, BaseModelMixin):
    __tablename__ = "workflow_steps"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False, default="Workflow Step")
    description = Column(Text, nullable=True)
    step_order = Column(Integer, nullable=False, default=1)

    step_type = Column(String(50), nullable=False)
    # Types: CONTEXT_GATHER, AI_DECISION, POLICY_CHECK, RISK_ASSESSMENT, CONDITION,
    # TOOL_EXECUTION, APPROVAL, WAIT, NOTIFICATION, ESCALATION, VERIFICATION,
    # SUB_WORKFLOW, COMPLETE, FAIL

    configuration = Column(JSON, default=dict, nullable=False)
    timeout_seconds = Column(Integer, default=300, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_backoff_seconds = Column(Integer, default=5, nullable=False)
    continue_on_failure = Column(Boolean, default=False, nullable=False)

    # Backward compatibility columns from Phase 2
    agent_id = Column(String(36), nullable=True, index=True)
    agent_run_id = Column(String(36), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)

    step_input = synonym("input_data")
    step_output = synonym("output_data")

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    step_runs = relationship("WorkflowStepRun", back_populates="workflow_step", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# WorkflowRun (Durable Execution Instance)
# ---------------------------------------------------------------------------

class WorkflowRun(Base, BaseModelMixin):
    __tablename__ = "workflow_runs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    trigger_event_id = Column(String(36), nullable=True, index=True)
    idempotency_key = Column(String(255), nullable=True, index=True)

    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # PENDING, RUNNING, WAITING, WAITING_FOR_APPROVAL, WAITING_FOR_EVENT,
    # PAUSED, RETRYING, COMPLETED, FAILED, CANCELLED, ESCALATED, TIMED_OUT, BLOCKED

    current_step_id = Column(String(36), nullable=True)
    current_step_order = Column(Integer, default=1, nullable=False)

    # Dynamic execution state
    input_data = Column(JSON, default=dict, nullable=False)
    context_data = Column(JSON, default=dict, nullable=False)
    decision_data = Column(JSON, default=dict, nullable=False)
    execution_data = Column(JSON, default=dict, nullable=False)
    error_data = Column(JSON, default=dict, nullable=False)

    # Execution controls and timestamps
    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    paused_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="runs")
    step_runs = relationship("WorkflowStepRun", back_populates="workflow_run", cascade="all, delete-orphan", order_by="WorkflowStepRun.attempt_number")
    approvals = relationship("Approval", back_populates="workflow_run", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="workflow_run", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# WorkflowStepRun (Durable Step Execution Attempt)
# ---------------------------------------------------------------------------

class WorkflowStepRun(Base, BaseModelMixin):
    __tablename__ = "workflow_step_runs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_step_id = Column(String(36), ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # PENDING, RUNNING, WAITING, WAITING_FOR_APPROVAL, SUCCEEDED, FAILED, SKIPPED, RETRYING, TIMED_OUT, CANCELLED

    attempt_number = Column(Integer, default=1, nullable=False)
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    decision_data = Column(JSON, default=dict, nullable=False)

    tool_execution_id = Column(String(36), ForeignKey("tool_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    approval_id = Column(String(36), nullable=True, index=True)

    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="step_runs")
    workflow_step = relationship("WorkflowStep", back_populates="step_runs")


# ---------------------------------------------------------------------------
# Approval (Human-in-the-loop Governance Boundary — Phase 10)
# ---------------------------------------------------------------------------

class Approval(Base, BaseModelMixin):
    __tablename__ = "approvals"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_step_run_id = Column(String(36), ForeignKey("workflow_step_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_execution_id = Column(String(36), ForeignKey("tool_executions.id", ondelete="SET NULL"), nullable=True, index=True)

    requested_by_type = Column(String(50), default="AI_EMPLOYEE", nullable=False)  # AI_EMPLOYEE, USER, SYSTEM
    requested_by_id = Column(String(36), nullable=True)
    requested_by = Column(String(255), default="OpsPilot AI Supervisor", nullable=False)

    approval_type = Column(String(50), nullable=False, default="HIGH_RISK_OPERATION", index=True)
    # Types: REFUND, ORDER_CANCELLATION, ORDER_MODIFICATION, RETURN_APPROVAL,
    # INVENTORY_ADJUSTMENT, PURCHASE_ORDER, CUSTOMER_COMMUNICATION, VENDOR_ACTION,
    # POLICY_EXCEPTION, HIGH_RISK_OPERATION

    risk_level = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # Statuses: PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED, SUPERSEDED

    title = Column(String(255), nullable=False, default="Action Approval Request")
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)

    # Action binding & Cryptographic SHA-256 payload immutability
    action_type = Column(String(100), nullable=True)
    action_payload = Column(JSON, default=dict, nullable=False)
    action_payload_hash = Column(String(64), nullable=True, index=True)

    # Snapshots
    policy_snapshot = Column(JSON, default=dict, nullable=False)
    risk_snapshot = Column(JSON, default=dict, nullable=False)

    # Multi-level approval configuration
    approval_mode = Column(String(50), default="ONE_APPROVER", nullable=False)  # ONE_APPROVER, ALL_REQUIRED, ANY_ONE
    required_roles = Column(JSON, default=lambda: ["MANAGER"], nullable=False)
    approvals_received = Column(JSON, default=list, nullable=False)  # list of {user_id, role, approved_at, comment}

    # Decision metadata
    expires_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    # Backward compatibility attributes
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    ai_recommendation = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=False, default="invoice")
    resource_id = Column(String(100), nullable=True)
    requested_at = Column(DateTime, default=get_utc_now, nullable=False)
    decision_reason = Column(Text, nullable=True)

    request_type = synonym("resource_type")
    requester_name = synonym("requested_by")
    affected_entity_type = synonym("resource_type")
    affected_entity_id = synonym("resource_id")
    approved_by_user_id = synonym("approved_by")
    decided_at = synonym("approved_at")

    # Relationships
    workflow = relationship("Workflow", back_populates="approvals")
    workflow_run = relationship("WorkflowRun", back_populates="approvals")
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by])
    comments = relationship("ApprovalComment", back_populates="approval", cascade="all, delete-orphan", order_by="ApprovalComment.created_at")
    escalations = relationship("Escalation", back_populates="approval")


# ---------------------------------------------------------------------------
# ApprovalComment (Audited Human Feedback)
# ---------------------------------------------------------------------------

class ApprovalComment(Base, BaseModelMixin):
    __tablename__ = "approval_comments"

    approval_id = Column(String(36), ForeignKey("approvals.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    comment = Column(Text, nullable=False)

    user = relationship("User")
    approval = relationship("Approval", back_populates="comments")


# ---------------------------------------------------------------------------
# Escalation (SLA-Governed Human Escalation Engine — Phase 10)
# ---------------------------------------------------------------------------

class Escalation(Base, BaseModelMixin):
    __tablename__ = "escalations"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    approval_id = Column(String(36), ForeignKey("approvals.id", ondelete="SET NULL"), nullable=True, index=True)

    level = Column(String(50), nullable=False, default="LEVEL_1", index=True)  # LEVEL_1, LEVEL_2, LEVEL_3, CRITICAL
    reason = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="HIGH", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), nullable=False, default="OPEN", index=True)   # OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CANCELLED

    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_team = Column(String(100), nullable=True)  # SUPPORT, OPERATIONS, FINANCE, ADMIN
    due_at = Column(DateTime, nullable=True, index=True)  # SLA deadline
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(Text, nullable=True)
    dedup_key = Column(String(255), nullable=True, index=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="escalations")
    approval = relationship("Approval", back_populates="escalations")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
