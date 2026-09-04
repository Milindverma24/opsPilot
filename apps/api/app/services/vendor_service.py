from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import Vendor


class VendorService:
    @staticmethod
    def create_vendor(
        db: Session,
        organization_id: str,
        name: str,
        vendor_code: Optional[str] = None,
        tax_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        status: str = "ACTIVE",
        approved: bool = True,
        risk_level: str = "LOW",
        bank_details: Optional[Dict[str, Any]] = None
    ) -> Vendor:
        vendor = Vendor(
            organization_id=organization_id,
            name=name,
            vendor_code=vendor_code,
            tax_id=tax_id,
            email=email,
            phone=phone,
            address=address,
            status=status,
            approved=approved,
            risk_level=risk_level,
            bank_details=bank_details or {}
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    @staticmethod
    def get_by_id(db: Session, vendor_id: str, organization_id: str) -> Optional[Vendor]:
        return db.query(Vendor).filter(
            Vendor.id == vendor_id,
            Vendor.organization_id == organization_id
        ).first()

    @staticmethod
    def list_vendors(db: Session, organization_id: str, limit: int = 100) -> List[Vendor]:
        return db.query(Vendor).filter(
            Vendor.organization_id == organization_id
        ).limit(limit).all()
