from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.ecommerce import SupportTicket, CustomerConversation, ConversationMessage
from apps.api.app.services.support_service import SupportService
from apps.api.app.services.tenant_service import TenantService

router = APIRouter(prefix="/support", tags=["Support & Customer Care"])


class CreateTicketRequest(BaseModel):
    customer_id: str
    subject: str = Field(..., example="Where is my order? Delivery delayed")
    description: str = Field(..., example="Tracking says delayed in transit. Need this before Friday.")
    order_id: Optional[str] = None
    priority: str = Field("MEDIUM", example="HIGH")


class AddMessageRequest(BaseModel):
    sender_type: str = Field("CUSTOMER", example="CUSTOMER")  # CUSTOMER, EMPLOYEE, AI_AGENT
    content: str = Field(..., example="Please check the current delivery ETA")
    sender_id: Optional[str] = None


@router.get("/tickets")
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = SupportService.list_tickets(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status,
        priority_filter=priority
    )
    data = []
    for t in items:
        data.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "customer_id": t.customer_id,
            "customer_name": t.customer.name if t.customer else "Unknown",
            "order_id": t.order_id,
            "order_number": t.order.order_number if hasattr(t, "order") and t.order else None,
            "subject": t.subject,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = SupportService.create_ticket(
        db=db,
        organization_id=current_user.organization_id,
        customer_id=payload.customer_id,
        subject=payload.subject,
        description=payload.description,
        order_id=payload.order_id,
        priority=payload.priority
    )
    return {"data": {"id": ticket.id, "ticket_number": ticket.ticket_number, "priority": ticket.priority}}


@router.get("/conversations")
def list_support_conversations(
    status: Optional[str] = Query(None, example="WAITING_FOR_HUMAN"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists customer conversations for human agent support inbox."""
    query = db.query(CustomerConversation).filter(
        CustomerConversation.organization_id == current_user.organization_id
    )
    if status:
        query = query.filter(CustomerConversation.status == status.upper())

    convs = query.order_by(CustomerConversation.updated_at.desc()).all()
    data = []
    for c in convs:
        last_msg = c.messages[-1].content if c.messages else ""
        data.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "customer_name": c.customer.name if c.customer else "Guest Shopper",
            "channel": c.channel,
            "status": c.status,
            "assigned_agent_id": c.assigned_agent_id,
            "last_message": last_msg,
            "messages_count": len(c.messages),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
    return {"data": data}


@router.get("/conversations/{customer_id}")
def get_customer_conversation(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = SupportService.get_or_create_conversation(db, current_user.organization_id, customer_id)
    messages_data = []
    for m in conv.messages:
        messages_data.append({
            "id": m.id,
            "sender_type": m.sender_type,
            "sender_id": m.sender_id,
            "content": m.content,
            "is_untrusted": m.is_untrusted,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return {
        "data": {
            "conversation_id": conv.id,
            "customer_id": conv.customer_id,
            "channel": conv.channel,
            "status": conv.status,
            "messages": messages_data
        }
    }


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    conversation_id: str,
    payload: AddMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = SupportService.add_conversation_message(
        db=db,
        organization_id=current_user.organization_id,
        conversation_id=conversation_id,
        sender_type=payload.sender_type,
        content=payload.content,
        sender_id=payload.sender_id or current_user.id
    )
    return {
        "data": {
            "id": msg.id,
            "sender_type": msg.sender_type,
            "content": msg.content,
            "is_untrusted": msg.is_untrusted
        }
    }


class AssignConversationRequest(BaseModel):
    user_id: str = Field(..., example="usr_123")


class TakeoverConversationRequest(BaseModel):
    message: str = Field(..., example="Hello, I am taking over this ticket to assist you directly.")


@router.post("/conversations/{id}/assign")
def assign_conversation(
    id: str,
    payload: AssignConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assigns conversation to a specific human employee."""
    conv = db.query(CustomerConversation).filter(
        CustomerConversation.id == id,
        CustomerConversation.organization_id == current_user.organization_id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    conv.assigned_agent_id = payload.user_id
    db.commit()
    return {"data": {"id": conv.id, "assigned_agent_id": conv.assigned_agent_id}}


@router.post("/conversations/{id}/takeover")
def takeover_conversation(
    id: str,
    payload: TakeoverConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Human support employee takes over conversation and posts message to customer."""
    conv = db.query(CustomerConversation).filter(
        CustomerConversation.id == id,
        CustomerConversation.organization_id == current_user.organization_id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    conv.assigned_agent_id = current_user.id
    conv.status = "OPEN"

    msg = ConversationMessage(
        organization_id=current_user.organization_id,
        conversation_id=conv.id,
        sender_type="HUMAN_AGENT",
        sender_id=current_user.id,
        message_type="TEXT",
        content=payload.message,
        is_untrusted=False,
        msg_metadata={"agent_name": current_user.full_name if hasattr(current_user, "full_name") else "Human Support"}
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"data": {"id": msg.id, "content": msg.content, "sender_type": msg.sender_type}}


@router.post("/tickets/{id}/resolve")
def resolve_ticket(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolves a customer support ticket."""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == id,
        SupportTicket.organization_id == current_user.organization_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    ticket.status = "RESOLVED"
    db.commit()
    return {"data": {"id": ticket.id, "status": "RESOLVED"}}


