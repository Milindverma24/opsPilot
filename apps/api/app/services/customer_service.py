from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.operations import Customer


class CustomerService:
    @staticmethod
    def create_customer(
        db: Session,
        organization_id: str,
        name: str,
        customer_number: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        status: str = "ACTIVE"
    ) -> Customer:
        cust = Customer(
            organization_id=organization_id,
            name=name,
            customer_number=customer_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company_name=company_name,
            status=status
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)
        return cust

    @staticmethod
    def get_by_id(db: Session, customer_id: str, organization_id: str) -> Optional[Customer]:
        return db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id
        ).first()

    @staticmethod
    def list_customers(db: Session, organization_id: str, limit: int = 100) -> List[Customer]:
        return db.query(Customer).filter(
            Customer.organization_id == organization_id
        ).limit(limit).all()
