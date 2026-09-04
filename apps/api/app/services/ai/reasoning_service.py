"""
Phase 7 — Reasoning Service.

Evaluates intent, verified entities, and gathered context to produce an
auditable, structured reasoning result.
Strict principle: No actions are executed here; reasoning is purely cognitive.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.api.app.core.llm_provider import get_llm_provider
from apps.api.app.schemas.agent_schemas import (
    ContextItem,
    DecisionType,
    EntityExtractionResult,
    IntentType,
    ReasoningResult,
)


class ReasoningService:
    def __init__(self):
        self.provider = get_llm_provider()

    def reason(
        self,
        intent: str,
        entities: EntityExtractionResult,
        context_items: List[ContextItem],
        user_message: str,
        channel: str = "WEB_CHAT",
    ) -> ReasoningResult:
        """
        Execute deterministic cognitive reasoning first;
        fallback to LLM provider for nuanced inquiries.
        """
        evidence_ids = [item.source_id for item in context_items if item.source_id]

        # -------------------------------------------------------------------
        # 1. Prompt Injection Refusal
        # -------------------------------------------------------------------
        if intent == IntentType.PROMPT_INJECTION.value or "PROMPT_INJECTION" in entities.untrusted_flags:
            return ReasoningResult(
                decision=DecisionType.REFUSE,
                decision_summary="Security violation: Untrusted prompt injection or system override detected. Refusing instruction.",
                reason_codes=["SECURITY_PROMPT_INJECTION"],
                evidence_ids=[],
                confidence=1.0,
                proposed_response=(
                    "I am the UrbanThread Operations Assistant. "
                    "I can only assist with verified customer orders, products, shipping, and store operations."
                ),
                required_actions=[],
            )

        # -------------------------------------------------------------------
        # 2. Order Status
        # -------------------------------------------------------------------
        if intent == IntentType.ORDER_STATUS.value:
            order_ctx = next((item for item in context_items if item.source_type == "ORDER"), None)
            if not order_ctx:
                return ReasoningResult(
                    decision=DecisionType.ASK_CLARIFICATION,
                    decision_summary="Order status requested but order could not be identified or found in database.",
                    reason_codes=["MISSING_ORDER_NUMBER"],
                    evidence_ids=[],
                    confidence=0.95,
                    proposed_response="Could you please provide your order number (e.g., ORD-1001) so I can check the status for you?",
                    required_actions=[],
                )

            order_meta = order_ctx.metadata
            status = order_meta.get("status", "UNKNOWN")
            order_num = order_meta.get("order_number", "your order")
            shipment_ctx = next((item for item in context_items if item.source_type == "SHIPMENT"), None)
            tracking_info = ""
            if shipment_ctx:
                tnum = shipment_ctx.metadata.get("tracking_number")
                carrier = shipment_ctx.metadata.get("carrier")
                tracking_info = f" Carrier: {carrier}, Tracking #: {tnum}."

            response_msg = f"Order {order_num} is currently {status}.{tracking_info}"
            return ReasoningResult(
                decision=DecisionType.ANSWER,
                decision_summary=f"Found order {order_num} with status {status}. Responding with verified order details.",
                reason_codes=["ORDER_FOUND", f"ORDER_STATUS_{status}"],
                evidence_ids=evidence_ids,
                confidence=0.98,
                proposed_response=response_msg,
                required_actions=[],
            )

        # -------------------------------------------------------------------
        # 3. Order Cancellation
        # -------------------------------------------------------------------
        if intent == IntentType.ORDER_CANCELLATION.value:
            order_ctx = next((item for item in context_items if item.source_type == "ORDER"), None)
            if not order_ctx:
                return ReasoningResult(
                    decision=DecisionType.ASK_CLARIFICATION,
                    decision_summary="Cancellation requested without valid order number.",
                    reason_codes=["MISSING_ORDER_NUMBER"],
                    evidence_ids=[],
                    confidence=0.90,
                    proposed_response="Please provide the order number for the order you wish to cancel.",
                    required_actions=[],
                )

            order_status = order_ctx.metadata.get("status", "").upper()
            order_num = order_ctx.metadata.get("order_number")

            if order_status in ("SHIPPED", "DELIVERED"):
                return ReasoningResult(
                    decision=DecisionType.REFUSE,
                    decision_summary=f"Order {order_num} has already been {order_status.lower()} and cannot be cancelled directly.",
                    reason_codes=["ORDER_ALREADY_SHIPPED_CANNOT_CANCEL"],
                    evidence_ids=evidence_ids,
                    confidence=0.95,
                    proposed_response=(
                        f"Order {order_num} has already been {order_status.lower()} and cannot be cancelled directly. "
                        "Once it arrives, you may initiate a return within 30 days."
                    ),
                    required_actions=["INITIATE_RETURN_WORKFLOW"],
                )

            # Order is PENDING / PROCESSING -> Requires approval or cancellation action
            return ReasoningResult(
                decision=DecisionType.REQUEST_APPROVAL,
                decision_summary=f"Cancellation requested for order {order_num} in status {order_status}. Requires human approval before executing cancellation.",
                reason_codes=["ORDER_CANCELLATION_REQUESTED", "APPROVAL_REQUIRED_FOR_CANCELLATION"],
                evidence_ids=evidence_ids,
                confidence=0.92,
                proposed_response=f"I have received your request to cancel order {order_num}. A team member is reviewing the cancellation request.",
                required_actions=["CANCEL_ORDER", "RESTOCK_INVENTORY", "ISSUE_REFUND"],
            )

        # -------------------------------------------------------------------
        # 4. Return or Refund Request
        # -------------------------------------------------------------------
        if intent in (IntentType.RETURN_REQUEST.value, IntentType.REFUND_REQUEST.value):
            order_ctx = next((item for item in context_items if item.source_type == "ORDER"), None)
            if not order_ctx:
                return ReasoningResult(
                    decision=DecisionType.ASK_CLARIFICATION,
                    decision_summary="Return/refund requested but no order number provided.",
                    reason_codes=["MISSING_ORDER_NUMBER"],
                    evidence_ids=[],
                    confidence=0.90,
                    proposed_response="To process your return or refund request, please provide your order number.",
                    required_actions=[],
                )

            order_status = order_ctx.metadata.get("status", "").upper()
            order_num = order_ctx.metadata.get("order_number")

            if order_status != "DELIVERED":
                return ReasoningResult(
                    decision=DecisionType.REFUSE,
                    decision_summary=f"Order {order_num} is {order_status}. Returns and refunds are only accepted after delivery.",
                    reason_codes=["ORDER_NOT_DELIVERED_FOR_RETURN"],
                    evidence_ids=evidence_ids,
                    confidence=0.95,
                    proposed_response=f"Order {order_num} is currently {order_status}. A return or refund can only be initiated once the package has been delivered.",
                    required_actions=[],
                )

            return ReasoningResult(
                decision=DecisionType.REQUEST_APPROVAL,
                decision_summary=f"Return/refund requested for delivered order {order_num}. Prepared return authorization requiring review.",
                reason_codes=["RETURN_ELIGIBLE", "REFUND_REQUIRES_APPROVAL"],
                evidence_ids=evidence_ids,
                confidence=0.92,
                proposed_response=f"Your return request for order {order_num} has been initiated and submitted for approval.",
                required_actions=["CREATE_RETURN_RECORD", "SEND_RETURN_LABEL"],
            )

        # -------------------------------------------------------------------
        # 5. Product & Inventory Inquiries
        # -------------------------------------------------------------------
        if intent in (IntentType.PRODUCT_QUESTION.value, IntentType.INVENTORY_QUESTION.value):
            product_ctx = next((item for item in context_items if item.source_type == "PRODUCT"), None)
            inv_ctx = next((item for item in context_items if item.source_type == "INVENTORY"), None)

            if product_ctx:
                p_meta = product_ctx.metadata
                p_name = p_meta.get("name", "the requested item")
                p_price = p_meta.get("base_price", "N/A")
                in_stock = inv_ctx.metadata.get("in_stock", True) if inv_ctx else True

                stock_str = "in stock and available to order" if in_stock else "currently out of stock"
                return ReasoningResult(
                    decision=DecisionType.ANSWER,
                    decision_summary=f"Product {p_name} found. Information provided with stock status.",
                    reason_codes=["PRODUCT_FOUND", "IN_STOCK" if in_stock else "OUT_OF_STOCK"],
                    evidence_ids=evidence_ids,
                    confidence=0.95,
                    proposed_response=f"{p_name} is priced at ₹{p_price} and is {stock_str}.",
                    required_actions=[],
                )

            return ReasoningResult(
                decision=DecisionType.ANSWER,
                decision_summary="General product question without specific SKU match.",
                reason_codes=["PRODUCT_CATALOG_QUERY"],
                evidence_ids=[],
                confidence=0.85,
                proposed_response="We offer a wide range of premium apparel at UrbanThread. Could you specify which item or SKU you are interested in?",
                required_actions=[],
            )

        # -------------------------------------------------------------------
        # 6. Shipping Questions / Delays
        # -------------------------------------------------------------------
        if intent in (IntentType.SHIPPING_QUESTION.value, IntentType.SHIPPING_DELAY.value):
            shipment_ctx = next((item for item in context_items if item.source_type == "SHIPMENT"), None)
            if shipment_ctx:
                s_meta = shipment_ctx.metadata
                carrier = s_meta.get("carrier", "our courier partner")
                status = s_meta.get("status", "in transit")
                eta = s_meta.get("estimated_delivery", "shortly")
                return ReasoningResult(
                    decision=DecisionType.ANSWER,
                    decision_summary=f"Shipment details found: {carrier}, status: {status}.",
                    reason_codes=["SHIPMENT_FOUND"],
                    evidence_ids=evidence_ids,
                    confidence=0.95,
                    proposed_response=f"Your package is with {carrier} and currently marked as {status}. Estimated delivery: {eta}.",
                    required_actions=[],
                )

            return ReasoningResult(
                decision=DecisionType.ANSWER,
                decision_summary="General shipping policy provided.",
                reason_codes=["GENERAL_SHIPPING_POLICY"],
                evidence_ids=evidence_ids,
                confidence=0.90,
                proposed_response="UrbanThread standard shipping typically takes 3 to 5 business days across India. Express shipping is 1 to 2 business days.",
                required_actions=[],
            )

        # -------------------------------------------------------------------
        # 7. Complaints
        # -------------------------------------------------------------------
        if intent == IntentType.COMPLAINT.value:
            return ReasoningResult(
                decision=DecisionType.CREATE_SUPPORT_TICKET,
                decision_summary="Customer complaint received. Creating support ticket for expedited resolution.",
                reason_codes=["CUSTOMER_COMPLAINT_ESCALATED"],
                evidence_ids=evidence_ids,
                confidence=0.90,
                proposed_response="I am truly sorry to hear about your experience. I have created an expedited support ticket for our customer care team to address this immediately.",
                required_actions=["CREATE_SUPPORT_TICKET"],
            )

        # -------------------------------------------------------------------
        # 8. Vendor Requests
        # -------------------------------------------------------------------
        if intent == IntentType.VENDOR_REQUEST.value:
            return ReasoningResult(
                decision=DecisionType.REQUEST_APPROVAL,
                decision_summary="Vendor operational request received. Requires operations manager review.",
                reason_codes=["VENDOR_INQUIRY_APPROVAL_REQUIRED"],
                evidence_ids=evidence_ids,
                confidence=0.88,
                proposed_response="Thank you for your vendor inquiry. It has been routed to our procurement and operations team for review.",
                required_actions=["CREATE_OPERATIONS_TASK"],
            )

        # -------------------------------------------------------------------
        # 9. Fallback / Nuanced query through Provider
        # -------------------------------------------------------------------
        sections = [{"section": item.source_type, "content": item.content} for item in context_items]
        raw_reason = self.provider.reason(
            system_prompt="You are UrbanThread AI Operations Employee.",
            task_prompt=f"User intent: {intent}. Message: {user_message}",
            context_sections=sections,
        )

        return ReasoningResult(
            decision=DecisionType(raw_reason.get("decision", DecisionType.ANSWER.value)),
            decision_summary=raw_reason.get("decision_summary", "Completed automated reasoning."),
            reason_codes=raw_reason.get("reason_codes", ["REASONING_COMPLETE"]),
            evidence_ids=raw_reason.get("evidence_ids", evidence_ids),
            confidence=raw_reason.get("confidence", 0.85),
            proposed_response=raw_reason.get("proposed_response", "Thank you for reaching out to UrbanThread."),
            required_actions=raw_reason.get("required_actions", []),
        )
