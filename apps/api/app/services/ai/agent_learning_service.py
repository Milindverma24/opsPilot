"""
Phase 13 — Agent Learning & Feedback Service.
Orchestrates:
- AgentExperience capture
- Human & customer feedback ingestion
- Curated LearningExample dataset generation
- Fine-tuning JSONL export
- ImprovementCandidate proposal, human approval, versioning, and rollback
"""
import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from apps.api.app.models.learning import (
    AgentExperience,
    AgentFeedback,
    CustomerMessageFeedback,
    LearningExample,
    ImprovementCandidate,
    AgentPromptVersion,
)
from apps.api.app.models.agent import AIEmployee
from apps.api.app.models.base import get_utc_now


class AgentLearningService:
    """
    Controlled improvement pipeline with mandatory human approval.
    AI generates candidate proposals; Humans review, approve, version, and deploy.
    """

    # -----------------------------------------------------------------------
    # 1. Experience Capture
    # -----------------------------------------------------------------------

    @classmethod
    def record_experience(
        cls,
        db: Session,
        organization_id: str,
        agent_id: str,
        trigger_type: str,
        input_summary: str,
        decision_summary: str,
        actions_taken: List[Dict[str, Any]],
        outcome: str = "SUCCESS",
        success: bool = True,
        confidence: float = 1.0,
        risk_level: str = "LOW",
        agent_run_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        human_intervention: bool = False,
        human_correction: Optional[str] = None,
        customer_feedback: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0
    ) -> AgentExperience:
        exp = AgentExperience(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_run_id=agent_run_id,
            workflow_run_id=workflow_run_id,
            trigger_type=trigger_type,
            input_summary=input_summary[:1000] if input_summary else "",
            decision_summary=decision_summary[:1000] if decision_summary else "",
            actions_taken=actions_taken or [],
            outcome=outcome,
            success=success,
            confidence=confidence,
            risk_level=risk_level,
            human_intervention=human_intervention,
            human_correction=human_correction,
            customer_feedback=customer_feedback,
            execution_duration_ms=duration_ms
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    # -----------------------------------------------------------------------
    # 2. Human Feedback & Learning Example Generation
    # -----------------------------------------------------------------------

    @classmethod
    def record_human_feedback(
        cls,
        db: Session,
        organization_id: str,
        agent_id: str,
        reviewer_user_id: str,
        feedback_type: str,
        rating: int,
        correction: Optional[str] = None,
        comment: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_behavior: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None
    ) -> AgentFeedback:
        fb = AgentFeedback(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_run_id=agent_run_id,
            workflow_run_id=workflow_run_id,
            reviewer_user_id=reviewer_user_id,
            feedback_type=feedback_type,
            rating=rating,
            correction=correction,
            comment=comment,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        # If human provided a concrete correction, automatically generate a curated LearningExample
        if correction and expected_behavior:
            le = LearningExample(
                organization_id=organization_id,
                source_type="HUMAN_FEEDBACK",
                source_id=fb.id,
                input=actual_behavior or comment or "User Request",
                expected_output=expected_behavior,
                actual_output=actual_behavior,
                correction=correction,
                category="POLICY_COMPLIANCE" if feedback_type == "POLICY_VIOLATION" else "RESPONSE_GENERATION",
                quality_score=1.0,
                approved=True,  # Verified by human reviewer
                reviewer_id=reviewer_user_id,
                dataset_version="v1.0"
            )
            db.add(le)
            db.commit()

        return fb

    # -----------------------------------------------------------------------
    # 3. Customer Chat Feedback
    # -----------------------------------------------------------------------

    @classmethod
    def record_customer_feedback(
        cls,
        db: Session,
        organization_id: str,
        conversation_id: str,
        rating: int,
        was_helpful: bool = True,
        message_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        comment: Optional[str] = None,
        reason: Optional[str] = None
    ) -> CustomerMessageFeedback:
        fb = CustomerMessageFeedback(
            organization_id=organization_id,
            conversation_id=conversation_id,
            message_id=message_id,
            customer_id=customer_id,
            rating=rating,
            was_helpful=was_helpful,
            comment=comment,
            reason=reason
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb

    # -----------------------------------------------------------------------
    # 4. Dataset Export for Fine-Tuning Preparation (JSONL)
    # -----------------------------------------------------------------------

    @classmethod
    def export_finetuning_dataset_jsonl(
        cls,
        db: Session,
        organization_id: str,
        category: Optional[str] = None,
        only_approved: bool = True
    ) -> str:
        """
        Exports approved learning examples formatted as OpenAI / standard Chat JSONL strings:
        {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
        """
        query = db.query(LearningExample).filter(
            LearningExample.organization_id == organization_id
        )
        if only_approved:
            query = query.filter(LearningExample.approved == True)
        if category:
            query = query.filter(LearningExample.category == category)

        examples = query.all()
        lines = []

        system_instruction = (
            "You are an autonomous AI employee for UrbanThread, a synthetic fashion e-commerce brand. "
            "You strictly follow store policies, never hallucinate discounts, and execute safe business tools."
        )

        for ex in examples:
            row = {
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": ex.input},
                    {"role": "assistant", "content": ex.expected_output or ex.correction or ""}
                ]
            }
            lines.append(json.dumps(row))

        return "\n".join(lines)

    # -----------------------------------------------------------------------
    # 5. Improvement Candidate Management
    # -----------------------------------------------------------------------

    @classmethod
    def generate_candidate(
        cls,
        db: Session,
        organization_id: str,
        agent_id: str,
        candidate_type: str,
        title: str,
        description: str,
        proposed_change: Dict[str, Any],
        evidence: Optional[Dict[str, Any]] = None,
        expected_impact: Optional[str] = None,
        risk: str = "LOW",
        created_by: str = "system-evaluator"
    ) -> ImprovementCandidate:
        """
        Proposes an improvement candidate (e.g. from human corrections).
        Candidate starts in 'GENERATED' status and CANNOT be deployed without Human Approval.
        """
        candidate = ImprovementCandidate(
            organization_id=organization_id,
            agent_id=agent_id,
            candidate_type=candidate_type,
            title=title,
            description=description,
            proposed_change=proposed_change,
            evidence=evidence or {},
            expected_impact=expected_impact,
            risk=risk,
            status="GENERATED",
            created_by=created_by
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def approve_candidate(
        cls,
        db: Session,
        organization_id: str,
        candidate_id: str,
        reviewer_id: str
    ) -> ImprovementCandidate:
        candidate = db.query(ImprovementCandidate).filter(
            ImprovementCandidate.id == candidate_id,
            ImprovementCandidate.organization_id == organization_id
        ).first()

        if not candidate:
            raise ValueError("Improvement candidate not found.")

        candidate.status = "APPROVED"
        candidate.reviewed_by = reviewer_id
        candidate.reviewed_at = get_utc_now()
        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def reject_candidate(
        cls,
        db: Session,
        organization_id: str,
        candidate_id: str,
        reviewer_id: str
    ) -> ImprovementCandidate:
        candidate = db.query(ImprovementCandidate).filter(
            ImprovementCandidate.id == candidate_id,
            ImprovementCandidate.organization_id == organization_id
        ).first()

        if not candidate:
            raise ValueError("Improvement candidate not found.")

        candidate.status = "REJECTED"
        candidate.reviewed_by = reviewer_id
        candidate.reviewed_at = get_utc_now()
        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def deploy_candidate(
        cls,
        db: Session,
        organization_id: str,
        candidate_id: str,
        deployed_by: str
    ) -> AgentPromptVersion:
        """
        Deploys an APPROVED improvement candidate into a new versioned AgentPromptVersion.
        AI is blocked from self-deploying!
        """
        candidate = db.query(ImprovementCandidate).filter(
            ImprovementCandidate.id == candidate_id,
            ImprovementCandidate.organization_id == organization_id
        ).first()

        if not candidate:
            raise ValueError("Candidate not found.")
        if candidate.status != "APPROVED":
            raise ValueError(f"Cannot deploy candidate with status '{candidate.status}'. Must be APPROVED first.")

        # Determine next version string
        latest = db.query(AgentPromptVersion).filter(
            AgentPromptVersion.organization_id == organization_id,
            AgentPromptVersion.agent_id == candidate.agent_id
        ).order_by(AgentPromptVersion.created_at.desc()).first()

        new_version_num = "v1.1"
        if latest and latest.version.startswith("v"):
            try:
                major, minor = latest.version[1:].split(".")
                new_version_num = f"v{major}.{int(minor) + 1}"
            except Exception:
                new_version_num = "v1.2"

        # Create new version
        new_version = AgentPromptVersion(
            organization_id=organization_id,
            agent_id=candidate.agent_id,
            version=new_version_num,
            system_prompt=candidate.proposed_change.get("system_prompt", latest.system_prompt if latest else "UrbanThread AI Employee"),
            behavior_rules=candidate.proposed_change.get("behavior_rules", latest.behavior_rules if latest else []),
            output_schema=candidate.proposed_change.get("output_schema", latest.output_schema if latest else {}),
            model=candidate.proposed_change.get("model", latest.model if latest else "gpt-4o-mini"),
            temperature=candidate.proposed_change.get("temperature", latest.temperature if latest else 0.1),
            configuration=candidate.proposed_change.get("configuration", latest.configuration if latest else {}),
            status="ACTIVE",
            created_by=deployed_by,
            approved_by=deployed_by,
            activated_at=get_utc_now()
        )

        # Retire prior active versions
        db.query(AgentPromptVersion).filter(
            AgentPromptVersion.organization_id == organization_id,
            AgentPromptVersion.agent_id == candidate.agent_id,
            AgentPromptVersion.status == "ACTIVE"
        ).update({"status": "RETIRED"})

        candidate.status = "DEPLOYED"
        candidate.deployed_at = get_utc_now()

        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        return new_version

    @classmethod
    def rollback_candidate(
        cls,
        db: Session,
        organization_id: str,
        candidate_id: str,
        actor_id: str
    ) -> AgentPromptVersion:
        """
        Rolls back a deployed candidate to the previous ACTIVE version.
        """
        candidate = db.query(ImprovementCandidate).filter(
            ImprovementCandidate.id == candidate_id,
            ImprovementCandidate.organization_id == organization_id
        ).first()

        if not candidate:
            raise ValueError("Candidate not found.")

        # Find the previous retired version
        prev_version = db.query(AgentPromptVersion).filter(
            AgentPromptVersion.organization_id == organization_id,
            AgentPromptVersion.agent_id == candidate.agent_id,
            AgentPromptVersion.status == "RETIRED"
        ).order_by(AgentPromptVersion.created_at.desc()).first()

        if not prev_version:
            raise ValueError("No prior version available to rollback to.")

        # Retire currently active
        db.query(AgentPromptVersion).filter(
            AgentPromptVersion.organization_id == organization_id,
            AgentPromptVersion.agent_id == candidate.agent_id,
            AgentPromptVersion.status == "ACTIVE"
        ).update({"status": "RETIRED"})

        prev_version.status = "ACTIVE"
        prev_version.activated_at = get_utc_now()
        candidate.status = "ROLLED_BACK"

        db.commit()
        db.refresh(prev_version)
        return prev_version
