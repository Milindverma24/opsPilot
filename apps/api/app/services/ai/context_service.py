"""
Phase 7 — Context Gathering Service.

Coordinates bounded context retrieval across multiple read-only adapters.
Guarantees strict tenant isolation and source provenance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.schemas.agent_schemas import (
    ContextItem,
    ContextRequirement,
    EntityExtractionResult,
    IntentType,
)
from apps.api.app.services.ai.context_providers import (
    CustomerContextProvider,
    OrderContextProvider,
    ProductContextProvider,
    ShipmentContextProvider,
    SupportContextProvider,
    InventoryContextProvider,
    KnowledgeContextProvider,
)


class ContextGatheringService:
    def __init__(self):
        self.customer_provider = CustomerContextProvider()
        self.order_provider = OrderContextProvider()
        self.product_provider = ProductContextProvider()
        self.shipment_provider = ShipmentContextProvider()
        self.support_provider = SupportContextProvider()
        self.inventory_provider = InventoryContextProvider()
        self.knowledge_provider = KnowledgeContextProvider()

    def determine_requirements(self, intent: str, entities: EntityExtractionResult) -> List[ContextRequirement]:
        """Map intent + extracted entities to explicit context requirements."""
        reqs: List[ContextRequirement] = []

        if intent in (IntentType.ORDER_STATUS.value, IntentType.ORDER_CHANGE.value, IntentType.ORDER_CANCELLATION.value):
            reqs.append(ContextRequirement(source_type="ORDER", is_mandatory=True, query_params={"order_numbers": entities.order_numbers}))
            reqs.append(ContextRequirement(source_type="SHIPMENT", is_mandatory=False, query_params={"tracking_numbers": entities.tracking_numbers}))
            reqs.append(ContextRequirement(source_type="POLICY", is_mandatory=False, query_params={"keyword": "order_cancellation" if "CANCEL" in intent else "order"}))

        elif intent in (IntentType.SHIPPING_QUESTION.value, IntentType.SHIPPING_DELAY.value):
            reqs.append(ContextRequirement(source_type="SHIPMENT", is_mandatory=True, query_params={"tracking_numbers": entities.tracking_numbers}))
            reqs.append(ContextRequirement(source_type="ORDER", is_mandatory=False, query_params={"order_numbers": entities.order_numbers}))
            reqs.append(ContextRequirement(source_type="POLICY", is_mandatory=False, query_params={"keyword": "shipping"}))

        elif intent in (IntentType.RETURN_REQUEST.value, IntentType.REFUND_REQUEST.value, IntentType.EXCHANGE_REQUEST.value):
            reqs.append(ContextRequirement(source_type="ORDER", is_mandatory=True, query_params={"order_numbers": entities.order_numbers}))
            reqs.append(ContextRequirement(source_type="POLICY", is_mandatory=True, query_params={"keyword": "return" if "RETURN" in intent else "refund"}))
            reqs.append(ContextRequirement(source_type="CUSTOMER", is_mandatory=False, query_params={"customer_ids": entities.customer_ids, "emails": entities.emails}))

        elif intent in (IntentType.PRODUCT_QUESTION.value, IntentType.INVENTORY_QUESTION.value):
            reqs.append(ContextRequirement(source_type="PRODUCT", is_mandatory=True, query_params={"skus": entities.skus}))
            reqs.append(ContextRequirement(source_type="INVENTORY", is_mandatory=False, query_params={"skus": entities.skus}))

        elif intent == IntentType.COMPLAINT.value:
            reqs.append(ContextRequirement(source_type="SUPPORT", is_mandatory=False, query_params={}))
            reqs.append(ContextRequirement(source_type="ORDER", is_mandatory=False, query_params={"order_numbers": entities.order_numbers}))
            reqs.append(ContextRequirement(source_type="CUSTOMER", is_mandatory=False, query_params={"emails": entities.emails}))

        elif intent == IntentType.COUPON_QUESTION.value:
            reqs.append(ContextRequirement(source_type="POLICY", is_mandatory=False, query_params={"keyword": "discount"}))

        else:
            # Fallback: if we have order numbers, fetch orders; if skus, fetch products
            if entities.order_numbers:
                reqs.append(ContextRequirement(source_type="ORDER", is_mandatory=False, query_params={"order_numbers": entities.order_numbers}))
            if entities.skus:
                reqs.append(ContextRequirement(source_type="PRODUCT", is_mandatory=False, query_params={"skus": entities.skus}))

        return reqs

    def gather_context(
        self,
        db: Session,
        organization_id: str,
        intent: str,
        entities: EntityExtractionResult,
        actor_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        max_items: int = 10,
    ) -> List[ContextItem]:
        """
        Execute bounded context gathering across providers with strict tenant isolation.
        """
        items: List[ContextItem] = []
        requirements = self.determine_requirements(intent, entities)
        params = additional_params or {}

        # 1. Gather Orders
        for onum in entities.order_numbers:
            order_items = self.order_provider.gather(db, organization_id, {"order_number": onum})
            items.extend(order_items)
            # If we found an order, look up associated shipment
            for oi in order_items:
                order_id = oi.metadata.get("order_id") or oi.source_id
                shipment_items = self.shipment_provider.gather(db, organization_id, {"order_id": order_id})
                items.extend(shipment_items)
                customer_id = oi.metadata.get("customer_id")
                if customer_id:
                    cust_items = self.customer_provider.gather(db, organization_id, {"customer_id": customer_id})
                    items.extend(cust_items)

        # 2. Gather Shipments by tracking number
        for tnum in entities.tracking_numbers:
            items.extend(self.shipment_provider.gather(db, organization_id, {"tracking_number": tnum}))

        # 3. Gather Products & Inventory by SKU
        for sku in entities.skus:
            items.extend(self.product_provider.gather(db, organization_id, {"sku": sku}))
            items.extend(self.inventory_provider.gather(db, organization_id, {"sku": sku}))

        # 4. Gather Customer by email / phone / actor_id
        for email in entities.emails:
            items.extend(self.customer_provider.gather(db, organization_id, {"email": email}))
        for phone in entities.phones:
            items.extend(self.customer_provider.gather(db, organization_id, {"phone": phone}))
        if actor_id and not items:
            items.extend(self.customer_provider.gather(db, organization_id, {"customer_id": actor_id}))

        # 5. Gather Knowledge / Policies
        policy_keyword = intent.lower()
        if "RETURN" in intent:
            policy_keyword = "return"
        elif "REFUND" in intent:
            policy_keyword = "refund"
        elif "SHIP" in intent:
            policy_keyword = "shipping"
        elif "CANCEL" in intent:
            policy_keyword = "cancellation"
        elif "DISCOUNT" in intent or "COUPON" in intent:
            policy_keyword = "discount"

        policy_items = self.knowledge_provider.gather(db, organization_id, {"keyword": policy_keyword})
        items.extend(policy_items)

        # Deduplicate items by (source_type, source_id)
        seen = set()
        deduped: List[ContextItem] = []
        for item in items:
            key = (item.source_type, item.source_id)
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped[:max_items]
