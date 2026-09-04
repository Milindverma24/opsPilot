from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.tenant import Organization, Department, Team


class OrganizationService:
    @staticmethod
    def create_organization(
        db: Session,
        name: str,
        slug: str,
        industry: Optional[str] = "Technology",
        description: Optional[str] = None,
        website_url: Optional[str] = None,
        email_domain: Optional[str] = None,
        country: str = "India",
        timezone: str = "Asia/Kolkata",
        currency: str = "INR",
        status: str = "ACTIVE",
        settings: Optional[Dict[str, Any]] = None
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug,
            industry=industry,
            description=description,
            website_url=website_url,
            email_domain=email_domain,
            country=country,
            timezone=timezone,
            currency=currency,
            status=status,
            is_active=(status == "ACTIVE"),
            settings=settings or {}
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_by_id(db: Session, organization_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == organization_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug).first()

    @staticmethod
    def create_department(
        db: Session,
        organization_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Department:
        dept = Department(
            organization_id=organization_id,
            name=name,
            description=description
        )
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def list_departments(db: Session, organization_id: str) -> List[Department]:
        return db.query(Department).filter(Department.organization_id == organization_id).all()

    @staticmethod
    def create_team(
        db: Session,
        organization_id: str,
        name: str,
        department_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Team:
        team = Team(
            organization_id=organization_id,
            department_id=department_id,
            name=name,
            description=description
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def list_teams(db: Session, organization_id: str) -> List[Team]:
        return db.query(Team).filter(Team.organization_id == organization_id).all()
