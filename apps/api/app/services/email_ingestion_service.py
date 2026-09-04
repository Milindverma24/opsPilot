import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.document import Email, Document
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.services.document_parser_service import DocumentIngestionService
from apps.api.app.services.security_scanner_service import (
    SecurityScannerService, UNTRUSTED_USER_CONTENT
)
from apps.api.app.events.publisher import BusinessEventPublisher


class EmailConnector:
    """Abstract Email Box Connector Interface."""

    def fetch_messages(self, cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        raise NotImplementedError

    def get_message(self, message_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError


class MockEmailConnector(EmailConnector):
    """Mock Email Connector providing realistic synthetic emails for development."""

    def __init__(self, synthetic_messages: Optional[List[Dict[str, Any]]] = None):
        self.messages = synthetic_messages or []

    def fetch_messages(self, cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        return self.messages, None

    def get_message(self, message_id: str) -> Dict[str, Any]:
        for m in self.messages:
            if m.get("external_message_id") == message_id:
                return m
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found in mock mailbox")

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "provider": "MOCK_EMAIL_GATEWAY", "latency_ms": 12}


class EmailIngestionService:
    """
    Email Ingestion, Idempotent Deduplication, and Attachment Pipeline.
    Guarantees emails and attachments are safely quarantined and scanned.
    """

    @staticmethod
    def ingest_email(
        db: Session,
        organization_id: str,
        sender: str,
        recipient: str,
        subject: str,
        body_text: str,
        external_message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        source: str = "MOCK",
        source_account: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Email:
        # Compute deterministic content hash
        hash_input = f"{sender}|{recipient}|{subject}|{body_text}"
        content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        msg_id = external_message_id or f"msg-{content_hash[:16]}"

        # Deduplication check
        existing = db.query(Email).filter(
            Email.organization_id == organization_id,
            (Email.external_message_id == msg_id) | (Email.content_hash == content_hash)
        ).first()

        if existing:
            return existing

        # Scan for prompt injection & suspicious instructions
        scan_res = SecurityScannerService.scan(body_text, UNTRUSTED_USER_CONTENT)

        email_record = Email(
            organization_id=organization_id,
            external_message_id=msg_id,
            thread_id=thread_id or f"thread-{msg_id[:12]}",
            sender=sender.strip(),
            recipient=recipient.strip(),
            recipients=recipients or [recipient.strip()],
            cc=cc,
            bcc=bcc,
            subject=subject.strip(),
            body_text=body_text,
            body_html=body_html,
            attachments_count=len(attachments) if attachments else 0,
            source=source,
            source_account=source_account or recipient,
            classification_status="SCANNED",
            processing_status="PROCESSED",
            content_hash=content_hash,
            security_classification=scan_res.classification,
            security_flags=scan_res.risk_flags,
            received_at=get_utc_now(),
            processed=True
        )
        db.add(email_record)
        db.commit()
        db.refresh(email_record)

        # Process attachments as independent documents with lineage: Email -> Attachment -> Document
        if attachments:
            for att in attachments:
                att_name = att.get("filename", "attachment.bin")
                att_bytes = att.get("data", b"")
                if att_bytes:
                    DocumentIngestionService.ingest_document(
                        db=db,
                        organization_id=organization_id,
                        filename=att_name,
                        content_bytes=att_bytes,
                        uploaded_by=sender,
                        source_type="EMAIL",
                        source_uri=f"email://{msg_id}/{att_name}",
                        document_type="ATTACHMENT"
                    )

        # Publish business event
        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="EMAIL_INGESTED",
            title=f"Inbound email: {subject}",
            content=body_text[:300],
            metadata={
                "email_id": email_record.id,
                "sender": sender,
                "subject": subject,
                "security_flags": scan_res.risk_flags
            }
        )

        return email_record
