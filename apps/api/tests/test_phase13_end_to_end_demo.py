"""
Phase 13 Required End-to-End Demo:
Scenario:
1. Customer asks: "Can I return these jeans?"
2. AI answers using RAG.
3. Customer gives negative feedback.
4. Human agent corrects AI: "The return window is 30 days for this product."
5. System records: original answer, feedback, correction, source, policy.
6. Learning system creates an improvement candidate.
7. Manager reviews it and approves.
8. New version is evaluated via regression suite.
9. Upon passing regression tests, manager activates it.
10. Command Center shows:
    - Previous version: 94% accuracy
    - New version: 97% accuracy
    - Policy compliance: 99.8%
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.core.database import Base
from apps.api.app.models.tenant import Organization, User
from apps.api.app.models.agent import AIEmployee
from apps.api.app.models.learning import (
    CustomerMemory,
    AgentMemory,
    AgentExperience,
    AgentFeedback,
    CustomerMessageFeedback,
    LearningExample,
    ImprovementCandidate,
    AgentPromptVersion,
    EvaluationRun,
)
from apps.api.app.services.ai.agent_learning_service import AgentLearningService
from apps.api.app.services.ai.agent_evaluation_service import AgentEvaluationService
from apps.api.app.models.base import get_utc_now


@pytest.fixture
def demo_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    org = Organization(id="org-urbanthread", name="UrbanThread", slug="urbanthread")
    session.add(org)

    manager = User(
        id="usr-manager",
        organization_id="org-urbanthread",
        email="manager@urbanthread.com",
        password_hash="mock_hash",
        full_name="Operations Manager",
        role="OPERATIONS_MANAGER",
        status="ACTIVE"
    )
    session.add(manager)

    agent = AIEmployee(
        id="aria-support-ai",
        organization_id="org-urbanthread",
        name="Aria",
        role="CUSTOMER_SUPPORT",
        health="HEALTHY",
        permissions=["orders.read", "refunds.execute"]
    )
    session.add(agent)

    # Initial baseline version v1.0 (94% accuracy)
    v1_0 = AgentPromptVersion(
        organization_id="org-urbanthread",
        agent_id="aria-support-ai",
        version="v1.0",
        system_prompt="You are Aria, customer assistant for UrbanThread. Follow standard policies.",
        behavior_rules=["Be polite"],
        model="gpt-4o-mini",
        temperature=0.1,
        status="ACTIVE",
        created_by="usr-manager",
        approved_by="usr-manager",
        activated_at=get_utc_now()
    )
    session.add(v1_0)
    session.commit()

    yield session
    session.close()


def test_complete_learning_demo_scenario(demo_session):
    # Step 1: Customer asks return question and AI generates response
    customer_inquiry = "Can I return these jeans?"
    ai_original_answer = "Returns must be requested within 14 days of dispatch."

    # Record experience
    exp = AgentExperience(
        organization_id="org-urbanthread",
        agent_id="aria-support-ai",
        agent_run_id="run-demo-101",
        trigger_type="CUSTOMER_MESSAGE",
        input_summary=customer_inquiry,
        decision_summary="Quoted 14 day return window from dispatch",
        actions_taken=[{"action": "rag_policy_search", "query": "jeans return window"}],
        outcome="CUSTOMER_REJECTED",
        success=False,
        confidence=0.82,
        risk_level="LOW",
        execution_duration_ms=420
    )
    demo_session.add(exp)
    demo_session.commit()
    assert exp.id is not None

    # Step 2: Customer gives negative feedback
    cust_fb = AgentLearningService.record_customer_feedback(
        db=demo_session,
        organization_id="org-urbanthread",
        conversation_id="conv-demo-01",
        rating=1,
        was_helpful=False,
        comment="Incorrect return window! Your website says 30 days."
    )
    assert cust_fb.rating == 1
    assert cust_fb.was_helpful is False

    # Step 3: Human agent corrects AI
    agent_fb = AgentLearningService.record_human_feedback(
        db=demo_session,
        organization_id="org-urbanthread",
        agent_id="aria-support-ai",
        reviewer_user_id="usr-manager",
        feedback_type="POLICY_VIOLATION",
        rating=1,
        correction="The return window is 30 days for this product category from the delivered date.",
        comment="AI quoted 14 days instead of official 30-day policy.",
        expected_behavior="Inform shopper that standard returns are 30 days from delivery.",
        actual_behavior="Quoted 14 days from dispatch."
    )
    assert agent_fb.id is not None

    # Step 4: Verify auto-generated LearningExample
    le = demo_session.query(LearningExample).filter(
        LearningExample.source_id == agent_fb.id
    ).first()
    assert le is not None
    assert le.approved is True
    assert "30 days" in le.correction

    # Step 5: Learning system creates Improvement Candidate
    cand = AgentLearningService.generate_candidate(
        db=demo_session,
        organization_id="org-urbanthread",
        agent_id="aria-support-ai",
        candidate_type="PROMPT_IMPROVEMENT",
        title="Clarify 30-Day Delivered Return Policy",
        description="Prevents confusion between dispatch date and delivery date for apparel returns.",
        proposed_change={
            "system_prompt": "You are Aria. Always calculate the 30-day return window from the DELIVERED timestamp.",
            "behavior_rules": ["Verify order delivery timestamp before rejecting return window."]
        },
        expected_impact="Eliminates policy confusion and elevates accuracy from 94% to 97%",
        risk="LOW"
    )
    assert cand.status == "GENERATED"

    # Verify AI cannot self-deploy
    with pytest.raises(ValueError, match="Cannot deploy candidate with status 'GENERATED'"):
        AgentLearningService.deploy_candidate(
            db=demo_session,
            organization_id="org-urbanthread",
            candidate_id=cand.id,
            deployed_by="aria-support-ai"
        )

    # Step 6: Operations Manager reviews and approves candidate
    approved = AgentLearningService.approve_candidate(
        db=demo_session,
        organization_id="org-urbanthread",
        candidate_id=cand.id,
        reviewer_id="usr-manager"
    )
    assert approved.status == "APPROVED"

    # Step 7: New version is evaluated via regression evaluation suite
    # Candidate version v1.1 achieves:
    # 97% accuracy, 99.8% policy compliance (vs previous version 94%)
    eval_run = AgentEvaluationService.run_regression_evaluation(
        db=demo_session,
        organization_id="org-urbanthread",
        agent_id="aria-support-ai",
        version_id="v1.1",
        simulated_metrics={
            "intent_accuracy": 0.97,          # Improved from 94% -> 97%
            "policy_compliance": 0.998,       # 99.8% compliance (meets >= 99.0%)
            "tool_selection_accuracy": 0.98,
            "rag_groundedness": 0.98
        }
    )
    assert eval_run.passed is True
    assert eval_run.metrics["intent_accuracy"] == 0.97
    assert eval_run.metrics["policy_compliance"] == 0.998

    # Step 8: Upon passing regression tests, manager activates / deploys it
    new_version = AgentLearningService.deploy_candidate(
        db=demo_session,
        organization_id="org-urbanthread",
        candidate_id=cand.id,
        deployed_by="usr-manager"
    )
    assert new_version.status == "ACTIVE"
    assert new_version.version == "v1.1"

    # Step 9: Verify baseline v1.0 was cleanly retired
    v1_0 = demo_session.query(AgentPromptVersion).filter(
        AgentPromptVersion.version == "v1.0"
    ).first()
    assert v1_0.status == "RETIRED"

    # Step 10: Verify roll-back capability
    rolled_back = AgentLearningService.rollback_candidate(
        db=demo_session,
        organization_id="org-urbanthread",
        candidate_id=cand.id,
        actor_id="usr-manager"
    )
    assert rolled_back.version == "v1.0"
    assert rolled_back.status == "ACTIVE"
    assert cand.status == "ROLLED_BACK"
