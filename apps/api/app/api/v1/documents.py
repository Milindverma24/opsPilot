from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.document import Document, DocumentChunk
from apps.api.app.services.document_parser_service import DocumentIngestionService
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/documents", tags=["Documents & Files"])


@router.get("")
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(Document.organization_id == current_user.organization_id)
    if status:
        query = query.filter(Document.processing_status == status.upper())
    if document_type:
        query = query.filter(Document.document_type == document_type.upper())
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))

    total = query.count()
    offset = max(0, (page - 1) * page_size)
    items = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for d in items:
        data.append({
            "id": d.id,
            "filename": d.filename,
            "document_type": d.document_type,
            "mime_type": d.mime_type,
            "file_size": d.file_size,
            "checksum": d.checksum,
            "processing_status": d.processing_status,
            "security_classification": d.security_classification,
            "security_flags": d.security_flags,
            "risk_level": d.risk_level,
            "chunks_count": len(d.chunks),
            "created_at": d.created_at.isoformat() if d.created_at else None
        })

    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("POLICY"),
    current_user: User = Depends(require_permission("documents.upload")),
    db: Session = Depends(get_db)
):
    """Upload and asynchronously process a business document (PDF, DOCX, XLSX, CSV, TXT, EML)."""
    content = await file.read()
    doc = DocumentIngestionService.ingest_document(
        db=db,
        organization_id=current_user.organization_id,
        filename=file.filename or "upload.bin",
        content_bytes=content,
        uploaded_by=current_user.id,
        document_type=document_type.upper()
    )
    return {
        "data": {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.processing_status,
            "chunks_count": len(doc.chunks)
        },
        "meta": {"message": f"Document '{doc.filename}' processed successfully."}
    }


@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    TenantService.verify_resource_ownership(doc, current_user, db, "document")

    chunks_data = []
    for c in doc.chunks:
        chunks_data.append({
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "section": c.section,
            "content": c.content,
            "metadata": c.chunk_metadata
        })

    return {
        "data": {
            "id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "mime_type": doc.mime_type,
            "file_size": doc.file_size,
            "checksum": doc.checksum,
            "source_type": doc.source_type,
            "source_uri": doc.source_uri,
            "processing_status": doc.processing_status,
            "security_classification": doc.security_classification,
            "security_flags": doc.security_flags,
            "risk_level": doc.risk_level,
            "raw_text": doc.raw_text,
            "extracted_fields": doc.extracted_fields,
            "chunks": chunks_data,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
    }
