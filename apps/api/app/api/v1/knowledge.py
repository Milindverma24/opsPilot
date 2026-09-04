from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.knowledge import KnowledgeDocument
from apps.api.app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])


class KnowledgeUploadRequest(BaseModel):
    title: str
    category: str = "SOP"
    content: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class QuestionRequest(BaseModel):
    question: str


@router.get("")
def list_knowledge_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == current_user.organization_id
    ).order_by(KnowledgeDocument.created_at.desc()).all()

    results = []
    for d in docs:
        results.append({
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "file_size": d.file_size,
            "status": d.status,
            "chunks_count": len(d.chunks),
            "content_preview": d.content[:200] + "..." if len(d.content) > 200 else d.content,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })

    # Default demo knowledge document if empty
    if not results:
        results = [
            {
                "id": "kb-seed-01",
                "title": "Corporate Finance Disbursement SOP",
                "category": "FINANCE_POLICY",
                "file_size": 2400,
                "status": "INDEXED",
                "chunks_count": 8,
                "content_preview": "Section 4.1: Any purchase invoice exceeding INR 100,000 must be reviewed and digitally approved by the Finance Manager prior to mock payment release...",
                "created_at": "2026-02-15T09:00:00Z"
            }
        ]

    return {"documents": results, "total": len(results)}


@router.post("/upload")
def upload_knowledge_document(
    payload: KnowledgeUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = KnowledgeService.index_document(
        organization_id=current_user.organization_id,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        db=db
    )
    return {
        "id": doc.id,
        "title": doc.title,
        "chunks_created": len(doc.chunks),
        "status": doc.status,
        "message": f"Document '{doc.title}' indexed into pgvector / semantic knowledge store."
    }


@router.post("/search")
def search_knowledge(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = KnowledgeService.search(
        organization_id=current_user.organization_id,
        query=payload.query,
        top_k=payload.top_k,
        db=db
    )
    return {"query": payload.query, "results": results}


@router.post("/ask")
def ask_policy_rag(
    payload: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ans = KnowledgeService.answer_policy_question(
        organization_id=current_user.organization_id,
        question=payload.question,
        db=db
    )
    return ans
