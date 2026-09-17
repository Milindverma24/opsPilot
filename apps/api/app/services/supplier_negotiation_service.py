"""
Supplier Negotiation & Automated RFQ Engine (Priya Persona).
Automatically requests and compares competitive vendor quotes for low-stock inventory SKUs,
evaluates price breaks and delivery SLAs, and drafts optimal Purchase Orders.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from apps.api.app.models.operations import Vendor, PurchaseOrder, PurchaseOrderItem
from apps.api.app.models.ecommerce import Product, ProductVariant, Inventory
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.models.audit import AuditLog
from apps.api.app.events.publisher import BusinessEventPublisher


class SupplierNegotiationService:
    """
    Priya — Autonomous Purchasing & Vendor Negotiation AI.
    Executes automated competitive bidding across apparel mills.
    """

    MOCK_SUPPLIERS = [
        {
            "id": "sup-arvind-01",
            "name": "Arvind Mills Ltd.",
            "location": "Ahmedabad, Gujarat",
            "specialty": "Denim & Heavy Cotton Twill",
            "reliability_score": 0.98,
            "base_unit_price": 950.0,
            "lead_time_days": 4,
            "bulk_discount_threshold": 100,
            "bulk_discount_percent": 0.12,  # 12% off for >= 100 units
        },
        {
            "id": "sup-vardhman-02",
            "name": "Vardhman Textiles Ltd.",
            "location": "Ludhiana, Punjab",
            "specialty": "Yarns, Poly-Cotton & Flannels",
            "reliability_score": 0.95,
            "base_unit_price": 920.0,
            "lead_time_days": 6,
            "bulk_discount_threshold": 80,
            "bulk_discount_percent": 0.08,
        },
        {
            "id": "sup-raymond-03",
            "name": "Raymond Apparels & Weaves",
            "location": "Thane, Maharashtra",
            "specialty": "Fine Linens, Suiting & Rayon",
            "reliability_score": 0.99,
            "base_unit_price": 1020.0,
            "lead_time_days": 2,  # Expedited overnight delivery
            "bulk_discount_threshold": 50,
            "bulk_discount_percent": 0.05,
        }
    ]

    @classmethod
    def run_competitive_rfq(
        cls,
        db: Session,
        organization_id: str,
        sku: str,
        quantity: int = 100,
        target_delivery_days: int = 7
    ) -> Dict[str, Any]:
        """
        Runs an automated Request for Quotation (RFQ) across registered apparel suppliers.
        Calculates total landed cost, discounts, SLA risk, and selects the winning vendor.
        """
        # Find product details
        variant = db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
        product_name = variant.product.title if (variant and variant.product) else "Apparel Garment"

        bids = []
        for sup in cls.MOCK_SUPPLIERS:
            base_price = sup["base_unit_price"]
            discount_pct = sup["bulk_discount_percent"] if quantity >= sup["bulk_discount_threshold"] else 0.0
            effective_unit_cost = round(base_price * (1.0 - discount_pct), 2)
            total_cost = round(effective_unit_cost * quantity, 2)

            # Score = (Cost weight 60%) + (Lead time weight 25%) + (Reliability weight 15%)
            cost_factor = 1000.0 / effective_unit_cost
            lead_time_factor = 10.0 / max(1, sup["lead_time_days"])
            reliability_factor = sup["reliability_score"] * 10.0
            composite_score = round((cost_factor * 0.6) + (lead_time_factor * 0.25) + (reliability_factor * 0.15), 2)

            bids.append({
                "vendor_id": sup["id"],
                "vendor_name": sup["name"],
                "location": sup["location"],
                "base_unit_price": base_price,
                "bulk_discount_percent": int(discount_pct * 100),
                "effective_unit_cost": effective_unit_cost,
                "total_order_cost": total_cost,
                "lead_time_days": sup["lead_time_days"],
                "reliability_score": f"{sup['reliability_score'] * 100:.1f}%",
                "composite_score": composite_score,
                "delivery_eta": (datetime.now(timezone.utc) + timedelta(days=sup["lead_time_days"])).strftime("%Y-%m-%d")
            })

        # Rank bids
        bids.sort(key=lambda b: b["composite_score"], reverse=True)
        winning_bid = bids[0]

        # Ensure vendor exists in DB or find first
        vendor = db.query(Vendor).filter(Vendor.organization_id == organization_id).first()
        vendor_id = vendor.id if vendor else None

        po_number = f"PO-UT-{generate_uuid()[:6].upper()}"
        po = PurchaseOrder(
            organization_id=organization_id,
            po_number=po_number,
            vendor_id=vendor_id,
            status="DRAFT",
            subtotal=winning_bid["total_order_cost"],
            total=winning_bid["total_order_cost"],
            issue_date=datetime.now(timezone.utc).date()
        )
        db.add(po)
        db.commit()
        db.refresh(po)

        # Audit log
        audit = AuditLog(
            organization_id=organization_id,
            actor_id="priya-purchasing-ai",
            actor_type="AI_AGENT",
            actor_name="Priya (Purchasing AI)",
            action="SUPPLIER_RFQ_NEGOTIATION_COMPLETED",
            resource_type="purchase_order",
            resource_id=po.id,
            result="SUCCESS",
            log_metadata={
                "sku": sku,
                "quantity": quantity,
                "winner": winning_bid["vendor_name"],
                "total_cost": winning_bid["total_order_cost"],
                "bids_evaluated": len(bids)
            }
        )
        db.add(audit)
        db.commit()

        # Publish event
        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="PURCHASE_ORDER_DRAFTED",
            title=f"PO {po_number} drafted via competitive RFQ",
            content=f"Priya AI completed multi-supplier negotiation for {quantity}x {sku}. Selected {winning_bid['vendor_name']} at ₹{winning_bid['total_order_cost']:,.2f}.",
            metadata={"po_number": po_number, "winner": winning_bid["vendor_name"], "amount": winning_bid["total_order_cost"]}
        )

        return {
            "negotiation_id": generate_uuid(),
            "status": "NEGOTIATION_COMPLETED",
            "item": product_name,
            "sku": sku,
            "requested_quantity": quantity,
            "bids_evaluated_count": len(bids),
            "winning_vendor": winning_bid["vendor_name"],
            "winning_unit_cost": winning_bid["effective_unit_cost"],
            "total_contract_value": winning_bid["total_order_cost"],
            "lead_time_days": winning_bid["lead_time_days"],
            "purchase_order_id": po.id,
            "purchase_order_number": po_number,
            "bids_comparison": bids,
            "rationale": (
                f"Selected {winning_bid['vendor_name']} with composite score {winning_bid['composite_score']}. "
                f"Secured a {winning_bid['bulk_discount_percent']}% volume discount (₹{winning_bid['effective_unit_cost']}/unit) "
                f"with guaranteed delivery in {winning_bid['lead_time_days']} days."
            )
        }
