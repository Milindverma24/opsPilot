"""
Phase 13 — Memory REST API.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.learning import CustomerMemory, AgentMemory
from apps.api.app.services.ai.agent_memory_service import AgentMemoryService


router = APIRouter(prefix="/memory", tags=["AI Memory"])


class StoreMemoryRequest(BaseModel):
    target: str = Field("CUSTOMER", example="CUSTOMER")  # CUSTOMER or AGENT
    customer_id: Optional[str] = Field(None, example="cust-001")
    agent_id: Optional[str] = Field(None, example="aria-support-ai")
    memory_type: str = Field(..., example="PREFERENCE")
    key: str = Field(..., example="preferred_fabric")
    value: Any = Field(..., example="Cotton and Linen")
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    ttl_days: Optional[int] = Field(None, example=90)


@router.post("", status_code=status.HTTP_201_CREATED)
def store_memory(
    payload: StoreMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stores a customer or operational agent memory record with sanitization."""
    if payload.target.upper() == "CUSTOMER":
        if not payload.customer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="customer_id is required for CUSTOMER memory.")
        mem, err = AgentMemoryService.store_customer_memory(
            db=db,
            organization_id=current_user.organization_id,
            customer_id=payload.customer_id,
            memory_type=payload.memory_type,
            key=payload.key,
            value=payload.value,
            confidence=payload.confidence or 1.0,
            ttl_days=payload.ttl_days
        )
        if not mem:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err or "Failed to store memory.")
        return {
            "data": {
                "id": mem.id,
                "key": mem.key,
                "is_conflicted": mem.is_conflicted,
                "warning": err
            }
        }
    else:
        mem = AgentMemoryService.store_agent_memory(
            db=db,
            organization_id=current_user.organization_id,
            agent_id=payload.agent_id,
            memory_type=payload.memory_type,
            key=payload.key,
            value=payload.value,
            confidence=payload.confidence or 1.0
        )
        return {"data": {"id": mem.id, "key": mem.key, "evidence_count": mem.evidence_count}}


@router.get("")
def list_memories(
    target: str = Query("CUSTOMER", regex="^(CUSTOMER|AGENT|WORKFLOW)$"),
    customer_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves active memories for the tenant."""
    if target == "CUSTOMER":
        if not customer_id:
            # Return all customer memories for org
            mems = db.query(CustomerMemory).filter(
                CustomerMemory.organization_id == current_user.organization_id
            ).all()
            return {
                "data": [
                    {
                        "id": m.id,
                        "customer_id": m.customer_id,
                        "memory_type": m.memory_type,
                        "key": m.key,
                        "value": m.value,
                        "confidence": m.confidence,
                        "is_conflicted": m.is_conflicted,
                        "expires_at": m.expires_at.isoformat() if m.expires_at else None
                    }
                    for m in mems
                ]
            }
        mems = AgentMemoryService.get_customer_memories(
            db=db,
            organization_id=current_user.organization_id,
            customer_id=customer_id,
            memory_type=memory_type
        )
        return {"data": mems}
    else:
        mems = AgentMemoryService.get_agent_memories(
            db=db,
            organization_id=current_user.organization_id,
            memory_type=memory_type
        )
        return {"data": mems}


@router.delete("/{id}")
def delete_memory(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes or invalidates a memory record."""
    cust_mem = db.query(CustomerMemory).filter(
        CustomerMemory.id == id,
        CustomerMemory.organization_id == current_user.organization_id
    ).first()
    if cust_mem:
        db.delete(cust_mem)
        db.commit()
        return {"data": {"id": id, "deleted": True}}

    agent_mem = db.query(AgentMemory).filter(
        AgentMemory.id == id,
        AgentMemory.organization_id == current_user.organization_id
    ).first()
    if agent_mem:
        db.delete(agent_mem)
        db.commit()
        return {"data": {"id": id, "deleted": True}}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
