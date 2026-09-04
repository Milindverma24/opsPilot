"""
Phase 7 — Memory Service.

Provides scoped, auditable short-term conversation context and
long-term customer profile memory.
Strict isolation: Always scoped by organization_id and customer_id.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.agent import AgentRun, AgentMessage
from apps.api.app.models.operations import Customer, Complaint
from apps.api.app.models.ecommerce import Order, CustomerConversation, ConversationMessage, SupportTicket


class MemoryService:
    def get_short_term_context(
        self,
        db: Session,
        organization_id: str,
        conversation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent conversation messages for turn-by-turn context.
        """
        history: List[Dict[str, Any]] = []

        if conversation_id:
            msgs = db.query(ConversationMessage).filter(
                ConversationMessage.organization_id == organization_id,
                ConversationMessage.conversation_id == conversation_id,
            ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()

            for m in reversed(msgs):
                history.append({
                    "role": m.sender_type.lower() if m.sender_type else "user",
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

        elif customer_id:
            # Check recent agent runs for this customer
            runs = db.query(AgentRun).filter(
                AgentRun.organization_id == organization_id,
                AgentRun.actor_id == customer_id,
            ).order_by(AgentRun.created_at.desc()).limit(limit).all()

            for r in reversed(runs):
                user_msg = r.input_data.get("message", "") if isinstance(r.input_data, dict) else ""
                ai_resp = r.decisions[0].get("proposed_response", "") if r.decisions else ""
                if user_msg:
                    history.append({"role": "customer", "content": user_msg})
                if ai_resp:
                    history.append({"role": "assistant", "content": ai_resp})

        return history

    def get_long_term_profile(
        self,
        db: Session,
        organization_id: str,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieves persistent operational profile for customer:
        order history counts, refund history, VIP status, open tickets.
        """
        customer = db.query(Customer).filter(
            Customer.organization_id == organization_id,
            Customer.id == customer_id,
        ).first()

        if not customer:
            return {}

        orders_count = db.query(Order).filter(
            Order.organization_id == organization_id,
            Order.customer_id == customer_id,
        ).count()

        open_tickets_count = db.query(SupportTicket).filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.customer_id == customer_id,
            SupportTicket.status.in_(["OPEN", "IN_PROGRESS"]),
        ).count()

        complaints_count = db.query(Complaint).filter(
            Complaint.organization_id == organization_id,
            Complaint.customer_id == customer_id,
        ).count()

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "total_orders": orders_count,
            "open_tickets": open_tickets_count,
            "total_complaints": complaints_count,
            "is_frequent_shopper": orders_count >= 5,
        }
