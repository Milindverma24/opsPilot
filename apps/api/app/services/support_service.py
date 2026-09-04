from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.ecommerce import (
    SupportTicket, CustomerConversation, ConversationMessage
)
from apps.api.app.models.operations import Customer
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher


class SupportService:
    """
    Customer Care & Support Ticket Service.
    Handles ticket triage, priority escalation, and conversation messaging
    with untrusted content tagging for prompt injection security.
    """

    @staticmethod
    def create_ticket(
        db: Session,
        organization_id: str,
        customer_id: str,
        subject: str,
        description: str,
        order_id: Optional[str] = None,
        priority: str = "MEDIUM",
        assigned_team_id: Optional[str] = None,
        assigned_user_id: Optional[str] = None
    ) -> SupportTicket:
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id
        ).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        tkt_num = f"TKT-{generate_uuid()[:8].upper()}"
        ticket = SupportTicket(
            organization_id=organization_id,
            customer_id=customer_id,
            order_id=order_id,
            ticket_number=tkt_num,
            subject=subject.strip(),
            description=description.strip(),
            priority=priority.upper(),
            status="OPEN",
            assigned_team_id=assigned_team_id,
            assigned_user_id=assigned_user_id
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        # Audit & Event
        audit = AuditLog(
            organization_id=organization_id,
            actor_id=customer_id,
            actor_type="CUSTOMER",
            actor_name=customer.name,
            action="SUPPORT_TICKET_CREATED",
            resource_type="support_ticket",
            resource_id=ticket.id,
            result="SUCCESS",
            log_metadata={"ticket_number": tkt_num, "priority": priority, "subject": subject}
        )
        db.add(audit)
        db.commit()

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="SUPPORT_TICKET_CREATED",
            title=f"Support Ticket {tkt_num} [{priority}]: {subject}",
            content=description[:300],
            metadata={"ticket_id": ticket.id, "customer_id": customer_id, "priority": priority}
        )

        return ticket

    @staticmethod
    def get_or_create_conversation(
        db: Session,
        organization_id: str,
        customer_id: str,
        channel: str = "WEBSITE"
    ) -> CustomerConversation:
        conv = db.query(CustomerConversation).filter(
            CustomerConversation.organization_id == organization_id,
            CustomerConversation.customer_id == customer_id,
            CustomerConversation.status == "OPEN"
        ).first()

        if not conv:
            conv = CustomerConversation(
                organization_id=organization_id,
                customer_id=customer_id,
                channel=channel.upper(),
                status="OPEN"
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        return conv

    @staticmethod
    def add_conversation_message(
        db: Session,
        organization_id: str,
        conversation_id: str,
        sender_type: str,
        content: str,
        sender_id: Optional[str] = None
    ) -> ConversationMessage:
        conv = db.query(CustomerConversation).filter(
            CustomerConversation.id == conversation_id,
            CustomerConversation.organization_id == organization_id
        ).first()

        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

        is_untrusted = (sender_type.upper() == "CUSTOMER")

        msg = ConversationMessage(
            organization_id=organization_id,
            conversation_id=conv.id,
            sender_type=sender_type.upper(),
            sender_id=sender_id,
            content=content.strip(),
            is_untrusted=is_untrusted
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        return msg

    @staticmethod
    def list_tickets(
        db: Session,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None
    ) -> Tuple[List[SupportTicket], int]:
        query = db.query(SupportTicket).filter(SupportTicket.organization_id == organization_id)
        if status_filter:
            query = query.filter(SupportTicket.status == status_filter.upper())
        if priority_filter:
            query = query.filter(SupportTicket.priority == priority_filter.upper())

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        items = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total
