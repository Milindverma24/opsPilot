from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.document import Document, DocumentChunk


class DocumentService:
    @staticmethod
    def create_document(
        db: Session,
        organization_id: str,
        filename: str,
        file_size: int,
        checksum: str,
        storage_path: str,
        uploaded_by: Optional[str] = None,
        mime_type: Optional[str] = None,
        document_type: str = "INVOICE",
        processing_status: str = "UPLOADED",
        raw_text: Optional[str] = None,
        extracted_fields: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        doc = Document(
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            filename=filename,
            original_filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            storage_path=storage_path,
            document_type=document_type,
            processing_status=processing_status,
            raw_text=raw_text,
            extracted_fields=extracted_fields or {},
            doc_metadata=metadata or {}
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_by_id(db: Session, document_id: str, organization_id: str) -> Optional[Document]:
        return db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()

    @staticmethod
    def list_documents(db: Session, organization_id: str, limit: int = 100) -> List[Document]:
        return db.query(Document).filter(
            Document.organization_id == organization_id
        ).order_by(Document.created_at.desc()).limit(limit).all()

    @staticmethod
    def save_chunk(
        db: Session,
        document_id: str,
        organization_id: str,
        chunk_index: int,
        content: str,
        token_count: int = 0,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            organization_id=organization_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            embedding=embedding,
            chunk_metadata=metadata or {}
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
