from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.document import BusinessEvent
from apps.api.app.workflows.engine import WorkflowEngine

router = APIRouter(prefix="/events", tags=["Operations Inbox"])


class EventCreateRequest(BaseModel):
    title: str
    content: str
    source: str = "MANUAL_UPLOAD"  # MANUAL_UPLOAD, EMAIL, WEBHOOK, API
    event_type: str = "OTHER"
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("")
def list_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(BusinessEvent).filter(BusinessEvent.organization_id == current_user.organization_id)
    if event_type:
        query = query.filter(BusinessEvent.event_type == event_type)
    if source:
        query = query.filter(BusinessEvent.source == source)
    if search:
        query = query.filter(BusinessEvent.title.ilike(f"%{search}%"))

    events = query.order_by(BusinessEvent.received_at.desc()).limit(limit).all()

    # Format into rich inbox representation
    results = []
    for ev in events:
        results.append({
            "id": ev.id,
            "title": ev.title,
            "event_type": ev.event_type,
            "source": ev.source,
            "received_at": ev.received_at.isoformat() if ev.received_at else None,
            "content_preview": (ev.content[:160] + "...") if ev.content else "",
            "metadata": ev.event_metadata or {}
        })

    # If empty, provide seeded demonstration event list
    if not results:
        results = [
            {
                "id": "ev-seed-01",
                "title": "Invoice INV-2026-001 from ABC Industrial Supplies",
                "event_type": "INVOICE",
                "source": "EMAIL",
                "received_at": "2026-02-28T08:30:00Z",
                "content_preview": "Invoice for safety helmets and neoprene gloves against PO-2026-001. Amount: ₹99,710.",
                "priority": "P2",
                "risk": "LOW",
                "confidence": 0.98,
                "status": "COMPLETED"
            },
            {
                "id": "ev-seed-02",
                "title": "Urgent Customer Complaint: Missing Order ORD-99214",
                "event_type": "COMPLAINT",
                "source": "EMAIL",
                "received_at": "2026-02-28T09:15:00Z",
                "content_preview": "This is the third time I have contacted you. Order still not arrived. Immediate refund demanded.",
                "priority": "P1",
                "risk": "HIGH",
                "confidence": 0.97,
                "status": "WAITING_APPROVAL"
            },
            {
                "id": "ev-seed-03",
                "title": "Quarterly Compute Statement INV-2026-002",
                "event_type": "INVOICE",
                "source": "API",
                "received_at": "2026-02-28T10:00:00Z",
                "content_preview": "Dedicated compute cluster Q1 billing. Total: ₹147,500. Exceeds standard approval threshold.",
                "priority": "P2",
                "risk": "HIGH",
                "confidence": 0.95,
                "status": "WAITING_APPROVAL"
            }
        ]

    return {"events": results, "total": len(results)}


@router.post("")
def ingest_event(
    payload: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ev = BusinessEvent(
        organization_id=current_user.organization_id,
        source=payload.source,
        event_type=payload.event_type,
        title=payload.title,
        content=payload.content,
        event_metadata=payload.metadata
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # Trigger autonomous workflow engine
    engine = WorkflowEngine(db)
    wf = engine.start_workflow(
        organization_id=current_user.organization_id,
        title=payload.title,
        content=payload.content,
        source=payload.source
    )

    return {
        "event_id": ev.id,
        "workflow_id": wf.id,
        "status": wf.status,
        "message": f"Event received and workflow {wf.status}"
    }
