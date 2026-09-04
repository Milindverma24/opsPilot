from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, DateTime, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, get_utc_now


class BusinessEvent(Base, BaseModelMixin):
    __tablename__ = "business_events"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(100), nullable=True, index=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    source = Column(String(50), nullable=False, default="MANUAL_UPLOAD")  # MANUAL_UPLOAD, EMAIL, WEBSITE, WEBHOOK, API
    event_type = Column(String(50), nullable=False, default="OTHER")      # INVOICE, COMPLAINT, ORDER_CREATED, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(String(50), default="RECEIVED", nullable=False)
    attachments = Column(JSON, default=list, nullable=False)
    event_metadata = Column("metadata", JSON, default=dict, nullable=False)
    received_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)

    documents = relationship("Document", back_populates="business_event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_biz_event_org_idemp", "organization_id", "idempotency_key"),
    )


class Document(Base, BaseModelMixin):
    __tablename__ = "documents"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("business_events.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by = Column(String(36), nullable=True)  # User id or email
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)      # in bytes
    checksum = Column(String(64), nullable=False, index=True)  # SHA-256 for idempotency & deduplication
    storage_path = Column(String(512), nullable=False)
    storage_key = Column(String(255), nullable=True)           # Storage abstraction key
    document_type = Column(String(50), nullable=True, default="INVOICE")
    source_type = Column(String(50), default="DOCUMENT", nullable=False)  # WEBSITE, EMAIL, DOCUMENT, API, MANUAL_ENTRY
    source_uri = Column(String(512), nullable=True)
    source_hash = Column(String(64), nullable=True)
    processing_status = Column(String(50), nullable=False, default="UPLOADED")  # UPLOADED, PROCESSING, PROCESSED, FAILED, QUARANTINED
    classification = Column(String(50), nullable=True, index=True)
    classification_confidence = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True, default="LOW")
    security_classification = Column(String(50), default="UNTRUSTED_EXTERNAL_DATA", nullable=False)
    security_flags = Column(JSON, default=list, nullable=False)
    raw_text = Column(Text, nullable=True)
    extracted_fields = Column(JSON, default=dict, nullable=False)
    doc_metadata = Column("metadata", JSON, default=dict, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Synonyms for backwards compatibility
    file_name = synonym("filename")
    file_type = synonym("document_type")
    file_hash = synonym("checksum")
    status = synonym("processing_status")
    confidence = synonym("classification_confidence")

    business_event = relationship("BusinessEvent", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="document")
    complaints = relationship("Complaint", back_populates="document")


class DocumentChunk(Base, BaseModelMixin):
    __tablename__ = "document_chunks"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(JSON, nullable=True)  # Stored as vector representation / JSON list
    chunk_metadata = Column("metadata", JSON, default=dict, nullable=False)

    document = relationship("Document", back_populates="chunks")


class Email(Base, BaseModelMixin):
    __tablename__ = "emails"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    external_message_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    recipients = Column(JSON, default=list, nullable=False)
    cc = Column(String(512), nullable=True)
    bcc = Column(String(512), nullable=True)
    subject = Column(String(512), nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    body = synonym("body_text")
    attachments_count = Column(Integer, default=0, nullable=False)
    source = Column(String(50), default="MOCK", nullable=False)
    source_account = Column(String(255), nullable=True)
    classification_status = Column(String(50), default="UNCLASSIFIED", nullable=False)
    processing_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, SYNCING, SYNCED, PROCESSED, FAILED
    content_hash = Column(String(64), nullable=True, index=True)
    security_classification = Column(String(50), default="UNTRUSTED_USER_CONTENT", nullable=False)
    security_flags = Column(JSON, default=list, nullable=False)
    received_at = Column(DateTime, default=get_utc_now, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)


class ImportJob(Base, BaseModelMixin):
    __tablename__ = "import_jobs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), default="CSV", nullable=False)     # CSV, JSON, API
    entity_type = Column(String(50), nullable=False)                    # customers, products, inventory, orders, vendors, purchase_orders
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)      # PENDING, PROCESSING, COMPLETED, PARTIALLY_COMPLETED, FAILED, CANCELLED
    total_records = Column(Integer, default=0, nullable=False)
    successful_records = Column(Integer, default=0, nullable=False)
    failed_records = Column(Integer, default=0, nullable=False)
    error_report = Column(JSON, default=list, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
