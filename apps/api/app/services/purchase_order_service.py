from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderService:
    @staticmethod
    def create_po(
        db: Session,
        organization_id: str,
        po_number: str,
        total: float,
        subtotal: float = 0.0,
        tax: float = 0.0,
        currency: str = "INR",
        vendor_id: Optional[str] = None,
        issue_date: Optional[date] = None,
        department: Optional[str] = None,
        status: str = "APPROVED",
        items: Optional[List[Dict[str, Any]]] = None
    ) -> PurchaseOrder:
        po = PurchaseOrder(
            organization_id=organization_id,
            po_number=po_number,
            vendor_id=vendor_id,
            issue_date=issue_date,
            currency=currency,
            subtotal=subtotal,
            tax=tax,
            total=total,
            status=status,
            department=department
        )
        db.add(po)
        db.flush()

        if items:
            for itm in items:
                poi = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    description=itm.get("description", "Item"),
                    quantity=float(itm.get("quantity", 1.0)),
                    unit_price=float(itm.get("unit_price", 0.0)),
                    tax=float(itm.get("tax", 0.0)),
                    total=float(itm.get("total", 0.0))
                )
                db.add(poi)

        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def get_by_id(db: Session, po_id: str, organization_id: str) -> Optional[PurchaseOrder]:
        return db.query(PurchaseOrder).filter(
            PurchaseOrder.id == po_id,
            PurchaseOrder.organization_id == organization_id
        ).first()

    @staticmethod
    def get_by_number(db: Session, po_number: str, organization_id: str) -> Optional[PurchaseOrder]:
        return db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number,
            PurchaseOrder.organization_id == organization_id
        ).first()

    @staticmethod
    def list_pos(db: Session, organization_id: str, limit: int = 100) -> List[PurchaseOrder]:
        return db.query(PurchaseOrder).filter(
            PurchaseOrder.organization_id == organization_id
        ).order_by(PurchaseOrder.created_at.desc()).limit(limit).all()

    @staticmethod
    def match_invoice_to_po(db: Session, organization_id: str, po_number: str, invoice_total: float, tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Validates whether an invoice amount matches an approved PO within tolerance.
        """
        po = PurchaseOrderService.get_by_number(db, po_number, organization_id)
        if not po:
            return {"matched": False, "reason": f"Purchase Order {po_number} not found in system."}

        if po.status != "APPROVED":
            return {"matched": False, "reason": f"PO {po_number} is in status {po.status}, not APPROVED."}

        diff = abs(po.total - invoice_total)
        allowed_diff = po.total * tolerance
        if diff > allowed_diff:
            return {
                "matched": False,
                "reason": f"Amount mismatch: Invoice total {invoice_total} differs from PO amount {po.total} by {diff:.2f}."
            }

        return {"matched": True, "po_id": po.id, "vendor_id": po.vendor_id, "po_total": po.total}
