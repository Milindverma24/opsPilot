from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User, Organization
from apps.api.app.services.authorization_service import require_permission

router = APIRouter(prefix="/organization", tags=["Organization"])


class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    email_domain: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


@router.get("")
def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve current tenant organization profile."""
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "industry": org.industry,
        "description": org.description,
        "website_url": org.website_url,
        "email_domain": org.email_domain,
        "country": org.country,
        "timezone": org.timezone,
        "currency": org.currency,
        "status": org.status,
        "settings": org.settings,
        "created_at": org.created_at.isoformat() if org.created_at else None
    }


@router.put("")
def update_current_organization(
    payload: UpdateOrganizationRequest,
    current_user: User = Depends(require_permission("organization.update")),
    db: Session = Depends(get_db)
):
    """Update current tenant settings. Restricted to organization administrators."""
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    if payload.name:
        org.name = payload.name
    if payload.industry:
        org.industry = payload.industry
    if payload.description is not None:
        org.description = payload.description
    if payload.website_url is not None:
        org.website_url = payload.website_url
    if payload.email_domain is not None:
        org.email_domain = payload.email_domain
    if payload.country:
        org.country = payload.country
    if payload.timezone:
        org.timezone = payload.timezone
    if payload.currency:
        org.currency = payload.currency
    if payload.settings is not None:
        org.settings = payload.settings

    db.commit()
    db.refresh(org)
    return {"status": "success", "message": "Organization settings updated successfully."}
