"""
Phase 13 — AI Memory, Learning, Feedback, and Evaluation Models.
Enforces multi-layer memory, experience capture, human feedback,
curated learning examples, improvement candidates, prompt versioning, and A/B experiments.
Strict governance: No uncontrolled self-training.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship

from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


# ---------------------------------------------------------------------------
# 1. Memory Architecture
# ---------------------------------------------------------------------------

class CustomerMemory(Base, BaseModelMixin):
    """
    Customer-specific long term memory with TTL, consent tracking,
    and strict tenant & user isolation.
    """
    __tablename__ = "customer_memories"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)

    # Memory types: PREFERENCE, SUPPORT_CONTEXT, PRODUCT_INTEREST, COMMUNICATION_PREFERENCE, ACCOUNT_CONTEXT
    memory_type = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False)

    source = Column(String(100), default="CUSTOMER_CHAT", nullable=False)  # CUSTOMER_CHAT, AGENT_INFERENCE, EXPLICIT_USER
    confidence = Column(Float, default=1.0, nullable=False)
    consent_status = Column(String(50), default="GRANTED", nullable=False)  # GRANTED, REVOKED, PENDING
    is_conflicted = Column(Boolean, default=False, nullable=False)          # Set when MEMORY_CONFLICT detected

    expires_at = Column(DateTime, nullable=True, index=True)

    __table_args__ = (
        Index("ix_cust_mem_lookup", "organization_id", "customer_id", "key"),
    )


class AgentMemory(Base, BaseModelMixin):
    """
    Operational knowledge acquired by AI employees from executions:
    recurring issues, frequent questions, common failure causes.
    Never overrides RAG policies.
    """
    __tablename__ = "agent_memories"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)

    # Memory types: WORKFLOW_FAILURE_PATTERN, COMMON_INQUIRY, INVENTORY_BOTTLENECK, SUCCESSFUL_WORKFLOW_PATTERN, ESCALATION_CAUSE
    memory_type = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False)

    confidence = Column(Float, default=1.0, nullable=False)
    evidence_count = Column(Integer, default=1, nullable=False)
    is_conflicted = Column(Boolean, default=False, nullable=False)
    last_observed_at = Column(DateTime, default=get_utc_now, nullable=False)

    __table_args__ = (
        Index("ix_agent_mem_lookup", "organization_id", "memory_type", "key"),
    )


class WorkflowMemory(Base, BaseModelMixin):
    """
    Aggregated operational knowledge on workflow executions, failure bottlenecks,
    and carrier/vendor timeouts.
    """
    __tablename__ = "workflow_memories"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_definition_id = Column(String(36), nullable=True, index=True)
    workflow_name = Column(String(100), nullable=False, index=True)

    total_runs = Column(Integer, default=0, nullable=False)
    successful_runs = Column(Integer, default=0, nullable=False)
    failed_runs = Column(Integer, default=0, nullable=False)
    escalated_runs = Column(Integer, default=0, nullable=False)

    common_failure_reasons = Column(JSON, default=list, nullable=False)  # [{"reason": "Vendor timeout", "count": 3}]
    avg_duration_ms = Column(Integer, default=0, nullable=False)


# ---------------------------------------------------------------------------
# 2. Experience Capture & Human/Customer Feedback
# ---------------------------------------------------------------------------

class AgentExperience(Base, BaseModelMixin):
    """
    Concise, auditable execution summary for each AI action.
    Never stores hidden chain-of-thought.
    """
    __tablename__ = "agent_experiences"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    agent_run_id = Column(String(36), nullable=True, index=True)
    workflow_run_id = Column(String(36), nullable=True, index=True)

    trigger_type = Column(String(50), nullable=False)  # CUSTOMER_MESSAGE, EMAIL, WORKFLOW, MANUAL
    input_summary = Column(Text, nullable=False)
    decision_summary = Column(Text, nullable=False)    # Concise reasoning, no raw CoT
    actions_taken = Column(JSON, default=list, nullable=False)

    # Outcomes: SUCCESS, PARTIAL_SUCCESS, FAILURE, ESCALATED, HUMAN_CORRECTED, CUSTOMER_REJECTED, TIMEOUT, CANCELLED
    outcome = Column(String(50), default="SUCCESS", nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    risk_level = Column(String(20), default="LOW", nullable=False)

    human_intervention = Column(Boolean, default=False, nullable=False)
    human_correction = Column(Text, nullable=True)
    customer_feedback = Column(JSON, nullable=True)
    execution_duration_ms = Column(Integer, default=0, nullable=False)


class AgentFeedback(Base, BaseModelMixin):
    """
    Human operator reviews, corrections, and grading on AI decisions.
    """
    __tablename__ = "agent_feedbacks"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    agent_run_id = Column(String(36), nullable=True, index=True)
    workflow_run_id = Column(String(36), nullable=True, index=True)
    tool_execution_id = Column(String(36), nullable=True, index=True)

    reviewer_user_id = Column(String(36), nullable=False, index=True)

    # Types: CORRECT, INCORRECT, PARTIALLY_CORRECT, POLICY_VIOLATION, WRONG_TOOL, WRONG_INTENT,
    # WRONG_RESPONSE, WRONG_ESCALATION, MISSING_CONTEXT, HALLUCINATION, CUSTOMER_UNSATISFIED, EXCELLENT
    feedback_type = Column(String(50), nullable=False, index=True)
    rating = Column(Integer, default=5, nullable=False)  # 1 to 5
    correction = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)


class CustomerMessageFeedback(Base, BaseModelMixin):
    """
    Turn-by-turn customer satisfaction rating on individual AI chat responses.
    """
    __tablename__ = "customer_message_feedbacks"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    message_id = Column(String(36), nullable=True, index=True)
    customer_id = Column(String(36), nullable=True, index=True)

    rating = Column(Integer, nullable=False)  # 1 (thumb down) to 5 (stars)
    was_helpful = Column(Boolean, default=True, nullable=False)
    comment = Column(Text, nullable=True)
    reason = Column(String(100), nullable=True)


# ---------------------------------------------------------------------------
# 3. Learning Dataset & Fine-Tuning Preparation
# ---------------------------------------------------------------------------

class LearningExample(Base, BaseModelMixin):
    """
    Curated input/output/correction examples prepared for model evaluation and fine-tuning.
    """
    __tablename__ = "learning_examples"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Source types: HUMAN_FEEDBACK, CUSTOMER_FEEDBACK, FAILED_AGENT_RUN, FAILED_WORKFLOW, TOOL_FAILURE, POLICY_VIOLATION, MANUAL_EXAMPLE, EVALUATION_CASE
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(36), nullable=True)

    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    actual_output = Column(Text, nullable=True)
    correction = Column(Text, nullable=True)

    # Categories: INTENT_CLASSIFICATION, ENTITY_EXTRACTION, RAG_ANSWER, TOOL_SELECTION, POLICY_COMPLIANCE, RESPONSE_GENERATION, ESCALATION, WORKFLOW_DECISION
    category = Column(String(50), nullable=False, index=True)
    quality_score = Column(Float, default=1.0, nullable=False)
    approved = Column(Boolean, default=False, nullable=False, index=True)
    reviewer_id = Column(String(36), nullable=True)
    dataset_version = Column(String(50), default="v1.0", nullable=False, index=True)


# ---------------------------------------------------------------------------
# 4. Improvement Candidate System & Prompt Versioning
# ---------------------------------------------------------------------------

class ImprovementCandidate(Base, BaseModelMixin):
    """
    Proposed prompt/rule/configuration refinement generated from learning patterns.
    AI generates proposals; Human approval is strictly mandatory before deployment.
    """
    __tablename__ = "improvement_candidates"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)

    # Types: PROMPT_IMPROVEMENT, FEW_SHOT_EXAMPLE, ROUTING_IMPROVEMENT, RAG_CONFIGURATION, TOOL_SELECTION_RULE, ESCALATION_RULE, WORKFLOW_CONFIGURATION, MODEL_CONFIGURATION, THRESHOLD_CHANGE
    candidate_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict, nullable=False)
    proposed_change = Column(JSON, nullable=False)
    expected_impact = Column(Text, nullable=True)
    risk = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH

    # Statuses: GENERATED, UNDER_REVIEW, APPROVED, REJECTED, DEPLOYED, ROLLED_BACK
    status = Column(String(50), default="GENERATED", nullable=False, index=True)
    created_by = Column(String(36), default="system-evaluator", nullable=False)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)


class AgentPromptVersion(Base, BaseModelMixin):
    """
    Version-controlled agent prompts and system configurations.
    Only approved versions may become ACTIVE. Retains full rollback history.
    """
    __tablename__ = "agent_prompt_versions"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    version = Column(String(20), nullable=False)  # e.g. "v1.0", "v1.1"

    system_prompt = Column(Text, nullable=False)
    behavior_rules = Column(JSON, default=list, nullable=False)
    output_schema = Column(JSON, default=dict, nullable=False)
    model = Column(String(100), default="gpt-4o-mini", nullable=False)
    temperature = Column(Float, default=0.1, nullable=False)
    configuration = Column(JSON, default=dict, nullable=False)

    # Status: DRAFT, TESTING, APPROVED, ACTIVE, RETIRED
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    approved_by = Column(String(36), nullable=True)
    activated_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# 5. Evaluation Runs & A/B Experiments
# ---------------------------------------------------------------------------

class EvaluationRun(Base, BaseModelMixin):
    """
    Regression evaluation run against benchmark datasets.
    Tracks accuracy, groundedness, policy compliance, and failure delta.
    """
    __tablename__ = "evaluation_runs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    version_id = Column(String(36), nullable=True)
    dataset_version = Column(String(50), default="v1.0", nullable=False)

    metrics = Column(JSON, default=dict, nullable=False)
    # {
    #   "intent_accuracy": 0.95,
    #   "rag_groundedness": 0.98,
    #   "policy_compliance": 0.998,
    #   "tool_selection_accuracy": 0.99
    # }
    passed = Column(Boolean, default=True, nullable=False)
    failure_reasons = Column(JSON, default=list, nullable=False)
    executed_by = Column(String(36), default="system", nullable=False)


class AgentExperiment(Base, BaseModelMixin):
    """
    A/B controlled experiment routing a percentage of traffic to candidate version.
    """
    __tablename__ = "agent_experiments"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    agent_id = Column(String(36), nullable=False, index=True)

    baseline_version = Column(String(50), nullable=False)
    candidate_version = Column(String(50), nullable=False)
    traffic_percentage = Column(Float, default=10.0, nullable=False)  # 10% to candidate

    metrics = Column(JSON, default=dict, nullable=False)
    # Statuses: DRAFT, RUNNING, PAUSED, COMPLETED, CANCELLED
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
