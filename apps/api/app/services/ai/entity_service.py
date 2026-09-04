"""
Entity Extraction Service — Phase 7.

Extracts structured entities from natural language.
CRITICAL: All extracted IDs are verified against the database before being trusted.
The AI never gets raw SQL access — it gets only verified entity references.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from apps.api.app.core.llm_provider import get_llm_provider
from apps.api.app.schemas.agent_schemas import (
    EntityExtractionResult,
    ExtractedEntity,
    IntentType,
)
from apps.api.app.models.ecommerce import Order, Product, ProductVariant, Shipment
from apps.api.app.models.operations import Customer


class EntityExtractionService:
    """
    Extracts and DB-verifies entities from customer messages.
    """

    def __init__(self, db: Optional[Session] = None, organization_id: Optional[str] = None):
        self.db = db
        self.organization_id = organization_id
        self.llm = get_llm_provider()

    def extract(
        self,
        arg1: Any,
        arg2: Any = None,
        arg3: Optional[str] = None,
    ) -> EntityExtractionResult:
        """
        Flexible extractor accepting:
        - extract(db: Session, organization_id: str, message: str)
        - extract(message: str, intent: Optional[IntentType] = None)
        """
        db = self.db
        org_id = self.organization_id
        message = ""

        if isinstance(arg1, Session):
            db = arg1
            org_id = str(arg2) if arg2 else None
            message = str(arg3 or "")
        elif isinstance(arg1, str):
            message = arg1
            if isinstance(arg2, str) and not arg3 and ("org" in arg2 or "-" in arg2):
                org_id = arg2
            elif isinstance(arg2, Session):
                db = arg2
        else:
            message = str(arg1 or "")

        # 1. Deterministic regex extraction
        result = self._regex_extract(message)

        # 2. Database verification if session & org available
        if db and org_id:
            result = self._verify_entities(db, org_id, result)

        return result

    def _regex_extract(self, message: str) -> EntityExtractionResult:
        result = EntityExtractionResult(extraction_method="deterministic")
        order_numbers: List[str] = []
        skus: List[str] = []
        tracking_numbers: List[str] = []
        amounts: List[float] = []
        emails: List[str] = []
        phones: List[str] = []

        # Order numbers: ORD-1001, UT-1001, UT1001, UT-ALICE-101
        for match in re.finditer(r'\b((?:ORD|UT)[-_]?[A-Za-z0-9_-]{3,20})\b', message, re.IGNORECASE):
            val = match.group(1).upper()
            if val not in order_numbers:
                order_numbers.append(val)
                if not result.order_number:
                    result.order_number = ExtractedEntity(value=val, raw_text=match.group(0))


        # SKUs: SKU-TSHIRT-BLK, SKU-JEANS-01, SKU-12345
        for match in re.finditer(r'\b(SKU-[A-Z0-9_-]+)\b', message, re.IGNORECASE):
            val = match.group(1).upper()
            if val not in skus:
                skus.append(val)
                if not result.sku:
                    result.sku = ExtractedEntity(value=val, raw_text=match.group(0))

        # Tracking numbers: BDT-99214, DEL-10099, [A-Z]{2}\d{8,20}
        for match in re.finditer(r'\b((?:BDT|DEL|FED|DHL|EXP)[-_]?\d{4,16})\b', message, re.IGNORECASE):
            val = match.group(1).upper()
            if val not in tracking_numbers:
                tracking_numbers.append(val)
                if not result.tracking_number:
                    result.tracking_number = ExtractedEntity(value=val, raw_text=match.group(0))

        # Amounts: Rs 4500, ₹15000, 1998.0 INR
        for match in re.finditer(r'(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d{1,2})?)', message, re.IGNORECASE):
            try:
                amt = float(match.group(1).replace(",", ""))
                if amt not in amounts:
                    amounts.append(amt)
                    if result.refund_amount is None:
                        result.refund_amount = amt
            except ValueError:
                pass

        # Emails
        for match in re.finditer(r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', message):
            em = match.group(1).lower()
            if em not in emails:
                emails.append(em)

        # Phones: +919876543210, 9876543210
        for match in re.finditer(r'(\+?\d{10,13})', message):
            ph = match.group(1)
            if ph not in phones:
                phones.append(ph)

        # Size
        size_match = re.search(r'\b(XS|S|M|L|XL|XXL|2XL|3XL)\b', message, re.IGNORECASE)
        if size_match:
            result.size = size_match.group(1).upper()

        # Color
        colors = ["black", "white", "blue", "red", "green", "grey", "gray", "navy", "beige", "brown", "pink", "yellow", "olive"]
        msg_lower = message.lower()
        for c in colors:
            if c in msg_lower:
                result.color = c
                break

        # Coupon code
        coupon_match = re.search(r'\b(SAVE\d+|WELCOME\d+|URBAN\d+|FLAT\d+)\b', message, re.IGNORECASE)
        if coupon_match:
            result.coupon_code = coupon_match.group(1).upper()

        # Populate multi-value fields
        result.order_numbers = order_numbers
        result.skus = skus
        result.tracking_numbers = tracking_numbers
        result.amounts = amounts
        result.emails = emails
        result.phones = phones
        result.raw_extractions = {
            "order_numbers": order_numbers,
            "skus": skus,
            "tracking_numbers": tracking_numbers,
            "amounts": amounts,
            "emails": emails,
            "phones": phones,
        }

        return result

    def _verify_entities(self, db: Session, organization_id: str, result: EntityExtractionResult) -> EntityExtractionResult:
        """
        Cross-checks all extracted IDs against database records scoped strictly by organization_id.
        """
        verified_orders: List[str] = []
        order_ids: List[str] = []
        verified_skus: List[str] = []
        customer_ids: List[str] = []

        # 1. Verify Orders
        for onum in result.order_numbers:
            order = db.query(Order).filter(
                Order.organization_id == organization_id,
                Order.order_number == onum.upper(),
            ).first()
            if order:
                verified_orders.append(onum)
                order_ids.append(str(order.id))
                if str(order.customer_id) not in customer_ids:
                    customer_ids.append(str(order.customer_id))
                if result.order_number and result.order_number.value == onum:
                    result.order_number.db_verified = True
                    result.order_number.db_id = str(order.id)

        # 2. Verify SKUs
        for sku in result.skus:
            prod = db.query(Product).filter(
                Product.organization_id == organization_id,
                Product.sku == sku.upper(),
            ).first()
            if not prod:
                variant = db.query(ProductVariant).filter(
                    ProductVariant.organization_id == organization_id,
                    ProductVariant.sku == sku.upper(),
                ).first()
                if variant:
                    verified_skus.append(sku)
            else:
                verified_skus.append(sku)

            if sku in verified_skus and result.sku and result.sku.value == sku:
                result.sku.db_verified = True
                result.sku.db_id = str(prod.id) if prod else None

        # 3. Verify Tracking
        for tnum in result.tracking_numbers:
            shipment = db.query(Shipment).filter(
                Shipment.organization_id == organization_id,
                Shipment.tracking_number == tnum.upper(),
            ).first()
            if shipment and result.tracking_number and result.tracking_number.value == tnum:
                result.tracking_number.db_verified = True
                result.tracking_number.db_id = str(shipment.id)

        # 4. Verify Customers by Email
        for email in result.emails:
            cust = db.query(Customer).filter(
                Customer.organization_id == organization_id,
                Customer.email == email.lower(),
            ).first()
            if cust and str(cust.id) not in customer_ids:
                customer_ids.append(str(cust.id))
                if not result.customer_id:
                    result.customer_id = ExtractedEntity(value=str(cust.id), raw_text=email, db_verified=True, db_id=str(cust.id))

        result.verified_order_numbers = verified_orders
        result.order_ids = order_ids
        result.verified_skus = verified_skus
        result.customer_ids = customer_ids

        return result
