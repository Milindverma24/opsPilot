"""
Phase 11 — Customer Chat & AI Assistant REST API.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user_optional, get_current_user
from apps.api.app.models.tenant import User, Organization
from apps.api.app.models.ecommerce import CustomerConversation, ConversationMessage
from apps.api.app.models.base import get_utc_now
from apps.api.app.services.customer_ai_service import CustomerAIService


router = APIRouter(prefix="/customer", tags=["Customer AI Assistant"])


class StartConversationRequest(BaseModel):
    channel: str = Field("WEBSITE_CHAT", example="WEBSITE_CHAT")
    customer_id: Optional[str] = None
    organization_slug: Optional[str] = Field("urbanthread", example="urbanthread")


class SendMessageRequest(BaseModel):
    content: str = Field(..., example="Where is my order UT-10482?")


class SubmitFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, example=5)
    feedback: Optional[str] = Field(None, example="Aria helped me track my delayed package quickly!")
    was_helpful: Optional[bool] = Field(True, example=True)


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def start_conversation(
    payload: StartConversationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Starts a customer chat session.
    Works for both authenticated customers and guest shoppers.
    """
    # Determine organization
    org = None
    if current_user and current_user.organization_id:
        org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        org = db.query(Organization).filter(Organization.slug == payload.organization_slug).first()
    if not org:
        org = db.query(Organization).first()

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    cust_id = None
    if current_user and current_user.role and current_user.role.name == "CUSTOMER":
        cust_id = current_user.id
    elif payload.customer_id:
        cust_id = payload.customer_id

    conv = CustomerConversation(
        organization_id=org.id,
        customer_id=cust_id,
        channel=payload.channel,
        status="OPEN",
        context={}
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Initial greeting from Aria
    greeting = (
        "Hello! 👋 I'm Aria, your UrbanThread AI Assistant. "
        "I can help you track orders, manage returns or exchanges, check sizing, or answer any policy questions. "
        "How can I assist you today?"
    )
    initial_msg = ConversationMessage(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type="AI_AGENT",
        sender_id="aria-support-ai",
        message_type="SUGGESTION",
        content=greeting,
        is_untrusted=False,
        msg_metadata={
            "suggested_actions": [
                "Track my order",
                "Return an item",
                "Shipping policy",
                "Find my size"
            ]
        }
    )
    db.add(initial_msg)
    db.commit()

    return {
        "data": {
            "conversation_id": conv.id,
            "channel": conv.channel,
            "status": conv.status,
            "customer_id": conv.customer_id,
            "greeting": greeting,
            "suggested_actions": [
                "Track my order",
                "Return an item",
                "Shipping policy",
                "Find my size"
            ]
        }
    }


@router.get("/conversations")
def list_customer_conversations(
    customer_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Lists conversations for an authenticated customer."""
    target_cust = current_user.id if current_user else customer_id
    if not target_cust:
        return {"data": []}

    convs = db.query(CustomerConversation).filter(
        CustomerConversation.customer_id == target_cust
    ).order_by(CustomerConversation.created_at.desc()).all()

    data = []
    for c in convs:
        last_msg = c.messages[-1].content if c.messages else ""
        data.append({
            "id": c.id,
            "status": c.status,
            "channel": c.channel,
            "last_message": last_msg,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return {"data": data}


@router.get("/conversations/{id}")
def get_conversation_details(
    id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieves conversation thread and message cards."""
    conv = db.query(CustomerConversation).filter(CustomerConversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # If conversation is bound to a customer, enforce customer ownership if authenticated
    if conv.customer_id and current_user and current_user.role and current_user.role.name == "CUSTOMER":
        if conv.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation.")

    messages_data = []
    for m in conv.messages:
        messages_data.append({
            "id": m.id,
            "sender_type": m.sender_type,
            "sender_id": m.sender_id,
            "message_type": m.message_type,
            "content": m.content,
            "metadata": m.msg_metadata,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

    return {
        "data": {
            "id": conv.id,
            "channel": conv.channel,
            "status": conv.status,
            "customer_id": conv.customer_id,
            "rating": conv.rating,
            "messages": messages_data
        }
    }


@router.post("/conversations/{id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    id: str,
    payload: SendMessageRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Sends a message to Aria AI and returns the autonomous response."""
    conv = db.query(CustomerConversation).filter(CustomerConversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    cust_id = conv.customer_id
    if current_user and current_user.role and current_user.role.name == "CUSTOMER":
        cust_id = current_user.id

    client_ip = request.client.host if request.client else "127.0.0.1"

    result = CustomerAIService.process_customer_message(
        db=db,
        organization_id=conv.organization_id,
        conversation_id=conv.id,
        message_text=payload.content,
        authenticated_customer_id=cust_id,
        client_ip=client_ip
    )

    return {"data": result}


@router.post("/conversations/{id}/close")
def close_conversation(
    id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Closes an active customer conversation."""
    conv = db.query(CustomerConversation).filter(CustomerConversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    conv.status = "CLOSED"
    conv.closed_at = get_utc_now()
    db.commit()

    return {"data": {"status": "CLOSED", "closed_at": conv.closed_at.isoformat()}}


@router.post("/conversations/{id}/feedback")
def submit_feedback(
    id: str,
    payload: SubmitFeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Submits customer rating and feedback."""
    conv = db.query(CustomerConversation).filter(CustomerConversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    conv.rating = payload.rating
    conv.feedback = payload.feedback
    conv.was_helpful = payload.was_helpful
    db.commit()

    return {
        "data": {
            "conversation_id": conv.id,
            "rating": conv.rating,
            "feedback": conv.feedback,
            "was_helpful": conv.was_helpful
        }
    }


@router.post("/conversations/{id}/handoff")
def request_handoff(
    id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Directly requests human support handoff."""
    conv = db.query(CustomerConversation).filter(CustomerConversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    result = CustomerAIService._execute_human_handoff(
        db=db,
        organization_id=conv.organization_id,
        conversation=conv,
        reason="Explicit human agent requested via UI button"
    )

    return {"data": result}
