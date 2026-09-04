from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import Complaint


class ComplaintService:
    @staticmethod
    def create_complaint(
        db: Session,
        organization_id: str,
        description: str,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        order_id: Optional[str] = None,
        category: str = "OTHER",
        sentiment: str = "NEUTRAL",
        urgency: str = "MEDIUM",
        priority: str = "P3",
        refund_amount: float = 0.0,
        requested_resolution: Optional[str] = None,
        status: str = "OPEN",
        ai_confidence: float = 1.0,
        source_email_id: Optional[str] = None
    ) -> Complaint:
        comp = Complaint(
            organization_id=organization_id,
            description=description,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            order_id=order_id,
            category=category,
            sentiment=sentiment,
            urgency=urgency,
            priority=priority,
            refund_amount=refund_amount,
            requested_resolution=requested_resolution,
            status=status,
            ai_confidence=ai_confidence,
            source_email_id=source_email_id
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        return comp

    @staticmethod
    def get_by_id(db: Session, complaint_id: str, organization_id: str) -> Optional[Complaint]:
        return db.query(Complaint).filter(
            Complaint.id == complaint_id,
            Complaint.organization_id == organization_id
        ).first()

    @staticmethod
    def list_complaints(db: Session, organization_id: str, limit: int = 100) -> List[Complaint]:
        return db.query(Complaint).filter(
            Complaint.organization_id == organization_id
        ).order_by(Complaint.created_at.desc()).limit(limit).all()
