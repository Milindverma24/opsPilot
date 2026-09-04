from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


# ---------------------------------------------------------------------------
# AI Employee Identity
# ---------------------------------------------------------------------------

class AIEmployee(Base, BaseModelMixin):
    """
    The explicit AI employee persona for an organization.
    Not a superadmin — has a restricted, auditable set of permissions.
    """
    __tablename__ = "ai_employees"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)                        # "UrbanThread Operations Employee"
    role = Column(String(100), nullable=False)                        # AI_OPERATIONS_EMPLOYEE
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)     # ACTIVE, INACTIVE, SUSPENDED
    permissions = Column(JSON, default=list, nullable=False)          # ["customers.read", "orders.read", ...]
    configuration = Column(JSON, default=dict, nullable=False)        # model, temperature, thresholds
    llm_provider = Column(String(50), default="deterministic", nullable=False)
    llm_model = Column(String(100), default="gpt-4o-mini", nullable=False)
    max_steps = Column(Integer, default=12, nullable=False)
    max_replans = Column(Integer, default=3, nullable=False)
    timeout_seconds = Column(Integer, default=120, nullable=False)
    confidence_threshold_auto = Column(Float, default=0.90, nullable=False)
    confidence_threshold_review = Column(Float, default=0.70, nullable=False)

    # Phase 12: Workforce Health, Heartbeat & Telemetry
    health = Column(String(20), default="HEALTHY", nullable=False)     # HEALTHY, DEGRADED, CRITICAL, FAILED
    current_task = Column(String(255), nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    completed_tasks_count = Column(Integer, default=0, nullable=False)
    failed_tasks_count = Column(Integer, default=0, nullable=False)
    total_latency_ms = Column(Integer, default=0, nullable=False)
    queue_size = Column(Integer, default=0, nullable=False)

    runs = relationship("AgentRun", foreign_keys="AgentRun.ai_employee_id", back_populates="ai_employee")



# ---------------------------------------------------------------------------
# Agent (legacy — kept for backward compatibility)
# ---------------------------------------------------------------------------

class Agent(Base, BaseModelMixin):
    __tablename__ = "agents"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    agent_type = Column(String(50), nullable=False, index=True)
    model = Column(String(100), default="gpt-4o", nullable=False)
    system_prompt = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    temperature = Column(Float, default=0.1, nullable=False)

    code = synonym("agent_type")
    is_active = synonym("enabled")

    runs = relationship("AgentRun", foreign_keys="AgentRun.agent_id", back_populates="agent")


# ---------------------------------------------------------------------------
# Agent Run — Extended for Phase 7
# ---------------------------------------------------------------------------

class AgentRun(Base, BaseModelMixin):
    """
    Persistent, reboot-survivable agent run state.
    Every field is auditable. No hidden chain-of-thought stored.
    """
    __tablename__ = "agent_runs"

    # Identity
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_employee_id = Column(String(36), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)

    # Idempotency
    idempotency_key = Column(String(255), nullable=True, index=True)

    # Trigger
    trigger_type = Column(String(50), nullable=True)    # CUSTOMER_MESSAGE, EMAIL_RECEIVED, BUSINESS_EVENT, MANUAL_TRIGGER, SCHEDULED_TASK
    trigger_id = Column(String(36), nullable=True)      # ID of the triggering entity (email_id, event_id, etc.)
    actor_type = Column(String(50), nullable=True)      # CUSTOMER, USER, SYSTEM, AI_EMPLOYEE
    actor_id = Column(String(36), nullable=True)

    # Status
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # PENDING, RUNNING, WAITING_FOR_APPROVAL, WAITING_FOR_TOOL, COMPLETED, FAILED, CANCELLED, BLOCKED
    current_step = Column(String(100), nullable=True)   # CLASSIFYING, GATHERING_CONTEXT, REASONING, etc.

    # Data
    input_data = Column(JSON, default=dict, nullable=False)
    context_data = Column(JSON, default=list, nullable=False)       # List[ContextItem]
    extracted_data = Column(JSON, default=dict, nullable=False)     # EntityExtractionResult
    decisions = Column(JSON, default=list, nullable=False)          # List[ReasoningResult]
    policy_results = Column(JSON, default=list, nullable=False)     # List[PolicyResult]
    planned_actions = Column(JSON, default=list, nullable=False)    # ActionPlan
    completed_actions = Column(JSON, default=list, nullable=False)  # Phase 8

    # Intelligence outputs
    intent = Column(String(100), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)      # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    # Decision summary (auditable, no hidden reasoning)
    decision_summary = Column(Text, nullable=True)
    reason_codes = Column(JSON, default=list, nullable=False)
    evidence_ids = Column(JSON, default=list, nullable=False)

    # Human approval
    requires_human_approval = Column(Boolean, default=False, nullable=False)
    approval_id = Column(String(36), nullable=True)     # FK to approvals table
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Failure tracking
    failure_code = Column(String(100), nullable=True)   # CONTEXT_NOT_FOUND, LOW_CONFIDENCE, etc.
    failure_summary = Column(Text, nullable=True)
    errors = Column(JSON, default=list, nullable=False)

    # Model telemetry
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    model_used = Column(String(100), nullable=True)
    total_steps = Column(Integer, default=0, nullable=False)
    replan_count = Column(Integer, default=0, nullable=False)

    # Legacy
    token_usage = Column(Integer, default=0, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    ai_employee = relationship("AIEmployee", foreign_keys=[ai_employee_id], back_populates="runs")
    agent = relationship("Agent", foreign_keys=[agent_id], back_populates="runs")
    steps = relationship("AgentStep", back_populates="agent_run", cascade="all, delete-orphan", order_by="AgentStep.created_at")
    messages = relationship("AgentMessage", back_populates="agent_run", cascade="all, delete-orphan")
    tool_executions = relationship("ToolExecution", back_populates="agent_run")


# ---------------------------------------------------------------------------
# Agent Step — Persistent execution record
# ---------------------------------------------------------------------------

class AgentStep(Base, BaseModelMixin):
    """
    Each step in the reasoning pipeline is persisted separately.
    Steps are never overwritten — append-only for full audit trail.
    """
    __tablename__ = "agent_steps"

    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    step_index = Column(Integer, nullable=False)         # 0-based ordering
    step_type = Column(String(100), nullable=False)      # CLASSIFY, GATHER_CONTEXT, RETRIEVE_KNOWLEDGE, REASON, ASSESS_RISK, PLAN, etc.
    status = Column(String(50), nullable=False)          # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED

    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)

    # Timing
    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Error
    error = Column(Text, nullable=True)
    step_metadata = Column(JSON, default=dict, nullable=False)

    agent_run = relationship("AgentRun", back_populates="steps")


# ---------------------------------------------------------------------------
# Agent Message (legacy conversation tracking)
# ---------------------------------------------------------------------------

class AgentMessage(Base, BaseModelMixin):
    __tablename__ = "agent_messages"

    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)
    msg_metadata = Column("metadata", JSON, default=dict, nullable=False)
    tool_call_id = Column(String(100), nullable=True)
    name = Column(String(100), nullable=True)

    agent_run = relationship("AgentRun", back_populates="messages")


# ---------------------------------------------------------------------------
# Tool (allowlisted action vocabulary)
# ---------------------------------------------------------------------------

class Tool(Base, BaseModelMixin):
    __tablename__ = "tools"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=True)
    description = Column(String(512), nullable=False)
    category = Column(String(50), default="READ", nullable=False, index=True)
    # READ, CUSTOMER, ORDER, INVENTORY, PAYMENT, RETURN, REFUND,
    # SUPPORT, COMMUNICATION, VENDOR, PURCHASE, SYSTEM

    # Schemas
    input_schema = Column(JSON, default=dict, nullable=False)
    output_schema = Column(JSON, default=dict, nullable=False)

    # Permissions & Risk
    required_permission = Column(String(100), nullable=False)       # legacy single permission
    required_permissions = Column(JSON, default=list, nullable=False)  # list of permissions
    risk_level = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    approval_mode = Column(String(20), default="NEVER", nullable=False)  # NEVER, ON_RISK, ALWAYS

    # Handler
    handler_key = Column(String(100), nullable=True)  # maps to registered Python handler
    version = Column(String(20), default="v1", nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    max_retries = Column(Integer, default=0, nullable=False)

    # State
    enabled = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)       # for circuit breaker

    is_enabled = synonym("enabled")
    executions = relationship("ToolExecution", foreign_keys="ToolExecution.tool_id", back_populates="tool")


# ToolDefinition is an alias for Tool
ToolDefinition = Tool


class ToolExecution(Base, BaseModelMixin):
    """
    Immutable execution record for every tool invocation.
    Phase 8: full authorization pipeline state captured per row.
    """
    __tablename__ = "tool_executions"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(String(36), ForeignKey("tools.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    tool_version = Column(String(20), default="v1", nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Who requested this
    requested_by = Column(String(36), nullable=True)         # agent_id or user_id
    requested_by_type = Column(String(50), default="AI_AGENT", nullable=False)  # AI_AGENT, USER
    approved_by_user_id = Column(String(36), nullable=True)

    # Input / Output
    input_data = Column(JSON, default=dict, nullable=False)
    validated_input = Column(JSON, default=dict, nullable=False)     # post-validation snapshot
    output_data = Column(JSON, default=dict, nullable=False)
    execution_receipt = Column(JSON, default=dict, nullable=False)   # immutable action receipt

    # Authorization pipeline results
    permission_granted = Column(Boolean, nullable=True)
    policy_decision = Column(String(20), nullable=True)     # ALLOW, DENY, CONDITIONAL
    risk_level = Column(String(20), nullable=True)
    risk_score = Column(Float, nullable=True)
    approval_required = Column(Boolean, default=False, nullable=False)
    approval_id = Column(String(36), nullable=True)
    approval_hash = Column(String(64), nullable=True)       # deterministic action hash for binding

    # Status
    status = Column(String(50), default="REQUESTED", nullable=False, index=True)
    # REQUESTED, VALIDATING, BLOCKED, WAITING_FOR_APPROVAL,
    # APPROVED, EXECUTING, SUCCEEDED, FAILED, CANCELLED, TIMED_OUT, UNKNOWN
    error_code = Column(String(100), nullable=True)
    error = Column(Text, nullable=True)
    block_reason = Column(Text, nullable=True)

    # Execution mode
    execution_mode = Column(String(20), default="LIVE_MOCK", nullable=False)  # PLAN_ONLY, DRY_RUN, LIVE_MOCK

    # Idempotency
    idempotency_key = Column(String(255), nullable=True, index=True)

    # Timing
    started_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    is_mock = Column(Boolean, default=True, nullable=False)

    # Synonyms for backward compatibility
    input_params = synonym("input_data")
    output_result = synonym("output_data")

    agent_run = relationship("AgentRun", back_populates="tool_executions")
    tool = relationship("Tool", foreign_keys=[tool_id], back_populates="executions")
