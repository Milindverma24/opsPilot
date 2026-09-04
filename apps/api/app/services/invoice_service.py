from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import Invoice, InvoiceLineItem


class InvoiceService:
    @staticmethod
    def create_invoice(
        db: Session,
        organization_id: str,
        invoice_number: str,
        total: float,
        subtotal: float = 0.0,
        tax: float = 0.0,
        currency: str = "INR",
        vendor_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        purchase_order_number: Optional[str] = None,
        document_id: Optional[str] = None,
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None,
        payment_terms: Optional[str] = None,
        status: str = "RECEIVED",
        risk_level: str = "LOW",
        risk_score: float = 0.0,
        ai_confidence: float = 1.0,
        bank_details: Optional[Dict[str, Any]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None
    ) -> Invoice:
        inv = Invoice(
            organization_id=organization_id,
            invoice_number=invoice_number,
            total=total,
            subtotal=subtotal,
            tax=tax,
            currency=currency,
            vendor_id=vendor_id,
            purchase_order_id=purchase_order_id,
            purchase_order_number=purchase_order_number,
            document_id=document_id,
            invoice_date=invoice_date,
            due_date=due_date,
            payment_terms=payment_terms,
            status=status,
            risk_level=risk_level,
            risk_score=risk_score,
            ai_confidence=ai_confidence,
            bank_details=bank_details or {}
        )
        db.add(inv)
        db.flush()

        if line_items:
            for item in line_items:
                li = InvoiceLineItem(
                    invoice_id=inv.id,
                    description=item.get("description", "Item"),
                    quantity=float(item.get("quantity", 1.0)),
                    unit_price=float(item.get("unit_price", 0.0)),
                    tax=float(item.get("tax", 0.0)),
                    total=float(item.get("total", 0.0))
                )
                db.add(li)

        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def get_by_id(db: Session, invoice_id: str, organization_id: str) -> Optional[Invoice]:
        return db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.organization_id == organization_id
        ).first()

    @staticmethod
    def get_by_number(db: Session, invoice_number: str, organization_id: str) -> Optional[Invoice]:
        return db.query(Invoice).filter(
            Invoice.invoice_number == invoice_number,
            Invoice.organization_id == organization_id
        ).first()

    @staticmethod
    def is_duplicate(db: Session, invoice_number: str, organization_id: str) -> bool:
        return db.query(Invoice).filter(
            Invoice.invoice_number == invoice_number,
            Invoice.organization_id == organization_id
        ).count() > 0

    @staticmethod
    def list_invoices(db: Session, organization_id: str, limit: int = 100) -> List[Invoice]:
        return db.query(Invoice).filter(
            Invoice.organization_id == organization_id
        ).order_by(Invoice.created_at.desc()).limit(limit).all()
