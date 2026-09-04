from datetime import date
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Boolean, Date
from sqlalchemy.orm import relationship
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin


class KnowledgeDocument(Base, BaseModelMixin):
    __tablename__ = "knowledge_documents"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default="SOP")  # POLICY, SOP, GUIDELINE, MANUAL, FAQ, COMPLIANCE, PRODUCT, HR, FINANCE, SUPPORT, OPERATIONS
    version = Column(String(20), default="1.0", nullable=False)
    approved = Column(Boolean, default=True, nullable=False)
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    source = Column(String(255), nullable=True, default="INTERNAL_POLICY")
    content = Column(Text, nullable=False)
    status = Column(String(50), default="INDEXED", nullable=False)
    file_type = Column(String(50), default="text/plain", nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    doc_metadata = Column("metadata", JSON, default=dict, nullable=False)

    chunks = relationship("KnowledgeChunk", back_populates="knowledge_document", cascade="all, delete-orphan")


class KnowledgeChunk(Base, BaseModelMixin):
    __tablename__ = "knowledge_chunks"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # List of vector floats for pgvector/cosine similarity
    token_count = Column(Integer, default=0, nullable=False)
    chunk_metadata = Column("metadata", JSON, default=dict, nullable=False)

    knowledge_document = relationship("KnowledgeDocument", back_populates="chunks")
