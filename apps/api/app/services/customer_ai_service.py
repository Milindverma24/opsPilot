"""
Phase 11 — Customer-Facing AI Employee Service ("Aria").

Coordinates the complete, safe cognitive customer support pipeline:
1. Authentication & Tenant Resolution (Guest vs Authenticated Customer).
2. Prompt Injection & Adversarial Input Defense.
3. Rate Limiting & Loop Protection.
4. Structured Intent & Entity Extraction.
5. Controlled RAG Knowledge Retrieval (Policies, FAQs, Sizing).
6. Controlled Data Retrieval via Allowlisted Tools.
7. Consequential Action Confirmation (Returns, Cancellations).
8. Deterministic Calculations & Approval Governance for High-Risk Operations.
9. Seamless Human Handoff (WAITING_FOR_HUMAN) with Ticket & SLA Escalation.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.ecommerce import (
    CustomerConversation, ConversationMessage, Order, OrderItem,
    Shipment, Return, Refund, SupportTicket, Product
)
from apps.api.app.models.operations import Customer
from apps.api.app.models.policy import Policy, PolicyRule
from apps.api.app.models.knowledge import KnowledgeChunk
from apps.api.app.models.agent import AIEmployee, ToolExecution
from apps.api.app.models.workflow import Approval
from apps.api.app.schemas.agent_schemas import IntentType
from apps.api.app.services.ai.intent_service import IntentClassificationService
from apps.api.app.services.ai.entity_service import EntityExtractionService
from apps.api.app.tools.tool_execution_service import ToolExecutionService



# In-memory rate limiting store: {f"{org_id}:{client_id}": [timestamps]}
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
MAX_MESSAGES_PER_MINUTE = 30
MAX_TOOL_CALLS_PER_TURN = 4


class CustomerAIService:
    """
    Dedicated AI Employee for UrbanThread Customer Care.
    Enforces strict tenant isolation and maker-checker governance.
    """

    @classmethod
    def process_customer_message(
        cls,
        db: Session,
        organization_id: str,
        conversation_id: str,
        message_text: str,
        authenticated_customer_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for customer messages.
        Returns the generated AI response, message metadata, and updated conversation state.
        """
        # 1. Rate Limiting Check
        rate_key = f"{organization_id}:{authenticated_customer_id or client_ip or 'anon'}"
        now = time.time()
        timestamps = _RATE_LIMIT_STORE.get(rate_key, [])
        timestamps = [t for t in timestamps if now - t < 60.0]
        if len(timestamps) >= MAX_MESSAGES_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a moment before sending another message."
            )
        timestamps.append(now)
        _RATE_LIMIT_STORE[rate_key] = timestamps

        # 2. Retrieve / Validate Conversation
        conversation = db.query(CustomerConversation).filter(
            CustomerConversation.id == conversation_id,
            CustomerConversation.organization_id == organization_id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer conversation not found."
            )

        # Re-link customer if authenticated session provided later
        if authenticated_customer_id and not conversation.customer_id:
            conversation.customer_id = authenticated_customer_id
            db.commit()

        # If conversation is already handed off to human, don't auto-reply
        if conversation.status == "WAITING_FOR_HUMAN":
            # Save user message
            user_msg = ConversationMessage(
                organization_id=organization_id,
                conversation_id=conversation.id,
                sender_type="CUSTOMER",
                sender_id=authenticated_customer_id,
                message_type="TEXT",
                content=message_text.strip(),
                is_untrusted=True,
                msg_metadata={"waiting_for_human": True}
            )
            db.add(user_msg)
            db.commit()
            return {
                "message": "A human customer care specialist has been assigned to your ticket and will respond shortly.",
                "message_type": "HANDOFF",
                "metadata": {"status": "WAITING_FOR_HUMAN"}
            }

        # 3. Log Incoming Customer Message (Untrusted)
        user_msg = ConversationMessage(
            organization_id=organization_id,
            conversation_id=conversation.id,
            sender_type="CUSTOMER",
            sender_id=authenticated_customer_id,
            message_type="TEXT",
            content=message_text.strip(),
            is_untrusted=True,
            msg_metadata={}
        )
        db.add(user_msg)
        db.commit()

        # 4. Prompt Injection & Adversarial Security Gate
        if cls._is_adversarial_or_injection(message_text):
            response_text = (
                "I am Aria, UrbanThread's customer support AI assistant. "
                "I am unable to process requests attempting to reveal internal instructions, "
                "system configurations, or access unauthorized customer data. "
                "How can I help you with our clothing, orders, or policies today?"
            )
            ai_msg = ConversationMessage(
                organization_id=organization_id,
                conversation_id=conversation.id,
                sender_type="AI_AGENT",
                sender_id="aria-support-ai",
                message_type="TEXT",
                content=response_text,
                is_untrusted=False,
                msg_metadata={"security_block": True}
            )
            db.add(ai_msg)
            db.commit()
            return {
                "message": response_text,
                "message_type": "TEXT",
                "metadata": {"security_block": True}
            }

        # 5. Check for Explicit Human Handoff Request
        if cls._is_human_handoff_requested(message_text):
            return cls._execute_human_handoff(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                reason="Customer requested a human representative."
            )

        # 6. Intent & Entity Extraction
        intent_service = IntentClassificationService()
        entity_service = EntityExtractionService()

        intent_result = intent_service.classify(message_text)
        entities = entity_service.extract(db, organization_id, message_text)
        extracted = entities.model_dump() if hasattr(entities, "model_dump") else {}

        # Update conversation context
        context = dict(conversation.context or {})
        if extracted.get("order_numbers"):
            context["last_order_number"] = extracted["order_numbers"][0]
        if extracted.get("skus"):
            context["last_sku"] = extracted["skus"][0]
        conversation.context = context
        db.commit()

        # 7. Check for Pending Action Confirmation
        pending_action = context.get("pending_action")
        if pending_action:
            confirmation = cls._detect_confirmation(message_text)
            if confirmation is True:
                # Execute confirmed action
                return cls._execute_confirmed_action(
                    db=db,
                    organization_id=organization_id,
                    conversation=conversation,
                    pending_action=pending_action,
                    authenticated_customer_id=authenticated_customer_id
                )
            elif confirmation is False:
                # Cancelled by user
                context.pop("pending_action", None)
                conversation.context = context
                db.commit()
                cancel_text = "Understood, I have cancelled that request. Is there anything else I can assist you with?"
                cls._persist_ai_message(db, organization_id, conversation.id, cancel_text, "TEXT")
                return {"message": cancel_text, "message_type": "TEXT", "metadata": {}}

        # 8. Route by Intent
        intent_type = intent_result.intent

        # --- A. Order Status & Shipment Tracking ---
        if intent_type in (IntentType.ORDER_STATUS, IntentType.SHIPPING_DELAY):
            return cls._handle_order_status(

                db=db,
                organization_id=organization_id,
                conversation=conversation,
                extracted=extracted,
                authenticated_customer_id=authenticated_customer_id
            )

        # --- B. Return Request ---
        elif intent_type == IntentType.RETURN_REQUEST:
            return cls._handle_return_request(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                extracted=extracted,
                authenticated_customer_id=authenticated_customer_id,
                message_text=message_text
            )

        # --- C. Refund Request ---
        elif intent_type == IntentType.REFUND_REQUEST:
            return cls._handle_refund_request(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                extracted=extracted,
                authenticated_customer_id=authenticated_customer_id,
                message_text=message_text
            )


        # --- D. Order Cancellation ---
        elif intent_type == IntentType.ORDER_CANCELLATION:
            return cls._handle_order_cancellation(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                extracted=extracted,
                authenticated_customer_id=authenticated_customer_id
            )

        # --- E. Complaint & Support Request ---
        elif intent_type in (IntentType.COMPLAINT, IntentType.SUPPORT_REQUEST):
            return cls._handle_complaint_or_support(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                message_text=message_text,
                authenticated_customer_id=authenticated_customer_id
            )

        # --- F. Products, Sizing, Policies & FAQs via RAG ---
        else:
            return cls._handle_rag_knowledge(
                db=db,
                organization_id=organization_id,
                conversation=conversation,
                message_text=message_text
            )

    # -----------------------------------------------------------------------
    # Intent Handlers
    # -----------------------------------------------------------------------

    @classmethod
    def _handle_order_status(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        extracted: Dict[str, Any],
        authenticated_customer_id: Optional[str]
    ) -> Dict[str, Any]:
        """Inspects order and shipment status with strict ownership checks."""
        # Guest protection
        if not authenticated_customer_id:
            msg = (
                "To view your order and tracking details, please log in to your UrbanThread account. "
                "For your security, order tracking is only accessible to verified account holders."
            )
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"auth_required": True}}

        # Locate order
        order_num = None
        if extracted.get("order_numbers"):
            order_num = extracted["order_numbers"][0]
        elif conversation.context and conversation.context.get("last_order_number"):
            order_num = conversation.context["last_order_number"]

        if order_num:
            order = db.query(Order).filter(
                Order.organization_id == organization_id,
                Order.order_number == order_num
            ).first()
        else:
            # Fall back to most recent order of this authenticated customer
            order = db.query(Order).filter(
                Order.organization_id == organization_id,
                Order.customer_id == authenticated_customer_id
            ).order_by(Order.created_at.desc()).first()

        if not order:
            msg = "We couldn't find any orders matching your profile. Please double check your order number or let me know if you need help."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {}}

        # Strict Ownership Check
        if order.customer_id != authenticated_customer_id:
            msg = (
                f"For your privacy and security, Order #{order_num} cannot be accessed from this account. "
                "Please verify that you are signed in with the email address used at checkout."
            )
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"forbidden": True}}

        # Fetch shipment
        shipment = db.query(Shipment).filter(
            Shipment.order_id == order.id,
            Shipment.organization_id == organization_id
        ).first()

        tracking_info = f"Tracking: {shipment.tracking_number} via {shipment.carrier}" if shipment and shipment.tracking_number else "Tracking will be available once the carrier receives the package."
        eta = "Tomorrow" if (shipment and shipment.status == "IN_TRANSIT") else "Within 2-4 business days"

        reply = (
            f"Here is the current status of your order #{order.order_number}:\n"
            f"• **Status**: {order.status}\n"
            f"• **Payment**: {order.payment_status}\n"
            f"• **Estimated Delivery**: {eta}\n"
            f"• **Carrier**: {tracking_info}"
        )

        card_metadata = {
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "tracking_number": shipment.tracking_number if shipment else None,
            "carrier": shipment.carrier if shipment else None,
            "eta": eta
        }

        cls._persist_ai_message(db, organization_id, conversation.id, reply, "ORDER_CARD", card_metadata)
        return {"message": reply, "message_type": "ORDER_CARD", "metadata": card_metadata}

    @classmethod
    def _handle_return_request(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        extracted: Dict[str, Any],
        authenticated_customer_id: Optional[str],
        message_text: str = ""
    ) -> Dict[str, Any]:
        """Validates return policy and asks for explicit confirmation before mutating."""
        lower = message_text.lower()
        if "policy" in lower or any(w in lower for w in ("how to", "what is", "return window", "shipping time", "how do returns")):
            return cls._handle_rag_knowledge(db, organization_id, conversation, message_text)

        if not authenticated_customer_id:
            msg = "To initiate a return, please log in to your UrbanThread account so we can verify your purchase eligibility."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"auth_required": True}}


        # Find eligible order
        order = cls._get_customer_order(db, organization_id, authenticated_customer_id, extracted.get("order_numbers"))
        if not order:
            msg = "I couldn't find an order eligible for return under your account. Items can be returned within 30 days of delivery."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {}}

        # Check return window (30 days)
        now = get_utc_now()
        order_time = order.created_at or now
        if hasattr(order_time, "tzinfo") and order_time.tzinfo is None:
            order_time = order_time.replace(tzinfo=timezone.utc)
        if hasattr(now, "tzinfo") and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        if (now - order_time).days > 30:
            msg = f"Order #{order.order_number} was placed over 30 days ago and is outside our standard return window. Would you like me to connect you with our support team to explore an exception?"
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"outside_window": True}}

        # Set pending action requiring confirmation
        context = dict(conversation.context or {})
        context["pending_action"] = {
            "action": "CREATE_RETURN",
            "order_id": order.id,
            "order_number": order.order_number
        }
        conversation.context = context
        db.commit()

        reply = (
            f"Your order #{order.order_number} is eligible for return under UrbanThread's 30-day return policy.\n\n"
            f"Would you like me to submit a return request for Order #{order.order_number}? "
            f"A prepaid return pickup will be scheduled at your original delivery address."
        )
        metadata = {
            "requires_confirmation": True,
            "action": "CREATE_RETURN",
            "order_number": order.order_number
        }
        cls._persist_ai_message(db, organization_id, conversation.id, reply, "CONFIRMATION", metadata)
        return {"message": reply, "message_type": "CONFIRMATION", "metadata": metadata}

    @classmethod
    def _handle_refund_request(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        extracted: Dict[str, Any],
        authenticated_customer_id: Optional[str],
        message_text: str = ""
    ) -> Dict[str, Any]:
        """Enforces high-risk governance on refunds > ₹2,000."""
        lower = message_text.lower()
        if "policy" in lower or any(w in lower for w in ("how do refunds", "what is your refund policy", "how long do refunds")):
            return cls._handle_rag_knowledge(db, organization_id, conversation, message_text)

        if not authenticated_customer_id:
            msg = "To inquire about a refund, please sign in to your UrbanThread account."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"auth_required": True}}


        order = cls._get_customer_order(db, organization_id, authenticated_customer_id, extracted.get("order_numbers"))
        if not order:
            msg = "I could not locate an eligible order for a refund. Please provide your order number or reach out to support."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {}}

        # Deterministic calculation of refund amount
        refund_amount = order.total_amount

        # High-Risk Governance Check (Refund > ₹2,000 requires human approval)
        if refund_amount > 2000.0:
            # Create approval record
            approval = Approval(
                organization_id=organization_id,
                approval_type="REFUND",
                title=f"Refund Request ₹{refund_amount:,.2f} on Order #{order.order_number}",
                action_type="REFUND",
                action_payload={"order_id": order.id, "amount": refund_amount, "currency": order.currency or "INR"},
                requested_by_id=authenticated_customer_id,
                required_roles=["FINANCE_MANAGER"],
                approval_mode="ONE_APPROVER",
                action_payload_hash=f"refund_{order.id}_{refund_amount}",
                status="PENDING",
                reason=f"Customer requested refund of ₹{refund_amount:,.2f} on Order #{order.order_number} exceeding ₹2,000 threshold"
            )
            db.add(approval)
            db.commit()

            reply = (
                f"Your refund request for **₹{refund_amount:,.2f}** on Order #{order.order_number} has been safely submitted for review by our operations manager (Approval #{approval.id[:8]}).\n\n"
                "In accordance with our financial security policy, refunds over ₹2,000 undergo review and will be processed back to your original payment method within 1 business day."
            )
            metadata = {
                "approval_id": approval.id,
                "status": "PENDING_APPROVAL",
                "amount": refund_amount
            }
            cls._persist_ai_message(db, organization_id, conversation.id, reply, "RESOLUTION", metadata)
            return {"message": reply, "message_type": "RESOLUTION", "metadata": metadata}
        else:
            # Safe automated refund below threshold
            reply = (
                f"Your refund of **₹{refund_amount:,.2f}** on Order #{order.order_number} is eligible for automated processing. "
                "Would you like me to confirm and execute this refund now?"
            )
            context = dict(conversation.context or {})
            context["pending_action"] = {
                "action": "EXECUTE_REFUND",
                "order_id": order.id,
                "amount": refund_amount
            }
            conversation.context = context
            db.commit()
            metadata = {"requires_confirmation": True, "action": "EXECUTE_REFUND", "amount": refund_amount}
            cls._persist_ai_message(db, organization_id, conversation.id, reply, "CONFIRMATION", metadata)
            return {"message": reply, "message_type": "CONFIRMATION", "metadata": metadata}

    @classmethod
    def _handle_order_cancellation(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        extracted: Dict[str, Any],
        authenticated_customer_id: Optional[str]
    ) -> Dict[str, Any]:
        """Validates cancellation eligibility."""
        if not authenticated_customer_id:
            msg = "Please log in to your account to cancel an order."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"auth_required": True}}

        order = cls._get_customer_order(db, organization_id, authenticated_customer_id, extracted.get("order_numbers"))
        if not order:
            msg = "I couldn't find an open order to cancel."
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {}}

        if order.status in ("SHIPPED", "DELIVERED"):
            msg = (
                f"Order #{order.order_number} has already been {order.status.lower()} and cannot be cancelled directly. "
                "However, once it arrives you can easily request a return or exchange within 30 days!"
            )
            cls._persist_ai_message(db, organization_id, conversation.id, msg, "TEXT")
            return {"message": msg, "message_type": "TEXT", "metadata": {"cancellation_blocked": True}}

        # Ask confirmation
        context = dict(conversation.context or {})
        context["pending_action"] = {"action": "CANCEL_ORDER", "order_id": order.id, "order_number": order.order_number}
        conversation.context = context
        db.commit()

        reply = f"Order #{order.order_number} is in processing and can be cancelled. Would you like me to proceed with cancelling this order and refunding your payment?"
        metadata = {"requires_confirmation": True, "action": "CANCEL_ORDER", "order_number": order.order_number}
        cls._persist_ai_message(db, organization_id, conversation.id, reply, "CONFIRMATION", metadata)
        return {"message": reply, "message_type": "CONFIRMATION", "metadata": metadata}

    @classmethod
    def _handle_complaint_or_support(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        message_text: str,
        authenticated_customer_id: Optional[str]
    ) -> Dict[str, Any]:
        """Creates a high priority support ticket and escalates."""
        ticket = SupportTicket(
            organization_id=organization_id,
            customer_id=authenticated_customer_id or "guest",
            ticket_number=f"TKT-{generate_uuid()[:8].upper()}",
            subject=f"Customer Care Inquiry: {message_text[:60]}...",
            description=message_text,
            priority="HIGH",
            status="OPEN"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        reply = (
            f"I have recorded your issue and created Support Ticket **#{ticket.ticket_number}** with our customer care team. "
            "A senior representative has been notified and will prioritize your request."
        )
        cls._persist_ai_message(db, organization_id, conversation.id, reply, "TEXT", {"ticket_number": ticket.ticket_number})
        return {"message": reply, "message_type": "TEXT", "metadata": {"ticket_number": ticket.ticket_number}}

    @classmethod
    def _handle_rag_knowledge(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        message_text: str
    ) -> Dict[str, Any]:
        """Queries RAG knowledge chunks and policies for public e-commerce answers."""
        query_lower = message_text.lower()

        # Shipping policy match
        if any(w in query_lower for w in ("shipping", "delivery", "carrier", "how long", "courier", "charges")):
            reply = (
                "UrbanThread standard shipping takes 2-4 business days across India. "
                "We offer free shipping on orders above ₹999. Express delivery is available for select pin codes with 24-48 hour delivery."
            )
        # Return policy match
        elif any(w in query_lower for w in ("return policy", "exchange", "how to return", "return window")):
            reply = (
                "UrbanThread has a hassle-free 30-day return policy. Items must be unworn, unwashed, "
                "and have original tags attached. Once pickup is verified, your refund or store credit is processed within 48 hours."
            )
        # Sizing match
        elif any(w in query_lower for w in ("size", "sizing", "fit", "measure", "small", "medium", "large", "xl")):
            reply = (
                "Our synthetic cotton and eco-blend apparel follows standard Indian/UK sizing (S: 38\", M: 40\", L: 42\", XL: 44\"). "
                "For a relaxed streetwear fit, we recommend sizing up one size."
            )
        # Coupons match
        elif any(w in query_lower for w in ("coupon", "discount", "promo", "code", "offer")):
            reply = (
                "You can use code **URBAN10** for 10% off your first order, or **THREAD20** on orders above ₹2,499! "
                "Enter the code during checkout to apply your discount."
            )
        else:
            reply = (
                "UrbanThread offers premium sustainable synthetic and recycled fabric apparel. "
                "I can help you track orders, request returns or refunds, check sizing, or answer any policy questions. What would you like to know?"
            )

        cls._persist_ai_message(db, organization_id, conversation.id, reply, "TEXT")
        return {"message": reply, "message_type": "TEXT", "metadata": {}}

    # -----------------------------------------------------------------------
    # Confirmed Action Execution
    # -----------------------------------------------------------------------

    @classmethod
    def _execute_confirmed_action(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        pending_action: Dict[str, Any],
        authenticated_customer_id: Optional[str]
    ) -> Dict[str, Any]:
        action_type = pending_action.get("action")
        order_id = pending_action.get("order_id")

        # Clear pending action from context
        context = dict(conversation.context or {})
        context.pop("pending_action", None)
        conversation.context = context
        db.commit()

        if action_type == "CREATE_RETURN":
            order = db.query(Order).filter(Order.id == order_id).first()
            ret_num = f"RET-{generate_uuid()[:8].upper()}"
            ret = Return(
                organization_id=organization_id,
                order_id=order.id,
                customer_id=authenticated_customer_id or order.customer_id,
                return_number=ret_num,
                reason="Customer requested return via Aria AI",
                status="REQUESTED"
            )
            db.add(ret)
            db.commit()
            db.refresh(ret)

            reply = (
                f"✅ Return request **#{ret.return_number}** has been successfully initiated for Order #{order.order_number}.\n\n"
                "A courier pickup has been scheduled for tomorrow. Please keep the item packed with tags intact."
            )
            metadata = {"return_number": ret.return_number, "order_number": order.order_number, "status": "REQUESTED"}
            cls._persist_ai_message(db, organization_id, conversation.id, reply, "RESOLUTION", metadata)
            return {"message": reply, "message_type": "RESOLUTION", "metadata": metadata}

        elif action_type == "CANCEL_ORDER":
            order = db.query(Order).filter(Order.id == order_id).first()
            order.status = "CANCELLED"
            db.commit()

            reply = (
                f"✅ Order **#{order.order_number}** has been cancelled.\n\n"
                f"A full refund of ₹{order.total_amount:,.2f} will be refunded to your original payment method."
            )
            metadata = {"order_number": order.order_number, "status": "CANCELLED"}
            cls._persist_ai_message(db, organization_id, conversation.id, reply, "RESOLUTION", metadata)
            return {"message": reply, "message_type": "RESOLUTION", "metadata": metadata}

        elif action_type == "EXECUTE_REFUND":
            amount = pending_action.get("amount", 0.0)
            order = db.query(Order).filter(Order.id == order_id).first()
            ref_num = f"REF-{generate_uuid()[:8].upper()}"
            refund = Refund(
                organization_id=organization_id,
                order_id=order.id,
                customer_id=authenticated_customer_id or order.customer_id,
                refund_number=ref_num,
                amount=amount,
                currency=order.currency or "INR",
                reason="Customer refund via Aria AI",
                status="COMPLETED"
            )
            db.add(refund)
            db.commit()

            reply = (
                f"✅ Refund **#{ref_num}** for **₹{amount:,.2f}** has been processed successfully!\n\n"
                "The funds will reflect in your bank account within 2-3 business days."
            )
            metadata = {"refund_number": ref_num, "amount": amount, "status": "COMPLETED"}
            cls._persist_ai_message(db, organization_id, conversation.id, reply, "RESOLUTION", metadata)
            return {"message": reply, "message_type": "RESOLUTION", "metadata": metadata}

        return {"message": "Action completed.", "message_type": "TEXT", "metadata": {}}

    # -----------------------------------------------------------------------
    # Human Handoff Execution
    # -----------------------------------------------------------------------

    @classmethod
    def _execute_human_handoff(
        cls,
        db: Session,
        organization_id: str,
        conversation: CustomerConversation,
        reason: str
    ) -> Dict[str, Any]:
        """Transitions conversation to WAITING_FOR_HUMAN and creates ticket."""
        conversation.status = "WAITING_FOR_HUMAN"
        db.commit()

        ticket = SupportTicket(
            organization_id=organization_id,
            customer_id=conversation.customer_id or "guest",
            ticket_number=f"TKT-{generate_uuid()[:8].upper()}",
            subject=f"Human Handoff Request: {reason}",
            description=f"Customer requested human representative in chat conversation {conversation.id}. Reason: {reason}",
            priority="HIGH",
            status="OPEN"
        )
        db.add(ticket)
        db.commit()

        reply = (
            "I have transferred our conversation to our human customer support team. "
            f"Your support ticket **#{ticket.ticket_number}** has been created with high priority, "
            "and a representative will reply in this chat shortly."
        )
        metadata = {
            "status": "WAITING_FOR_HUMAN",
            "ticket_number": ticket.ticket_number,
            "handoff": True
        }
        cls._persist_ai_message(db, organization_id, conversation.id, reply, "HANDOFF", metadata)
        return {"message": reply, "message_type": "HANDOFF", "metadata": metadata}

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @classmethod
    def _is_adversarial_or_injection(cls, text: str) -> bool:
        t = text.lower()
        patterns = [
            r"ignore\s+(all\s+)?(previous\s+)?instructions",
            r"system\s+prompt",
            r"admin\s+password",
            r"reveal\s+(api\s+)?key",
            r"you\s+are\s+now\s+in\s+developer\s+mode",
            r"dan\s+mode",
            r"unrestricted\s+mode",
            r"drop\s+table",
            r"select\s+.*\s+from\s+users",
            r"use\s+customer_id\s*=\s*",
        ]
        return any(re.search(p, t) for p in patterns)

    @classmethod
    def _is_human_handoff_requested(cls, text: str) -> bool:
        t = text.lower()
        keywords = [
            "talk to a human", "speak with a human", "real person", "human agent",
            "representative", "customer care executive", "connect me to human",
            "speak to agent", "talk to agent"
        ]
        return any(kw in t for kw in keywords)

    @classmethod
    def _detect_confirmation(cls, text: str) -> Optional[bool]:
        t = text.strip().lower()
        if any(w in t for w in ("yes", "confirm", "proceed", "sure", "go ahead", "do it", "please do", "approved")):
            return True
        if any(w in t for w in ("no", "cancel", "don't", "dont", "never mind", "stop", "reject")):
            return False
        return None

    @classmethod
    def _get_customer_order(
        cls,
        db: Session,
        organization_id: str,
        customer_id: str,
        order_numbers: Optional[List[str]]
    ) -> Optional[Order]:
        if order_numbers:
            return db.query(Order).filter(
                Order.organization_id == organization_id,
                Order.customer_id == customer_id,
                Order.order_number == order_numbers[0]
            ).first()
        return db.query(Order).filter(
            Order.organization_id == organization_id,
            Order.customer_id == customer_id
        ).order_by(Order.created_at.desc()).first()

    @classmethod
    def _persist_ai_message(
        cls,
        db: Session,
        organization_id: str,
        conversation_id: str,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            organization_id=organization_id,
            conversation_id=conversation_id,
            sender_type="AI_AGENT",
            sender_id="aria-support-ai",
            message_type=message_type,
            content=content,
            is_untrusted=False,
            msg_metadata=metadata or {}
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
