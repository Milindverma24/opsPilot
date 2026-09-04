"""
Phase 13 — Agent Memory Service.
Provides multi-layer memory management with:
- Tenant and customer isolation
- TTL expiration
- Sensitive data & prompt injection filtering
- Memory conflict detection (MEMORY_CONFLICT)
- Safe customer & agent operational memory access
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from apps.api.app.models.learning import CustomerMemory, AgentMemory, WorkflowMemory
from apps.api.app.models.base import get_utc_now
from apps.api.app.services.security.pii_redaction_service import PIIRedactionService
from apps.api.app.services.ai.prompt_injection_scanner import PromptInjectionScanner


class AgentMemoryService:
    """
    Tenant-isolated memory manager for customer preferences and agent operational patterns.
    """

    # -----------------------------------------------------------------------
    # Customer Memory
    # -----------------------------------------------------------------------

    @classmethod
    def store_customer_memory(
        cls,
        db: Session,
        organization_id: str,
        customer_id: str,
        memory_type: str,
        key: str,
        value: Any,
        source: str = "CUSTOMER_CHAT",
        confidence: float = 1.0,
        consent_status: str = "GRANTED",
        ttl_days: Optional[int] = None
    ) -> Tuple[Optional[CustomerMemory], Optional[str]]:
        """
        Stores customer memory with PII sanitization, prompt injection check,
        and conflict detection.
        """
        if consent_status == "REVOKED":
            return None, "Customer has revoked consent for memory persistence."

        # Filter prompt injections in memory values
        str_val = str(value)
        scan = PromptInjectionScanner.scan(str_val)
        if scan.detected:
            return None, f"Security shield: Memory value rejected due to detected {scan.categories[0]} pattern."

        # Sanitize sensitive secrets
        sanitized_value = PIIRedactionService.redact_dict(value) if isinstance(value, (dict, list)) else PIIRedactionService.redact_text(str_val)

        # Check existing memory for conflict
        existing = db.query(CustomerMemory).filter(
            CustomerMemory.organization_id == organization_id,
            CustomerMemory.customer_id == customer_id,
            CustomerMemory.key == key
        ).first()

        now = get_utc_now()
        expires_at = now + timedelta(days=ttl_days) if ttl_days else None

        if existing:
            # Check if value conflicts significantly
            if existing.value != sanitized_value and existing.confidence >= 0.8:
                existing.is_conflicted = True
                existing.value = sanitized_value  # Update with latest, but flag conflict
                existing.confidence = confidence
                existing.updated_at = now
                existing.expires_at = expires_at
                db.commit()
                db.refresh(existing)
                return existing, "MEMORY_CONFLICT: Conflicting memory detected. Value updated and flagged for human review."
            else:
                existing.value = sanitized_value
                existing.confidence = confidence
                existing.updated_at = now
                existing.expires_at = expires_at
                existing.is_conflicted = False
                db.commit()
                db.refresh(existing)
                return existing, None

        mem = CustomerMemory(
            organization_id=organization_id,
            customer_id=customer_id,
            memory_type=memory_type,
            key=key,
            value=sanitized_value,
            source=source,
            confidence=confidence,
            consent_status=consent_status,
            is_conflicted=False,
            expires_at=expires_at
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        return mem, None

    @classmethod
    def get_customer_memories(
        cls,
        db: Session,
        organization_id: str,
        customer_id: str,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves active customer memories, excluding expired records.
        """
        now = get_utc_now()
        query = db.query(CustomerMemory).filter(
            CustomerMemory.organization_id == organization_id,
            CustomerMemory.customer_id == customer_id,
            CustomerMemory.consent_status == "GRANTED",
            or_(CustomerMemory.expires_at == None, CustomerMemory.expires_at > now)
        )

        if memory_type:
            query = query.filter(CustomerMemory.memory_type == memory_type)

        memories = query.all()
        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "key": m.key,
                "value": m.value,
                "source": m.source,
                "confidence": m.confidence,
                "is_conflicted": m.is_conflicted,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "expires_at": m.expires_at.isoformat() if m.expires_at else None
            }
            for m in memories
        ]

    # -----------------------------------------------------------------------
    # Agent Operational Memory
    # -----------------------------------------------------------------------

    @classmethod
    def store_agent_memory(
        cls,
        db: Session,
        organization_id: str,
        agent_id: Optional[str],
        memory_type: str,
        key: str,
        value: Any,
        confidence: float = 1.0
    ) -> AgentMemory:
        existing = db.query(AgentMemory).filter(
            AgentMemory.organization_id == organization_id,
            AgentMemory.memory_type == memory_type,
            AgentMemory.key == key
        ).first()

        now = get_utc_now()
        if existing:
            existing.value = value
            existing.evidence_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.05)
            existing.last_observed_at = now
            db.commit()
            db.refresh(existing)
            return existing

        mem = AgentMemory(
            organization_id=organization_id,
            agent_id=agent_id,
            memory_type=memory_type,
            key=key,
            value=value,
            confidence=confidence,
            evidence_count=1,
            last_observed_at=now
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        return mem

    @classmethod
    def get_agent_memories(
        cls,
        db: Session,
        organization_id: str,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(AgentMemory).filter(
            AgentMemory.organization_id == organization_id
        )
        if memory_type:
            query = query.filter(AgentMemory.memory_type == memory_type)

        memories = query.order_by(AgentMemory.evidence_count.desc()).all()
        return [
            {
                "id": m.id,
                "agent_id": m.agent_id,
                "memory_type": m.memory_type,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence,
                "evidence_count": m.evidence_count,
                "last_observed_at": m.last_observed_at.isoformat() if m.last_observed_at else None
            }
            for m in memories
        ]

    # -----------------------------------------------------------------------
    # Workflow Memory
    # -----------------------------------------------------------------------

    @classmethod
    def record_workflow_execution(
        cls,
        db: Session,
        organization_id: str,
        workflow_name: str,
        success: bool,
        duration_ms: int,
        failure_reason: Optional[str] = None
    ) -> WorkflowMemory:
        wf_mem = db.query(WorkflowMemory).filter(
            WorkflowMemory.organization_id == organization_id,
            WorkflowMemory.workflow_name == workflow_name
        ).first()

        if not wf_mem:
            wf_mem = WorkflowMemory(
                organization_id=organization_id,
                workflow_name=workflow_name,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                escalated_runs=0,
                common_failure_reasons=[],
                avg_duration_ms=0
            )
            db.add(wf_mem)

        wf_mem.total_runs += 1
        if success:
            wf_mem.successful_runs += 1
        else:
            wf_mem.failed_runs += 1
            if failure_reason:
                reasons = list(wf_mem.common_failure_reasons or [])
                found = False
                for r in reasons:
                    if r.get("reason") == failure_reason:
                        r["count"] = r.get("count", 0) + 1
                        found = True
                        break
                if not found:
                    reasons.append({"reason": failure_reason, "count": 1})
                wf_mem.common_failure_reasons = reasons

        # Running average of duration
        wf_mem.avg_duration_ms = int(
            ((wf_mem.avg_duration_ms * (wf_mem.total_runs - 1)) + duration_ms) / wf_mem.total_runs
        )

        db.commit()
        db.refresh(wf_mem)
        return wf_mem
