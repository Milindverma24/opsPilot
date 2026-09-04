from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from apps.api.app.models.document import BusinessEvent
from apps.api.app.models.audit import AuditLog
from apps.api.app.models.base import get_utc_now, generate_uuid


class BusinessEventPublisher:
    """
    Durable Business Event Publisher for OpsPilot.
    Persists business events to the relational store and creates audit trail records.
    Designed for future ingestion by Celery, Redis, or autonomous AI workers.
    """

    @staticmethod
    def publish(
        db: Session,
        organization_id: str,
        event_type: str,
        title: str,
        content: Optional[str] = None,
        source: str = "BUSINESS_CORE",
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        actor_id: str = "system",
        actor_type: str = "SYSTEM",
        actor_name: str = "OpsPilot Core"
    ) -> BusinessEvent:
        event = BusinessEvent(
            organization_id=organization_id,
            event_id=f"EVT-{generate_uuid()[:8].upper()}",
            idempotency_key=idempotency_key or f"{event_type}_{generate_uuid()}",
            source=source,
            event_type=event_type,
            title=title,
            content=content,
            status="PUBLISHED",
            event_metadata=metadata or {},
            received_at=get_utc_now()
        )
        db.add(event)

        # Audit log for event emission
        audit = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_name=actor_name,
            action=event_type,
            resource_type="business_event",
            resource_id=event.id,
            result="SUCCESS",
            log_metadata=metadata or {}
        )
        db.add(audit)
        db.commit()
        db.refresh(event)

        return event
