from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.document import Email
from apps.api.app.services.email_ingestion_service import EmailIngestionService, MockEmailConnector
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/emails", tags=["Emails & Communications"])


class IngestEmailRequest(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    external_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    source: str = "INBOUND_API"


@router.get("")
def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Email).filter(Email.organization_id == current_user.organization_id)
    if search:
        query = query.filter(Email.subject.ilike(f"%{search}%") | Email.sender.ilike(f"%{search}%"))

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(Email.received_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for e in items:
        data.append({
            "id": e.id,
            "external_message_id": e.external_message_id,
            "sender": e.sender,
            "recipient": e.recipient,
            "subject": e.subject,
            "attachments_count": e.attachments_count,
            "processing_status": e.processing_status,
            "security_classification": e.security_classification,
            "security_flags": e.security_flags,
            "received_at": e.received_at.isoformat() if e.received_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.get("/{email_id}")
def get_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    em = db.query(Email).filter(
        Email.id == email_id,
        Email.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(em, current_user, db, "email")

    return {
        "data": {
            "id": em.id,
            "external_message_id": em.external_message_id,
            "thread_id": em.thread_id,
            "sender": em.sender,
            "recipient": em.recipient,
            "recipients": em.recipients,
            "subject": em.subject,
            "body_text": em.body_text,
            "attachments_count": em.attachments_count,
            "security_classification": em.security_classification,
            "security_flags": em.security_flags,
            "received_at": em.received_at.isoformat() if em.received_at else None
        }
    }


@router.post("/inbound", status_code=status.HTTP_201_CREATED)
def ingest_email(
    payload: IngestEmailRequest,
    current_user: User = Depends(require_permission("emails.manage")),
    db: Session = Depends(get_db)
):
    """Direct inbound email webhook ingestion endpoint."""
    em = EmailIngestionService.ingest_email(
        db=db,
        organization_id=current_user.organization_id,
        sender=payload.sender,
        recipient=payload.recipient,
        subject=payload.subject,
        body_text=payload.body,
        external_message_id=payload.external_message_id,
        thread_id=payload.thread_id,
        source=payload.source
    )
    return {
        "data": {
            "id": em.id,
            "subject": em.subject,
            "security_flags": em.security_flags,
            "classification": em.security_classification
        },
        "meta": {"message": "Email ingested successfully."}
    }


@router.post("/test-connector")
def test_email_connector(
    current_user: User = Depends(require_permission("emails.manage")),
):
    connector = MockEmailConnector()
    return connector.health_check()
