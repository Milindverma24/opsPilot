import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from apps.api.app.models.audit import AuditLog


def simple_text_embedding(text: str, dim: int = 2048) -> List[float]:
    """
    Deterministic dense vector representation with stopword removal.
    """
    stopwords = {"a", "an", "the", "and", "or", "is", "are", "was", "were", "in", "on", "at", "by", "for", "with", "about", "to", "from", "it", "this", "that", "does", "do"}
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in stopwords and len(w) > 2]
    vec = [0.0] * dim
    if not words:
        return vec
    for w in words:
        h = 0
        for ch in w:
            h = (h * 31 + ord(ch)) % dim
        vec[h] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class KnowledgeService:
    @classmethod
    def index_document(cls, organization_id: str, title: str, category: str, content: str, db: Session) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            organization_id=organization_id,
            title=title,
            category=category,
            file_type="text/plain",
            file_size=len(content.encode("utf-8")),
            content=content,
            status="INDEXED"
        )
        db.add(doc)
        db.flush()

        # Chunk text into ~300 character pieces
        chunks = cls._chunk_text(content, chunk_size=300, overlap=50)
        for idx, chunk_text in enumerate(chunks):
            emb = simple_text_embedding(chunk_text)
            chunk = KnowledgeChunk(
                organization_id=organization_id,
                knowledge_document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                token_count=len(chunk_text.split()),
                embedding=emb
            )
            db.add(chunk)

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def search(cls, organization_id: str, query: str, top_k: int = 3, db: Session = None) -> List[Dict[str, Any]]:
        if not db or not query:
            return []

        query_emb = simple_text_embedding(query)
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.organization_id == organization_id).all()

        scored_chunks = []
        for ch in chunks:
            sim = cosine_similarity(query_emb, ch.embedding or [])
            scored_chunks.append({
                "chunk_id": ch.id,
                "document_id": ch.knowledge_document_id,
                "document_title": ch.knowledge_document.title if ch.knowledge_document else "Unknown",
                "category": ch.knowledge_document.category if ch.knowledge_document else "SOP",
                "content": ch.content,
                "score": round(sim, 4)
            })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def answer_policy_question(cls, organization_id: str, question: str, db: Session) -> Dict[str, Any]:
        results = cls.search(organization_id, question, top_k=2, db=db)
        if not results or results[0]["score"] < 0.10:
            return {
                "question": question,
                "answer": "Policy not found. Human review required.",
                "policy_found": False,
                "source": None,
                "relevant_section": None
            }

        top = results[0]
        return {
            "question": question,
            "answer": f"According to {top['document_title']}: {top['content']}",
            "policy_found": True,
            "source": top["document_title"],
            "relevant_section": top["content"],
            "confidence": top["score"]
        }

    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks
